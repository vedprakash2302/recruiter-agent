from fastapi import FastAPI, HTTPException, Depends, status, Request, Query, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, AsyncGenerator
import os
import webbrowser
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import asyncio
import json

# Import the Gmail tools we created earlier
from gmail_tools import GmailService, SCOPES
from tools.extract_tools import get_job_content, process_resume_pdf, get_resume_content, extract_applicant_details
from globalc import global_lock, JOB_DETAILS, CV_DETAILS

# Import LangChain components for Groq (for email improvement)
try:
    from langchain_groq import ChatGroq
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Groq LLM for email improvement
groq_model = None
if GROQ_AVAILABLE:
    try:
        groq_model = ChatGroq(model="llama3-8b-8192")
        logger.info("Groq LLM initialized successfully with model: llama3-8b-8192")
        
        # Email improvement prompt
        email_improvement_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert email editor specializing in recruitment communications.
Your task is to improve existing recruitment emails based on specific user requests while maintaining professionalism and effectiveness.

Focus on:
1. Clarity and readability
2. Professional tone
3. Persuasive language
4. Proper structure
5. Actionable improvements based on the user's request"""),
            ("human", """Please improve the following recruitment email based on this request: "{improvement_request}"

Original Email:
{email_content}

Candidate Context:
{context}

Provide the improved version that addresses the specific improvement request while maintaining the email's effectiveness.""")
        ])
        
        # Create improvement chain
        email_improvement_chain = email_improvement_prompt | groq_model | StrOutputParser()
        
        # Email generation prompt
        email_generation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert recruitment email writer specializing in personalized outreach.
Your task is to create compelling, professional recruitment emails that attract top talent.

Focus on:
1. Professional yet engaging tone
2. Clear value proposition
3. Personalized content based on candidate background
4. Specific job details and company benefits
5. Strong call-to-action
6. Concise but informative structure

Email Structure:
- Subject: Compelling subject line
- Opening: Personal greeting and connection
- Body: Role overview, why they're a great fit, company benefits
- Closing: Clear next steps and contact information"""),
            ("human", """Create a professional recruitment email for the following candidate:

Candidate Information:
- Name: {candidate_name}
- Email: {candidate_email}
- Current Company: {current_company}
- Current Position: {current_position}
- Skills: {skills}

Job Information:
- Job Title: {job_title}
- Company: {job_company}
- Requirements: {job_requirements}
- Benefits: {job_benefits}

Please generate a complete recruitment email that would appeal to this candidate. Make it personalized and compelling.""")
        ])
        
        # Create generation chain
        email_generation_chain = email_generation_prompt | groq_model | StrOutputParser()
        
    except Exception as e:
        logger.error(f"Failed to initialize Groq LLM: {e}")
        groq_model = None
else:
    logger.warning("LangChain Groq not available. Email improvement will be disabled.")

# Initialize FastAPI app
app = FastAPI(
    title="AI Recruiter Agent API",
    description="API for handling recruiter agent operations with Gmail integration and resume processing",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],  # Include Next.js ports and wildcard for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gmail service
gmail_service = GmailService()

# Set up templates
templates = Jinja2Templates(directory="templates")

# Mount static files
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Startup event to check authentication and prompt OAuth if needed
@app.on_event("startup")
async def startup_event():
    """Check authentication on startup and prompt OAuth if needed."""
    try:
        if not gmail_service.is_authenticated():
            print("\n🔐 Gmail authentication required!")
            print("Opening browser for OAuth authentication...")
            print("\n⚠️  IMPORTANT: If you see 'Access blocked' error:")
            print("   1. Go to Google Cloud Console (https://console.cloud.google.com)")
            print("   2. Navigate to APIs & Services > OAuth consent screen")
            print("   3. Add your email as a test user in the 'Test users' section")
            print("   4. OR publish the app (make it external)")
            print("   5. Try authentication again")
            print("\n🔧 Alternatively, you can:")
            print("   - Use a Google Workspace account (if available)")
            print("   - Contact the app developer to add you as a test user")
            
            auth_url = gmail_service.get_auth_url()
            webbrowser.open(auth_url)
            print(f"\n🌐 OAuth URL: {auth_url}")
            print("📧 After authentication, return to this terminal.")
        else:
            print("✅ Gmail authentication already configured!")
    except Exception as e:
        print(f"⚠️ OAuth setup error: {e}")
        print("Please ensure credentials.json is properly configured.")
        print("\n🔧 Google Cloud Console setup required:")
        print("   1. Enable Gmail API")
        print("   2. Create OAuth 2.0 credentials")
        print("   3. Configure OAuth consent screen")
        print("   4. Add test users or publish the app")

# Request/Response Models
class EmailRequest(BaseModel):
    to: str
    subject: str
    message: str
    sender: str = "me"

class EmailResponse(BaseModel):
    message_id: str
    status: str = "success"

class SearchQuery(BaseModel):
    query: str = "is:inbox"
    max_results: int = 10

class FileUploadResponse(BaseModel):
    filename: str
    content_type: str
    link: str
    upload_time: str
    status: str = "success"

# Resume processing models
class ResumeProcessRequest(BaseModel):
    url: str  # Job description URL
    filename: str  # Resume filename including extension

class ProcessingResult(BaseModel):
    success: bool
    message: str
    job_url: str
    resume_filename: str
    analysis: Optional[dict] = None
    error: Optional[str] = None

# Authentication status check
class AuthStatus(BaseModel):
    authenticated: bool
    auth_url: Optional[str] = None

# Email improvement models
class EmailImprovementRequest(BaseModel):
    email_content: str
    improvement_request: str
    context: Optional[dict] = {}

# Email generation models
class EmailGenerationRequest(BaseModel):
    candidate_name: str
    candidate_email: str
    current_company: Optional[str] = ""
    current_position: Optional[str] = ""
    skills: Optional[List[str]] = []
    job_title: str
    job_company: str
    job_requirements: Optional[List[str]] = []
    job_benefits: Optional[List[str]] = []

# Root endpoint - automatically redirects to OAuth if not authenticated
@app.get("/", response_class=HTMLResponse)
async def root(request: Request, auth_complete: bool = Query(False)):
    """Root endpoint that automatically prompts for Gmail OAuth if not authenticated."""
    is_authenticated = gmail_service.is_authenticated()
    
    # If not authenticated and this isn't a post-auth callback, redirect to OAuth
    if not is_authenticated and not auth_complete:
        try:
            auth_url = gmail_service.get_auth_url()
            return RedirectResponse(url=auth_url, status_code=302)
        except Exception as e:
            # If we can't get auth URL, show error page with manual link
            return templates.TemplateResponse(
                "index.html",
                {
                    "request": request,
                    "authenticated": False,
                    "auth_url": None,
                    "error": f"OAuth setup error: {str(e)}. Please ensure credentials.json is properly configured."
                }
            )
    
    # Show the template (either authenticated or post-auth)
    auth_url = None
    if not is_authenticated:
        try:
            auth_url = gmail_service.get_auth_url()
        except Exception as e:
            pass
    
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "authenticated": is_authenticated, "auth_url": auth_url}
    )

# Auth status endpoint
@app.get("/auth/status", response_model=AuthStatus)
async def auth_status():
    """Check if the user is authenticated with Gmail API."""
    is_authenticated = gmail_service.is_authenticated()
    auth_url = None
    
    if not is_authenticated:
        try:
            auth_url = gmail_service.get_auth_url()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting auth URL: {str(e)}"
            )
    
    return {"authenticated": is_authenticated, "auth_url": auth_url}

# OAuth2 callback endpoint
@app.get("/oauth2callback")
async def oauth2_callback(code: str = Query(...)):
    """Handle OAuth2 callback from Google."""
    try:
        gmail_service.fetch_token(code)
        # Redirect back to root with auth_complete flag to prevent redirect loop
        return RedirectResponse(url="/?auth_complete=true")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error authenticating: {str(e)}"
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Send email endpoint
@app.post("/send-email/", response_model=EmailResponse)
async def send_email(email: EmailRequest):
    """
    Send an email using Gmail API
    """
    try:
        message = gmail_service.create_message(
            sender=email.sender,
            to=email.to,
            subject=email.subject,
            message_text=email.message
        )
        result = gmail_service.send_message('me', message)
        return {
            "message_id": result["id"],
            "status": "sent"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )

# Search emails endpoint
@app.post("/search-emails/")
async def search_emails(search: SearchQuery):
    """
    Search emails based on query
    """
    try:
        messages = gmail_service.list_messages(
            query=search.query,
            max_results=search.max_results
        )
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search emails: {str(e)}"
        )

# Get email details endpoint
@app.get("/emails/{email_id}")
async def get_email(email_id: str):
    """
    Get details of a specific email
    """
    try:
        message = gmail_service.get_message('me', email_id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email not found"
            )
        return message
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve email: {str(e)}"
        )

# Get email thread history
@app.get("/emails/thread/{email_id}")
async def get_email_thread(email_id: str):
    """
    Get the complete thread history for a specific email
    
    Args:
        email_id: The ID of any email in the thread
        
    Returns:
        List of messages in the thread, sorted chronologically (oldest first)
    """
    try:
        # First get the email to get its thread ID
        email = gmail_service.get_message('me', email_id)
        if not email or 'thread_id' not in email:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email not found or invalid thread ID"
            )
        
        # Get all messages in the thread
        thread_messages = gmail_service.get_thread_messages('me', email['thread_id'])
        
        if not thread_messages:
            return {"message": "No messages found in thread", "thread_id": email['thread_id']}
            
        # Sort messages by date (oldest first)
        thread_messages.sort(key=lambda x: x.get('date', ''))
        
        return {
            "thread_id": email['thread_id'],
            "messages": thread_messages
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve email thread: {str(e)}"
        )

# Handle file upload with link
@app.post("/upload/")
async def upload_file(
    file: UploadFile = File(...),
    link: str = Form(...)
):
    """
    Handle file upload with an associated link.
    
    Args:
        file: The uploaded PDF file
        link: A string link associated with the file
        
    Returns:
        Details about the uploaded file, link, and extracted information
    """
    # Check if the file is a PDF
    if file.content_type != 'application/pdf':
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )
    
    try:
        # Ensure resumes directory exists
        resumes_dir = Path("resumes")
        resumes_dir.mkdir(exist_ok=True)
        
        # Save the uploaded file to resumes directory
        file_path = resumes_dir / file.filename
        
        # Read and write the file content
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"File saved to: {file_path}")
        
        # Process job content and resume
        job_processing_result = get_job_content(link)
        resume_processing_result = process_resume_pdf(file.filename)
        
        # Get the extracted details from global variables
        with global_lock:
            job_details = dict(JOB_DETAILS)
            cv_details = dict(CV_DETAILS)
            logger.info(f"Job details extracted: {job_details}")
            logger.info(f"CV details extracted: {cv_details}")
        
        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "link": link,
            "upload_time": datetime.now().isoformat(),
            "status": f"File uploaded successfully to resumes/{file.filename}",
            "extracted_data": {
                "applicant_details": cv_details,
                "job_details": job_details
            },
            "processing_results": {
                "job_processing": job_processing_result,
                "resume_processing": resume_processing_result
            }
        }
        
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file: {str(e)}"
        )

# Email improvement endpoint (original - non-streaming)
@app.post("/improve")
async def improve_email(request: EmailImprovementRequest):
    """
    Improve an existing email using Groq AI
    """
    if not GROQ_AVAILABLE or groq_model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email improvement service not available. Groq LLM not initialized."
        )
    
    logger.info(f"Email improvement requested: {request.improvement_request[:50]}...")
    
    try:
        # Validate input
        if not request.email_content.strip():
            raise HTTPException(status_code=400, detail="Email content cannot be empty")
        
        if not request.improvement_request.strip():
            raise HTTPException(status_code=400, detail="Improvement request cannot be empty")
        
        # Prepare context string
        context_str = ""
        if request.context:
            if 'candidate_info' in request.context:
                candidate = request.context['candidate_info']
                context_str += f"Candidate: {candidate.get('name', 'Unknown')} at {candidate.get('currentCompany', 'Unknown Company')}\n"
                context_str += f"Skills: {', '.join(candidate.get('skills', []))}\n"
            
            if 'job_info' in request.context:
                job = request.context['job_info']
                context_str += f"Job: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown Company')}\n"
        
        chain_input = {
            "improvement_request": request.improvement_request,
            "email_content": request.email_content,
            "context": context_str if context_str else "No additional context provided"
        }
        
        logger.info("Invoking Groq LLM for email improvement")
        
        # Improve the email content
        improved_content = await asyncio.to_thread(
            email_improvement_chain.invoke,
            chain_input
        )
        
        logger.info("Email improvement completed successfully")
        
        response = {
            "improved_content": improved_content,
            "improvement_request": request.improvement_request,
            "improved_at": datetime.now().isoformat(),
            "original_length": len(request.email_content),
            "improved_length": len(improved_content)
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to improve email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to improve email: {str(e)}")

# Streaming email improvement endpoint
@app.post("/improve/stream")
async def improve_email_stream(request: EmailImprovementRequest):
    """
    Improve an existing email using Groq AI with real-time streaming
    """
    if not GROQ_AVAILABLE or groq_model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email improvement service not available. Groq LLM not initialized."
        )
    
    logger.info(f"Streaming email improvement requested: {request.improvement_request[:50]}...")
    
    # Validate input
    if not request.email_content.strip():
        raise HTTPException(status_code=400, detail="Email content cannot be empty")
    
    if not request.improvement_request.strip():
        raise HTTPException(status_code=400, detail="Improvement request cannot be empty")
    
    async def generate_streaming_response() -> AsyncGenerator[str, None]:
        try:
            # Prepare context string
            context_str = ""
            if request.context:
                if 'candidate_info' in request.context:
                    candidate = request.context['candidate_info']
                    context_str += f"Candidate: {candidate.get('name', 'Unknown')} at {candidate.get('currentCompany', 'Unknown Company')}\n"
                    context_str += f"Skills: {', '.join(candidate.get('skills', []))}\n"
                
                if 'job_info' in request.context:
                    job = request.context['job_info']
                    context_str += f"Job: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown Company')}\n"
            
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Starting email improvement...', 'timestamp': datetime.now().isoformat()})}\n\n"
            
            # Create streaming chain
            chain_input = {
                "improvement_request": request.improvement_request,
                "email_content": request.email_content,
                "context": context_str if context_str else "No additional context provided"
            }
            
            logger.info("Invoking Groq LLM for streaming email improvement")
            
            # Send processing status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Processing with Groq AI...', 'timestamp': datetime.now().isoformat()})}\n\n"
            
            accumulated_content = ""
            
            # Stream the response from Groq
            try:
                # For streaming, we need to use the streaming capabilities of Groq
                stream = await asyncio.to_thread(
                    lambda: groq_model.stream(email_improvement_prompt.format_prompt(**chain_input).to_messages())
                )
                
                for chunk in stream:
                    if hasattr(chunk, 'content') and chunk.content:
                        accumulated_content += chunk.content
                        chunk_data = {
                            'type': 'chunk',
                            'content': chunk.content,
                            'accumulated': accumulated_content,
                            'timestamp': datetime.now().isoformat()
                        }
                        yield f"data: {json.dumps(chunk_data)}\n\n"
                        
                        # Small delay to make streaming visible
                        await asyncio.sleep(0.05)
            
            except Exception as e:
                # Fallback to non-streaming if streaming fails
                logger.warning(f"Streaming failed, falling back to standard mode: {e}")
                
                improved_content = await asyncio.to_thread(
                    email_improvement_chain.invoke,
                    chain_input
                )
                
                # Simulate streaming by sending content in chunks
                words = improved_content.split()
                accumulated_content = ""
                
                for i, word in enumerate(words):
                    accumulated_content += word
                    if i < len(words) - 1:
                        accumulated_content += " "
                    
                    chunk_data = {
                        'type': 'chunk',
                        'content': word + (" " if i < len(words) - 1 else ""),
                        'accumulated': accumulated_content,
                        'timestamp': datetime.now().isoformat()
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                    
                    # Small delay for typing effect
                    await asyncio.sleep(0.1)
            
            # Send completion
            completion_data = {
                'type': 'complete',
                'final_content': accumulated_content,
                'improvement_request': request.improvement_request,
                'original_length': len(request.email_content),
                'improved_length': len(accumulated_content),
                'completed_at': datetime.now().isoformat()
            }
            yield f"data: {json.dumps(completion_data)}\n\n"
            
            logger.info("Streaming email improvement completed successfully")
            
        except Exception as e:
            logger.error(f"Streaming email improvement failed: {str(e)}")
            error_data = {
                'type': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_streaming_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

# Email generation endpoint
@app.post("/api/email/generate")
async def generate_email(request: EmailGenerationRequest):
    """
    Generate a new recruitment email using Groq AI
    """
    if not GROQ_AVAILABLE or groq_model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email generation service not available. Groq LLM not initialized."
        )
    
    logger.info(f"Email generation requested for candidate: {request.candidate_name}")
    
    try:
        # Validate required inputs
        if not request.candidate_name.strip():
            raise HTTPException(status_code=400, detail="Candidate name is required")
        
        if not request.job_title.strip():
            raise HTTPException(status_code=400, detail="Job title is required")
        
        if not request.job_company.strip():
            raise HTTPException(status_code=400, detail="Job company is required")
        
        # Prepare input data for the prompt
        skills_str = ", ".join(request.skills) if request.skills else "Not specified"
        requirements_str = ", ".join(request.job_requirements) if request.job_requirements else "Not specified"
        benefits_str = ", ".join(request.job_benefits) if request.job_benefits else "Not specified"
        
        chain_input = {
            "candidate_name": request.candidate_name,
            "candidate_email": request.candidate_email,
            "current_company": request.current_company or "Not specified",
            "current_position": request.current_position or "Not specified",
            "skills": skills_str,
            "job_title": request.job_title,
            "job_company": request.job_company,
            "job_requirements": requirements_str,
            "job_benefits": benefits_str
        }
        
        logger.info("Invoking Groq LLM for email generation")
        
        # Generate the email content
        generated_content = await asyncio.to_thread(
            email_generation_chain.invoke,
            chain_input
        )
        
        logger.info("Email generation completed successfully")
        
        # Extract subject line from generated content (assume first line is subject)
        lines = generated_content.strip().split('\n')
        subject_line = ""
        email_content = generated_content
        
        # Try to extract subject if it's formatted properly
        for i, line in enumerate(lines):
            if line.lower().startswith('subject:'):
                subject_line = line.replace('Subject:', '').replace('subject:', '').strip()
                # Remove the subject line from content and rejoin
                email_content = '\n'.join(lines[:i] + lines[i+1:]).strip()
                break
        
        # If no explicit subject found, generate a default one
        if not subject_line:
            subject_line = f"Exciting {request.job_title} Opportunity at {request.job_company}"
        
        response = {
            "email_content": email_content,
            "subject": subject_line,
            "generated_at": datetime.now().isoformat()
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate email: {str(e)}")

# Get messages by email address
@app.get("/emails/search")
async def search_emails_by_address(
    email: str = Query(..., description="Email address to search for (from or to)"),
    max_results: int = Query(10, description="Maximum number of messages to return", le=50)
):
    """
    Get messages by email address (from or to)
    
    Args:
        email: Email address to search for (e.g., example@gmail.com)
        max_results: Maximum number of messages to return (default: 10, max: 50)
        
    Returns:
        List of messages involving the specified email, sorted by date (newest first)
    """
    try:
        # Basic email validation
        if '@' not in email or '.' not in email.split('@')[-1]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please provide a valid email address"
            )
            
        messages = gmail_service.get_messages_by_email(email, max_results)
        
        if not messages:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "email": email,
                    "message": "No messages found with this email address",
                    "suggestions": [
                        "Check if the email address is correct",
                        "Try with a different email address",
                        "Make sure you have the necessary Gmail permissions"
                    ]
                }
            )
            
        return {
            "email": email,
            "total_messages": len(messages),
            "messages": messages
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to search messages",
                "details": str(e),
                "email": email
            }
        )

# Resume processing endpoints
@app.post("/api/process-resume", response_model=ProcessingResult)
async def process_resume(request: ResumeProcessRequest):
    """
    Process uploaded resume against job description
    
    This endpoint receives:
    - url: plaintext URL of job description
    - filename: plaintext filename including extension (e.g., my_awesome_resume.pdf)
    
    The file should already be uploaded to the resumes/ directory
    """
    try:
        logger.info(f"Processing resume: {request.filename} for job: {request.url}")
        
        # Validate inputs
        if not request.url.strip():
            raise HTTPException(status_code=400, detail="Job URL is required")
        
        if not request.filename.strip():
            raise HTTPException(status_code=400, detail="Resume filename is required")
        
        # Check if resume file exists
        resumes_dir = Path("resumes")
        resume_path = resumes_dir / request.filename
        
        if not resume_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Resume file not found: {request.filename}"
            )
        
        # Here you would integrate with your AI processing logic
        # For now, we'll simulate the processing
        
        analysis_result = await analyze_resume_against_job(
            resume_path=str(resume_path),
            job_url=request.url
        )
        
        return ProcessingResult(
            success=True,
            message="Resume processed successfully",
            job_url=request.url,
            resume_filename=request.filename,
            analysis=analysis_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing resume: {str(e)}")
        return ProcessingResult(
            success=False,
            message="Processing failed",
            job_url=request.url,
            resume_filename=request.filename,
            error=str(e)
        )

async def analyze_resume_against_job(resume_path: str, job_url: str) -> dict:
    """
    Analyze resume against job description
    
    This function would integrate with your AI models to:
    1. Extract text from PDF resume
    2. Fetch and parse job description from URL
    3. Perform matching analysis
    4. Generate recommendations
    
    For now, returning a mock analysis
    """
    
    # Mock analysis - replace with actual AI processing
    analysis = {
        "resume_path": resume_path,
        "job_url": job_url,
        "match_score": 85,
        "strengths": [
            "Strong technical skills alignment",
            "Relevant industry experience",
            "Good educational background"
        ],
        "recommendations": [
            "Highlight specific achievements with metrics",
            "Emphasize remote work experience",
            "Add relevant certifications"
        ],
        "missing_skills": [
            "Cloud platforms experience",
            "Agile methodology",
            "Team leadership"
        ],
        "cover_letter_suggestions": [
            "Mention specific interest in company mission",
            "Reference recent company achievements",
            "Connect personal experience to role requirements"
        ]
    }
    
    logger.info(f"Analysis completed with match score: {analysis['match_score']}%")
    return analysis

@app.get("/api/health")
async def api_health_check():
    """Detailed health check for API functionality"""
    resumes_dir = Path("resumes")
    return {
        "status": "healthy",
        "resumes_directory_exists": resumes_dir.exists(),
        "resumes_directory_path": str(resumes_dir.absolute()),
        "resume_count": len(list(resumes_dir.glob("*.pdf"))) if resumes_dir.exists() else 0,
        "gmail_authenticated": gmail_service.is_authenticated()
    }

@app.get("/api/resumes")
async def list_resumes():
    """List all uploaded resumes"""
    resumes_dir = Path("resumes")
    
    if not resumes_dir.exists():
        return {"resumes": [], "count": 0}
    
    resumes = []
    for resume_file in resumes_dir.glob("*.pdf"):
        stat = resume_file.stat()
        resumes.append({
            "filename": resume_file.name,
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime
        })
    
    return {
        "resumes": sorted(resumes, key=lambda x: x["created"], reverse=True),
        "count": len(resumes)
    }

# Analyse resume endpoint
@app.post("/analyse")
async def analyse_resume(filename: str = Form(...)):
    """
    Analyse a resume PDF file that has already been uploaded.
    
    Args:
        filename: The filename of the uploaded resume (should be in resumes/ folder)
        
    Returns:
        Structured applicant information extracted from the resume
    """
    try:
        logger.info(f"Analysing resume: {filename}")
        
        # Validate filename
        if not filename.strip():
            raise HTTPException(status_code=400, detail="Filename is required")
        
        # Check if resume file exists
        resumes_dir = Path("resumes")
        resume_path = resumes_dir / filename
        
        if not resume_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Resume file not found: {filename}"
            )
        
        # Extract text from PDF using existing tools
        logger.info(f"Extracting text from: {resume_path}")
        docs = get_resume_content(str(resume_path))
        
        if not docs:
            raise HTTPException(
                status_code=400,
                detail="Failed to extract text from PDF"
            )
        
        # Combine all pages into a single text
        resume_text = "\n\n".join(doc.page_content for doc in docs)
        logger.info(f"Extracted {len(resume_text)} characters from resume")
        
        # Extract structured information using Groq LLM
        logger.info("Calling extract_applicant_details...")
        applicant_details = extract_applicant_details(resume_text)
        
        logger.info(f"Analysis completed successfully: {applicant_details}")
        
        return {
            "success": True,
            "filename": filename,
            "applicant_details": applicant_details,
            "analysis_timestamp": datetime.now().isoformat(),
            "message": f"Resume analysis completed successfully for {filename}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analysing resume {filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyse resume: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    
    # Create resumes directory if it doesn't exist
    resumes_dir = Path("resumes")
    resumes_dir.mkdir(exist_ok=True)
    
    logger.info("Starting AI Recruiter Agent Server...")
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

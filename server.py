from fastapi import FastAPI, HTTPException, Depends, status, Request, Query, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
import os
import webbrowser
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Import the Gmail tools we created earlier
from gmail_tools import GmailService, SCOPES
from tools.extract_tools import get_job_content, process_resume_pdf
from globalc import global_lock, JOB_DETAILS, CV_DETAILS

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
@app.post("/upload/", response_model=FileUploadResponse)
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
        Details about the uploaded file and link
    """
    # Check if the file is a PDF
    if file.content_type != 'application/pdf':
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )
    
    get_job_content(link)
    process_resume_pdf(file.filename)
    with global_lock:
        job_details = JOB_DETAILS
        print(job_details)
        cv_details = CV_DETAILS
        print(cv_details)
    # Here you would typically save the file to disk or process it
    # For now, we'll just return the file info and link

    # resume_content = process_resume_pdf(file.filename)    
    
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "link": link,
        "upload_time": datetime.now().isoformat(),
        "status": "File uploaded successfully"
    }

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

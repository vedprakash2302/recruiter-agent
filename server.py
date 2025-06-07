from fastapi import FastAPI, HTTPException, Depends, status, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import os
import logging
from pathlib import Path

# Import the Gmail tools we created earlier
from gmail_tools import GmailService, SCOPES

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

# Authentication status check
class AuthStatus(BaseModel):
    authenticated: bool
    auth_url: Optional[str] = None

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

# Root endpoint - redirects to auth status
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint that shows authentication status and provides login link if needed."""
    is_authenticated = gmail_service.is_authenticated()
    auth_url = None
    
    if not is_authenticated:
        try:
            auth_url = gmail_service.get_auth_url()
        except Exception as e:
            return f"Error getting auth URL: {str(e)}"
    
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
        return RedirectResponse(url="/")
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

from fastapi import FastAPI, HTTPException, Depends, status, Request, Query, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
import os
from datetime import datetime
from dotenv import load_dotenv

# Import the Gmail tools we created earlier
from gmail_tools import GmailService, SCOPES
from tools.extract_tools import get_job_content,process_resume_pdf
from globalc import global_lock, JOB_DETAILS, CV_DETAILS

load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Recruiter Agent API",
    description="API for handling recruiter agent operations",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize FastAPI app and Gmail service
app = FastAPI(
    title="Recruiter Agent API",
    description="API for handling recruiter agent operations with Gmail integration",
    version="1.0.0"
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

class FileUploadResponse(BaseModel):
    filename: str
    content_type: str
    link: str
    upload_time: str
    status: str = "success"

# Authentication status check
class AuthStatus(BaseModel):
    authenticated: bool
    auth_url: Optional[str] = None

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

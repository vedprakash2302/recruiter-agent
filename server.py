from fastapi import FastAPI, HTTPException, Depends, status, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import os

# Import the Gmail tools we created earlier
from gmail_tools import GmailService, SCOPES

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

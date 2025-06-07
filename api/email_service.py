from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
import asyncio
from datetime import datetime, timedelta
import uuid
import os
import logging
from dotenv import load_dotenv

# Import LangChain components for Groq
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Recruiter Email Service",
    description="FastAPI service with Groq-powered email generation and improvement",
    version="1.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Groq LLM
try:
    model = ChatGroq(model="llama3-8b-8192")
    logger.info("Groq LLM initialized successfully with model: llama3-8b-8192")
except Exception as e:
    logger.error(f"Failed to initialize Groq LLM: {e}")
    raise

# Email generation prompt
email_generation_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a professional recruiter AI assistant specializing in writing compelling recruitment emails. 

Your task is to create personalized, professional recruitment emails that:
1. Are engaging and conversational yet professional
2. Highlight relevant candidate skills and experience
3. Present the job opportunity clearly and attractively
4. Include specific benefits and role details
5. Have a clear call-to-action
6. Are personalized to the candidate's background

Always write in a warm, human tone while maintaining professionalism."""),
    ("human", """Please draft a recruitment email with the following details:

Candidate Information:
- Name: {candidate_name}
- Email: {candidate_email}
- Current Company: {current_company}
- Current Position: {current_position}
- Skills: {skills}

Job Information:
- Title: {job_title}
- Company: {job_company}
- Requirements: {job_requirements}
- Benefits: {job_benefits}

Create a compelling email that would interest this candidate in the opportunity.""")
])

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

# Create chains
email_generation_chain = email_generation_prompt | model | StrOutputParser()
email_improvement_chain = email_improvement_prompt | model | StrOutputParser()

# Store pending email approvals and sent emails
pending_approvals: Dict[str, dict] = {}
sent_emails: Dict[str, dict] = {}
email_threads: Dict[str, list] = {}

# Pydantic models
class EmailGenerationRequest(BaseModel):
    candidate_name: str
    candidate_email: str
    current_company: Optional[str] = ""
    current_position: Optional[str] = ""
    skills: List[str] = []
    job_title: str
    job_company: str
    job_requirements: List[str] = []
    job_benefits: List[str] = []

class EmailImprovementRequest(BaseModel):
    email_content: str
    improvement_request: str
    context: Optional[dict] = {}

class EmailRequest(BaseModel):
    id: str
    to: str
    subject: str
    content: str
    metadata: Optional[dict] = None

class ApprovalResponse(BaseModel):
    approved: bool
    id: str

class EmailSendRequest(BaseModel):
    id: Optional[str] = None
    to: str
    subject: str
    content: str
    metadata: Optional[dict] = None

# Helper functions
def generate_subject_line(job_title: str, job_company: str, candidate_name: str) -> str:
    """Generate an appropriate subject line for the recruitment email"""
    return f"Exciting {job_title} Opportunity at {job_company} - {candidate_name}"

def format_list_for_prompt(items: List[str]) -> str:
    """Format a list of items for use in prompts"""
    if not items:
        return "Not specified"
    return ", ".join(items)

# API Endpoints

@app.post("/api/email/generate")
async def generate_email(request: EmailGenerationRequest):
    """Generate a recruitment email using Groq AI"""
    try:
        # Prepare the input for the chain
        chain_input = {
            "candidate_name": request.candidate_name,
            "candidate_email": request.candidate_email,
            "current_company": request.current_company or "their current company",
            "current_position": request.current_position or "their current role",
            "skills": format_list_for_prompt(request.skills),
            "job_title": request.job_title,
            "job_company": request.job_company,
            "job_requirements": format_list_for_prompt(request.job_requirements),
            "job_benefits": format_list_for_prompt(request.job_benefits)
        }
        
        # Generate the email content
        email_content = await asyncio.to_thread(
            email_generation_chain.invoke, 
            chain_input
        )
        
        # Generate subject line
        subject = generate_subject_line(
            request.job_title, 
            request.job_company, 
            request.candidate_name
        )
        
        return {
            "email_content": email_content,
            "subject": subject,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate email: {str(e)}")

@app.post("/api/email/improve")
async def improve_email(request: EmailImprovementRequest):
    """Improve an existing email using Groq AI"""
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

@app.post("/api/email/pending")
async def create_pending_email(email: EmailRequest):
    """Create a pending email request that needs approval"""
    email_id = email.id or str(uuid.uuid4())
    pending_approvals[email_id] = {
        "email": email.dict(),
        "created_at": datetime.now(),
        "status": "pending"
    }
    return {"id": email_id, "status": "pending"}

@app.get("/api/email/pending")
async def get_pending_emails():
    """Get all pending email requests"""
    # Clean up old requests (older than 24 hours)
    current_time = datetime.now()
    expired_ids = [
        id for id, data in pending_approvals.items()
        if current_time - data["created_at"] > timedelta(hours=24)
    ]
    for id in expired_ids:
        del pending_approvals[id]
    
    return {"pending_emails": [
        {**data["email"], "created_at": data["created_at"].isoformat()}
        for data in pending_approvals.values()
        if data["status"] == "pending"
    ]}

@app.post("/api/email/approve")
async def approve_email(approval: ApprovalResponse):
    """Approve or reject a pending email"""
    if approval.id not in pending_approvals:
        raise HTTPException(status_code=404, detail="Email request not found")
    
    if approval.approved:
        # Move to sent emails and create initial thread
        email_data = pending_approvals[approval.id]["email"]
        sent_emails[approval.id] = {
            "email": email_data,
            "sent_at": datetime.now(),
            "status": "sent"
        }
        
        # Create initial thread entry
        email_threads[approval.id] = [{
            "id": 1,
            "sender": "recruiter@company.com",  # This would come from config
            "recipient": email_data["to"],
            "timestamp": datetime.now().isoformat(),
            "content": "Initial recruitment email sent",
            "type": "sent",
            "status": "delivered"
        }]
        
        pending_approvals[approval.id]["status"] = "approved_and_sent"
    else:
        pending_approvals[approval.id]["status"] = "rejected"
    
    return {"id": approval.id, "status": pending_approvals[approval.id]["status"]}

@app.post("/api/email/send")
async def send_email(request: EmailSendRequest):
    """Send an email directly (bypass approval queue)"""
    email_id = request.id or str(uuid.uuid4())
    
    try:
        # In a real implementation, this would integrate with an email service
        # For now, we'll simulate the sending process
        
        email_data = {
            "id": email_id,
            "to": request.to,
            "subject": request.subject,
            "content": request.content,
            "metadata": request.metadata
        }
        
        # Store as sent
        sent_emails[email_id] = {
            "email": email_data,
            "sent_at": datetime.now(),
            "status": "sent"
        }
        
        # Create initial thread
        email_threads[email_id] = [{
            "id": 1,
            "sender": "recruiter@company.com",
            "recipient": request.to,
            "timestamp": datetime.now().isoformat(),
            "content": "Initial recruitment email sent",
            "type": "sent",
            "status": "delivered"
        }]
        
        # Simulate a potential reply (for demo purposes)
        if request.metadata and 'candidateInfo' in request.metadata:
            candidate_name = request.metadata['candidateInfo'].get('name', 'Candidate')
            email_threads[email_id].append({
                "id": 2,
                "sender": request.to,
                "recipient": "recruiter@company.com",
                "timestamp": (datetime.now() + timedelta(hours=2)).isoformat(),
                "content": f"Hi, thank you for reaching out! This opportunity sounds interesting. I'd love to learn more about the role and the team. When would be a good time for a call?",
                "type": "received",
                "status": "read"
            })
        
        return {
            "id": email_id,
            "status": "sent",
            "sent_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

@app.get("/api/email/thread/{email_id}")
async def get_email_thread(email_id: str):
    """Get the conversation thread for a specific email"""
    if email_id not in email_threads:
        raise HTTPException(status_code=404, detail="Email thread not found")
    
    return {
        "email_id": email_id,
        "messages": email_threads[email_id]
    }

@app.get("/api/email/sent")
async def get_sent_emails():
    """Get all sent emails"""
    return {"sent_emails": [
        {**data["email"], "sent_at": data["sent_at"].isoformat()}
        for data in sent_emails.values()
    ]}

# Health check
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "groq_model": "llama3-8b-8192",
        "pending_emails": len(pending_approvals),
        "sent_emails": len(sent_emails)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
import asyncio
from datetime import datetime, timedelta

app = FastAPI()

# Store pending email approvals
pending_approvals: Dict[str, dict] = {}

class EmailRequest(BaseModel):
    id: str
    to: str
    subject: str
    content: str
    metadata: Optional[dict] = None

class ApprovalResponse(BaseModel):
    approved: bool
    id: str

@app.post("/api/email/pending")
async def create_pending_email(email: EmailRequest):
    """Create a pending email request that needs approval"""
    pending_approvals[email.id] = {
        "email": email.dict(),
        "created_at": datetime.now(),
        "status": "pending"
    }
    return {"id": email.id, "status": "pending"}

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
    
    pending_approvals[approval.id]["status"] = "approved" if approval.approved else "rejected"
    return {"id": approval.id, "status": pending_approvals[approval.id]["status"]}

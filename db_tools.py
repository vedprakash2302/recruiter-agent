from langchain_core.tools import tool
from sqlalchemy import text
from db.setup import engine
from typing import Dict, Any
from db.setup import get_db
from db.schema import Base

def get_applicant_and_job(applicant_id: int) -> Any:
    """Get applicant and job data from database"""
    db = next(get_db())
    
    result = db.query(Base.classes.applicants, Base.classes.jobs).join(
        Base.classes.jobs, Base.classes.applicants.job_id == Base.classes.jobs.job_id
    ).filter(Base.classes.applicants.applicant_id == applicant_id).first()
    
    return result

@tool
def get_database_schema() -> str:
    """Get information about the database schema (tables and their columns).
    
    Returns:
        String representation of the database schema
    """
    return "Database schema: \n" + str(Base.metadata.tables)
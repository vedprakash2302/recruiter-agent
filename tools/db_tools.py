from langchain_core.tools import tool
from db.setup import get_db
from db.schema import Base, Applicant, Job, User

@tool
def get_applicant_details(applicant_id: int) -> str:
    """Get detailed information about an applicant including their job information.
    
    Args:
        applicant_id: The ID of the applicant to retrieve
        
    Returns:
        Formatted string with applicant and job details
    """
    try:
        db = next(get_db())
        
        # Query applicant with their job information
        result = db.query(Applicant, Job).join(
            Job, Applicant.job_id == Job.job_id
        ).filter(Applicant.applicant_id == applicant_id).first()
        
        if not result:
            return f"No applicant found with ID: {applicant_id}"
        
        applicant, job = result
        
        # Format the response
        details = f"""
                  Applicant Details:
                  - ID: {applicant.applicant_id}
                  - Name: {applicant.first_name} {applicant.last_name}
                  - Email: {applicant.email}
                  - Overall Score: {applicant.overall_score or 'Not evaluated yet'}
                  - Processing Status: {applicant.processing_status.value}
                  - Resume S3 Key: {applicant.resume_s3_object_key}
                  - Created: {applicant.created_at}

                  Job Details:
                  - Company: {job.company_name}
                  - Title: {job.job_title}
                  - Location: {job.job_location}
                  - Department: {job.job_department}
                  - Job URL: {job.job_url}
                  - Processing Status: {job.processing_status.value}

                  Evaluation Summary:
                  - Strengths: {applicant.strengths_summary or 'Not evaluated yet'}
                  - Weaknesses: {applicant.weaknesses_summary or 'Not evaluated yet'}
                  """
        
        return details.strip()
        
    except Exception as e:
        return f"Error retrieving applicant details: {str(e)}"

@tool
def get_job_details(job_id: int) -> str:
    """Get detailed information about a job including applicant count and user info.
    
    Args:
        job_id: The ID of the job to retrieve
        
    Returns:
        Formatted string with job details and statistics
    """
    try:
        db = next(get_db())
        
        # Query job with user information
        result = db.query(Job, User).join(
            User, Job.user_id == User.user_id
        ).filter(Job.job_id == job_id).first()
        
        if not result:
            return f"No job found with ID: {job_id}"
        
        job, user = result
        
        # Get applicant count for this job
        applicant_count = db.query(Applicant).filter(Applicant.job_id == job_id).count()
        
        # Format the response
        details = f"""
                    Job Details:

                    - Job URL: {job.job_url}
                    """
        
        return details.strip()
        
    except Exception as e:
        return f"Error retrieving job details: {str(e)}"

@tool
def get_database_schema() -> str:
    """Get information about the database schema (tables and their columns).
    
    Returns:
        String representation of the database schema
    """
    return "Database schema: \n" + str(Base.metadata.tables)
from langchain_core.tools import tool
from typing import Optional, Dict, Any
from db.setup import get_db
from db.schema import Base, Applicant, Job, User, ResumeProcessingStatus, JobProcessingStatus

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
def save_applicant(
    job_id: int,
    created_by: int,
    resume_filename: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    extracted_resume_text: Optional[str] = None,
    processing_status: str = "not_started"
) -> str:
    """Save a new applicant to the database.
    
    Args:
        job_id: ID of the job this applicant is applying for
        created_by: ID of the user who created this applicant record
        resume_filename: Name of the resume file
        first_name: First name of the applicant
        last_name: Last name of the applicant
        email: Email address of the applicant
        extracted_resume_text: Extracted text from the resume
        processing_status: Current processing status (default: not_started)
        
    Returns:
        Success message with applicant ID or error message
    """
    try:
        db = next(get_db())
        
        # Create new applicant
        new_applicant = Applicant(
            first_name=first_name,
            last_name=last_name,
            email=email,
            resume_filename=resume_filename,
            job_id=job_id,
            created_by=created_by,
            extracted_resume_text=extracted_resume_text,
            processing_status=ResumeProcessingStatus[processing_status] if processing_status else ResumeProcessingStatus.not_started
        )
        
        db.add(new_applicant)
        db.commit()
        db.refresh(new_applicant)
        
        return f"Successfully created applicant with ID: {new_applicant.applicant_id}"
        
    except Exception as e:
        db.rollback()
        return f"Error saving applicant: {str(e)}"

@tool
def update_applicant(
    applicant_id: int,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    extracted_resume_text: Optional[str] = None,
    processing_status: Optional[str] = None,
    overall_score: Optional[float] = None,
    strengths_summary: Optional[str] = None,
    weaknesses_summary: Optional[str] = None
) -> str:
    """Update an existing applicant in the database.
    
    Args:
        applicant_id: ID of the applicant to update
        first_name: Updated first name
        last_name: Updated last name
        email: Updated email
        extracted_resume_text: Updated extracted resume text
        processing_status: Updated processing status
        overall_score: Updated overall score
        strengths_summary: Updated strengths summary
        weaknesses_summary: Updated weaknesses summary
        
    Returns:
        Success message or error message
    """
    try:
        db = next(get_db())
        
        # Get the applicant
        applicant = db.query(Applicant).filter(Applicant.applicant_id == applicant_id).first()
        if not applicant:
            return f"No applicant found with ID: {applicant_id}"
        
        # Update fields if provided
        if first_name is not None:
            applicant.first_name = first_name
        if last_name is not None:
            applicant.last_name = last_name
        if email is not None:
            applicant.email = email
        if extracted_resume_text is not None:
            applicant.extracted_resume_text = extracted_resume_text
        if processing_status is not None:
            applicant.processing_status = ResumeProcessingStatus[processing_status]
        if overall_score is not None:
            applicant.overall_score = overall_score
        if strengths_summary is not None:
            applicant.strengths_summary = strengths_summary
        if weaknesses_summary is not None:
            applicant.weaknesses_summary = weaknesses_summary
        
        db.commit()
        return f"Successfully updated applicant with ID: {applicant_id}"
        
    except Exception as e:
        db.rollback()
        return f"Error updating applicant: {str(e)}"

@tool
def save_job(
    job_url: str,
    user_id: int,
    extracted_job_description: Optional[str] = None,
    processing_status: str = "not_started"
) -> str:
    """Save a new job to the database.
    
    Args:
        job_url: URL of the job posting
        user_id: ID of the user who created this job
        extracted_job_description: Extracted job description text
        processing_status: Current processing status (default: not_started)
        
    Returns:
        Success message with job ID or error message
    """
    try:
        db = next(get_db())
        
        # Create new job
        new_job = Job(
            job_url=job_url,
            user_id=user_id,
            extracted_job_description=extracted_job_description,
            processing_status=JobProcessingStatus[processing_status] if processing_status else JobProcessingStatus.not_started
        )
        
        db.add(new_job)
        db.commit()
        db.refresh(new_job)
        
        return f"Successfully created job with ID: {new_job.job_id}"
        
    except Exception as e:
        db.rollback()
        return f"Error saving job: {str(e)}"

@tool
def update_job(
    job_id: int,
    job_url: Optional[str] = None,
    extracted_job_description: Optional[str] = None,
    processing_status: Optional[str] = None
) -> str:
    """Update an existing job in the database.
    
    Args:
        job_id: ID of the job to update
        job_url: Updated job URL
        extracted_job_description: Updated job description
        processing_status: Updated processing status
        
    Returns:
        Success message or error message
    """
    try:
        db = next(get_db())
        
        # Get the job
        job = db.query(Job).filter(Job.job_id == job_id).first()
        if not job:
            return f"No job found with ID: {job_id}"
        
        # Update fields if provided
        if job_url is not None:
            job.job_url = job_url
        if extracted_job_description is not None:
            job.extracted_job_description = extracted_job_description
        if processing_status is not None:
            job.processing_status = JobProcessingStatus[processing_status]
        
        db.commit()
        return f"Successfully updated job with ID: {job_id}"
        
    except Exception as e:
        db.rollback()
        return f"Error updating job: {str(e)}"

@tool
def get_database_schema() -> str:
    """Get information about the database schema (tables and their columns).
    
    Returns:
        String representation of the database schema
    """
    return "Database schema: \n" + str(Base.metadata.tables)
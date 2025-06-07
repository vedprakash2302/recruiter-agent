import json
from typing import Dict, Any
import os
from langchain_community.document_loaders import PDFPlumberLoader, WebBaseLoader
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# Import database tools and global variables
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from tools.db_tools import save_applicant
from globalc import JOB_DETAILS, CV_DETAILS, global_lock


def get_resume_content(pdf_path):
    """
    Extract text from a PDF file
    Args:
        pdf_path (str): Path to the PDF file
    Returns:
        str: Extracted text from the PDF 
    """
    loader = PDFPlumberLoader(pdf_path)
    data = loader.load()
    print("Resume loaded successfully")
    return data

def extract_job_details(job_text: str) -> Dict[str, Any]:
    """
    Extract structured information from job description text using Groq LLM.
    
    Args:
        job_text: Raw text extracted from the job posting
        
    Returns:
        Dictionary containing structured job information
    """
    try:
        # Initialize Groq LLM
        llm = ChatGroq(
            temperature=0,
            model_name="meta-llama/llama-4-scout-17b-16e-instruct",
        )
        
        # Define the output parser
        parser = JsonOutputParser()
        
        # Define the prompt template
        template = """
        Extract the following information from the job description below. 
        Return ONLY a JSON object with the following structure:
        {{
            "job_title": "string | null",
            "company_name": "string | null",
            "location": "string | null",
            "job_type": "string | null",
            "experience_level": "string | null",
            "salary_range": "string | null",
            "skills_required": ["string"],
            "responsibilities": ["string"],
            "qualifications": ["string"],
            "extracted_job_description": "string"
        }}
        
        Rules:
        - Only include information that is explicitly mentioned in the job description
        - If a field cannot be determined, set it to null or empty list
        - extracted_job_description should be the first 1000 characters of the cleaned job text
        - skills_required, responsibilities, and qualifications should be lists of strings
        - Job type should be one of: Full-time, Part-time, Contract, Temporary, Internship, or null if not specified
        - Experience level should be one of: Entry Level, Mid Level, Senior, Executive, or null if not specified
        
        Job Description:
        {job_text}
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        
        # Create the chain
        chain = prompt | llm | parser
        
        # Run the chain
        result = chain.invoke({"job_text": job_text})
        
        # Clean and validate the result
        cleaned_result = {
            "job_title": result.get("job_title"),
            "company_name": result.get("company_name"),
            "location": result.get("location"),
            "job_type": result.get("job_type"),
            "experience_level": result.get("experience_level"),
            "salary_range": result.get("salary_range"),
            "skills_required": result.get("skills_required", []),
            "responsibilities": result.get("responsibilities", []),
            "qualifications": result.get("qualifications", []),
            "extracted_job_description": job_text[:1000]  # First 1000 chars of original text
        }
        
        print("\nExtracted Job Details:")
        print("-" * 50)
        print(f"Job Title: {cleaned_result['job_title']}")
        print(f"Company: {cleaned_result['company_name']}")
        print(f"Location: {cleaned_result['location']}")
        print(f"Type: {cleaned_result['job_type']}")
        print(f"Experience: {cleaned_result['experience_level']}")
        print(f"Salary: {cleaned_result['salary_range']}")
        print(f"Skills ({len(cleaned_result['skills_required'])}): {', '.join(cleaned_result['skills_required'][:3])}...")
        print("-" * 50 + "\n")
        
        # Save to global variable
        with global_lock:
            JOB_DETAILS.clear()
            JOB_DETAILS.update(cleaned_result)
            
        return cleaned_result
        
    except Exception as e:
        print(f"❌ Error extracting job details: {str(e)}")
        error_result = {
            "job_title": None,
            "company_name": None,
            "location": None,
            "job_type": None,
            "experience_level": None,
            "salary_range": None,
            "skills_required": [],
            "responsibilities": [],
            "qualifications": [],
            "extracted_job_description": job_text[:1000] if job_text else ""
        }
        
        # Save error state to global variable
        with global_lock:
            JOB_DETAILS.clear()
            JOB_DETAILS.update(error_result)
            
        return error_result

def get_job_content(job_url: str) -> Dict[str, Any]:
    """
    Load and process job description from URL and extract structured information.
    
    Args:
        job_url: URL of the job posting
        
    Returns:
        Dictionary containing structured job information or error message
    """
    try:
        print(f"📄 Loading job description from: {job_url}")
        loader = WebBaseLoader(job_url)
        docs = loader.load()
        
        if not docs:
            error_msg = "❌ No content found at the provided URL"
            print(error_msg)
            return {"error": error_msg, "job_url": job_url}
            
        # Combine all pages into a single text
        job_text = "".join(doc.page_content for doc in docs)
        print('Job description loaded successfully')
        
        # Extract job details
        job_details = extract_job_details(job_text)
        return job_details
        
    except Exception as e:
        error_msg = f"❌ Error loading job description: {str(e)}"
        print(error_msg)
        return {"error": error_msg, "job_url": job_url}

def extract_applicant_details(resume_text: str) -> Dict[str, Any]:
    """
    Extract structured information from resume text using Groq LLM.
    
    Args:
        resume_text: Raw text extracted from the resume PDF
        
    Returns:
        Dictionary containing structured applicant information
    """
    try:
        # Initialize Groq LLM
        llm = ChatGroq(
            temperature=0,
            model_name="meta-llama/llama-4-scout-17b-16e-instruct",
        )
        
        # Define the output parser
        parser = JsonOutputParser()
        
        # Define the prompt template
        prompt = ChatPromptTemplate.from_template(
            """
            Extract the following information from the resume text below. 
            Return ONLY a JSON object with the following structure:
            {{
                "first_name": "string | null",
                "last_name": "string | null",
                "email": "string | null",
                "extracted_resume_text": "string"
            }}
            
            Rules:
            - Only include information that is explicitly mentioned in the resume
            - If a field cannot be determined, set it to null
            - extracted_resume_text should be the first 500 characters of the cleaned resume text
            - Email must be a valid email format if present
            - Names should be properly capitalized
            
            Resume Text:
            {resume_text}
            """
        )
        
        # Create the chain
        chain = prompt | llm | parser
        
        # Run the chain
        result = chain.invoke({"resume_text": resume_text})
        
        # Clean and validate the result
        cleaned_result = {
            "first_name": result.get("first_name"),
            "last_name": result.get("last_name"),
            "email": result.get("email"),
            "extracted_resume_text": resume_text[:500]  # First 500 chars of original text
        }
        
        print("\nExtracted Applicant Details:")
        print("-" * 50)
        print(f"First Name: {cleaned_result['first_name']}")
        print(f"Last Name: {cleaned_result['last_name']}")
        print(f"Email: {cleaned_result['email']}")
        print(f"Extracted Text Preview: {cleaned_result['extracted_resume_text'][:100]}...")
        print("-" * 50 + "\n")
        
        # Save to global variable
        with global_lock:
            CV_DETAILS.clear()
            CV_DETAILS.update(cleaned_result)
            
        return cleaned_result
        
    except Exception as e:
        print(f"❌ Error extracting applicant details: {str(e)}")
        error_result = {
            "first_name": None,
            "last_name": None,
            "email": None,
            "extracted_resume_text": resume_text[:500] if resume_text else ""
        }
        
        # Save error state to global variable
        with global_lock:
            CV_DETAILS.clear()
            CV_DETAILS.update(error_result)
            
        return error_result

def process_resume_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Process a resume PDF, extract structured information, and save to database.
    
    Args:
        pdf_path: Path to the resume PDF file
        job_id: ID of the job this applicant is applying for
        created_by: ID of the user who is processing this resume
        
    Returns:
        Dictionary containing saved applicant information including database ID
    """
    try:
        # Extract text from PDF
        docs = get_resume_content(pdf_path)
        if not docs:
            return {"error": "Failed to extract text from PDF"}
            
        # Combine all pages into a single text
        resume_text = "\n\n".join(doc.page_content for doc in docs)
        
        # Extract structured information
        extracted_data = extract_applicant_details(resume_text)                    
        
        return {
            "success": True           
        }
        
    except Exception as e:
        print(f"❌ Error processing resume: {str(e)}")
        return {
            "error": f"Failed to process resume: {str(e)}",
            "success": False
        }

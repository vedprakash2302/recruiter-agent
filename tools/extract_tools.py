import json
from typing import Dict, Any
import os
from langchain_community.document_loaders import PDFPlumberLoader, WebBaseLoader
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# Import database tools
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from tools.db_tools import save_applicant


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

def get_job_content(job_url: str) -> str:
    """Load and process job description from URL"""
    try:
        print(f"📄 Loading job description from: {job_url}")
        loader = WebBaseLoader(job_url)
        docs = loader.load()
        formatted_text = "".join(doc.page_content for doc in docs)
        print('Job description loaded successfully')
        return formatted_text
    except Exception as e:
        print(f"❌ Error loading job URL: {str(e)}")
        return f"Error loading URL: {str(e)}"

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
        
        return cleaned_result
        
    except Exception as e:
        print(f"❌ Error extracting applicant details: {str(e)}")
        return {
            "first_name": None,
            "last_name": None,
            "email": None,
            "extracted_resume_text": resume_text[:500] if resume_text else ""
        }

def process_resume_pdf(pdf_path: str, job_id: int, created_by: int) -> Dict[str, Any]:
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
        print(f"\nProcessing resume: {pdf_path}")
        
        # Extract text from PDF
        resume_data = get_resume_content(pdf_path)
        if not resume_data:
            error_msg = "❌ No content extracted from resume"
            print(error_msg)
            return {"error": error_msg}
            
        # Combine all pages into a single text
        resume_text = "\n".join([doc.page_content for doc in resume_data])
        
        # Extract structured information
        applicant_info = extract_applicant_details(resume_text)
        
        if not applicant_info:
            error_msg = "❌ Failed to extract applicant information"
            print(error_msg)
            return {"error": error_msg}
        
        # Get the base filename for resume_filename
        resume_filename = os.path.basename(pdf_path)
        
        # Prepare data for saving to database
        save_data = {
            "job_id": job_id,
            "created_by": created_by,
            "resume_filename": resume_filename,
            "first_name": applicant_info.get("first_name"),
            "last_name": applicant_info.get("last_name"),
            "email": applicant_info.get("email"),
            "extracted_resume_text": applicant_info.get("extracted_resume_text", "")[:1000],  # Truncate if too long
        }
        
        print("\nSaving applicant to database...")
        save_result = save_applicant(**save_data)
        print(f"Save result: {save_result}")
        
        # Add database save result to the return value
        applicant_info["save_result"] = save_result
        
        # Try to extract the applicant ID from the save result
        if "Successfully created applicant with ID:" in save_result:
            applicant_id = save_result.split(":")[-1].strip()
            applicant_info["applicant_id"] = int(applicant_id)
        
        return applicant_info
        
    except Exception as e:
        error_msg = f"❌ Error processing resume: {str(e)}"
        print(error_msg)
        return {"error": error_msg}
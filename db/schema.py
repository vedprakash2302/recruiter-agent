from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from typing import List, Dict, Any, Optional
from datetime import datetime

Base = declarative_base()

# Enums
class ResumeProcessingStatus(enum.Enum):
    not_started = "not_started"
    processing = "processing"
    completed = "completed"
    failed = "failed"

class JobProcessingStatus(enum.Enum):
    not_started = "not_started"
    processing = "processing"
    completed = "completed"
    failed = "failed"

# Users table
class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer(), primary_key=True, autoincrement=True)
    clerk_id = Column(String(255), nullable=False, unique=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime(), default=func.now(), nullable=False)
    updated_at = Column(DateTime(), default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")
    applicants = relationship("Applicant", back_populates="created_by_user", cascade="all, delete-orphan")

# Jobs table
class Job(Base):
    __tablename__ = "jobs"
    
    job_id = Column(Integer(), primary_key=True, autoincrement=True)
    job_url = Column(Text(), nullable=False)
    processing_status = Column(Enum(JobProcessingStatus), nullable=False, default=JobProcessingStatus.not_started)
    extracted_job_description = Column(Text())
    
    # Relationships
    user = relationship("User", back_populates="jobs")
    applicants = relationship("Applicant", back_populates="job", cascade="all, delete-orphan")

# Applicants table
class Applicant(Base):
    __tablename__ = "applicants"
    
    applicant_id = Column(Integer(), primary_key=True, autoincrement=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(255))
    resume_filename = Column(Text(), nullable=False)
    extracted_resume_text = Column(Text())
    job_id = Column(Integer(), ForeignKey("jobs.job_id", ondelete="CASCADE"), nullable=False)
    created_by = Column(Integer(), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    processing_status = Column(Enum(ResumeProcessingStatus), nullable=False, default=ResumeProcessingStatus.not_started)
    
    # Relationships
    job = relationship("Job", back_populates="applicants")
    created_by_user = relationship("User", back_populates="applicants")

# Type definitions for better type hints
class UserCreate:
    clerk_id: str
    first_name: str
    last_name: str
    email: str

class UserUpdate:
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None

class JobCreate:
    job_url: str
    extracted_job_description: Optional[str] = None

class JobUpdate:
    job_url: Optional[str] = None
    processing_status: Optional[JobProcessingStatus] = None
    extracted_job_description: Optional[str] = None

class ApplicantCreate:
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    resume_filename: str
    job_id: int
    extracted_resume_text: Optional[str] = None

class ApplicantUpdate:
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    processing_status: Optional[ResumeProcessingStatus] = None 
    extracted_resume_text: Optional[str] = None
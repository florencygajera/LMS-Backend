"""
Recruitment Service Schemas
Agniveer Sentinel - Phase 1: Recruitment System
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from models.base import ApplicationStatus


# Candidate Schemas
class CandidateBase(BaseModel):
    """Base candidate schema"""
    date_of_birth: date
    gender: str = Field(..., max_length=20)
    blood_group: Optional[str] = Field(None, max_length=10)
    aadhaar_number: Optional[str] = Field(None, max_length=12)
    pan_number: Optional[str] = Field(None, max_length=10)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=10)
    father_name: Optional[str] = Field(None, max_length=255)
    mother_name: Optional[str] = Field(None, max_length=255)
    emergency_contact_name: Optional[str] = Field(None, max_length=255)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    education_qualification: Optional[str] = Field(None, max_length=100)
    passing_year: Optional[int] = None
    marks_percentage: Optional[float] = None
    height_cm: Optional[int] = None
    weight_kg: Optional[float] = None
    chest_cm: Optional[int] = None


class CandidateCreate(CandidateBase):
    """Schema for creating candidate"""
    pass


class CandidateUpdate(BaseModel):
    """Schema for updating candidate"""
    blood_group: Optional[str] = Field(None, max_length=10)
    aadhaar_number: Optional[str] = Field(None, max_length=12)
    pan_number: Optional[str] = Field(None, max_length=10)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=10)
    father_name: Optional[str] = Field(None, max_length=255)
    mother_name: Optional[str] = Field(None, max_length=255)
    emergency_contact_name: Optional[str] = Field(None, max_length=255)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    education_qualification: Optional[str] = Field(None, max_length=100)
    passing_year: Optional[int] = None
    marks_percentage: Optional[float] = None
    height_cm: Optional[int] = None
    weight_kg: Optional[float] = None
    chest_cm: Optional[int] = None


class CandidateResponse(CandidateBase):
    """Candidate response schema"""
    id: int
    uuid: str
    user_id: int
    application_status: ApplicationStatus
    registration_id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Document Schemas
class DocumentUploadResponse(BaseModel):
    """Document upload response"""
    document_id: int
    document_type: str
    file_url: str
    file_name: str
    
    model_config = ConfigDict(from_attributes=True)


# Application Schemas
class ApplicationCreate(BaseModel):
    """Application creation schema"""
    recruitment_batch: str = Field(..., max_length=50)
    force_type: Optional[str] = Field(None, max_length=50)
    trade_category: Optional[str] = Field(None, max_length=100)


class ApplicationResponse(BaseModel):
    """Application response schema"""
    id: int
    candidate_id: int
    recruitment_batch: str
    force_type: Optional[str]
    trade_category: Optional[str]
    age_eligible: bool
    education_eligible: bool
    physical_eligible: bool
    documents_verified: bool
    overall_eligible: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ApplicationVerificationRequest(BaseModel):
    """Schema for application verification."""

    recruitment_batch: str = Field(..., max_length=50)
    force_type: Optional[str] = Field(None, max_length=50)
    trade_category: Optional[str] = Field(None, max_length=100)
    age_eligible: bool
    education_eligible: bool
    physical_eligible: bool
    documents_verified: bool
    verification_notes: Optional[str] = None


# Exam Center Schemas
class ExamCenterResponse(BaseModel):
    """Exam center response schema"""
    id: int
    center_code: str
    center_name: str
    address: str
    city: str
    state: str
    pincode: str
    capacity: int
    current_booked: int
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)


# Exam Schemas
class ExamResponse(BaseModel):
    """Exam response schema"""
    id: int
    exam_name: str
    exam_code: str
    description: Optional[str]
    exam_date: date
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    total_questions: int
    total_marks: int
    passing_marks: int
    is_published: bool
    
    model_config = ConfigDict(from_attributes=True)


# Exam Registration Schemas
class ExamRegistrationResponse(BaseModel):
    """Exam registration response"""
    id: int
    candidate_id: int
    exam_id: int
    registration_number: str
    status: str
    is_present: bool
    marks_obtained: Optional[float]
    result_status: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


# Admit Card Schemas
class AdmitCardResponse(BaseModel):
    """Admit card response schema"""
    id: int
    candidate_id: int
    exam_id: int
    admit_card_number: str
    exam_venue: str
    exam_date: date
    exam_start_time: str
    exam_end_time: str
    qr_code_url: Optional[str]
    candidate_photo_url: Optional[str]
    pdf_url: Optional[str]
    generated_at: datetime
    email_sent: bool
    sms_sent: bool
    
    model_config = ConfigDict(from_attributes=True)


# Application Status Schema
class ApplicationStatusResponse(BaseModel):
    """Application status response"""
    registration_id: str
    application_status: ApplicationStatus
    admit_card: Optional[AdmitCardResponse]
    exam_registration: Optional[ExamRegistrationResponse]






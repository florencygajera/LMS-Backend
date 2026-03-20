"""
Recruitment Service Models
Agniveer Sentinel - Phase 1: Recruitment System
"""

from sqlalchemy import Column, Integer, String, DateTime, Date, Enum, Boolean, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime, date, timezone
from core.database import Base
from models.base import BaseModel, ApplicationStatus


# Candidate Model
class Candidate(BaseModel):
    """Candidate/Applicant model"""
    __tablename__ = "candidates"
    
    # User reference
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Personal Information
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(20), nullable=False)
    blood_group = Column(String(10), nullable=True)
    aadhaar_number = Column(String(12), unique=True, nullable=True)
    pan_number = Column(String(10), nullable=True)
    
    # Address
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    pincode = Column(String(10), nullable=True)
    
    # Family Information
    father_name = Column(String(255), nullable=True)
    mother_name = Column(String(255), nullable=True)
    emergency_contact_name = Column(String(255), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    
    # Educational Information
    education_qualification = Column(String(100), nullable=True)
    passing_year = Column(Integer, nullable=True)
    marks_percentage = Column(Float, nullable=True)
    
    # Eligibility
    height_cm = Column(Integer, nullable=True)
    weight_kg = Column(Float, nullable=True)
    chest_cm = Column(Integer, nullable=True)
    
    # Application Status
    application_status = Column(Enum(ApplicationStatus), default=ApplicationStatus.DRAFT)
    registration_id = Column(String(50), unique=True, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="candidate_profile")
    documents = relationship("CandidateDocument", back_populates="candidate")
    application = relationship("Application", back_populates="candidate", uselist=False)
    admit_card = relationship("AdmitCard", back_populates="candidate", uselist=False)
    
    def __repr__(self):
        return f"<Candidate(id={self.id}, registration_id={self.registration_id})>"


# Candidate Document Model
class CandidateDocument(BaseModel):
    """Uploaded documents for candidates"""
    __tablename__ = "candidate_documents"
    
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    document_type = Column(String(50), nullable=False)  # photo, aadhaar, education, certificate
    file_url = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(50), nullable=True)
    ocr_processed = Column(Boolean, default=False)
    ocr_text = Column(Text, nullable=True)
    
    # Relationships
    candidate = relationship("Candidate", back_populates="documents")
    
    def __repr__(self):
        return f"<CandidateDocument(id={self.id}, type={self.document_type})>"


# Application Model
class Application(BaseModel):
    """Recruitment application"""
    __tablename__ = "applications"
    
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, unique=True)
    
    # Application Details
    recruitment_batch = Column(String(50), nullable=False)
    force_type = Column(String(50), nullable=True)  # Army, Navy, Air Force
    trade_category = Column(String(100), nullable=True)
    
    # Eligibility Verification
    age_eligible = Column(Boolean, default=False)
    education_eligible = Column(Boolean, default=False)
    physical_eligible = Column(Boolean, default=False)
    documents_verified = Column(Boolean, default=False)
    overall_eligible = Column(Boolean, default=False)
    
    # Verification Notes
    verification_notes = Column(Text, nullable=True)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    
    # Relationships
    candidate = relationship("Candidate", back_populates="application")
    
    def __repr__(self):
        return f"<Application(id={self.id}, candidate_id={self.candidate_id})>"


# Exam Center Model
class ExamCenter(BaseModel):
    """Exam center locations"""
    __tablename__ = "exam_centers"
    
    center_code = Column(String(20), unique=True, nullable=False)
    center_name = Column(String(255), nullable=False)
    address = Column(Text, nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    pincode = Column(String(10), nullable=False)
    capacity = Column(Integer, nullable=False)
    current_booked = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Exams at this center
    exams = relationship("Exam", back_populates="exam_center")
    
    def __repr__(self):
        return f"<ExamCenter(id={self.id}, name={self.center_name})>"


# Exam Model
class Exam(BaseModel):
    """Exam scheduling"""
    __tablename__ = "exams"
    
    exam_name = Column(String(255), nullable=False)
    exam_code = Column(String(20), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    
    # Schedule
    exam_date = Column(Date, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    
    # Center
    exam_center_id = Column(Integer, ForeignKey("exam_centers.id"), nullable=False)
    
    # Status
    is_published = Column(Boolean, default=False)
    total_questions = Column(Integer, default=100)
    total_marks = Column(Integer, default=100)
    passing_marks = Column(Integer, default=40)
    
    # Relationships
    exam_center = relationship("ExamCenter", back_populates="exams")
    questions = relationship("ExamQuestion", back_populates="exam")
    registrations = relationship("ExamRegistration", back_populates="exam")
    
    def __repr__(self):
        return f"<Exam(id={self.id}, name={self.exam_name})>"


# Question Bank
class ExamQuestion(BaseModel):
    """Question bank for exams"""
    __tablename__ = "exam_questions"
    
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    
    question_text = Column(Text, nullable=False)
    question_type = Column(String(20), default="multiple_choice")  # multiple_choice, true_false
    options = Column(Text, nullable=False)  # JSON string of options
    correct_answer = Column(String(500), nullable=False)
    marks = Column(Integer, default=1)
    negative_marks = Column(Float, default=0.25)
    category = Column(String(100), nullable=True)  # General Knowledge, Math, Reasoning, etc.
    difficulty = Column(String(20), default="medium")  # easy, medium, hard
    is_active = Column(Boolean, default=True)
    
    # Relationships
    exam = relationship("Exam", back_populates="questions")
    
    def __repr__(self):
        return f"<ExamQuestion(id={self.id}, exam_id={self.exam_id})>"


# Exam Registration
class ExamRegistration(BaseModel):
    """Candidate exam registration"""
    __tablename__ = "exam_registrations"
    
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    
    registration_number = Column(String(50), unique=True, nullable=False)
    status = Column(String(20), default="registered")  # registered, appeared, absent, cancelled
    
    # Attendance
    check_in_time = Column(DateTime, nullable=True)
    check_out_time = Column(DateTime, nullable=True)
    is_present = Column(Boolean, default=False)
    
    # Results
    marks_obtained = Column(Float, nullable=True)
    total_marks = Column(Float, nullable=True)
    percentile = Column(Float, nullable=True)
    result_status = Column(String(20), nullable=True)  # qualified, not_qualified
    
    # Relationships
    candidate = relationship("Candidate")
    exam = relationship("Exam", back_populates="registrations")
    
    def __repr__(self):
        return f"<ExamRegistration(id={self.id}, candidate_id={self.candidate_id})>"


# Admit Card Model
class AdmitCard(BaseModel):
    """Generated admit cards"""
    __tablename__ = "admit_cards"
    
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, unique=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    exam_registration_id = Column(Integer, ForeignKey("exam_registrations.id"), nullable=False)
    
    admit_card_number = Column(String(50), unique=True, nullable=False)
    
    # Exam Details
    exam_venue = Column(String(255), nullable=False)
    exam_date = Column(Date, nullable=False)
    exam_start_time = Column(String(20), nullable=False)
    exam_end_time = Column(String(20), nullable=False)
    
    # QR Code
    qr_code_url = Column(String(500), nullable=True)
    
    # Photo
    candidate_photo_url = Column(String(500), nullable=True)
    
    # PDF
    pdf_url = Column(String(500), nullable=True)
    generated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Delivery Status
    email_sent = Column(Boolean, default=False)
    email_sent_at = Column(DateTime, nullable=True)
    sms_sent = Column(Boolean, default=False)
    sms_sent_at = Column(DateTime, nullable=True)
    
    # Relationships
    candidate = relationship("Candidate", back_populates="admit_card")
    exam = relationship("Exam")
    exam_registration = relationship("ExamRegistration")
    
    def __repr__(self):
        return f"<AdmitCard(id={self.id}, admit_card_number={self.admit_card_number})>"






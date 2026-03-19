"""
Soldier Service Models
Agniveer Sentinel - Phase 2: Soldier Management LMS
"""

from sqlalchemy import Column, Integer, String, DateTime, Date, Enum, Boolean, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime, date, time
from common.core.database import Base
from common.models.base import BaseModel, TrainingType, PaymentStatus


# Soldier Model
class Soldier(BaseModel):
    """Soldier profile model"""
    __tablename__ = "soldiers"
    
    # User reference
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Personal Information
    soldier_id = Column(String(50), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(20), nullable=False)
    blood_group = Column(String(10), nullable=True)
    phone_number = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    
    # Emergency Contact
    emergency_contact_name = Column(String(255), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    emergency_contact_relation = Column(String(50), nullable=True)
    
    # Address
    permanent_address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    pincode = Column(String(10), nullable=True)
    
    # Service Information
    joining_date = Column(Date, nullable=False)
    rank = Column(String(50), nullable=True)
    battalion_id = Column(Integer, ForeignKey("battalions.id"), nullable=True)
    
    # Profile Photo
    profile_photo_url = Column(String(500), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    service_status = Column(String(20), default="active")  # active, on_leave, retired
    
    # Relationships
    user = relationship("User", back_populates="soldier_profile")
    battalion = relationship("Battalion", back_populates="soldiers")
    documents = relationship("SoldierDocument", back_populates="soldier")
    medical_records = relationship("MedicalRecord", back_populates="soldier")
    training_records = relationship("TrainingRecord", back_populates="soldier")
    schedules = relationship("DailySchedule", back_populates="soldier")
    equipment = relationship("Equipment", back_populates="soldier")
    events = relationship("SoldierEvent", back_populates="soldier")
    stipends = relationship("Stipend", back_populates="soldier")
    
    def __repr__(self):
        return f"<Soldier(id={self.id}, soldier_id={self.soldier_id}, name={self.full_name})>"


# Soldier Document Model
class SoldierDocument(BaseModel):
    """Uploaded documents for soldiers"""
    __tablename__ = "soldier_documents"
    
    soldier_id = Column(Integer, ForeignKey("soldiers.id"), nullable=False)
    document_type = Column(String(50), nullable=False)  # aadhaar, medical, education, training
    document_name = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    expiry_date = Column(Date, nullable=True)
    ocr_processed = Column(Boolean, default=False)
    ocr_text = Column(Text, nullable=True)
    
    # Relationships
    soldier = relationship("Soldier", back_populates="documents")
    
    def __repr__(self):
        return f"<SoldierDocument(id={self.id}, type={self.document_type})>"


# Battalion Model
class Battalion(BaseModel):
    """Battalion/unit management"""
    __tablename__ = "battalions"
    
    battalion_name = Column(String(255), nullable=False)
    battalion_code = Column(String(20), unique=True, nullable=False)
    location = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    commander_name = Column(String(255), nullable=True)
    commander_phone = Column(String(20), nullable=True)
    mission_details = Column(Text, nullable=True)
    total_strength = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    soldiers = relationship("Soldier", back_populates="battalion")
    postings = relationship("BattalionPosting", back_populates="battalion")
    
    def __repr__(self):
        return f"<Battalion(id={self.id}, name={self.battalion_name})>"


# Battalion Posting
class BattalionPosting(BaseModel):
    """Soldier posting history"""
    __tablename__ = "battalion_postings"
    
    soldier_id = Column(Integer, ForeignKey("soldiers.id"), nullable=False)
    battalion_id = Column(Integer, ForeignKey("battalions.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    posting_type = Column(String(50), default="permanent")  # permanent, temporary, training
    remarks = Column(Text, nullable=True)
    
    # Relationships
    soldier = relationship("Soldier")
    battalion = relationship("Battalion", back_populates="postings")
    
    def __repr__(self):
        return f"<BattalionPosting(id={self.id}, soldier_id={self.soldier_id}, battalion_id={self.battalion_id})>"


# Medical Record Model
class MedicalRecord(BaseModel):
    """Medical history for soldiers"""
    __tablename__ = "medical_records"
    
    soldier_id = Column(Integer, ForeignKey("soldiers.id"), nullable=False)
    
    # Record Details
    record_type = Column(String(50), nullable=False)  # checkup, treatment, emergency
    doctor_name = Column(String(255), nullable=False)
    hospital_name = Column(String(255), nullable=True)
    diagnosis = Column(Text, nullable=True)
    symptoms = Column(Text, nullable=True)
    treatment = Column(Text, nullable=True)
    medicines = Column(Text, nullable=True)  # JSON string
    
    # Dates
    visit_date = Column(Date, nullable=False)
    follow_up_date = Column(Date, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Relationships
    soldier = relationship("Soldier", back_populates="medical_records")
    attachments = relationship("MedicalAttachment", back_populates="medical_record")
    
    def __repr__(self):
        return f"<MedicalRecord(id={self.id}, soldier_id={self.soldier_id}, doctor={self.doctor_name})>"


# Medical Attachment
class MedicalAttachment(BaseModel):
    """Medical document attachments"""
    __tablename__ = "medical_attachments"
    
    medical_record_id = Column(Integer, ForeignKey("medical_records.id"), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, image, lab_report
    
    # Relationships
    medical_record = relationship("MedicalRecord", back_populates="attachments")
    
    def __repr__(self):
        return f"<MedicalAttachment(id={self.id}, medical_record_id={self.medical_record_id})>"


# Training Record Model
class TrainingRecord(BaseModel):
    """Training performance records"""
    __tablename__ = "training_records"
    
    soldier_id = Column(Integer, ForeignKey("soldiers.id"), nullable=False)
    trainer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Training Details
    training_date = Column(Date, nullable=False)
    training_type = Column(Enum(TrainingType), nullable=False)
    
    # Fitness Metrics
    running_time_minutes = Column(Float, nullable=True)
    pushups_count = Column(Integer, nullable=True)
    pullups_count = Column(Integer, nullable=True)
    endurance_score = Column(Float, nullable=True)
    bmi = Column(Float, nullable=True)
    
    # Mental Training
    strategy_exercises = Column(Float, nullable=True)
    decision_score = Column(Float, nullable=True)
    psychological_score = Column(Float, nullable=True)
    
    # Weapons Training
    shooting_accuracy = Column(Float, nullable=True)
    weapon_handling_score = Column(Float, nullable=True)
    combat_drill_score = Column(Float, nullable=True)
    
    # Overall
    overall_score = Column(Float, nullable=True)
    remarks = Column(Text, nullable=True)
    
    # Relationships
    soldier = relationship("Soldier", back_populates="training_records")
    
    def __repr__(self):
        return f"<TrainingRecord(id={self.id}, soldier_id={self.soldier_id}, date={self.training_date})>"


# Daily Schedule Model
class DailySchedule(BaseModel):
    """Daily training schedule for soldiers"""
    __tablename__ = "daily_schedules"
    
    soldier_id = Column(Integer, ForeignKey("soldiers.id"), nullable=False)
    
    # Schedule Details
    schedule_date = Column(Date, nullable=False)
    day_of_week = Column(String(20), nullable=False)
    
    # Activities (JSON string)
    activities = Column(Text, nullable=False)  # JSON: [{"time": "05:00", "activity": "PT", "location": "Ground"}]
    
    # Weather Adjustment
    is_adjusted = Column(Boolean, default=False)
    adjustment_reason = Column(String(255), nullable=True)
    
    # Status
    is_completed = Column(Boolean, default=False)
    
    # Relationships
    soldier = relationship("Soldier", back_populates="schedules")
    
    def __repr__(self):
        return f"<DailySchedule(id={self.id}, soldier_id={self.soldier_id}, date={self.schedule_date})>"


# Equipment Model
class Equipment(BaseModel):
    """Uniform and equipment tracking"""
    __tablename__ = "equipment"
    
    soldier_id = Column(Integer, ForeignKey("soldiers.id"), nullable=False)
    
    # Equipment Details
    equipment_type = Column(String(50), nullable=False)  # uniform, weapon, gear
    equipment_id = Column(String(50), unique=True, nullable=False)
    equipment_name = Column(String(255), nullable=False)
    serial_number = Column(String(100), nullable=True)
    
    # Issue/Return
    issue_date = Column(Date, nullable=False)
    return_date = Column(Date, nullable=True)
    condition = Column(String(50), default="good")  # good, damaged, lost
    
    # Relationships
    soldier = relationship("Soldier", back_populates="equipment")
    
    def __repr__(self):
        return f"<Equipment(id={self.id}, soldier_id={self.soldier_id}, name={self.equipment_name})>"


# Soldier Events and Achievements
class SoldierEvent(BaseModel):
    """Events and achievements for soldiers"""
    __tablename__ = "soldier_events"
    
    soldier_id = Column(Integer, ForeignKey("soldiers.id"), nullable=False)
    
    # Event Details
    event_type = Column(String(50), nullable=False)  # competition, award, training, mission
    event_name = Column(String(255), nullable=False)
    event_date = Column(Date, nullable=False)
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    # Achievement
    position = Column(String(50), nullable=True)
    award_name = Column(String(255), nullable=True)
    certificate_url = Column(String(500), nullable=True)
    
    # Relationships
    soldier = relationship("Soldier", back_populates="events")
    
    def __repr__(self):
        return f"<SoldierEvent(id={self.id}, soldier_id={self.soldier_id}, event={self.event_name})>"


# Stipend Model
class Stipend(BaseModel):
    """Soldier stipend/payment records"""
    __tablename__ = "stipends"
    
    soldier_id = Column(Integer, ForeignKey("soldiers.id"), nullable=False)
    
    # Payment Details
    month = Column(Integer, nullable=False)  # 1-12
    year = Column(Integer, nullable=False)
    base_amount = Column(Float, nullable=False)
    allowances = Column(Float, default=0)
    deductions = Column(Float, default=0)
    net_amount = Column(Float, nullable=False)
    
    # Status
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    payment_date = Column(DateTime, nullable=True)
    transaction_id = Column(String(100), nullable=True)
    bank_reference = Column(String(100), nullable=True)
    
    # Relationships
    soldier = relationship("Soldier", back_populates="stipends")
    
    def __repr__(self):
        return f"<Stipend(id={self.id}, soldier_id={self.soldier_id}, month={self.month}, year={self.year})>"


# Performance Ranking
class PerformanceRanking(BaseModel):
    """Monthly performance rankings"""
    __tablename__ = "performance_rankings"
    
    soldier_id = Column(Integer, ForeignKey("soldiers.id"), nullable=False)
    battalion_id = Column(Integer, ForeignKey("battalions.id"), nullable=True)
    
    # Ranking Period
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    
    # Scores
    fitness_score = Column(Float, nullable=False)
    weapon_score = Column(Float, nullable=False)
    mental_score = Column(Float, nullable=False)
    attendance_score = Column(Float, nullable=False)
    discipline_score = Column(Float, nullable=False)
    overall_score = Column(Float, nullable=False)
    
    # Rank
    rank = Column(Integer, nullable=False)
    
    # Relationships
    soldier = relationship("Soldier")
    battalion = relationship("Battalion")
    
    def __repr__(self):
        return f"<PerformanceRanking(id={self.id}, soldier_id={self.soldier_id}, rank={self.rank})>"


# SOS Alert
class SOSAlert(BaseModel):
    """Emergency SOS alerts"""
    __tablename__ = "sos_alerts"
    
    # Alert Details
    alert_message = Column(Text, nullable=False)
    alert_type = Column(String(50), default="emergency")  # emergency, drill, test
    
    # Status
    is_active = Column(Boolean, default=True)
    triggered_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    triggered_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    # Scope
    battalion_id = Column(Integer, ForeignKey("battalions.id"), nullable=True)  # null = all
    
    # Relationships
    battalion = relationship("Battalion")
    
    def __repr__(self):
        return f"<SOSAlert(id={self.id}, triggered_at={self.triggered_at})>"

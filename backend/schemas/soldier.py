"""
Soldier Service Schemas
Agniveer Sentinel - Phase 2: Soldier Management LMS
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from models.base import TrainingType, PaymentStatus


# Soldier Schemas
class SoldierBase(BaseModel):
    """Base soldier schema"""
    full_name: str = Field(..., max_length=255)
    date_of_birth: date
    gender: str = Field(..., max_length=20)
    blood_group: Optional[str] = Field(None, max_length=10)
    phone_number: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    emergency_contact_name: Optional[str] = Field(None, max_length=255)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relation: Optional[str] = Field(None, max_length=50)
    permanent_address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=10)
    joining_date: date
    rank: Optional[str] = Field(None, max_length=50)


class SoldierCreate(SoldierBase):
    """Schema for creating soldier"""
    user_id: int
    battalion_id: Optional[int] = None


class SoldierUpdate(BaseModel):
    """Schema for updating soldier"""
    phone_number: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    emergency_contact_name: Optional[str] = Field(None, max_length=255)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relation: Optional[str] = Field(None, max_length=50)
    permanent_address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=10)
    rank: Optional[str] = Field(None, max_length=50)
    battalion_id: Optional[int] = None
    service_status: Optional[str] = Field(None, max_length=20)


class SoldierResponse(SoldierBase):
    """Soldier response schema"""
    id: int
    uuid: str
    soldier_id: str
    user_id: int
    battalion_id: Optional[int]
    profile_photo_url: Optional[str]
    is_active: bool
    service_status: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Battalion Schemas
class BattalionBase(BaseModel):
    """Base battalion schema"""
    battalion_name: str = Field(..., max_length=255)
    battalion_code: str = Field(..., max_length=20)
    location: str = Field(..., max_length=255)
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=100)
    commander_name: Optional[str] = Field(None, max_length=255)
    commander_phone: Optional[str] = Field(None, max_length=20)
    mission_details: Optional[str] = None


class BattalionCreate(BattalionBase):
    """Schema for creating battalion"""
    pass


class BattalionResponse(BattalionBase):
    """Battalion response schema"""
    id: int
    total_strength: int
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Medical Record Schemas
class MedicalRecordBase(BaseModel):
    """Base medical record schema"""
    record_type: str = Field(..., max_length=50)
    doctor_name: str = Field(..., max_length=255)
    hospital_name: Optional[str] = Field(None, max_length=255)
    diagnosis: Optional[str] = None
    symptoms: Optional[str] = None
    treatment: Optional[str] = None
    medicines: Optional[str] = None
    visit_date: date
    follow_up_date: Optional[date] = None


class MedicalRecordCreate(MedicalRecordBase):
    """Schema for creating medical record"""
    pass


class MedicalRecordResponse(MedicalRecordBase):
    """Medical record response schema"""
    id: int
    soldier_id: int
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Training Record Schemas
class TrainingRecordBase(BaseModel):
    """Base training record schema"""
    training_date: date
    training_type: TrainingType
    running_time_minutes: Optional[float] = None
    pushups_count: Optional[int] = None
    pullups_count: Optional[int] = None
    endurance_score: Optional[float] = None
    bmi: Optional[float] = None
    strategy_exercises: Optional[float] = None
    decision_score: Optional[float] = None
    psychological_score: Optional[float] = None
    shooting_accuracy: Optional[float] = None
    weapon_handling_score: Optional[float] = None
    combat_drill_score: Optional[float] = None
    overall_score: Optional[float] = None
    remarks: Optional[str] = None


class TrainingRecordCreate(TrainingRecordBase):
    """Schema for creating training record"""
    pass


class TrainingRecordResponse(TrainingRecordBase):
    """Training record response schema"""
    id: int
    soldier_id: int
    trainer_id: Optional[int]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Schedule Schemas
class DailyScheduleBase(BaseModel):
    """Base daily schedule schema"""
    schedule_date: date
    activities: str  # JSON string


class DailyScheduleCreate(DailyScheduleBase):
    """Schema for creating daily schedule"""
    pass


class DailyScheduleResponse(DailyScheduleBase):
    """Daily schedule response schema"""
    id: int
    soldier_id: int
    day_of_week: str
    is_adjusted: bool
    adjustment_reason: Optional[str]
    is_completed: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Equipment Schemas
class EquipmentBase(BaseModel):
    """Base equipment schema"""
    equipment_type: str = Field(..., max_length=50)
    equipment_id: str = Field(..., max_length=50)
    equipment_name: str = Field(..., max_length=255)
    serial_number: Optional[str] = Field(None, max_length=100)
    issue_date: date
    return_date: Optional[date] = None
    condition: str = Field(default="good", max_length=50)


class EquipmentCreate(EquipmentBase):
    """Schema for creating equipment"""
    pass


class EquipmentResponse(EquipmentBase):
    """Equipment response schema"""
    id: int
    soldier_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Event Schemas
class SoldierEventBase(BaseModel):
    """Base soldier event schema"""
    event_type: str = Field(..., max_length=50)
    event_name: str = Field(..., max_length=255)
    event_date: date
    location: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    position: Optional[str] = Field(None, max_length=50)
    award_name: Optional[str] = Field(None, max_length=255)
    certificate_url: Optional[str] = None


class SoldierEventCreate(SoldierEventBase):
    """Schema for creating soldier event"""
    pass


class SoldierEventResponse(SoldierEventBase):
    """Soldier event response schema"""
    id: int
    soldier_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Stipend Schemas
class StipendBase(BaseModel):
    """Base stipend schema"""
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2020)
    base_amount: float
    allowances: float = 0
    deductions: float = 0
    net_amount: float


class StipendResponse(StipendBase):
    """Stipend response schema"""
    id: int
    soldier_id: int
    payment_status: PaymentStatus
    payment_date: Optional[datetime]
    transaction_id: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Ranking Schemas
class PerformanceRankingResponse(BaseModel):
    """Performance ranking response schema"""
    id: int
    soldier_id: int
    battalion_id: Optional[int]
    month: int
    year: int
    fitness_score: float
    weapon_score: float
    mental_score: float
    attendance_score: float
    discipline_score: float
    overall_score: float
    rank: int
    
    model_config = ConfigDict(from_attributes=True)


# SOS Alert Schemas
class SOSAlertCreate(BaseModel):
    """Schema for creating SOS alert"""
    alert_message: str
    alert_type: str = Field(default="emergency", max_length=50)
    battalion_id: Optional[int] = None


class SOSAlertResponse(BaseModel):
    """SOS alert response schema"""
    id: int
    alert_message: str
    alert_type: str
    is_active: bool
    triggered_by: int
    triggered_at: datetime
    resolved_at: Optional[datetime]
    battalion_id: Optional[int]
    
    model_config = ConfigDict(from_attributes=True)




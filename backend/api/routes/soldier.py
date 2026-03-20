"""
Soldier Management Endpoints
Agniveer Sentinel - Phase 2: Soldier Management LMS
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, date, timedelta
from typing import Optional, List
import uuid
import random
import string
import json

from core.database import get_db
from core.audit import log_security_event
from core.authorization import (
    admin_required,
    can_access_medical_record,
    can_access_soldier_profile,
    trainer_required,
)
from core.security import get_current_user
from core.storage import storage
from models.base import UserRole
from models.user import User
from models.soldier import (
    Soldier, SoldierDocument, Battalion, BattalionPosting,
    MedicalRecord, TrainingRecord, DailySchedule, Equipment,
    SoldierEvent, Stipend, PerformanceRanking, SOSAlert
)
from schemas.soldier import (
    SoldierCreate, SoldierUpdate, SoldierResponse,
    BattalionCreate, BattalionResponse,
    MedicalRecordCreate, MedicalRecordResponse,
    TrainingRecordCreate, TrainingRecordResponse,
    DailyScheduleCreate, DailyScheduleResponse,
    EquipmentCreate, EquipmentResponse,
    SoldierEventCreate, SoldierEventResponse,
    StipendResponse, PerformanceRankingResponse,
    SOSAlertCreate, SOSAlertResponse
)


router = APIRouter()

@router.get("/")
async def soldier_service_test():
    return {"message": "soldier service working"}


@router.get("/health")
async def soldier_health():
    return {"status": "healthy", "service": "soldier"}


def generate_soldier_id() -> str:
    """Generate unique soldier ID"""
    prefix = "AGN"
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"{prefix}{random_str}"


# ==================== Soldier Profile Endpoints ====================

@router.post("/profile", response_model=SoldierResponse, status_code=status.HTTP_201_CREATED)
async def create_soldier_profile(
    soldier_data: SoldierCreate,
    request: Request,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db)
):
    """Create soldier profile (Admin)"""
    # Check if user already has soldier profile
    result = await db.execute(select(Soldier).where(Soldier.user_id == current_user.id))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Soldier profile already exists"
        )
    
    # Create soldier
    soldier = Soldier(
        user_id=soldier_data.user_id,
        soldier_id=generate_soldier_id(),
        full_name=soldier_data.full_name,
        date_of_birth=soldier_data.date_of_birth,
        gender=soldier_data.gender,
        blood_group=soldier_data.blood_group,
        phone_number=soldier_data.phone_number,
        email=soldier_data.email,
        emergency_contact_name=soldier_data.emergency_contact_name,
        emergency_contact_phone=soldier_data.emergency_contact_phone,
        emergency_contact_relation=soldier_data.emergency_contact_relation,
        permanent_address=soldier_data.permanent_address,
        city=soldier_data.city,
        state=soldier_data.state,
        pincode=soldier_data.pincode,
        joining_date=soldier_data.joining_date,
        rank=soldier_data.rank,
        battalion_id=soldier_data.battalion_id,
    )
    
    db.add(soldier)
    await db.flush()
    
    # Update battalion strength
    if soldier_data.battalion_id:
        result = await db.execute(select(Battalion).where(Battalion.id == soldier_data.battalion_id))
        battalion = result.scalar_one_or_none()
        if battalion:
            battalion.total_strength += 1
    
    # Update user role
    result = await db.execute(select(User).where(User.id == soldier_data.user_id))
    user = result.scalar_one_or_none()
    if user:
        user.role = UserRole.SOLDIER

    await log_security_event(
        db,
        action="soldier_profile_created",
        request=request,
        user=current_user,
        resource_type="soldier",
        resource_id=soldier.id,
        details=f"user_id={soldier_data.user_id}",
    )

    await db.commit()
    await db.refresh(soldier)
    
    return soldier


@router.get("/profile", response_model=SoldierResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current soldier's profile"""
    result = await db.execute(select(Soldier).where(Soldier.user_id == current_user.id))
    soldier = result.scalar_one_or_none()
    
    if not soldier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Soldier profile not found"
        )
    
    return soldier


@router.get("/profile/{soldier_id}", response_model=SoldierResponse)
async def get_soldier_profile(
    soldier_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get soldier profile by ID (Admin)"""
    soldier = await can_access_soldier_profile(soldier_id, current_user, db)
    return soldier


@router.put("/profile", response_model=SoldierResponse)
async def update_my_profile(
    soldier_data: SoldierUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current soldier's profile"""
    result = await db.execute(select(Soldier).where(Soldier.user_id == current_user.id))
    soldier = result.scalar_one_or_none()
    
    if not soldier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Soldier profile not found"
        )
    
    # Update fields
    for field, value in soldier_data.model_dump(exclude_unset=True).items():
        setattr(soldier, field, value)

    await log_security_event(
        db,
        action="soldier_profile_updated",
        request=request,
        user=current_user,
        resource_type="soldier",
        resource_id=soldier.id,
    )

    await db.commit()
    await db.refresh(soldier)
    
    return soldier


@router.post("/documents", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload soldier documents"""
    result = await db.execute(select(Soldier).where(Soldier.user_id == current_user.id))
    soldier = result.scalar_one_or_none()
    
    if not soldier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Soldier profile not found"
        )
    
    file_content = await file.read()
    object_key = f"soldiers/{soldier.soldier_id}/{document_type}_{uuid.uuid4()}_{file.filename}"
    object_uri = storage.upload_bytes(object_key, file_content, file.content_type or "application/octet-stream")
    
    document = SoldierDocument(
        soldier_id=soldier.id,
        document_type=document_type,
        document_name=file.filename,
        file_url=object_uri,
        file_name=file.filename,
    )
    
    db.add(document)
    await db.flush()
    await db.commit()
    
    return {"document_id": document.id, "file_url": storage.generate_presigned_url(object_uri)}


# ==================== Battalion Endpoints ====================

@router.post("/battalions", response_model=BattalionResponse, status_code=status.HTTP_201_CREATED)
async def create_battalion(
    battalion_data: BattalionCreate,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db)
):
    """Create new battalion (Admin)"""
    battalion = Battalion(**battalion_data.model_dump())
    db.add(battalion)
    await db.commit()
    await db.refresh(battalion)
    return battalion


@router.get("/battalions", response_model=list[BattalionResponse])
async def list_battalions(
    db: AsyncSession = Depends(get_db)
):
    """List all battalions"""
    result = await db.execute(select(Battalion).where(Battalion.is_active == True))
    return result.scalars().all()


@router.get("/battalions/{battalion_id}", response_model=BattalionResponse)
async def get_battalion(
    battalion_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get battalion details"""
    result = await db.execute(select(Battalion).where(Battalion.id == battalion_id))
    battalion = result.scalar_one_or_none()
    
    if not battalion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Battalion not found"
        )
    
    return battalion


# ==================== Medical Record Endpoints ====================

@router.post("/medical-records", response_model=MedicalRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_medical_record(
    record_data: MedicalRecordCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create medical record"""
    # Get soldier
    result = await db.execute(select(Soldier).where(Soldier.user_id == current_user.id))
    soldier = result.scalar_one_or_none()
    
    if not soldier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Soldier profile not found"
        )
    
    record = MedicalRecord(
        soldier_id=soldier.id,
        **record_data.model_dump()
    )
    
    db.add(record)
    await log_security_event(
        db,
        action="medical_record_created",
        request=request,
        user=current_user,
        resource_type="medical_record",
        details=f"soldier_id={soldier.id}",
    )
    await db.commit()
    await db.refresh(record)
    
    return record


@router.get("/medical-records", response_model=list[MedicalRecordResponse])
async def list_medical_records(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List medical records"""
    result = await db.execute(select(Soldier).where(Soldier.user_id == current_user.id))
    soldier = result.scalar_one_or_none()
    
    if not soldier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Soldier profile not found"
        )
    
    result = await db.execute(
        select(MedicalRecord).where(
            MedicalRecord.soldier_id == soldier.id,
            MedicalRecord.is_active == True
        ).order_by(desc(MedicalRecord.visit_date))
    )
    
    return result.scalars().all()


@router.get("/medical-records/{record_id}", response_model=MedicalRecordResponse)
async def get_medical_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get specific medical record"""
    record = await can_access_medical_record(record_id, current_user, db)
    return record


# ==================== Training Record Endpoints ====================

@router.post("/training-records", response_model=TrainingRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_training_record(
    record_data: TrainingRecordCreate,
    current_user: User = Depends(trainer_required),
    db: AsyncSession = Depends(get_db)
):
    """Create training record (Trainer)"""
    record = TrainingRecord(**record_data.model_dump())
    record.trainer_id = current_user.id
    
    db.add(record)
    await db.commit()
    await db.refresh(record)
    
    return record


@router.get("/training-records", response_model=list[TrainingRecordResponse])
async def list_training_records(
    current_user: User = Depends(get_current_user),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    training_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List training records"""
    result = await db.execute(select(Soldier).where(Soldier.user_id == current_user.id))
    soldier = result.scalar_one_or_none()
    
    if not soldier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Soldier profile not found"
        )
    
    query = select(TrainingRecord).where(TrainingRecord.soldier_id == soldier.id)
    
    if start_date:
        query = query.where(TrainingRecord.training_date >= start_date)
    if end_date:
        query = query.where(TrainingRecord.training_date <= end_date)
    if training_type:
        query = query.where(TrainingRecord.training_type == training_type)
    
    result = await db.execute(query.order_by(desc(TrainingRecord.training_date)))
    
    return result.scalars().all()


# ==================== Schedule Endpoints ====================

@router.get("/schedule", response_model=list[DailyScheduleResponse])
async def get_daily_schedule(
    date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get daily schedule"""
    result = await db.execute(select(Soldier).where(Soldier.user_id == current_user.id))
    soldier = result.scalar_one_or_none()
    
    if not soldier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Soldier profile not found"
        )
    
    query = select(DailySchedule).where(DailySchedule.soldier_id == soldier.id)
    
    if date:
        query = query.where(DailySchedule.schedule_date == date)
    
    result = await db.execute(query.order_by(DailySchedule.schedule_date))
    
    return result.scalars().all()


# ==================== Equipment Endpoints ====================

@router.get("/equipment", response_model=list[EquipmentResponse])
async def list_equipment(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List soldier equipment"""
    result = await db.execute(select(Soldier).where(Soldier.user_id == current_user.id))
    soldier = result.scalar_one_or_none()
    
    if not soldier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Soldier profile not found"
        )
    
    result = await db.execute(
        select(Equipment).where(Equipment.soldier_id == soldier.id)
    )
    
    return result.scalars().all()


# ==================== Events Endpoints ====================

@router.get("/events", response_model=list[SoldierEventResponse])
async def list_events(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List soldier events and achievements"""
    result = await db.execute(select(Soldier).where(Soldier.user_id == current_user.id))
    soldier = result.scalar_one_or_none()
    
    if not soldier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Soldier profile not found"
        )
    
    result = await db.execute(
        select(SoldierEvent).where(SoldierEvent.soldier_id == soldier.id)
        .order_by(desc(SoldierEvent.event_date))
    )
    
    return result.scalars().all()


# ==================== Stipend Endpoints ====================

@router.get("/stipends", response_model=list[StipendResponse])
async def list_stipends(
    current_user: User = Depends(get_current_user),
    year: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """List soldier stipends"""
    result = await db.execute(select(Soldier).where(Soldier.user_id == current_user.id))
    soldier = result.scalar_one_or_none()
    
    if not soldier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Soldier profile not found"
        )
    
    query = select(Stipend).where(Stipend.soldier_id == soldier.id)
    
    if year:
        query = query.where(Stipend.year == year)
    
    result = await db.execute(query.order_by(desc(Stipend.year), desc(Stipend.month)))
    
    return result.scalars().all()


# ==================== Ranking Endpoints ====================

@router.get("/rankings", response_model=list[PerformanceRankingResponse])
async def get_rankings(
    battalion_id: Optional[int] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get performance rankings"""
    query = select(PerformanceRanking)
    
    if battalion_id:
        query = query.where(PerformanceRanking.battalion_id == battalion_id)
    if month:
        query = query.where(PerformanceRanking.month == month)
    if year:
        query = query.where(PerformanceRanking.year == year)
    
    result = await db.execute(query.order_by(PerformanceRanking.rank))
    
    return result.scalars().all()


# ==================== SOS Alert Endpoints ====================

@router.post("/sos", response_model=SOSAlertResponse, status_code=status.HTTP_201_CREATED)
async def trigger_sos(
    sos_data: SOSAlertCreate,
    request: Request,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db)
):
    """Trigger SOS alert (Admin)"""
    sos = SOSAlert(
        alert_message=sos_data.alert_message,
        alert_type=sos_data.alert_type,
        battalion_id=sos_data.battalion_id,
        triggered_by=current_user.id,
    )
    
    db.add(sos)
    await log_security_event(
        db,
        action="sos_triggered",
        request=request,
        user=current_user,
        resource_type="sos_alert",
        details=sos_data.alert_message,
    )
    await db.commit()
    await db.refresh(sos)
    
    # Would trigger WebSocket notifications here
    
    return sos


@router.get("/sos/active", response_model=List[SOSAlertResponse])
async def get_active_sos(
    db: AsyncSession = Depends(get_db)
):
    """Get active SOS alerts"""
    result = await db.execute(
        select(SOSAlert).where(SOSAlert.is_active == True)
        .order_by(desc(SOSAlert.triggered_at))
    )
    
    return result.scalars().all()


@router.post("/sos/{sos_id}/resolve")
async def resolve_sos(
    sos_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Resolve SOS alert"""
    result = await db.execute(select(SOSAlert).where(SOSAlert.id == sos_id))
    sos = result.scalar_one_or_none()
    
    if not sos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SOS alert not found"
        )
    
    sos.is_active = False
    sos.resolved_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "SOS resolved successfully"}






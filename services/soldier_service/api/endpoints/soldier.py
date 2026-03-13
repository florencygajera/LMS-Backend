"""
Soldier Management Endpoints
Agniveer Sentinel - Phase 2: Soldier Management LMS
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, date, timedelta
from typing import Optional, List
import uuid
import random
import string
import json

from common.core.database import get_db
from common.core.security import get_current_user
from common.models.base import UserRole
from services.auth_service.models.user import User
from services.soldier_service.models.soldier import (
    Soldier, SoldierDocument, Battalion, BattalionPosting,
    MedicalRecord, TrainingRecord, DailySchedule, Equipment,
    SoldierEvent, Stipend, PerformanceRanking, SOSAlert
)
from services.soldier_service.schemas.soldier import (
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


def generate_soldier_id() -> str:
    """Generate unique soldier ID"""
    prefix = "AGN"
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"{prefix}{random_str}"


# ==================== Soldier Profile Endpoints ====================

@router.post("/profile", response_model=SoldierResponse, status_code=status.HTTP_201_CREATED)
async def create_soldier_profile(
    soldier_data: SoldierCreate,
    current_user: User = Depends(get_current_user),
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
    result = await db.execute(select(Soldier).where(Soldier.id == soldier_id))
    soldier = result.scalar_one_or_none()
    
    if not soldier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Soldier not found"
        )
    
    return soldier


@router.put("/profile", response_model=SoldierResponse)
async def update_my_profile(
    soldier_data: SoldierUpdate,
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
    
    # Upload to S3/MinIO
    file_name = f"{soldier.soldier_id}/{document_type}_{uuid.uuid4()}_{file.filename}"
    file_url = f"https://storage.example.com/{file_name}"
    
    document = SoldierDocument(
        soldier_id=soldier.id,
        document_type=document_type,
        document_name=file.filename,
        file_url=file_url,
        file_name=file.filename,
    )
    
    db.add(document)
    await db.commit()
    
    return {"document_id": document.id, "file_url": file_url}


# ==================== Battalion Endpoints ====================

@router.post("/battalions", response_model=BattalionResponse, status_code=status.HTTP_201_CREATED)
async def create_battalion(
    battalion_data: BattalionCreate,
    current_user: User = Depends(get_current_user),
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
    result = await db.execute(select(MedicalRecord).where(MedicalRecord.id == record_id))
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical record not found"
        )
    
    return record


# ==================== Training Record Endpoints ====================

@router.post("/training-records", response_model=TrainingRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_training_record(
    record_data: TrainingRecordCreate,
    current_user: User = Depends(get_current_user),
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


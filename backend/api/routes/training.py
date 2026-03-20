"""
Training Service API Endpoints
Agniveer Sentinel - Soldier Management LMS
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional
from datetime import date, datetime

from core.database import get_db
from core.audit import log_security_event
from core.authorization import trainer_required
from core.security import get_current_user
from models.base import UserRole, TrainingType
from models.user import User
from models.soldier import Soldier, TrainingRecord, Battalion
from services.excel_processor import excel_processor
from schemas.training import (
    TrainingRecordCreate, TrainingRecordResponse,
    TrainingUploadResponse, TrainingStatsResponse
)


router = APIRouter()

@router.get("/")
async def training_service_test():
    return {"message": "training service working"}


@router.get("/health")
async def training_health():
    return {"status": "healthy", "service": "training"}


@router.post("/upload", response_model=TrainingUploadResponse)
async def upload_training_excel(
    file: UploadFile = File(...),
    request: Request = None,
    current_user: User = Depends(trainer_required),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload Excel sheet with training data
    Trainers upload daily training performance data
    """
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Excel files (.xlsx, .xls) are accepted"
        )
    
    # Read file content
    content = await file.read()
    
    # Process Excel
    result = await excel_processor.process_excel(content, db)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )

    await log_security_event(
        db,
        action="training_excel_uploaded",
        request=request,
        user=current_user,
        resource_type="training_upload",
        details=f"processed={result['processed']} failed={result['failed']}",
    )
    await db.commit()
    
    return TrainingUploadResponse(
        success=True,
        processed=result["processed"],
        failed=result["failed"],
        errors=result.get("errors", [])
    )


@router.post("/records", response_model=TrainingRecordResponse)
async def create_single_training_record(
    record_data: TrainingRecordCreate,
    current_user: User = Depends(trainer_required),
    db: AsyncSession = Depends(get_db)
):
    """Create a single training record"""
    # Verify soldier exists
    result = await db.execute(select(Soldier).where(Soldier.id == record_data.soldier_id))
    soldier = result.scalar_one_or_none()
    
    if not soldier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Soldier not found"
        )
    
    # Create record
    record = TrainingRecord(
        soldier_id=record_data.soldier_id,
        trainer_id=current_user.id,
        training_date=record_data.training_date,
        training_type=record_data.training_type,
        running_time_minutes=record_data.running_time_minutes,
        pushups_count=record_data.pushups_count,
        pullups_count=record_data.pullups_count,
        endurance_score=record_data.endurance_score,
        bmi=record_data.bmi,
        strategy_exercises=record_data.strategy_exercises,
        decision_score=record_data.decision_score,
        psychological_score=record_data.psychological_score,
        shooting_accuracy=record_data.shooting_accuracy,
        weapon_handling_score=record_data.weapon_handling_score,
        combat_drill_score=record_data.combat_drill_score,
        overall_score=record_data.overall_score,
        remarks=record_data.remarks,
    )
    
    db.add(record)
    await db.commit()
    await db.refresh(record)
    
    return record


@router.get("/records", response_model=list[TrainingRecordResponse])
async def get_training_records(
    soldier_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    training_type: Optional[TrainingType] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get training records - soldiers see own, admins see all"""
    query = select(TrainingRecord)
    
    # For soldiers, only show their own records
    if current_user.role == UserRole.SOLDIER:
        result = await db.execute(select(Soldier).where(Soldier.user_id == current_user.id))
        soldier = result.scalar_one_or_none()
        if soldier:
            query = query.where(TrainingRecord.soldier_id == soldier.id)
    elif soldier_id:
        query = query.where(TrainingRecord.soldier_id == soldier_id)
    
    if start_date:
        query = query.where(TrainingRecord.training_date >= start_date)
    if end_date:
        query = query.where(TrainingRecord.training_date <= end_date)
    if training_type:
        query = query.where(TrainingRecord.training_type == training_type)
    
    query = query.order_by(desc(TrainingRecord.training_date))
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/stats/{soldier_id}", response_model=TrainingStatsResponse)
async def get_soldier_training_stats(
    soldier_id: int,
    month: Optional[int] = None,
    year: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get training statistics for a soldier"""
    # Verify soldier exists
    result = await db.execute(select(Soldier).where(Soldier.id == soldier_id))
    soldier = result.scalar_one_or_none()
    
    if not soldier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Soldier not found"
        )
    
    # Build query
    query = select(TrainingRecord).where(TrainingRecord.soldier_id == soldier_id)
    
    if month and year:
        # Filter for specific month
        from datetime import datetime
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date()
        else:
            end_date = datetime(year, month + 1, 1).date()
        query = query.where(
            TrainingRecord.training_date >= start_date,
            TrainingRecord.training_date < end_date
        )
    
    result = await db.execute(query)
    records = result.scalars().all()
    
    # Calculate stats
    if not records:
        return TrainingStatsResponse(
            soldier_id=soldier_id,
            total_records=0,
            avg_fitness_score=0,
            avg_weapons_score=0,
            avg_mental_score=0,
            avg_overall_score=0,
            best_shooting_accuracy=0,
            best_running_time=0,
            total_training_days=0
        )
    
    fitness_scores = []
    weapons_scores = []
    mental_scores = []
    overall_scores = []
    shooting_accuracies = []
    running_times = []
    
    for record in records:
        if record.endurance_score:
            fitness_scores.append(record.endurance_score)
        if record.pushups_count:
            fitness_scores.append(min(record.pushups_count, 100))
        if record.shooting_accuracy:
            weapons_scores.append(record.shooting_accuracy)
        if record.weapon_handling_score:
            weapons_scores.append(record.weapon_handling_score)
        if record.decision_score:
            mental_scores.append(record.decision_score)
        if record.psychological_score:
            mental_scores.append(record.psychological_score)
        if record.overall_score:
            overall_scores.append(record.overall_score)
        if record.shooting_accuracy:
            shooting_accuracies.append(record.shooting_accuracy)
        if record.running_time_minutes:
            running_times.append(record.running_time_minutes)
    
    return TrainingStatsResponse(
        soldier_id=soldier_id,
        total_records=len(records),
        avg_fitness_score=sum(fitness_scores) / len(fitness_scores) if fitness_scores else 0,
        avg_weapons_score=sum(weapons_scores) / len(weapons_scores) if weapons_scores else 0,
        avg_mental_score=sum(mental_scores) / len(mental_scores) if mental_scores else 0,
        avg_overall_score=sum(overall_scores) / len(overall_scores) if overall_scores else 0,
        best_shooting_accuracy=max(shooting_accuracies) if shooting_accuracies else 0,
        best_running_time=min(running_times) if running_times else 0,
        total_training_days=len(records)
    )


@router.get("/battalion/{battalion_id}/stats")
async def get_battalion_training_stats(
    battalion_id: int,
    month: Optional[int] = None,
    year: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get training statistics for an entire battalion"""
    # Verify battalion
    result = await db.execute(select(Battalion).where(Battalion.id == battalion_id))
    battalion = result.scalar_one_or_none()
    
    if not battalion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Battalion not found"
        )
    
    # Get soldiers in battalion
    result = await db.execute(select(Soldier).where(Soldier.battalion_id == battalion_id))
    soldiers = result.scalars().all()
    
    battalion_stats = {
        "battalion_id": battalion_id,
        "battalion_name": battalion.battalion_name,
        "total_soldiers": len(soldiers),
        "soldier_stats": []
    }
    
    for soldier in soldiers:
        # Get soldier stats
        query = select(TrainingRecord).where(TrainingRecord.soldier_id == soldier.id)
        
        if month and year:
            from datetime import datetime
            start_date = datetime(year, month, 1).date()
            if month == 12:
                end_date = datetime(year + 1, 1, 1).date()
            else:
                end_date = datetime(year, month + 1, 1).date()
            query = query.where(
                TrainingRecord.training_date >= start_date,
                TrainingRecord.training_date < end_date
            )
        
        result = await db.execute(query)
        records = result.scalars().all()
        
        if records:
            overall_scores = [r.overall_score for r in records if r.overall_score]
            avg_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0
            
            battalion_stats["soldier_stats"].append({
                "soldier_id": soldier.id,
                "soldier_name": soldier.full_name,
                "soldier_code": soldier.soldier_id,
                "total_records": len(records),
                "avg_score": round(avg_score, 2)
            })
    
    # Sort by average score
    battalion_stats["soldier_stats"].sort(key=lambda x: x["avg_score"], reverse=True)
    
    return battalion_stats






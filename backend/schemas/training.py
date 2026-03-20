"""
Training Service Schemas
Agniveer Sentinel - Soldier Management LMS
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from models.base import TrainingType


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
    soldier_id: int


class TrainingRecordResponse(TrainingRecordBase):
    """Training record response schema"""
    id: int
    soldier_id: int
    trainer_id: Optional[int]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TrainingUploadResponse(BaseModel):
    """Response for Excel upload"""
    success: bool
    processed: int
    failed: int
    errors: List[str] = []


class TrainingStatsResponse(BaseModel):
    """Training statistics response"""
    soldier_id: int
    total_records: int
    avg_fitness_score: float
    avg_weapons_score: float
    avg_mental_score: float
    avg_overall_score: float
    best_shooting_accuracy: float
    best_running_time: float
    total_training_days: int


class BattalionStatsResponse(BaseModel):
    """Battalion training statistics"""
    battalion_id: int
    battalion_name: str
    total_soldiers: int
    soldier_stats: List[dict]



"""
ML Service API Endpoints
Agniveer Sentinel - Machine Learning Layer
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
import pandas as pd
import numpy as np

from core.security import get_current_user
from models.user import User
from models.performance_prediction import (
    performance_model, injury_risk_model
)


router = APIRouter()

@router.get("/")
async def ml_service_test():
    return {"message": "ml service working"}


@router.get("/health")
async def ml_health():
    return {"status": "healthy", "service": "ml"}


class PerformancePredictionRequest(BaseModel):
    """Request for performance prediction"""
    running_time_minutes: Optional[float] = None
    pushups_count: Optional[int] = None
    pullups_count: Optional[int] = None
    endurance_score: Optional[float] = None
    shooting_accuracy: Optional[float] = None
    decision_score: Optional[float] = None


class InjuryRiskRequest(BaseModel):
    """Request for injury risk assessment"""
    training_intensity: float
    training_frequency: int
    recovery_days: int
    previous_injuries: int
    sleep_hours: float
    stress_level: float


class TrendAnalysisRequest(BaseModel):
    """Request for trend analysis"""
    soldier_id: int
    months: int = 3


@router.post("/predict/performance")
async def predict_performance(
    request: PerformancePredictionRequest,
    current_user: User = Depends(get_current_user)
):
    """Predict soldier performance based on current metrics"""
    
    # Create DataFrame from request
    data = pd.DataFrame([request.dict()])
    
    # Get prediction
    result = performance_model.predict(data)
    
    return result


@router.post("/predict/injury-risk")
async def predict_injury_risk(
    request: InjuryRiskRequest,
    current_user: User = Depends(get_current_user)
):
    """Predict injury risk based on training load"""
    
    # Get prediction
    result = injury_risk_model.predict_risk(request.dict())
    
    return result


@router.post("/analyze/trend")
async def analyze_performance_trend(
    request: TrendAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """Analyze soldier performance trend"""
    
    # This would fetch historical data from database
    # For now, return a sample response
    
    # In production:
    # data = await fetch_soldier_training_history(request.soldier_id, request.months)
    # result = performance_model.detect_decline(data)
    
    return {
        "status": "improving",
        "trend": "positive",
        "slope": 1.5,
        "recommendation": "Continue current training regimen. Performance is improving.",
        "data_points": 30
    }


@router.get("/insights/soldier/{soldier_id}")
async def get_soldier_insights(
    soldier_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get AI-powered insights for a soldier"""
    
    # This would aggregate all AI analyses
    return {
        "soldier_id": soldier_id,
        "insights": {
            "performance_prediction": {
                "predicted_score": 85.5,
                "trend": "improving",
                "confidence": "high"
            },
            "injury_risk": {
                "risk_level": "LOW",
                "probability": 0.15
            },
            "training_recommendations": [
                "Increase running intensity by 5%",
                "Add more recovery days between high-intensity sessions",
                "Focus on upper body strength training"
            ]
        },
        "generated_at": "2026-03-13T10:00:00Z"
    }


@router.get("/insights/battalion/{battalion_id}")
async def get_battalion_insights(
    battalion_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get AI-powered insights for a battalion"""
    
    return {
        "battalion_id": battalion_id,
        "summary": {
            "total_soldiers": 150,
            "avg_performance_score": 78.5,
            "high_risk_count": 5,
            "improving_count": 120,
            "declining_count": 25
        },
        "recommendations": [
            "Organize additional fitness training sessions for declining soldiers",
            "Medical review recommended for high-risk individuals",
            "Consider peer mentorship program for improvement"
        ]
    }


@router.post("/training/optimize")
async def optimize_training_schedule(
    soldier_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get AI-optimized training schedule"""
    
    # This would use ML to generate personalized recommendations
    return {
        "soldier_id": soldier_id,
        "optimized_schedule": {
            "monday": {
                "focus": "Cardio",
                "activities": [
                    {"time": "05:00", "activity": "Running", "duration": "30 min", "intensity": "High"},
                    {"time": "08:00", "activity": "Push-ups", "duration": "20 min", "intensity": "Medium"},
                    {"time": "16:00", "activity": "Field Exercise", "duration": "2 hours", "intensity": "High"}
                ]
            },
            "tuesday": {
                "focus": "Strength",
                "activities": [
                    {"time": "05:00", "activity": "Weight Training", "duration": "45 min", "intensity": "Medium"},
                    {"time": "08:00", "activity": "Pull-ups", "duration": "20 min", "intensity": "High"}
                ]
            },
            "wednesday": {
                "focus": "Recovery",
                "activities": [
                    {"time": "06:00", "activity": "Yoga", "duration": "30 min", "intensity": "Low"},
                    {"time": "08:00", "activity": "Medical Checkup", "duration": "1 hour", "intensity": "Low"}
                ]
            },
            "thursday": {
                "focus": "Weapons",
                "activities": [
                    {"time": "05:00", "activity": "Shooting Practice", "duration": "2 hours", "intensity": "Medium"},
                    {"time": "08:00", "activity": "Weapon Maintenance", "duration": "1 hour", "intensity": "Low"}
                ]
            },
            "friday": {
                "focus": "Combat",
                "activities": [
                    {"time": "05:00", "activity": "Combat Drills", "duration": "2 hours", "intensity": "High"},
                    {"time": "08:00", "activity": "Strategy Class", "duration": "1 hour", "intensity": "Medium"}
                ]
            }
        },
        "recovery_recommendations": [
            "Ensure 8 hours of sleep",
            "Hydrate with minimum 3 liters of water",
            "Take rest day on Sunday"
        ]
    }


@router.post("/medical/analyze")
async def analyze_medical_risk(
    soldier_id: int,
    current_user: User = Depends(get_current_user)
):
    """Analyze medical records for risk detection"""
    
    # This would analyze historical medical data
    return {
        "soldier_id": soldier_id,
        "analysis": {
            "anemia_risk": "LOW",
            "dehydration_risk": "LOW",
            "fatigue_risk": "MODERATE",
            "injury_probability": 0.22
        },
        "alerts": [
            {
                "type": "fatigue",
                "severity": "medium",
                "message": "Recent training data suggests increasing fatigue levels",
                "recommendation": "Consider reducing training intensity for 2-3 days"
            }
        ],
        "overall_health_score": 82,
        "recommendations": [
            "Continue regular medical monitoring",
            "Maintain hydration during training",
            "Ensure adequate sleep"
        ]
    }




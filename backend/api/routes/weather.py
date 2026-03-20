"""
Weather Service API Endpoints
Agniveer Sentinel - Soldier Management LMS
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from json import JSONDecodeError
import json

from core.security import get_current_user
from models.user import User
from services.weather_service import weather_service
from models.soldier import DailySchedule
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db


router = APIRouter()

@router.get("/")
async def weather_service_test():
    return {"message": "weather service working"}


@router.get("/health")
async def weather_health():
    return {"status": "healthy", "service": "weather"}


class ScheduleAdjustmentRequest(BaseModel):
    """Request to adjust schedule based on weather"""
    schedule: List[dict]
    location: str


class ScheduleAdjustmentResponse(BaseModel):
    """Response with adjusted schedule"""
    original_schedule: List[dict]
    adjusted_schedule: List[dict]
    weather_recommendation: dict
    adjustment_reason: str


@router.get("/current")
async def get_current_weather(
    location: str,
    current_user: User = Depends(get_current_user)
):
    """Get current weather for a location"""
    result = await weather_service.get_current_weather(location)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Weather service unavailable"
        )
    
    return {
        "location": result.get("name"),
        "country": result.get("sys", {}).get("country"),
        "temperature": result.get("main", {}).get("temp"),
        "feels_like": result.get("main", {}).get("feels_like"),
        "humidity": result.get("main", {}).get("humidity"),
        "description": result.get("weather", [{}])[0].get("description"),
        "icon": result.get("weather", [{}])[0].get("icon"),
        "wind_speed": result.get("wind", {}).get("speed")
    }


@router.get("/forecast")
async def get_weather_forecast(
    location: str,
    days: int = 5,
    current_user: User = Depends(get_current_user)
):
    """Get weather forecast"""
    result = await weather_service.get_forecast(location, days)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Weather service unavailable"
        )
    
    forecasts = []
    for item in result.get("list", []):
        forecasts.append({
            "datetime": item.get("dt_txt"),
            "temperature": item.get("main", {}).get("temp"),
            "humidity": item.get("main", {}).get("humidity"),
            "description": item.get("weather", [{}])[0].get("description"),
            "icon": item.get("weather", [{}])[0].get("icon"),
            "wind_speed": item.get("wind", {}).get("speed")
        })
    
    return {
        "location": result.get("city", {}).get("name"),
        "forecasts": forecasts
    }


@router.post("/recommendation")
async def get_training_recommendation(
    location: str,
    current_user: User = Depends(get_current_user)
):
    """Get training recommendation based on weather"""
    recommendation = await weather_service.get_training_recommendation(location)
    
    if "error" in recommendation:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=recommendation.get("error")
        )
    
    return recommendation


@router.post("/adjust-schedule", response_model=ScheduleAdjustmentResponse)
async def adjust_schedule_for_weather(
    request: ScheduleAdjustmentRequest,
    current_user: User = Depends(get_current_user)
):
    """Adjust training schedule based on weather conditions"""
    result = await weather_service.adjust_schedule(request.schedule, request.location)
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=result.get("error")
        )
    
    return ScheduleAdjustmentResponse(
        original_schedule=result["original_schedule"],
        adjusted_schedule=result["adjusted_schedule"],
        weather_recommendation=result["weather_recommendation"],
        adjustment_reason=result["adjustment_reason"]
    )


@router.get("/battalion/{battalion_id}/weather-alert")
async def check_battalion_weather(
    battalion_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Check weather and get alerts for a battalion location"""
    # Get battalion location (would be stored in Battalion model)
    # For now, use a default location
    location = "Delhi"  # This would be fetched from Battalion model
    
    recommendation = await weather_service.get_training_recommendation(location)
    
    return {
        "battalion_id": battalion_id,
        "location": location,
        "recommendation": recommendation,
        "needs_adjustment": recommendation.get("training_modification") != "normal"
    }


@router.post("/schedule/auto-adjust")
async def auto_adjust_soldier_schedule(
    soldier_id: int,
    schedule_date: date,
    location: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Automatically adjust a soldier's schedule based on weather"""
    # Get soldier's schedule
    result = await db.execute(
        select(DailySchedule).where(
            DailySchedule.soldier_id == soldier_id,
            DailySchedule.schedule_date == schedule_date
        )
    )
    schedule_record = result.scalar_one_or_none()
    
    if not schedule_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found for this date"
        )
    
    # Parse activities
    try:
        activities = json.loads(schedule_record.activities)
    except JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Stored schedule activities are invalid JSON: {exc.msg}",
        ) from exc
    
    # Adjust schedule
    result = await weather_service.adjust_schedule(activities, location)
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=result.get("error")
        )
    
    # Update schedule in database
    schedule_record.activities = json.dumps(result["adjusted_schedule"])
    schedule_record.is_adjusted = True
    schedule_record.adjustment_reason = result["adjustment_reason"]
    
    await db.commit()
    
    return {
        "success": True,
        "original_schedule": result["original_schedule"],
        "adjusted_schedule": result["adjusted_schedule"],
        "adjustment_reason": result["adjustment_reason"],
        "weather": result["weather_recommendation"]
    }






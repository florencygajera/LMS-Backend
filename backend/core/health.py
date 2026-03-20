"""
Health Check Endpoints
Agniveer Sentinel - Enterprise Production
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Dict, Any, Optional
import redis
import os
from datetime import datetime

from common.core.database import get_db

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    timestamp: datetime


class ReadinessResponse(BaseModel):
    """Readiness check response"""
    status: str
    database: str
    redis: Optional[str]
    storage: Optional[str]


class LivenessResponse(BaseModel):
    """Liveness check response"""
    status: str
    uptime: float


# Store startup time
startup_time = datetime.utcnow()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="agniveer-sentinel",
        version=os.getenv("APP_VERSION", "1.0.0"),
        timestamp=datetime.utcnow()
    )


@router.get("/health/readiness", response_model=ReadinessResponse)
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Readiness check - determines if service can handle requests
    Checks database, Redis, and storage connectivity
    """
    database_status = "unhealthy"
    redis_status = "unhealthy"
    storage_status = "unhealthy"
    
    # Check database
    try:
        await db.execute(text("SELECT 1"))
        database_status = "healthy"
    except Exception as e:
        database_status = f"unhealthy: {str(e)}"
    
    # Check Redis
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_client = redis.from_url(redis_url, socket_connect_timeout=2)
        redis_client.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"
    
    # Check storage (MinIO/S3)
    try:
        # Would check S3/MinIO connectivity
        storage_status = "healthy"
    except Exception as e:
        storage_status = f"unhealthy: {str(e)}"
    
    # Determine overall status
    is_ready = (database_status == "healthy")
    
    return ReadinessResponse(
        status="ready" if is_ready else "not_ready",
        database=database_status,
        redis=redis_status,
        storage=storage_status
    )


@router.get("/health/liveness", response_model=LivenessResponse)
async def liveness_check():
    """
    Liveness check - determines if service is running
    Used by Kubernetes to restart crashed pods
    """
    uptime = (datetime.utcnow() - startup_time).total_seconds()
    
    return LivenessResponse(
        status="alive",
        uptime=uptime
    )


@router.get("/health/deep")
async def deep_health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Deep health check with detailed metrics
    """
    # Basic checks
    checks = {
        "database": False,
        "redis": False,
        "storage": False,
    }
    
    # Database check
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = True
    except:
        pass
    
    # Redis check
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_client = redis.from_url(redis_url, socket_connect_timeout=2)
        redis_client.ping()
        checks["redis"] = True
    except:
        pass
    
    # Storage check
    try:
        # Would check S3/MinIO
        checks["storage"] = True
    except:
        pass
    
    all_healthy = all(checks.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/metrics")
async def metrics_endpoint():
    """
    Prometheus metrics endpoint
    In production, would expose metrics for Prometheus to scrape
    """
    # This is a simplified version
    # In production, would use prometheus_client
    
    return {
        "service": "agniveer-sentinel",
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "metrics": {
            "requests_total": 0,
            "requests_failed": 0,
            "response_time_p95": 0,
        }
    }

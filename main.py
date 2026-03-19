"""
Agniveer Sentinel - Unified Main Application
Combines all microservices into a single FastAPI application
"""
import os
os.environ['USE_SQLITE'] = 'true'

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Agniveer")

# Settings
from common.core.config import settings
from common.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Agniveer Sentinel Starting Up...")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # NOTE: AI Services (RAG, ML) are lazy-loaded on first request
    # to speed up startup time
    
    logger.info("Agniveer Ready")
    yield
    logger.info("Agniveer Shutting Down...")


# Create FastAPI application
app = FastAPI(
    title="Agniveer Sentinel",
    description="Military Training Platform - All Services",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== Include All Service Routers ==============

# Auth Service
try:
    from services.auth_service.api.endpoints import auth as auth_router
    app.include_router(
        auth_router.router,
        prefix=f"{settings.API_V1_PREFIX}/auth",
        tags=["Auth Service"]
    )
    logger.info("Auth Service router included")
except Exception as e:
    logger.warning(f"Could not include Auth Service: {e}")

# Recruitment Service
try:
    from services.recruitment_service.api.endpoints import recruitment as recruitment_router
    app.include_router(
        recruitment_router.router,
        prefix=f"{settings.API_V1_PREFIX}/recruitment",
        tags=["Recruitment Service"]
    )
    logger.info("Recruitment Service router included")
except Exception as e:
    logger.warning(f"Could not include Recruitment Service: {e}")

# Soldier Service
try:
    from services.soldier_service.api.endpoints import soldier as soldier_router
    app.include_router(
        soldier_router.router,
        prefix=f"{settings.API_V1_PREFIX}/soldier",
        tags=["Soldier Service"]
    )
    logger.info("Soldier Service router included")
except Exception as e:
    logger.warning(f"Could not include Soldier Service: {e}")

# Training Service
try:
    from services.training_service.api.endpoints import training as training_router
    app.include_router(
        training_router.router,
        prefix=f"{settings.API_V1_PREFIX}/training",
        tags=["Training Service"]
    )
    logger.info("Training Service router included")
except Exception as e:
    logger.warning(f"Could not include Training Service: {e}")

# Notification Service
try:
    from services.notification_service.api.endpoints import notifications as notification_router
    app.include_router(
        notification_router.router,
        prefix=f"{settings.API_V1_PREFIX}/notifications",
        tags=["Notification Service"]
    )
    logger.info("Notification Service router included")
except Exception as e:
    logger.warning(f"Could not include Notification Service: {e}")

# Report Service
try:
    from services.report_service.api.endpoints import reports as report_router
    app.include_router(
        report_router.router,
        prefix=f"{settings.API_V1_PREFIX}/reports",
        tags=["Report Service"]
    )
    logger.info("Report Service router included")
except Exception as e:
    logger.warning(f"Could not include Report Service: {e}")

# ML Service
try:
    from services.ml_service.api.endpoints import ml as ml_router
    app.include_router(
        ml_router.router,
        prefix=f"{settings.API_V1_PREFIX}/ml",
        tags=["ML Service"]
    )
    logger.info("ML Service router included")
except Exception as e:
    logger.warning(f"Could not include ML Service: {e}")

# Document Service
try:
    from services.document_service.api.endpoints import documents as document_router
    app.include_router(
        document_router.router,
        prefix=f"{settings.API_V1_PREFIX}/documents",
        tags=["Document Service"]
    )
    logger.info("Document Service router included")
except Exception as e:
    logger.warning(f"Could not include Document Service: {e}")

# Weather Service
try:
    from services.weather_service.api.endpoints import weather as weather_router
    app.include_router(
        weather_router.router,
        prefix=f"{settings.API_V1_PREFIX}/weather",
        tags=["Weather Service"]
    )
    logger.info("Weather Service router included")
except Exception as e:
    logger.warning(f"Could not include Weather Service: {e}")

# AgniAssist AI Services (RAG, OCR, Predict, Summarize)
try:
    from agniassist.routers import rag, ocr, predict, summarize
    app.include_router(rag.router, prefix="/api", tags=["AI - RAG Chatbot"])
    app.include_router(ocr.router, prefix="/api", tags=["AI - OCR Processing"])
    app.include_router(predict.router, prefix="/api", tags=["AI - ML Prediction"])
    app.include_router(summarize.router, prefix="/api", tags=["AI - Summarization"])
    logger.info("AgniAssist AI routers included")
except Exception as e:
    logger.warning(f"Could not include AgniAssist: {e}")


# ============== Health Check Endpoints ==============

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Agniveer Sentinel",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Agniveer Sentinel",
        "description": "Military Training Platform - Unified API",
        "version": "1.0.0",
        "endpoints": {
            "auth": f"{settings.API_V1_PREFIX}/auth",
            "recruitment": f"{settings.API_V1_PREFIX}/recruitment",
            "soldier": f"{settings.API_V1_PREFIX}/soldier",
            "training": f"{settings.API_V1_PREFIX}/training",
            "notifications": f"{settings.API_V1_PREFIX}/notifications",
            "reports": f"{settings.API_V1_PREFIX}/reports",
            "ml": f"{settings.API_V1_PREFIX}/ml",
            "documents": f"{settings.API_V1_PREFIX}/documents",
            "weather": f"{settings.API_V1_PREFIX}/weather",
            "ai_rag": "/api/ask",
            "ai_ocr": "/api/ocr",
            "ai_predict": "/api/predict",
            "ai_summarize": "/api/summarize"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

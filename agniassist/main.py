"""
AgniAssist - AI-Powered Backend System
Military-Grade AI Services for Agniveer LMS Portal

This module provides:
- RAG-based chatbot
- OCR document processing
- NLP entity extraction
- ML prediction system
- Generative AI summarization
"""

from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import hashlib
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AgniAssist")

# Initialize security - import from security module
try:
    from agniassist.security import security, verify_token
except ModuleNotFoundError:
    from security import security, verify_token

# API Storage path
DATA_DIR = Path("agniassist_data")
DATA_DIR.mkdir(exist_ok=True)

# Activity log
ACTIVITY_LOG = DATA_DIR / "activity_log.json"


def log_activity(endpoint: str, input_data: Dict, output_data: Dict):
    """Log all AI activity for security auditing"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "endpoint": endpoint,
        "input_hash": hashlib.sha256(json.dumps(input_data, sort_keys=True).encode()).hexdigest()[:16],
        "output_hash": hashlib.sha256(json.dumps(output_data, sort_keys=True).encode()).hexdigest()[:16]
    }
    
    logs = []
    if ACTIVITY_LOG.exists():
        with open(ACTIVITY_LOG, 'r') as f:
            try:
                logs = json.load(f)
            except:
                logs = []
    
    logs.append(log_entry)
    
    # Keep last 1000 entries
    logs = logs[-1000:]
    
    with open(ACTIVITY_LOG, 'w') as f:
        json.dump(logs, f, indent=2)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown"""
    logger.info("🚀 AgniAssist Starting Up...")
    logger.info("📁 Data directory: %s", DATA_DIR)
    
    # Initialize services
    try:
        from agniassist.services.rag_service import rag_service
        await rag_service.initialize()
        logger.info("✅ RAG Service initialized")
    except Exception as e:
        logger.warning(f"RAG Service init warning: {e}")
    
    try:
        from agniassist.services.ml_service import ml_service
        ml_service.initialize()
        logger.info("✅ ML Service initialized")
    except Exception as e:
        logger.warning(f"ML Service init warning: {e}")
    
    logger.info("🎯 AgniAssist Ready")
    yield
    
    logger.info("🛑 AgniAssist Shutting Down...")


# Create FastAPI application
app = FastAPI(
    title="AgniAssist - AI Services",
    description="Military-Grade AI Backend for Agniveer LMS",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Import and include routers
try:
    from agniassist.routers import rag, ocr, predict, summarize
except ModuleNotFoundError:
    # Fallback for running from within agniassist directory
    from routers import rag, ocr, predict, summarize

app.include_router(rag.router, prefix="/api", tags=["RAG Chatbot"])
app.include_router(ocr.router, prefix="/api", tags=["OCR Processing"])
app.include_router(predict.router, prefix="/api", tags=["ML Prediction"])
app.include_router(summarize.router, prefix="/api", tags=["Summarization"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AgniAssist",
        "version": "1.0.0",
        "mode": "offline"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AgniAssist",
        "description": "AI-Powered Backend System",
        "endpoints": {
            "chat": "/api/ask",
            "ocr": "/api/ocr",
            "predict": "/api/predict",
            "summarize": "/api/summarize"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

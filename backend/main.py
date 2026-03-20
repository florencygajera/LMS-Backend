"""Agniveer unified API entrypoint."""

from __future__ import annotations

import json
import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

import hashlib

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes.ocr import router as ai_ocr_router
from api.routes.predict import router as ai_predict_router
from api.routes.rag import router as ai_rag_router
from api.routes.summarize import router as ai_summarize_router
from core.config import settings
from core.database import get_database_url, init_db
from api.routes.auth import router as auth_router
from api.routes.documents import router as documents_router
from api.routes.ml import router as ml_router
from api.routes.notifications import router as notifications_router
from api.routes.recruitment import router as recruitment_router
from api.routes.reports import router as reports_router
from api.routes.soldier import router as soldier_router
from api.routes.training import router as training_router
from api.routes.weather import router as weather_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger("agniveer")

API_PREFIX = settings.API_V1_PREFIX

# ============================================================================
# AgniAssist Activity Logging Configuration
# ============================================================================

# API Storage path
DATA_DIR = Path("agniassist_data")
DATA_DIR.mkdir(exist_ok=True)

# Activity log
ACTIVITY_LOG = DATA_DIR / "activity_log.json"


def log_activity(endpoint: str, input_data: dict, output_data: dict):
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
            except Exception:
                logs = []
    
    logs.append(log_entry)
    
    # Keep last 1000 entries
    logs = logs[-1000:]
    
    with open(ACTIVITY_LOG, 'w') as f:
        json.dump(logs, f, indent=2)


# ============================================================================
# Application Lifespan
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Agniveer Sentinel starting")
    active_db_url = await init_db()
    logger.info("Database initialized using %s", active_db_url)
    
    # Initialize AgniAssist AI services
    logger.info("Initializing AI Services...")
    
    # Initialize RAG Service
    try:
        from services.rag_service import rag_service
        await rag_service.initialize()
        logger.info("? RAG Service initialized")
    except Exception as e:
        logger.warning(f"RAG Service init warning: {e}")
    
    # Initialize ML Service
    try:
        from services.ml_service import ml_service
        ml_service.initialize()
        logger.info("? ML Service initialized")
    except Exception as e:
        logger.warning(f"ML Service init warning: {e}")
    
    # OCR, NLP, and GenAI services initialize themselves at import time
    # Just verify they're importable
    try:
        from services.ocr_service import ocr_service
        logger.info("? OCR Service loaded")
    except Exception as e:
        logger.warning(f"OCR Service init warning: {e}")
    
    try:
        from services.nlp_service import nlp_service
        logger.info("? NLP Service loaded")
    except Exception as e:
        logger.warning(f"NLP Service init warning: {e}")
    
    try:
        from services.genai_service import genai_service
        logger.info("? GenAI Service loaded")
    except Exception as e:
        logger.warning(f"GenAI Service init warning: {e}")
    
    logger.info("?? All AI Services Ready")
    
    yield
    
    logger.info("Agniveer Sentinel shutting down")


# ============================================================================
# FastAPI App Creation
# ============================================================================

app = FastAPI(
    title="Agniveer",
    version="1.0.0",
    description="Military Training Platform - Unified API with AI Capabilities",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Middleware
# ============================================================================

@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    started_at = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
    logger.info(
        "%s %s -> %s (%sms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


def _envelope_payload(payload: Any, message: str = "Request successful") -> dict[str, Any]:
    if isinstance(payload, dict) and {"success", "data", "message"}.issubset(payload.keys()):
        return payload
    return {"success": True, "data": payload, "message": message}


@app.middleware("http")
async def standard_response_middleware(request: Request, call_next):
    response = await call_next(request)

    if not request.url.path.startswith(API_PREFIX):
        return response
    if response.status_code >= 400:
        return response
    media_type = response.media_type or response.headers.get("content-type", "")
    if "application/json" not in media_type:
        return response

    body = b""
    async for chunk in response.body_iterator:
        body += chunk
    if not body:
        return response

    payload = json.loads(body.decode("utf-8"))
    wrapped = _envelope_payload(payload)
    headers = dict(response.headers)
    headers.pop("content-length", None)
    return JSONResponse(status_code=response.status_code, content=wrapped, headers=headers)


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "data": None, "message": exc.detail},
        headers=exc.headers or {},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    logger.exception("Unhandled server error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"success": False, "data": None, "message": "Internal server error"},
    )


# ============================================================================
# Router Registration
# ============================================================================

SERVICE_ROUTERS = [
    (auth_router, f"{API_PREFIX}/auth", "Auth Service"),
    (recruitment_router, f"{API_PREFIX}/recruitment", "Recruitment Service"),
    (soldier_router, f"{API_PREFIX}/soldier", "Soldier Service"),
    (training_router, f"{API_PREFIX}/training", "Training Service"),
    (notifications_router, f"{API_PREFIX}/notifications", "Notification Service"),
    (reports_router, f"{API_PREFIX}/reports", "Report Service"),
    (ml_router, f"{API_PREFIX}/ml", "ML Service"),
    (documents_router, f"{API_PREFIX}/documents", "Document Service"),
    (weather_router, f"{API_PREFIX}/weather", "Weather Service"),
    (ai_rag_router, f"{API_PREFIX}/ai", "AI - RAG"),
    (ai_ocr_router, f"{API_PREFIX}/ai", "AI - OCR"),
    (ai_predict_router, f"{API_PREFIX}/ai", "AI - Prediction"),
    (ai_summarize_router, f"{API_PREFIX}/ai", "AI - Summarization"),
]


OPENAPI_REQUIRED_PREFIXES = [
    f"{API_PREFIX}/auth",
    f"{API_PREFIX}/documents",
    f"{API_PREFIX}/ml",
    f"{API_PREFIX}/notifications",
    f"{API_PREFIX}/recruitment",
    f"{API_PREFIX}/reports",
    f"{API_PREFIX}/soldier",
    f"{API_PREFIX}/training",
    f"{API_PREFIX}/weather",
]


def _missing_required_api_prefixes(fastapi_app: FastAPI) -> list[str]:
    registered_paths = {
        route.path for route in fastapi_app.routes if getattr(route, "methods", None)
    }
    return [
        prefix
        for prefix in OPENAPI_REQUIRED_PREFIXES
        if not any(path.startswith(prefix) for path in registered_paths)
    ]


for router, prefix, tag in SERVICE_ROUTERS:
    app.include_router(router, prefix=prefix, tags=[tag])
    logger.info("Loaded %s router at %s", tag, prefix)

missing_prefixes = _missing_required_api_prefixes(app)
if missing_prefixes:
    message = (
        "OpenAPI router registration is incomplete. Missing API prefixes: "
        + ", ".join(sorted(missing_prefixes))
    )
    logger.error(message)
    raise RuntimeError(message)


# ============================================================================
# Startup Event
# ============================================================================

@app.on_event("startup")
async def log_registered_routes() -> None:
    print("Registered routes:")
    for route in app.routes:
        print(route.path)


# ============================================================================
# Health and Root Endpoints
# ============================================================================

@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "success": True,
        "data": {"status": "ok", "database_url": get_database_url()},
        "message": "Service healthy",
    }


@app.get("/health/ai")
async def ai_health() -> dict[str, Any]:
    """AI Services health check"""
    return {
        "success": True,
        "data": {
            "status": "ok",
            "service": "AgniAssist",
            "version": "1.0.0",
            "mode": "integrated"
        },
        "message": "AI Services healthy",
    }


@app.get("/")
async def root() -> dict[str, Any]:
    return {
        "success": True,
        "data": {
            "docs": "/docs",
            "api_prefix": API_PREFIX,
            "service": "Agniveer Sentinel",
            "ai_service": "AgniAssist Integrated"
        },
        "message": "Agniveer Sentinel running",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)



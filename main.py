"""Agniveer Sentinel unified API entrypoint."""

from __future__ import annotations

import json
import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agniassist.routers.ocr import router as ai_ocr_router
from agniassist.routers.predict import router as ai_predict_router
from agniassist.routers.rag import router as ai_rag_router
from agniassist.routers.summarize import router as ai_summarize_router
from common.core.config import settings
from common.core.database import get_database_url, init_db
from services.auth_service.api.endpoints.auth import router as auth_router
from services.document_service.api.endpoints.documents import router as documents_router
from services.ml_service.api.endpoints.ml import router as ml_router
from services.notification_service.api.endpoints.notifications import (
    router as notifications_router,
)
from services.recruitment_service.api.endpoints.recruitment import (
    router as recruitment_router,
)
from services.report_service.api.endpoints.reports import router as reports_router
from services.soldier_service.api.endpoints.soldier import router as soldier_router
from services.training_service.api.endpoints.training import router as training_router
from services.weather_service.api.endpoints.weather import router as weather_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger("agniveer")

API_PREFIX = settings.API_V1_PREFIX


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Agniveer Sentinel starting")
    active_db_url = await init_db()
    logger.info("Database initialized using %s", active_db_url)
    yield
    logger.info("Agniveer Sentinel shutting down")


app = FastAPI(
    title="Agniveer Sentinel",
    version="1.0.0",
    description="Military Training Platform - Unified API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

for router, prefix, tag in SERVICE_ROUTERS:
    app.include_router(router, prefix=prefix, tags=[tag])
    logger.info("Loaded %s router at %s", tag, prefix)


@app.on_event("startup")
async def log_registered_routes() -> None:
    print("Registered routes:")
    for route in app.routes:
        print(route.path)


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "success": True,
        "data": {"status": "ok", "database_url": get_database_url()},
        "message": "Service healthy",
    }


@app.get("/")
async def root() -> dict[str, Any]:
    return {
        "success": True,
        "data": {"docs": "/docs", "api_prefix": API_PREFIX},
        "message": "Agniveer Sentinel running",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

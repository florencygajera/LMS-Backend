"""
Agniveer Sentinel - Unified Main Application (Clean Version)
"""

import os
os.environ['USE_SQLITE'] = 'true'

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import traceback

# ================= LOGGING =================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Agniveer")

# ================= SETTINGS =================
from common.core.config import settings
from common.core.database import init_db


# ================= LIFESPAN =================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Agniveer Starting...")

    try:
        await init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error("❌ Database init failed")
        traceback.print_exc()

    yield

    logger.info("🛑 Agniveer Shutting down...")


# ================= APP =================
app = FastAPI(
    title="Agniveer Sentinel",
    version="1.0.0",
    description="Military Training Platform - Unified API",
    lifespan=lifespan
)

# ================= CORS =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================= ROUTER LOADER FUNCTION =================
def include_router_safe(import_path: str, router_name: str, prefix: str, tag: str):
    try:
        module = __import__(import_path, fromlist=[router_name])
        router = getattr(module, router_name)

        app.include_router(
            router,
            prefix=prefix,
            tags=[tag]
        )

        logger.info(f"✅ {tag} loaded at {prefix}")

    except Exception:
        logger.error(f"❌ Failed to load {tag}")
        traceback.print_exc()


# ================= INCLUDE ALL SERVICES =================

API_PREFIX = settings.API_V1_PREFIX  # usually /api/v1

# Core Services
include_router_safe(
    "services.auth_service.api.endpoints.auth",
    "router",
    f"{API_PREFIX}/auth",
    "Auth Service"
)

include_router_safe(
    "services.recruitment_service.api.endpoints.recruitment",
    "router",
    f"{API_PREFIX}/recruitment",
    "Recruitment Service"
)

include_router_safe(
    "services.soldier_service.api.endpoints.soldier",
    "router",
    f"{API_PREFIX}/soldier",
    "Soldier Service"
)

include_router_safe(
    "services.training_service.api.endpoints.training",
    "router",
    f"{API_PREFIX}/training",
    "Training Service"
)

include_router_safe(
    "services.notification_service.api.endpoints.notifications",
    "router",
    f"{API_PREFIX}/notifications",
    "Notification Service"
)

include_router_safe(
    "services.report_service.api.endpoints.reports",
    "router",
    f"{API_PREFIX}/reports",
    "Report Service"
)

include_router_safe(
    "services.ml_service.api.endpoints.ml",
    "router",
    f"{API_PREFIX}/ml",
    "ML Service"
)

include_router_safe(
    "services.document_service.api.endpoints.documents",
    "router",
    f"{API_PREFIX}/documents",
    "Document Service"
)

include_router_safe(
    "services.weather_service.api.endpoints.weather",
    "router",
    f"{API_PREFIX}/weather",
    "Weather Service"
)


# ================= AGNIASSIST AI =================
include_router_safe(
    "agniassist.routers.rag",
    "router",
    "/api",
    "AI - RAG Chatbot"
)

include_router_safe(
    "agniassist.routers.ocr",
    "router",
    "/api",
    "AI - OCR"
)

include_router_safe(
    "agniassist.routers.predict",
    "router",
    "/api",
    "AI - Prediction"
)

include_router_safe(
    "agniassist.routers.summarize",
    "router",
    "/api",
    "AI - Summarization"
)


# ================= HEALTH =================
@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {
        "message": "Agniveer Sentinel Running",
        "docs": "/docs",
        "api_prefix": API_PREFIX
    }


# ================= RUN =================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True)
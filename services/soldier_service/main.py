"""Soldier Service Main Application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from common.core.config import settings
from common.core.database import init_db
from services.soldier_service.api.endpoints import soldier


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=f"{settings.APP_NAME} - Soldier Service",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    soldier.router,
    prefix=f"{settings.API_V1_PREFIX}/soldiers",
    tags=["Soldiers"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "soldier-service"}

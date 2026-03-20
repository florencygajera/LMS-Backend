"""ML Service Main Application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from common.core.config import settings
from common.core.database import init_db
from common.core.security_middleware import setup_security_middleware
from services.ml_service.api.endpoints import ml


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=f"{settings.APP_NAME} - ML Service",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

setup_security_middleware(app)

app.include_router(
    ml.router,
    prefix=f"{settings.API_V1_PREFIX}/ml",
    tags=["ML"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ml-service"}

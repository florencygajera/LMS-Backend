"""
Database Configuration Module
Agniveer Sentinel - Military Training Platform
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, DeclarativeBase
from sqlalchemy import Column, Integer, DateTime
from datetime import datetime
from typing import AsyncGenerator
from common.core.config import settings


# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


class TimestampMixin:
    """Mixin for timestamp columns"""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


def import_models() -> None:
    """Import SQLAlchemy models so they are registered in Base metadata."""
    # Importing model modules ensures Base.metadata knows all tables before create_all.
    from services.auth_service.models import user as _auth_models  # noqa: F401
    from services.recruitment_service.models import recruitment as _recruitment_models  # noqa: F401
    from services.soldier_service.models import soldier as _soldier_models  # noqa: F401
    
    # Training service uses soldier models (TrainingRecord is in soldier.py)
    # Report service generates reports from existing data
    # Notification service uses Redis, no persistent models needed
    # ML service uses file-based models
    # Weather service is external API
    # Document service stores files in S3/MinIO


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database connectivity for service startup."""
    import_models()
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: None)


async def drop_db():
    """Drop all database tables"""
    import_models()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

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


def get_engine():
    """Create engine dynamically to pick up config changes"""
    
    # SQLite doesn't support pool_size and max_overflow
    is_sqlite = settings.DATABASE_URL.startswith("sqlite")
    
    engine_kwargs = {
        "echo": settings.DEBUG,
        "pool_pre_ping": not is_sqlite,
    }
    
    if not is_sqlite:
        engine_kwargs["pool_size"] = 10
        engine_kwargs["max_overflow"] = 20
    
    return create_async_engine(
        settings.DATABASE_URL,
        **engine_kwargs
    )


# Create async engine (lazy initialization)
_engine = None

def get_db_engine():
    """Lazy initialization of database engine"""
    global _engine
    if _engine is None:
        _engine = get_engine()
    return _engine


# Create async session factory
AsyncSessionLocal = None

def get_async_session_local():
    """Get or create the async session factory"""
    global AsyncSessionLocal
    if AsyncSessionLocal is None:
        engine = get_db_engine()
        AsyncSessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return AsyncSessionLocal


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
    # Import from the model files directly to ensure they register with Base
    from services.auth_service.models.user import User, AuditLog, RefreshToken  # noqa: F401
    from services.recruitment_service.models.recruitment import (  # noqa: F401
        Candidate,
        CandidateDocument,
        Application,
        ExamCenter,
        Exam,
        ExamQuestion,
        ExamRegistration,
        AdmitCard,
    )
    from services.soldier_service.models.soldier import (  # noqa: F401
        Soldier,
        SoldierDocument,
        Battalion,
        BattalionPosting,
        MedicalRecord,
        MedicalAttachment,
        TrainingRecord,
        DailySchedule,
        Equipment,
        SoldierEvent,
        Stipend,
        PerformanceRanking,
        SOSAlert,
    )
    
    # Training service uses soldier models (TrainingRecord is in soldier.py)
    # Report service generates reports from existing data
    # Notification service uses Redis, no persistent models needed
    # ML service uses file-based models
    # Weather service is external API
    # Document service stores files in S3/MinIO


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session"""
    session_factory = get_async_session_local()
    async with session_factory() as session:
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
    engine = get_db_engine()
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: None)


async def drop_db():
    """Drop all database tables"""
    import_models()
    engine = get_db_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# Backward compatibility - module level attributes
def __getattr__(name):
    if name == "engine":
        return get_db_engine()
    if name == "AsyncSessionLocal":
        return get_async_session_local()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

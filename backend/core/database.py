"""Database configuration and session management."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import Column, DateTime, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.config import settings


logger = logging.getLogger(__name__)

# Check USE_SQLITE at module load time
_use_sqlite_env = os.environ.get("USE_SQLITE", "").strip().lower()
_USE_SQLITE = _use_sqlite_env in {"true", "1", "yes", "on"} or settings.USE_SQLITE

if _USE_SQLITE:
    _DATABASE_URL = "sqlite+aiosqlite:///./agniveer.db"
    logger.info("Using SQLite database (USE_SQLITE=true)")
else:
    _DATABASE_URL = settings.DATABASE_URL

# DEBUG: Log the actual database URL being used
logger.info(f"[DEBUG] Database Configuration -> USE_SQLITE={_USE_SQLITE}, DATABASE_URL={_DATABASE_URL}")

_engine = None
_async_session_local = None


def _build_engine(database_url: str):
    is_sqlite = database_url.startswith("sqlite")
    engine_kwargs = {
        "echo": settings.DEBUG,
        "pool_pre_ping": not is_sqlite,
    }
    if not is_sqlite:
        engine_kwargs["pool_size"] = 10
        engine_kwargs["max_overflow"] = 20
    return create_async_engine(database_url, **engine_kwargs)


def set_database_url(database_url: str) -> None:
    """Switch active database URL and reset engine/session factory."""
    global _DATABASE_URL, _engine, _async_session_local
    _DATABASE_URL = database_url
    _engine = None
    _async_session_local = None


def get_database_url() -> str:
    return _DATABASE_URL


def get_db_engine():
    """Lazy initialization of database engine."""
    global _engine
    if _engine is None:
        _engine = _build_engine(_DATABASE_URL)
    return _engine


def get_async_session_local():
    """Get or create the async session factory."""
    global _async_session_local
    if _async_session_local is None:
        _async_session_local = async_sessionmaker(
            get_db_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _async_session_local


class Base(DeclarativeBase):
    """Base class for all models."""


class TimestampMixin:
    """Mixin for timestamp columns."""

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


def import_models() -> None:
    """Import SQLAlchemy models so they are registered in Base metadata."""
    from models.user import AuditLog, RefreshToken, User  # noqa: F401
    from models.recruitment import (  # noqa: F401
        AdmitCard,
        Application,
        Candidate,
        CandidateDocument,
        Exam,
        ExamCenter,
        ExamQuestion,
        ExamRegistration,
    )
    from models.soldier import (  # noqa: F401
        Battalion,
        BattalionPosting,
        DailySchedule,
        Equipment,
        MedicalAttachment,
        MedicalRecord,
        PerformanceRanking,
        Soldier,
        SoldierDocument,
        SoldierEvent,
        SOSAlert,
        Stipend,
        TrainingRecord,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for getting a database session."""
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


async def _create_tables() -> None:
    import_models()
    engine = get_db_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _test_connection(database_url: str) -> bool:
    """
    Test if we can connect to the database.
    Returns True if connection successful, False otherwise.
    """
    is_sqlite = database_url.startswith("sqlite")
    if is_sqlite:
        # SQLite doesn't need connection test, just check file exists or is creatable
        return True
    
    try:
        engine = _build_engine(database_url)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        logger.info(f"[DB Connection Test] Successfully connected to {database_url[:30]}...")
        return True
    except Exception as e:
        logger.warning(f"[DB Connection Test] Failed to connect to {database_url[:30]}...: {e}")
        return False


async def init_db() -> str:
    """
    Initialize DB and create tables.
    Falls back to SQLite when primary database is unavailable.
    """
    current_url = get_database_url()
    
    # First, test the connection before trying to create tables
    logger.info(f"[DB Init] Testing connection to: {current_url[:50]}...")
    
    if not current_url.startswith("sqlite"):
        # Try PostgreSQL connection first
        connection_ok = await _test_connection(current_url)
        if not connection_ok:
            logger.warning("[DB Init] PostgreSQL connection failed, falling back to SQLite...")
            sqlite_url = "sqlite+aiosqlite:///./agniveer.db"
            set_database_url(sqlite_url)
            current_url = sqlite_url
    
    try:
        await _create_tables()
        return get_database_url()
    except Exception:
        sqlite_url = "sqlite+aiosqlite:///./agniveer.db"
        if get_database_url().startswith("sqlite"):
            logger.exception("Database initialization failed on SQLite.")
            raise
        logger.exception("Primary database init failed; switching to SQLite fallback.")
        set_database_url(sqlite_url)
        await _create_tables()
        return get_database_url()


async def drop_db():
    """Drop all database tables."""
    import_models()
    engine = get_db_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def __getattr__(name):
    if name == "engine":
        return get_db_engine()
    if name == "AsyncSessionLocal":
        return get_async_session_local()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")





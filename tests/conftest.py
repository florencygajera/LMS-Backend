"""
Testing Framework
Agniveer Sentinel - Enterprise Production
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import StaticPool

from common.core.database import Base
from common.core.config import settings


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def db_session():
    """Create test database session"""
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSession(engine) as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session):
    """Create test client"""
    # Import app from main
    from services.auth_service.main import app
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def sample_user_data():
    """Sample user data for tests"""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "password": "testpassword123"
    }


@pytest.fixture
def sample_soldier_data():
    """Sample soldier data for tests"""
    return {
        "full_name": "John Doe",
        "date_of_birth": "1995-01-01",
        "gender": "Male",
        "blood_group": "O+",
        "phone_number": "+1234567890",
        "email": "john@example.com",
        "emergency_contact_name": "Jane Doe",
        "emergency_contact_phone": "+0987654321",
        "permanent_address": "123 Test Street",
        "city": "Test City",
        "state": "Test State",
        "pincode": "123456",
        "joining_date": "2024-01-01",
        "rank": "Sepoy"
    }


@pytest.fixture
def sample_training_data():
    """Sample training data for tests"""
    return {
        "soldier_id": 1,
        "training_date": "2024-03-13",
        "training_type": "fitness",
        "running_time_minutes": 15.5,
        "pushups_count": 50,
        "pullups_count": 10,
        "endurance_score": 85.0,
        "bmi": 22.5
    }

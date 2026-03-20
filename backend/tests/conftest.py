"""
Testing Framework
Agniveer Sentinel - Enterprise Production
"""

from collections import defaultdict
from datetime import datetime, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.sql.elements import BinaryExpression

from core.database import get_db, import_models
from models.user import AuditLog, RefreshToken, User


class FakeScalarResult:
    def __init__(self, item):
        self._item = item

    def scalar_one_or_none(self):
        return self._item


class FakeAsyncSession:
    """Minimal async session used for API tests without an external database."""

    def __init__(self):
        self._store = defaultdict(list)
        self._ids = defaultdict(int)

    async def execute(self, statement):
        entity = statement.column_descriptions[0]["entity"]
        records = list(self._store[entity])

        for criterion in statement._where_criteria:
            if isinstance(criterion, BinaryExpression):
                field_name = criterion.left.key
                expected = criterion.right.value
                records = [r for r in records if getattr(r, field_name) == expected]

        return FakeScalarResult(records[0] if records else None)

    def add(self, instance):
        model = type(instance)
        if getattr(instance, "id", None) is None:
            self._ids[model] += 1
            instance.id = self._ids[model]

        if hasattr(instance, "uuid") and getattr(instance, "uuid", None) is None:
            instance.uuid = str(uuid4())
        if hasattr(instance, "created_at") and getattr(instance, "created_at", None) is None:
            instance.created_at = datetime.now(timezone.utc)
        if hasattr(instance, "updated_at") and getattr(instance, "updated_at", None) is None:
            instance.updated_at = datetime.now(timezone.utc)
        if isinstance(instance, User):
            if instance.is_active is None:
                instance.is_active = True
            if instance.is_verified is None:
                instance.is_verified = False

        if isinstance(instance, RefreshToken) and instance.is_revoked is None:
            instance.is_revoked = False

        self._store[model].append(instance)

    async def flush(self):
        return None

    async def commit(self):
        return None

    async def refresh(self, _instance):
        return None

    async def rollback(self):
        return None

    async def close(self):
        return None


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def db_session():
    yield FakeAsyncSession()


@pytest_asyncio.fixture
async def client(db_session):
    """Create test client with database dependency override."""
    from services.auth_service.main import app

    import_models()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for tests"""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "password": "testpassword123",
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
        "rank": "Sepoy",
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
        "bmi": 22.5,
    }





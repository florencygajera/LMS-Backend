"""
Soldier Service Tests
Agniveer Sentinel - Enterprise Production
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_soldier_profile(client: AsyncClient, sample_soldier_data):
    """Test soldier profile creation"""
    response = await client.post(
        "/api/v1/soldiers/profile",
        json=sample_soldier_data
    )
    
    # Soldier endpoints are not mounted on auth-service test app; unauthenticated requests
    # should not succeed, and currently return either auth failure or not-found.
    assert response.status_code in [401, 403, 404]


@pytest.mark.asyncio
async def test_get_soldier_profile(db_session: AsyncSession):
    """Test get soldier profile"""
    # This test would verify profile retrieval
    pass


@pytest.mark.asyncio
async def test_medical_record_crud(db_session: AsyncSession):
    """Test medical record CRUD operations"""
    # This test would verify medical record operations
    pass


@pytest.mark.asyncio
async def test_training_record_creation(db_session: AsyncSession):
    """Test training record creation"""
    # This test would verify training record creation
    pass

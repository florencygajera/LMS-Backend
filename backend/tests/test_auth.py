"""
Authentication Tests
Agniveer Sentinel - Enterprise Production
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient, sample_user_data):
    """Test user registration"""
    response = await client.post("/api/v1/auth/register", json=sample_user_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == sample_user_data["email"]
    assert data["username"] == sample_user_data["username"]


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, sample_user_data):
    """Test duplicate email registration"""
    # First registration
    await client.post("/api/v1/auth/register", json=sample_user_data)
    
    # Second registration with same email
    response = await client.post("/api/v1/auth/register", json=sample_user_data)
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, sample_user_data):
    """Test successful login"""
    # Register first
    await client.post("/api/v1/auth/register", json=sample_user_data)
    
    # Login
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": sample_user_data["username"],
            "password": sample_user_data["password"]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """Test login with invalid credentials"""
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "nonexistent",
            "password": "wrong"
        }
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, sample_user_data):
    """Test get current user"""
    # Register and login
    await client.post("/api/v1/auth/register", json=sample_user_data)
    login_response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": sample_user_data["username"],
            "password": sample_user_data["password"]
        }
    )
    token = login_response.json()["access_token"]
    
    # Get current user
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == sample_user_data["email"]


@pytest.mark.asyncio
async def test_change_password(client: AsyncClient, sample_user_data):
    """Test password change"""
    # Register and login
    await client.post("/api/v1/auth/register", json=sample_user_data)
    login_response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": sample_user_data["username"],
            "password": sample_user_data["password"]
        }
    )
    token = login_response.json()["access_token"]
    
    # Change password
    response = await client.post(
        "/api/v1/auth/password/change",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "current_password": sample_user_data["password"],
            "new_password": "newpassword123"
        }
    )
    
    assert response.status_code == 200




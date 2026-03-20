"""
Authentication Tests
Agniveer Sentinel - Enterprise Production
"""

import pytest
from httpx import AsyncClient


def _payload(response):
    data = response.json()
    if isinstance(data, dict) and "data" in data and "success" in data:
        return data["data"]
    return data


def _message(response):
    data = response.json()
    if isinstance(data, dict) and "message" in data:
        return data["message"]
    return ""


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient, sample_user_data):
    """Test user registration"""
    response = await client.post("/api/v1/auth/register", json=sample_user_data)
    
    assert response.status_code == 201
    data = _payload(response)
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
    assert "already registered" in _message(response).lower()


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
    data = _payload(response)
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
    token = _payload(login_response)["access_token"]
    
    # Get current user
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = _payload(response)
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
    token = _payload(login_response)["access_token"]
    
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


@pytest.mark.asyncio
async def test_refresh_token_flow(client: AsyncClient, sample_user_data):
    """Test refresh token exchange."""
    await client.post("/api/v1/auth/register", json=sample_user_data)
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": sample_user_data["username"], "password": sample_user_data["password"]},
    )
    login_data = _payload(login_response)
    refresh_token = login_data["refresh_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert response.status_code == 200
    data = _payload(response)
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(client: AsyncClient, sample_user_data):
    """Test logout revokes provided refresh token."""
    await client.post("/api/v1/auth/register", json=sample_user_data)
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": sample_user_data["username"], "password": sample_user_data["password"]},
    )
    login_data = _payload(login_response)
    refresh_token = login_data["refresh_token"]
    access_token = login_data["access_token"]

    logout_response = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"refresh_token": refresh_token},
    )
    assert logout_response.status_code == 200

    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_response.status_code == 401






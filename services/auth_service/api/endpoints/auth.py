"""
Authentication Endpoints
Agniveer Sentinel - Auth Service
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from typing import Optional

from common.core.database import get_db
from common.core.security import (
    get_password_hash, verify_password, 
    create_access_token, create_refresh_token, decode_token,
    get_current_user, RoleChecker
)
from common.models.base import UserRole
from services.auth_service.models.user import User, RefreshToken, AuditLog
from services.auth_service.schemas.user import (
    UserCreate, UserResponse, UserUpdate, UserLogin, Token,
    PasswordChange, PasswordReset, PasswordResetConfirm
)


router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user"""
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
        role=user_data.role,
        phone_number=user_data.phone_number,
    )
    db.add(user)
    await db.flush()
    
    # Log the registration
    audit_log = AuditLog(
        user_id=user.id,
        action="user_registered",
        details=f"User registered with role: {user_data.role.value}"
    )
    db.add(audit_log)
    await db.commit()
    
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """User login endpoint"""
    # Find user by username
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()
    
    # Check if user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        # Log failed attempt
        audit_log = AuditLog(
            user_id=user.id if user else None,
            action="login_failed",
            username=form_data.username,
            details="Invalid credentials"
        )
        db.add(audit_log)
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is locked. Please try again later."
        )
    
    # Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    # Reset failed login attempts
    user.failed_login_attempts = 0
    user.last_login = datetime.utcnow()
    
    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Store refresh token
    refresh_token_obj = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=datetime.utcnow() + timedelta(days=7),
        device_info=form_data.client_id
    )
    db.add(refresh_token_obj)
    
    # Log successful login
    audit_log = AuditLog(
        user_id=user.id,
        action="login_success",
        details=f"User logged in successfully"
    )
    db.add(audit_log)
    await db.commit()
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)):
    """Refresh access token using refresh token"""
    # Verify refresh token
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Check if refresh token exists in database
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token == refresh_token,
            RefreshToken.is_revoked == False
        )
    )
    stored_token = result.scalar_one_or_none()
    
    if not stored_token or stored_token.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired or revoked"
        )
    
    # Get user
    user_id = int(payload.get("sub"))
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Generate new tokens
    new_access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Revoke old refresh token
    stored_token.is_revoked = True
    
    # Store new refresh token
    new_refresh_token_obj = RefreshToken(
        user_id=user.id,
        token=new_refresh_token,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(new_refresh_token_obj)
    await db.commit()
    
    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Logout user and revoke refresh token"""
    # Log the logout
    audit_log = AuditLog(
        user_id=current_user.id,
        action="logout",
        details="User logged out"
    )
    db.add(audit_log)
    await db.commit()
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user information"""
    if user_data.email:
        # Check if email is already taken
        result = await db.execute(
            select(User).where(
                User.email == user_data.email,
                User.id != current_user.id
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        current_user.email = user_data.email
    
    if user_data.full_name:
        current_user.full_name = user_data.full_name
    
    if user_data.phone_number is not None:
        current_user.phone_number = user_data.phone_number
    
    if user_data.profile_photo_url is not None:
        current_user.profile_photo_url = user_data.profile_photo_url
    
    await db.commit()
    await db.refresh(current_user)
    
    return current_user


@router.post("/password/change")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password"""
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    current_user.password_changed_at = datetime.utcnow()
    
    # Log password change
    audit_log = AuditLog(
        user_id=current_user.id,
        action="password_changed",
        details="User changed their password"
    )
    db.add(audit_log)
    await db.commit()
    
    return {"message": "Password changed successfully"}


# Role-based access control
admin_only = RoleChecker([UserRole.SUPER_ADMIN, UserRole.ADMIN])

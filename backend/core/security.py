"""
Security Module - JWT Authentication & Password Hashing
Agniveer Sentinel - Military Training Platform
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Union, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.config import settings
from core.database import get_db


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """Get current authenticated user from token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    token_type: str = payload.get("type")
    
    if user_id is None or token_type != "access":
        raise credentials_exception
    
    # Import here to avoid circular imports
    from services.auth_service.models.user import User
    
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user


async def get_current_active_user(current_user = Depends(get_current_user)):
    """Get current active user"""
    return current_user


class RoleChecker:
    """Role-based access control checker"""
    
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, user = Depends(get_current_user)):
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(self.allowed_roles)}"
            )
        return user


# Role definitions
class UserRole:
    """User role constants"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    TRAINER = "trainer"
    DOCTOR = "doctor"
    SOLDIER = "soldier"
    CANDIDATE = "candidate"


# Permission definitions
class Permission:
    """Permission constants"""
    # Auth permissions
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    
    # Recruitment permissions
    MANAGE_RECRUITMENT = "manage_recruitment"
    VIEW_RECRUITMENT = "view_recruitment"
    
    # Exam permissions
    MANAGE_EXAMS = "manage_exams"
    TAKE_EXAM = "take_exam"
    VIEW_RESULTS = "view_results"
    
    # Soldier permissions
    MANAGE_SOLDIERS = "manage_soldiers"
    VIEW_SOLDIERS = "view_soldiers"
    
    # Medical permissions
    MANAGE_MEDICAL = "manage_medical"
    VIEW_MEDICAL = "view_medical"
    
    # Training permissions
    MANAGE_TRAINING = "manage_training"
    VIEW_TRAINING = "view_training"
    
    # Report permissions
    VIEW_REPORTS = "view_reports"
    GENERATE_REPORTS = "generate_reports"


# Role to permissions mapping
ROLE_PERMISSIONS = {
    UserRole.SUPER_ADMIN: [
        Permission.MANAGE_USERS, Permission.MANAGE_ROLES,
        Permission.MANAGE_RECRUITMENT, Permission.VIEW_RECRUITMENT,
        Permission.MANAGE_EXAMS, Permission.TAKE_EXAM, Permission.VIEW_RESULTS,
        Permission.MANAGE_SOLDIERS, Permission.VIEW_SOLDIERS,
        Permission.MANAGE_MEDICAL, Permission.VIEW_MEDICAL,
        Permission.MANAGE_TRAINING, Permission.VIEW_TRAINING,
        Permission.VIEW_REPORTS, Permission.GENERATE_REPORTS
    ],
    UserRole.ADMIN: [
        Permission.VIEW_RECRUITMENT,
        Permission.MANAGE_EXAMS, Permission.VIEW_RESULTS,
        Permission.MANAGE_SOLDIERS, Permission.VIEW_SOLDIERS,
        Permission.VIEW_MEDICAL,
        Permission.MANAGE_TRAINING, Permission.VIEW_TRAINING,
        Permission.VIEW_REPORTS, Permission.GENERATE_REPORTS
    ],
    UserRole.TRAINER: [
        Permission.VIEW_SOLDIERS,
        Permission.MANAGE_TRAINING, Permission.VIEW_TRAINING,
        Permission.VIEW_REPORTS, Permission.GENERATE_REPORTS
    ],
    UserRole.DOCTOR: [
        Permission.VIEW_SOLDIERS,
        Permission.MANAGE_MEDICAL, Permission.VIEW_MEDICAL
    ],
    UserRole.SOLDIER: [
        Permission.VIEW_TRAINING,
    ],
    UserRole.CANDIDATE: [
        Permission.VIEW_RECRUITMENT,
        Permission.TAKE_EXAM, Permission.VIEW_RESULTS
    ]
}



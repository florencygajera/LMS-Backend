"""
Authorization helpers.
"""

from typing import Iterable

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import get_current_user
from models.base import UserRole
from services.auth_service.models.user import User
from services.soldier_service.models.soldier import MedicalRecord, Soldier


def require_roles(*roles: UserRole):
    """Require the current user to have one of the supplied roles."""

    allowed_roles = set(roles)

    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to perform this action.",
            )
        return current_user

    return dependency


admin_required = require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)
trainer_required = require_roles(UserRole.TRAINER, UserRole.ADMIN, UserRole.SUPER_ADMIN)


async def can_access_soldier_profile(
    target_soldier_id: int,
    current_user: User,
    db: AsyncSession,
    allowed_roles: Iterable[UserRole] = (
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
        UserRole.TRAINER,
        UserRole.DOCTOR,
    ),
) -> Soldier:
    """Ensure the current user can access the requested soldier record."""

    result = await db.execute(select(Soldier).where(Soldier.id == target_soldier_id))
    soldier = result.scalar_one_or_none()
    if not soldier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Soldier not found")

    if current_user.role in set(allowed_roles) or soldier.user_id == current_user.id:
        return soldier

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to access this soldier profile.",
    )


async def can_access_medical_record(
    record_id: int,
    current_user: User,
    db: AsyncSession,
) -> MedicalRecord:
    """Ensure the current user can access the requested medical record."""

    result = await db.execute(select(MedicalRecord).where(MedicalRecord.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medical record not found")

    result = await db.execute(select(Soldier).where(Soldier.id == record.soldier_id))
    soldier = result.scalar_one_or_none()
    if not soldier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Soldier not found")

    if current_user.role in {
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
        UserRole.DOCTOR,
    } or soldier.user_id == current_user.id:
        return record

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to access this medical record.",
    )



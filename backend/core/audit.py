"""
Audit logging helpers.
"""

from typing import Optional

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from services.auth_service.models.user import AuditLog, User


async def log_security_event(
    db: AsyncSession,
    action: str,
    request: Optional[Request] = None,
    user: Optional[User] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    details: Optional[str] = None,
    status: str = "success",
) -> AuditLog:
    """Persist an audit event into the auth audit table."""

    audit_entry = AuditLog(
        user_id=user.id if user else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
        details=details,
        status=status,
    )
    db.add(audit_entry)
    await db.flush()
    return audit_entry

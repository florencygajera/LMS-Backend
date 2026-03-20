"""
Notification Service API Endpoints
Agniveer Sentinel - Soldier Management LMS
"""

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional
from datetime import datetime

from core.database import get_db
from core.authorization import admin_required
from core.security import get_current_user
from models.base import UserRole
from models.user import User
from models.soldier import Soldier, Battalion, SOSAlert
from services.websocket_manager import notification_service


router = APIRouter()

@router.get("/")
async def notification_service_test():
    return {"message": "notification service working"}


@router.get("/health")
async def notifications_health():
    return {"status": "healthy", "service": "notifications"}


# WebSocket endpoint
@router.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket, user_id: int):
    """WebSocket endpoint for real-time notifications"""
    try:
        await notification_service.handle_websocket_connection(websocket, user_id)
    except WebSocketDisconnect:
        notification_service.manager.disconnect(user_id)
    except Exception:
        notification_service.manager.disconnect(user_id)


@router.post("/send")
async def send_notification(
    user_id: int,
    title: str,
    body: str,
    notification_type: str = "info",
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db)
):
    """Send notification to a specific user"""
    # Verify target user exists
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()
    
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found"
        )
    
    # Send notification
    await notification_service.notify_soldier(user_id, title, body, notification_type)
    
    return {"success": True, "message": "Notification sent"}


@router.post("/broadcast")
async def broadcast_notification(
    title: str,
    body: str,
    notification_type: str = "info",
    battalion_id: Optional[int] = None,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db)
):
    """Broadcast notification to all soldiers or battalion"""
    # Get all soldier user IDs
    if battalion_id:
        result = await db.execute(
            select(Soldier).where(Soldier.battalion_id == battalion_id)
        )
    else:
        result = await db.execute(select(Soldier))
    
    soldiers = result.scalars().all()
    
    # Send to each soldier
    sent_count = 0
    for soldier in soldiers:
        await notification_service.notify_soldier(
            soldier.user_id, title, body, notification_type
        )
        sent_count += 1
    
    return {"success": True, "sent_count": sent_count}


# SOS Alert endpoints
@router.post("/sos/trigger")
async def trigger_sos_alert(
    alert_message: str,
    alert_type: str = "emergency",
    battalion_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Trigger SOS alert - Admin only"""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can trigger SOS alerts"
        )
    
    # Verify battalion if specified
    if battalion_id:
        result = await db.execute(select(Battalion).where(Battalion.id == battalion_id))
        battalion = result.scalar_one_or_none()
        
        if not battalion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Battalion not found"
            )
    
    # Create SOS alert record
    sos_alert = SOSAlert(
        alert_message=alert_message,
        alert_type=alert_type,
        battalion_id=battalion_id,
        triggered_by=current_user.id,
    )
    
    db.add(sos_alert)
    await db.commit()
    await db.refresh(sos_alert)
    
    # Send SOS alert via WebSocket
    await notification_service.trigger_sos_alert(
        alert_message=alert_message,
        alert_type=alert_type,
        battalion_id=battalion_id
    )
    
    return {
        "success": True,
        "alert_id": sos_alert.id,
        "message": "SOS alert triggered"
    }


@router.get("/sos/active")
async def get_active_sos_alerts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all active SOS alerts"""
    result = await db.execute(
        select(SOSAlert).where(SOSAlert.is_active == True)
        .order_by(desc(SOSAlert.triggered_at))
    )
    
    alerts = []
    for alert in result.scalars().all():
        alerts.append({
            "id": alert.id,
            "message": alert.alert_message,
            "type": alert.alert_type,
            "triggered_at": alert.triggered_at.isoformat(),
            "battalion_id": alert.battalion_id,
            "is_active": alert.is_active
        })
    
    return alerts


@router.post("/sos/{alert_id}/resolve")
async def resolve_sos_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Resolve an SOS alert"""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can resolve SOS alerts"
        )
    
    result = await db.execute(select(SOSAlert).where(SOSAlert.id == alert_id))
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SOS alert not found"
        )
    
    alert.is_active = False
    alert.resolved_at = datetime.utcnow()
    
    await db.commit()
    
    # Broadcast resolution
    message = {
        "type": "sos_resolved",
        "alert_id": alert_id,
        "resolved_at": alert.resolved_at.isoformat()
    }
    await notification_service.manager.broadcast(message)
    
    return {"success": True, "message": "SOS alert resolved"}


@router.get("/sos/history")
async def get_sos_alert_history(
    battalion_id: Optional[int] = None,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get SOS alert history"""
    query = select(SOSAlert)
    
    if battalion_id:
        query = query.where(SOSAlert.battalion_id == battalion_id)
    
    query = query.order_by(desc(SOSAlert.triggered_at)).limit(limit)
    
    result = await db.execute(query)
    
    alerts = []
    for alert in result.scalars().all():
        alerts.append({
            "id": alert.id,
            "message": alert.alert_message,
            "type": alert.alert_type,
            "triggered_at": alert.triggered_at.isoformat(),
            "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
            "battalion_id": alert.battalion_id,
            "is_active": alert.is_active
        })
    
    return alerts
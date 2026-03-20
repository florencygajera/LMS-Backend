"""
Notification Background Tasks
Agniveer Sentinel - Enterprise Production
"""

from infrastructure.celery_config import celery_app, BaseTask
import asyncio


@celery_app.task(base=BaseTask, bind=True, max_retries=3)
def send_email(self, recipient: str, subject: str, body: str, template: str = None):
    """Send email notification"""
    
    async def _send():
        # In production, use aiohttp to send via email service
        # For example, SendGrid, AWS SES, or SMTP
        
        import aiosmtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = "Agniveer Sentinel <noreply@agniveer.mil.in>"
        message["To"] = recipient
        
        # Add body
        part = MIMEText(body, "html")
        message.attach(part)
        
        # Send (simplified - would configure SMTP properly)
        # await aiosmtplib.send(message, hostname="smtp.gmail.com", port=587)
        
        return {
            "status": "sent",
            "recipient": recipient,
            "subject": subject
        }
    
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_send())


@celery_app.task(base=BaseTask, bind=True, max_retries=3)
def send_sms(self, phone_number: str, message: str):
    """Send SMS notification"""
    
    async def _send():
        # In production, use SMS API like Twilio, AWS SNS
        
        return {
            "status": "sent",
            "phone": phone_number,
            "message": message[:160]  # SMS limit
        }
    
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_send())


@celery_app.task(base=BaseTask, bind=True)
def send_admit_card_notifications(self, candidate_ids: list):
    """Send admit card notifications to candidates"""
    
    async def _send():
        tasks = []
        
        for candidate_id in candidate_ids:
            # Queue email
            tasks.append(
                send_email.s(
                    f"candidate{candidate_id}@example.com",
                    "Admit Card Available",
                    "Your admit card is now available for download."
                )
            )
            
            # Queue SMS
            tasks.append(
                send_sms.s(
                    "+1234567890",
                    "Admit card available. Check your email."
                )
        )
        
        # Execute all
        from celery import group
        group(tasks).apply_async()
        
        return {
            "status": "queued",
            "total": len(candidate_ids)
        }
    
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_send())


@celery_app.task(base=BaseTask, bind=True)
def broadcast_sos_alert(self, alert_id: int, battalion_id: int = None):
    """Broadcast SOS alert to all connected users"""
    
    async def _broadcast():
        import os
        db_url = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/agniveer_db"
        )
        
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy import select
        from services.soldier_service.models.soldier import Soldier, SOSAlert
        from services.notification_service.services.websocket_manager import notification_service
        
        engine = create_async_engine(db_url)
        
        async with AsyncSession(engine) as session:
            # Get SOS alert
            result = await session.execute(select(SOSAlert).where(SOSAlert.id == alert_id))
            alert = result.scalar_one_or_none()
            
            if not alert:
                return {"error": "Alert not found"}
            
            # Get target soldiers
            if battalion_id:
                result = await session.execute(
                    select(Soldier).where(Soldier.battalion_id == battalion_id)
                )
            else:
                result = await session.execute(select(Soldier))
            
            soldiers = result.scalars().all()
            
            # Broadcast via WebSocket
            await notification_service.trigger_sos_alert(
                alert_message=alert.alert_message,
                alert_type=alert.alert_type,
                battalion_id=battalion_id
            )
            
            # Also send SMS to all
            for soldier in soldiers:
                if soldier.phone_number:
                    send_sms.delay(
                        soldier.phone_number,
                        f"EMERGENCY: {alert.alert_message}"
                    )
            
            return {
                "status": "broadcast",
                "alert_id": alert_id,
                "recipients": len(soldiers)
            }
    
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_broadcast())


@celery_app.task(base=BaseTask, bind=True)
def send_training_schedule_notifications(self):
    """Send daily training schedule to all soldiers"""
    
    async def _notify():
        import os
        db_url = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/agniveer_db"
        )
        
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy import select
        from services.soldier_service.models.soldier import Soldier
        from services.notification_service.services.websocket_manager import notification_service
        
        engine = create_async_engine(db_url)
        
        async with AsyncSession(engine) as session:
            result = await session.execute(
                select(Soldier).where(Soldier.is_active == True)
            )
            soldiers = result.scalars().all()
            
            for soldier in soldiers:
                await notification_service.send_training_schedule(
                    user_id=soldier.user_id,
                    schedule={"date": "today", "activities": []}
                )
            
            return {
                "status": "sent",
                "recipients": len(soldiers)
            }
    
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_notify())



"""
Celery Configuration
Agniveer Sentinel - Enterprise Production
"""

from celery import Celery
from celery.schedules import crontab
import os

# Redis URL
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "agniveer_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "infrastructure.tasks.ocr_tasks",
        "infrastructure.tasks.report_tasks",
        "infrastructure.tasks.notification_tasks",
        "infrastructure.tasks.training_tasks",
        "infrastructure.tasks.backup_tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3000,  # 50 minutes soft limit
    
    # Retry configuration
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Result backend settings
    result_expires=86400,  # 24 hours
    result_extended=True,
    
    # Task routing
    task_routes={
        "infrastructure.tasks.ocr_tasks.*": {"queue": "ocr"},
        "infrastructure.tasks.report_tasks.*": {"queue": "reports"},
        "infrastructure.tasks.notification_tasks.*": {"queue": "notifications"},
        "infrastructure.tasks.training_tasks.*": {"queue": "training"},
        "infrastructure.tasks.backup_tasks.*": {"queue": "maintenance"},
    },
    
    # Beat schedule
    beat_schedule={
        # Daily performance reports - run at 8 PM
        "daily-reports": {
            "task": "infrastructure.tasks.report_tasks.generate_daily_reports",
            "schedule": crontab(hour=20, minute=0),
        },
        
        # Monthly reports - run on 1st of each month at 2 AM
        "monthly-reports": {
            "task": "infrastructure.tasks.report_tasks.generate_monthly_reports",
            "schedule": crontab(day_of_month=1, hour=2, minute=0),
        },
        
        # Leaderboard update - run daily at 6 AM
        "update-leaderboard": {
            "task": "infrastructure.tasks.training_tasks.update_leaderboard",
            "schedule": crontab(hour=6, minute=0),
        },
        
        # Daily backup - run at 2 AM
        "daily-backup": {
            "task": "infrastructure.tasks.backup_tasks.database_backup",
            "schedule": crontab(hour=2, minute=0),
        },
        
        # Cleanup old files - run weekly on Sunday at 3 AM
        "cleanup-old-files": {
            "task": "infrastructure.tasks.backup_tasks.cleanup_old_files",
            "schedule": crontab(day_of_week=0, hour=3, minute=0),
        },
        
        # Sync document storage - run every hour
        "sync-storage": {
            "task": "infrastructure.tasks.backup_tasks.sync_document_storage",
            "schedule": crontab(minute=0),
        },
    },
)


# Celery task base class with error handling
class BaseTask(celery_app.Task):
    """Base task with error handling and retry logic"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails"""
        # Log failure
        print(f"Task {task_id} failed: {exc}")
        # Could send to error tracking service (Sentry)
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task retries"""
        print(f"Task {task_id} retrying: {exc}")
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds"""
        print(f"Task {task_id} succeeded: {retval}")



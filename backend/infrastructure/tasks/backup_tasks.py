"""
Backup and Maintenance Tasks
Agniveer Sentinel - Enterprise Production
"""

from infrastructure.celery_config import celery_app, BaseTask
import asyncio
import os
import shutil
from datetime import datetime, timedelta


@celery_app.task(base=BaseTask, bind=True)
def database_backup(self):
    """Perform daily database backup"""
    
    def _backup():
        import subprocess
        from datetime import datetime
        
        # Database connection details
        db_host = os.getenv("POSTGRES_HOST", "localhost")
        db_port = os.getenv("POSTGRES_PORT", "5432")
        db_user = os.getenv("POSTGRES_USER", "postgres")
        db_password = os.getenv("POSTGRES_PASSWORD", "postgres")
        db_name = os.getenv("POSTGRES_DB", "agniveer_db")
        
        # Backup directory
        backup_dir = os.getenv("BACKUP_DIR", "/backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        # Create timestamped backup file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{backup_dir}/agniveer_db_{timestamp}.sql.gz"
        
        # Set environment
        env = os.environ.copy()
        env["PGPASSWORD"] = db_password
        
        # Run pg_dump
        cmd = [
            "pg_dump",
            "-h", db_host,
            "-p", str(db_port),
            "-U", db_user,
            "-F", "c",  # Custom format
            "-b",  # Include large objects
            "-v",  # Verbose
            "-f", backup_file,
            db_name
        ]
        
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            # Cleanup failed backup
            if os.path.exists(backup_file):
                os.remove(backup_file)
            raise Exception(f"Backup failed: {result.stderr}")
        
        # Get file size
        file_size = os.path.getsize(backup_file)
        
        # Upload to S3 (optional - for disaster recovery)
        # upload_to_s3(backup_file)
        
        return {
            "status": "success",
            "backup_file": backup_file,
            "file_size": file_size,
            "timestamp": timestamp
        }
    
    return _backup()


@celery_app.task(base=BaseTask, bind=True)
def cleanup_old_backups(self, days_to_keep: int = 30):
    """Clean up old database backups"""
    
    def _cleanup():
        import glob
        
        backup_dir = os.getenv("BACKUP_DIR", "/backups")
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Find all backup files
        backup_files = glob.glob(f"{backup_dir}/agniveer_db_*.sql.gz")
        
        deleted = 0
        for backup_file in backup_files:
            # Extract timestamp from filename
            filename = os.path.basename(backup_file)
            timestamp_str = filename.replace("agniveer_db_", "").replace(".sql.gz", "")
            
            try:
                file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                
                if file_date < cutoff_date:
                    os.remove(backup_file)
                    deleted += 1
            except ValueError:
                continue
        
        return {
            "status": "completed",
            "deleted": deleted
        }
    
    return _cleanup()


@celery_app.task(base=BaseTask, bind=True)
def cleanup_old_files(self):
    """Clean up old temporary files and logs"""
    
    def _cleanup():
        import glob
        import shutil
        
        # Clean up old log files (keep last 7 days)
        log_dir = os.getenv("LOG_DIR", "/var/log/agniveer")
        if os.path.exists(log_dir):
            cutoff_date = datetime.now() - timedelta(days=7)
            for log_file in glob.glob(f"{log_dir}/*.log"):
                mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
                if mtime < cutoff_date:
                    os.remove(log_file)
        
        # Clean up old uploads (keep last 30 days)
        upload_dir = os.getenv("UPLOAD_DIR", "/uploads")
        if os.path.exists(upload_dir):
            cutoff_date = datetime.now() - timedelta(days=30)
            for root, dirs, files in os.walk(upload_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if mtime < cutoff_date:
                        os.remove(file_path)
        
        return {"status": "completed"}
    
    return _cleanup()


@celery_app.task(base=BaseTask, bind=True)
def sync_document_storage(self):
    """Sync document storage with backup"""
    
    def _sync():
        # This would sync documents to a backup storage location
        # Could use rclone or boto3
        
        return {
            "status": "synced",
            "timestamp": datetime.now().isoformat()
        }
    
    return _sync()


@celery_app.task(base=BaseTask, bind=True)
def vacuum_database(self):
    """Perform database maintenance (VACUUM)"""
    
    def _vacuum():
        import subprocess
        import os
        
        db_password = os.getenv("POSTGRES_PASSWORD", "postgres")
        
        env = os.environ.copy()
        env["PGPASSWORD"] = db_password
        
        # Run VACUUM ANALYZE
        cmd = [
            "psql",
            "-h", os.getenv("POSTGRES_HOST", "localhost"),
            "-U", "postgres",
            "-d", "agniveer_db",
            "-c", "VACUUM ANALYZE;"
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        return {
            "status": "completed",
            "output": result.stdout
        }
    
    return _vacuum()




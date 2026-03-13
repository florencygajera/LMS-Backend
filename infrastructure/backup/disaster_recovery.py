"""
Disaster Recovery Scripts
Agniveer Sentinel - Enterprise Production
"""

import os
import subprocess
import boto3
from datetime import datetime, timedelta
import sys


class DisasterRecovery:
    """Disaster recovery management"""
    
    def __init__(self):
        self.s3_bucket = os.getenv("BACKUP_S3_BUCKET", "agniveer-backups")
        self.region = os.getenv("AWS_REGION", "eu-west-1")
        self.db_host = os.getenv("POSTGRES_HOST", "localhost")
        self.db_name = os.getenv("POSTGRES_DB", "agniveer_db")
        self.db_user = os.getenv("POSTGRES_USER", "postgres")
        
    def backup_database(self):
        """Perform full database backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"/tmp/agniveer_backup_{timestamp}.sql.gz"
        
        # Set password
        os.environ["PGPASSWORD"] = os.getenv("POSTGRES_PASSWORD", "postgres")
        
        # Run pg_dump
        cmd = [
            "pg_dump",
            "-h", self.db_host,
            "-U", self.db_user,
            "-F", "c",  # Custom format
            "-b",  # Blobs
            "-v",  # Verbose
            "-f", backup_file,
            self.db_name
        ]
        
        try:
            subprocess.run(cmd, check=True)
            print(f"Backup created: {backup_file}")
            
            # Upload to S3
            self.upload_to_s3(backup_file, f"daily/{timestamp}/agniveer_backup.sql.gz")
            
            # Cleanup local file
            os.remove(backup_file)
            
            return True
        except Exception as e:
            print(f"Backup failed: {e}")
            return False
    
    def upload_to_s3(self, local_file: str, s3_key: str):
        """Upload backup to S3"""
        s3_client = boto3.client('s3')
        
        try:
            s3_client.upload_file(
                local_file,
                self.s3_bucket,
                s3_key,
                ExtraArgs={
                    'ServerSideEncryption': 'AES256'
                }
            )
            print(f"Uploaded to S3: s3://{self.s3_bucket}/{s3_key}")
        except Exception as e:
            print(f"S3 upload failed: {e}")
    
    def restore_database(self, backup_timestamp: str):
        """Restore database from backup"""
        s3_key = f"daily/{backup_timestamp}/agniveer_backup.sql.gz"
        local_file = f"/tmp/restore_{backup_timestamp}.sql.gz"
        
        # Download from S3
        s3_client = boto3.client('s3')
        
        try:
            s3_client.download_file(self.s3_bucket, s3_key, local_file)
            print(f"Downloaded from S3: {s3_key}")
            
            # Drop existing database
            os.environ["PGPASSWORD"] = os.getenv("POSTGRES_PASSWORD", "postgres")
            
            # Drop and recreate database
            drop_cmd = [
                "psql",
                "-h", self.db_host,
                "-U", self.db_user,
                "-c", f"DROP DATABASE IF EXISTS {self.db_name}"
            ]
            subprocess.run(drop_cmd, check=True)
            
            create_cmd = [
                "psql",
                "-h", self.db_host,
                "-U", self.db_user,
                "-c", f"CREATE DATABASE {self.db_name}"
            ]
            subprocess.run(create_cmd, check=True)
            
            # Restore
            restore_cmd = [
                "pg_restore",
                "-h", self.db_host,
                "-U", self.db_user,
                "-d", self.db_name,
                "-v",
                local_file
            ]
            subprocess.run(restore_cmd, check=True)
            
            # Cleanup
            os.remove(local_file)
            
            print(f"Database restored successfully from {backup_timestamp}")
            return True
        except Exception as e:
            print(f"Restore failed: {e}")
            return False
    
    def cleanup_old_backups(self, retention_days: int = 30):
        """Clean up backups older than retention period"""
        s3_client = boto3.client('s3')
        
        try:
            # List objects
            response = s3_client.list_objects_v2(Bucket=self.s3_bucket, Prefix="daily/")
            
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            for obj in response.get('Contents', []):
                key = obj['Key']
                last_modified = obj['LastModified']
                
                if last_modified < cutoff_date:
                    s3_client.delete_object(Bucket=self.s3_bucket, Key=key)
                    print(f"Deleted old backup: {key}")
            
            print("Cleanup completed")
        except Exception as e:
            print(f"Cleanup failed: {e}")
    
    def create_snapshot(self):
        """Create database snapshot"""
        # Create RDS snapshot if using AWS RDS
        rds_client = boto3.client('rds', region_name=self.region)
        
        snapshot_id = f"agniveer-snapshot-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        try:
            response = rds_client.create_db_snapshot(
                DBSnapshotIdentifier=snapshot_id,
                DBInstanceIdentifier=os.getenv("RDS_INSTANCE_ID", "agniveer-db"),
                Tags=[
                    {'Key': 'Environment', 'Value': 'Production'},
                    {'Key': 'Backup', 'Value': 'Automated'}
                ]
            )
            print(f"Snapshot created: {snapshot_id}")
            return snapshot_id
        except Exception as e:
            print(f"Snapshot creation failed: {e}")
            return None
    
    def copy_to_drsite(self):
        """Copy latest backup to DR site"""
        # Copy backups to secondary region
        dr_region = os.getenv("DR_REGION", "eu-central-1")
        dr_bucket = os.getenv("DR_S3_BUCKET", "agniveer-backups-dr")
        
        s3_source = boto3.client('s3')
        s3_dest = boto3.client('s3', region_name=dr_region)
        
        try:
            # List latest backups
            response = s3_source.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix="daily/",
                SortBy='LastModified',
                Reverse=True
            )
            
            # Copy last 7 days to DR
            cutoff_date = datetime.now() - timedelta(days=7)
            
            for obj in response.get('Contents', [])[:10]:
                key = obj['Key']
                last_modified = obj['LastModified']
                
                if last_modified >= cutoff_date:
                    copy_source = {'Bucket': self.s3_bucket, 'Key': key}
                    s3_dest.copy_object(
                        CopySource=copy_source,
                        Bucket=dr_bucket,
                        Key=key,
                        ServerSideEncryption='AES256'
                    )
                    print(f"Copied to DR: {key}")
            
            print("DR copy completed")
        except Exception as e:
            print(f"DR copy failed: {e}")


def main():
    """Main function"""
    dr = DisasterRecovery()
    
    if len(sys.argv) < 2:
        print("Usage: python disaster_recovery.py [backup|restore|cleanup|snapshot|copy-dr]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "backup":
        dr.backup_database()
    elif command == "restore":
        if len(sys.argv) < 3:
            print("Usage: python disaster_recovery.py restore <timestamp>")
            sys.exit(1)
        dr.restore_database(sys.argv[2])
    elif command == "cleanup":
        dr.cleanup_old_backups()
    elif command == "snapshot":
        dr.create_snapshot()
    elif command == "copy-dr":
        dr.copy_to_drsite()
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()

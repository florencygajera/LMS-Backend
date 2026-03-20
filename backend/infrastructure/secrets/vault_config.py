"""
Secrets Management Configuration
Agniveer Sentinel - Enterprise Production
"""

import hvac
import os
import json


class SecretsManager:
    """HashiCorp Vault secrets management"""
    
    def __init__(self):
        self.vault_addr = os.getenv("VAULT_ADDR", "http://vault:8200")
        self.vault_token = os.getenv("VAULT_TOKEN")
        self.client = None
        
    def connect(self):
        """Connect to Vault"""
        if self.vault_token:
            self.client = hvac.Client(url=self.vault_addr, token=self.vault_token)
            print(f"Connected to Vault at {self.vault_addr}")
        else:
            print("Vault token not provided, using environment variables")
    
    def get_secret(self, path: str) -> dict:
        """Get secret from Vault"""
        if not self.client:
            # Fallback to environment
            return self._get_from_env(path)
        
        try:
            secret = self.client.secrets.kv.v2.read_secret_version(path=path)
            return secret['data']['data']
        except Exception as e:
            print(f"Failed to get secret from Vault: {e}")
            return self._get_from_env(path)
    
    def _get_from_env(self, path: str) -> dict:
        """Get secrets from environment as fallback"""
        # Map paths to env vars
        secrets_map = {
            'database': {
                'host': os.getenv('POSTGRES_HOST'),
                'port': os.getenv('POSTGRES_PORT'),
                'username': os.getenv('POSTGRES_USER'),
                'password': os.getenv('POSTGRES_PASSWORD'),
                'database': os.getenv('POSTGRES_DB')
            },
            'redis': {
                'host': os.getenv('REDIS_HOST'),
                'port': os.getenv('REDIS_PORT'),
                'password': os.getenv('REDIS_PASSWORD')
            },
            'jwt': {
                'secret_key': os.getenv('SECRET_KEY'),
                'algorithm': os.getenv('ALGORITHM', 'HS256')
            },
            's3': {
                'access_key': os.getenv('S3_ACCESS_KEY'),
                'secret_key': os.getenv('S3_SECRET_KEY'),
                'bucket': os.getenv('S3_BUCKET_NAME'),
                'endpoint': os.getenv('S3_ENDPOINT_URL')
            },
            'smtp': {
                'host': os.getenv('SMTP_HOST'),
                'port': os.getenv('SMTP_PORT'),
                'username': os.getenv('SMTP_USER'),
                'password': os.getenv('SMTP_PASSWORD')
            },
            'sms': {
                'api_key': os.getenv('SMS_API_KEY'),
                'api_url': os.getenv('SMS_API_URL')
            },
            'weather': {
                'api_key': os.getenv('OPENWEATHERMAP_API_KEY')
            }
        }
        
        return secrets_map.get(path, {})
    
    def set_secret(self, path: str, data: dict):
        """Set secret in Vault"""
        if not self.client:
            print("Vault not connected, cannot set secret")
            return False
        
        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=data
            )
            return True
        except Exception as e:
            print(f"Failed to set secret: {e}")
            return False
    
    def rotate_credentials(self):
        """Rotate all credentials"""
        # This would implement credential rotation policies
        print("Credential rotation triggered")
        
        # In production:
        # 1. Generate new credentials
        # 2. Update database/users
        # 3. Update Vault
        # 4. Restart services
        
        return {"status": "Rotation not implemented in demo"}


# Secrets required
SECRETS_SCHEMA = {
    "database": {
        "description": "Database credentials",
        "keys": ["host", "port", "username", "password", "database"]
    },
    "redis": {
        "description": "Redis cache credentials",
        "keys": ["host", "port", "password"]
    },
    "jwt": {
        "description": "JWT signing keys",
        "keys": ["secret_key", "algorithm"]
    },
    "s3": {
        "description": "S3/MinIO storage credentials",
        "keys": ["access_key", "secret_key", "bucket", "endpoint"]
    },
    "smtp": {
        "description": "Email service credentials",
        "keys": ["host", "port", "username", "password", "from_email"]
    },
    "sms": {
        "description": "SMS gateway credentials",
        "keys": ["api_key", "api_url"]
    },
    "weather": {
        "description": "Weather API key",
        "keys": ["api_key"]
    }
}


# Secrets rotation policy
ROTATION_POLICY = """
# Secrets Rotation Policy

## Database Credentials
- Rotation Frequency: Every 90 days
- Impact: Requires service restart
- Procedure: 
  1. Generate new credentials
  2. Update Vault
  3. Rolling restart of all services

## JWT Secrets
- Rotation Frequency: Every 30 days
- Impact: Users need to re-login
- Procedure:
  1. Generate new secret key
  2. Update Vault
  3. Deploy to all services

## API Keys (S3, SMS, etc.)
- Rotation Frequency: Every 60 days
- Impact: Low
- Procedure:
  1. Generate new keys
  2. Update Vault
  3. Deploy to relevant services
"""


# Singleton instance
secrets_manager = SecretsManager()



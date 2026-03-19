"""
Common Configuration Module
Agniveer Sentinel - Military Training Platform
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application Settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )
    
    # App Configuration
    APP_NAME: str = "Agniveer Sentinel"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "agniveer_db"
    
    # Use SQLite for local testing (set USE_SQLITE=true in .env)
    USE_SQLITE: bool = False
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL"""
        if self.USE_SQLITE:
            return "sqlite+aiosqlite:///./agniveer.db"
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def DATABASE_URL_SYNC(self) -> str:
        """Synchronous database URL"""
        if self.USE_SQLITE:
            return "sqlite:///./agniveer.db"
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    
    @property
    def REDIS_URL(self) -> str:
        """Construct Redis URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"
    
    # S3/MinIO Storage
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "agniveer-documents"
    S3_REGION: str = "us-east-1"
    S3_SECURE: bool = False
    
    # Weather API
    OPENWEATHERMAP_API_KEY: str = "your-api-key"
    OPENWEATHERMAP_BASE_URL: str = "https://api.openweathermap.org/data/2.5"
    
    # Email Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "noreply@agniveer.mil.in"
    SMTP_PASSWORD: str = "your-email-password"
    SMTP_FROM: str = "Agniveer Sentinel <noreply@agniveer.mil.in>"
    
    # SMS Configuration
    SMS_API_KEY: str = "your-sms-api-key"
    SMS_API_URL: str = "https://sms.example.com/api"
    
    # File Upload
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"]
    
    # OCR Configuration
    TESSERACT_DATA_PATH: Optional[str] = None
    
    # CORS
    BACKEND_CORS_ORIGINS_RAW: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        validation_alias="CORS_ORIGINS",
    )

    @property
    def BACKEND_CORS_ORIGINS(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.BACKEND_CORS_ORIGINS_RAW.split(",")
            if origin.strip()
        ]

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"debug", "development", "dev", "true", "1", "yes", "on"}:
                return True
            if normalized in {"release", "production", "prod", "false", "0", "no", "off"}:
                return False
        return value
    
    @field_validator("USE_SQLITE", mode="before")
    @classmethod
    def parse_sqlite(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "1", "yes", "on"}:
                return True
            if normalized in {"false", "0", "no", "off"}:
                return False
        return value



@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()

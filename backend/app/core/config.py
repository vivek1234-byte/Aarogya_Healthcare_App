from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, validator
import json
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "ArogyaSaathi Health Gateway"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Security & DPDP Compliance
    SECRET_KEY: str = "arogyasaathi_super_secret_jwt_key_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    
    # 32-byte Base64 AES-256 key for PII Encryption at rest
    PII_ENCRYPTION_KEY: str = "kXg_7vP8yR2mN5qL9wZ1tF4jB7cD0eH3aK6sV8xY2uI="
    # Salt for deterministic pseudonymization
    PSEUDONYM_SALT: str = "arogya_saathi_dpdp_salt_2026"

    # PostgreSQL Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "arogya_user"
    POSTGRES_PASSWORD: str = "arogya_secure_pass_2026"
    POSTGRES_DB: str = "arogyasaathi_db"

    DATABASE_URL: Union[str, None] = None
    SYNC_DATABASE_URL: Union[str, None] = None

    # Redis Cache & Message Broker
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery Task Queue
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # MinIO / S3 Object Storage
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "arogya_minio_admin"
    MINIO_SECRET_KEY: str = "arogya_minio_secret_key_2026"
    MINIO_BUCKET_AUDIO: str = "arogya-audio-records"
    MINIO_BUCKET_DOCS: str = "arogya-referral-docs"
    MINIO_SECURE: bool = False

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:8000",
        "*"
    ]

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_database_url(self, is_async: bool = True) -> str:
        if is_async:
            if self.DATABASE_URL:
                return self.DATABASE_URL
            return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        else:
            if self.SYNC_DATABASE_URL:
                return self.SYNC_DATABASE_URL
            return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()

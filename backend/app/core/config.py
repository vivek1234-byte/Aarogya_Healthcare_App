from typing import List, Union
import json
import os

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    HAS_PYDANTIC_SETTINGS = True
except ImportError:
    HAS_PYDANTIC_SETTINGS = False


if HAS_PYDANTIC_SETTINGS:
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

else:
    class SettingsFallback:
        PROJECT_NAME: str = os.getenv("PROJECT_NAME", "ArogyaSaathi Health Gateway")
        VERSION: str = os.getenv("VERSION", "0.1.0")
        API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")
        ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
        DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

        SECRET_KEY: str = os.getenv("SECRET_KEY", "arogyasaathi_super_secret_jwt_key_change_in_production")
        ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
        ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

        PII_ENCRYPTION_KEY: str = os.getenv("PII_ENCRYPTION_KEY", "kXg_7vP8yR2mN5qL9wZ1tF4jB7cD0eH3aK6sV8xY2uI=")
        PSEUDONYM_SALT: str = os.getenv("PSEUDONYM_SALT", "arogya_saathi_dpdp_salt_2026")

        POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
        POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
        POSTGRES_USER: str = os.getenv("POSTGRES_USER", "arogya_user")
        POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "arogya_secure_pass_2026")
        POSTGRES_DB: str = os.getenv("POSTGRES_DB", "arogyasaathi_db")

        DATABASE_URL: Union[str, None] = os.getenv("DATABASE_URL")
        SYNC_DATABASE_URL: Union[str, None] = os.getenv("SYNC_DATABASE_URL")

        REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
        REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
        REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
        CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

        MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "arogya_minio_admin")
        MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "arogya_minio_secret_key_2026")
        MINIO_BUCKET_AUDIO: str = os.getenv("MINIO_BUCKET_AUDIO", "arogya-audio-records")
        MINIO_BUCKET_DOCS: str = os.getenv("MINIO_BUCKET_DOCS", "arogya-referral-docs")
        MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"

        BACKEND_CORS_ORIGINS: List[str] = [
            "http://localhost:3000",
            "http://localhost:8080",
            "http://localhost:8000",
            "*"
        ]

        def get_database_url(self, is_async: bool = True) -> str:
            if is_async:
                if self.DATABASE_URL:
                    return self.DATABASE_URL
                return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            else:
                if self.SYNC_DATABASE_URL:
                    return self.SYNC_DATABASE_URL
                return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    settings = SettingsFallback()

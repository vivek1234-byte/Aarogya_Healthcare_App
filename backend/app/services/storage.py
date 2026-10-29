import io
import os
import uuid
from typing import Optional, Tuple
from app.core.config import settings

# Attempt import of minio, fallback to local file store if minio is unavailable or mock
try:
    from minio import Minio
    from minio.error import S3Error
    HAS_MINIO = True
except ImportError:
    HAS_MINIO = False


class StorageService:
    """
    Manages audio records, verbal consent clips, and doctor referral summaries
    in MinIO / S3 object storage with fallback to local storage for offline tests.
    """

    def __init__(self):
        self.endpoint = settings.MINIO_ENDPOINT
        self.access_key = settings.MINIO_ACCESS_KEY
        self.secret_key = settings.MINIO_SECRET_KEY
        self.secure = settings.MINIO_SECURE
        self.audio_bucket = settings.MINIO_BUCKET_AUDIO
        self.docs_bucket = settings.MINIO_BUCKET_DOCS
        self.client: Optional[Any] = None

        if HAS_MINIO:
            try:
                self.client = Minio(
                    self.endpoint,
                    access_key=self.access_key,
                    secret_key=self.secret_key,
                    secure=self.secure
                )
            except Exception:
                self.client = None

        # Local storage fallback directory
        self.local_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage_data")
        os.makedirs(os.path.join(self.local_dir, self.audio_bucket), exist_ok=True)
        os.makedirs(os.path.join(self.local_dir, self.docs_bucket), exist_ok=True)

    def _ensure_bucket(self, bucket_name: str):
        if self.client:
            try:
                if not self.client.bucket_exists(bucket_name):
                    self.client.make_bucket(bucket_name)
            except Exception:
                pass

    def upload_audio(self, file_bytes: bytes, filename: Optional[str] = None, content_type: str = "audio/wav") -> str:
        """Uploads audio recording (voice consent or triage audio) and returns storage URL."""
        if not filename:
            filename = f"audio_{uuid.uuid4().hex[:12]}.wav"

        # Try MinIO first
        if self.client:
            try:
                self._ensure_bucket(self.audio_bucket)
                stream = io.BytesIO(file_bytes)
                self.client.put_object(
                    self.audio_bucket,
                    filename,
                    stream,
                    length=len(file_bytes),
                    content_type=content_type
                )
                protocol = "https" if self.secure else "http"
                return f"{protocol}://{self.endpoint}/{self.audio_bucket}/{filename}"
            except Exception:
                pass

        # Local filesystem fallback
        dest_path = os.path.join(self.local_dir, self.audio_bucket, filename)
        with open(dest_path, "wb") as f:
            f.write(file_bytes)
        return f"file://{dest_path}"

    def upload_document(self, doc_content: str, filename: Optional[str] = None, content_type: str = "text/markdown") -> str:
        """Uploads doctor referral summary document and returns storage URL."""
        if not filename:
            filename = f"referral_{uuid.uuid4().hex[:12]}.md"

        data_bytes = doc_content.encode("utf-8")
        if self.client:
            try:
                self._ensure_bucket(self.docs_bucket)
                stream = io.BytesIO(data_bytes)
                self.client.put_object(
                    self.docs_bucket,
                    filename,
                    stream,
                    length=len(data_bytes),
                    content_type=content_type
                )
                protocol = "https" if self.secure else "http"
                return f"{protocol}://{self.endpoint}/{self.docs_bucket}/{filename}"
            except Exception:
                pass

        # Local filesystem fallback
        dest_path = os.path.join(self.local_dir, self.docs_bucket, filename)
        with open(dest_path, "wb") as f:
            f.write(data_bytes)
        return f"file://{dest_path}"


storage_service = StorageService()

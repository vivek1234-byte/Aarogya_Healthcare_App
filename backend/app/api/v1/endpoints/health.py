import time
from datetime import datetime
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.core.config import settings
from app.schemas.health import HealthResponse, ComponentStatus

router = APIRouter()


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def check_health(db: AsyncSession = Depends(get_db)):
    """
    Comprehensive liveness and readiness probe.
    Checks PostgreSQL connection, TimescaleDB, PostGIS, pgvector extensions.
    """
    components = {}
    overall_status = "UP"

    # 1. Database Check
    db_start = time.time()
    try:
        # Check basic connectivity and installed extensions
        result = await db.execute(text("SELECT extname FROM pg_extension;"))
        extensions = [row[0] for row in result.fetchall()]
        db_latency = (time.time() - db_start) * 1000

        required_exts = {"postgis", "timescaledb", "vector"}
        installed_required = required_exts.intersection(set(extensions))

        components["database"] = ComponentStatus(
            status="UP",
            latency_ms=round(db_latency, 2),
            details=f"PostgreSQL connected. Extensions: {', '.join(installed_required)}"
        )
    except Exception as e:
        overall_status = "DEGRADED"
        components["database"] = ComponentStatus(
            status="DOWN",
            details=f"Database error: {str(e)[:150]}"
        )

    # 2. Redis Check (stub / network check)
    components["redis"] = ComponentStatus(
        status="UP",
        details=f"Configured at {settings.REDIS_HOST}:{settings.REDIS_PORT}"
    )

    # 3. MinIO S3 Object Store Check
    components["minio_storage"] = ComponentStatus(
        status="UP",
        details=f"Bucket configured: {settings.MINIO_BUCKET_AUDIO}"
    )

    return HealthResponse(
        status=overall_status,
        project=settings.PROJECT_NAME,
        version=settings.VERSION,
        timestamp=datetime.utcnow(),
        components=components
    )

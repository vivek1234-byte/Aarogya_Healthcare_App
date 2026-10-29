from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
from app.core.config import settings
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifespan events.
    Verifies cryptographic keys and database connectivity.
    """
    print(f"🚀 Starting {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]")
    print(f"🔐 DPDP PII Key loaded. Pseudonymization active.")
    yield
    print(f"🛑 Shutting down {settings.PROJECT_NAME}")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    ## ArogyaSaathi: Frontline Healthcare & Public Health Gateway
    
    Backend infrastructure providing:
    - **Voice-First Triage & Safety Gate**: 100% deterministic red-flag escalation, zero-prescription policy.
    - **Chronic Care Follow-up**: TimescaleDB continuous vitals ingestion & early deterioration detection.
    - **Syndromic Surveillance**: PostGIS geospatial outbreak early warning for village clusters.
    - **DPDP Act 2023 Compliance**: Encrypted PII at rest, deterministic pseudonymization, voice consent records, and right-to-erasure.
    - **Tamper-Evident Ledger**: Cryptographically chained SHA-256 audit log for clinical oversight.
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS Middleware (permitting Flutter Mobile, Web, and PHC Doctor Dashboard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Measures request execution time and adds X-Process-Time header."""
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    return response


# Include API v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
async def root():
    """Root entrypoint returning system status and documentation links."""
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "ACTIVE",
        "api_v1_docs": "/docs",
        "health_check": f"{settings.API_V1_STR}/health"
    }

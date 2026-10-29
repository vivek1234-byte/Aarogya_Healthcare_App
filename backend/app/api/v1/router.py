from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, patients, vitals, triage, audit

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health Probes"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & RBAC"])
api_router.include_router(patients.router, prefix="/patients", tags=["Patients & DPDP"])
api_router.include_router(vitals.router, prefix="/vitals", tags=["Vitals & Chronic Care"])
api_router.include_router(triage.router, prefix="/triage", tags=["Voice Triage & Safety Gate"])
api_router.include_router(audit.router, prefix="/audit", tags=["Tamper-Evident Audit Ledger"])

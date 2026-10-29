from typing import List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogResponse, AuditChainVerificationResponse
from app.crud.audit import verify_audit_chain
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[AuditLogResponse])
async def get_audit_trail(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve tamper-evident audit logs.
    Restricted to Health Officers, Medical Officers, and System Administrators.
    """
    if current_user.role not in ["OFFICER", "DOCTOR", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to supervisory officers and doctors"
        )

    stmt = select(AuditLog).order_by(desc(AuditLog.id)).offset(skip).limit(limit)
    result = await db.execute(stmt)
    logs = result.scalars().all()
    return [AuditLogResponse.model_validate(log) for log in logs]


@router.get("/verify-chain", response_model=AuditChainVerificationResponse)
async def verify_ledger_integrity(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Verifies that the entire audit trail's SHA-256 chain is uncompromised and untampered.
    """
    if current_user.role not in ["OFFICER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to Health Officers and Administrators"
        )

    is_valid, count, broken_id = await verify_audit_chain(db)
    if not is_valid:
        return AuditChainVerificationResponse(
            is_valid=False,
            total_entries_verified=count,
            broken_entry_id=broken_id,
            message=f"CRITICAL: Audit log integrity violation detected at entry ID {broken_id}!"
        )

    return AuditChainVerificationResponse(
        is_valid=True,
        total_entries_verified=count,
        broken_entry_id=None,
        message=f"Audit trail verified. All {count} records mathematically valid."
    )

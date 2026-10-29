from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models.triage import Referral, Escalation
from app.models.user import User
from app.api.v1.endpoints.auth import get_current_user
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class ReferralReviewRequest(BaseModel):
    status: str = "ACCEPTED" # ACCEPTED, COMPLETED, CANCELLED
    doctor_notes: Optional[str] = None


class ReferralResponse(BaseModel):
    id: UUID
    encounter_id: UUID
    patient_id: UUID
    target_facility: str
    urgency_level: str
    summary_pdf_s3_url: Optional[str] = None
    summary_text: str
    status: str
    doctor_notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/pending", response_model=List[ReferralResponse])
async def list_pending_referrals(
    urgency: Optional[str] = Query(None, description="Filter by urgency e.g. CRITICAL_IMMEDIATE"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    PHC Doctor Escalation Queue.
    Returns all pending clinical referrals awaiting review, prioritized by urgency.
    """
    if current_user.role not in ["DOCTOR", "OFFICER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to medical officers and administrators"
        )

    stmt = select(Referral).where(Referral.status == "PENDING")
    if urgency:
        stmt = stmt.where(Referral.urgency_level == urgency)

    stmt = stmt.order_by(desc(Referral.created_at)).offset(skip).limit(limit)
    result = await db.execute(stmt)
    referrals = result.scalars().all()
    return [ReferralResponse.model_validate(r) for r in referrals]


@router.get("/{referral_id}", response_model=ReferralResponse)
async def get_referral_by_id(
    referral_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve details of a specific patient referral."""
    stmt = select(Referral).where(Referral.id == referral_id)
    result = await db.execute(stmt)
    referral = result.scalar_one_or_none()
    if not referral:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral not found")
    return ReferralResponse.model_validate(referral)


@router.patch("/{referral_id}/review", response_model=ReferralResponse)
async def review_referral(
    referral_id: UUID,
    review_in: ReferralReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Doctor reviews, accepts, or resolves a referral.
    """
    if current_user.role not in ["DOCTOR", "OFFICER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only medical officers can review referrals"
        )

    stmt = select(Referral).where(Referral.id == referral_id)
    result = await db.execute(stmt)
    referral = result.scalar_one_or_none()
    if not referral:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral not found")

    referral.status = review_in.status
    referral.doctor_id = current_user.id
    if review_in.doctor_notes:
        referral.doctor_notes = review_in.doctor_notes
    referral.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(referral)
    return ReferralResponse.model_validate(referral)

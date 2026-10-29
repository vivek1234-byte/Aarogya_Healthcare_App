from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.clinical import VitalsCreate, VitalsResponse, VitalsTrendResponse
from app.crud.vitals import record_vitals, get_patient_vitals_trend
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=VitalsResponse, status_code=status.HTTP_201_CREATED)
async def record_patient_vitals(
    vitals_in: VitalsCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ingests vital signs into TimescaleDB hypertable.
    Used by frontline health workers during home visits or clinic check-ins.
    """
    vitals = await record_vitals(db, vitals_in=vitals_in, recorded_by=current_user.id)
    return VitalsResponse.model_validate(vitals)


@router.get("/{patient_id}/trends", response_model=VitalsTrendResponse)
async def get_chronic_vitals_trend(
    patient_id: UUID,
    limit: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves time-series vitals with early deterioration calculation (Objective O2).
    Feeds directly into Flutter trend chart widgets.
    """
    records, deterioration_flag, reason = await get_patient_vitals_trend(db, patient_id=patient_id, limit=limit)
    
    # Calculate simple directional trend
    systolic_trend = "STABLE"
    if len(records) >= 2 and records[0].systolic_bp and records[-1].systolic_bp:
        diff = records[0].systolic_bp - records[-1].systolic_bp
        if diff > 10:
            systolic_trend = "RISING"
        elif diff < -10:
            systolic_trend = "FALLING"

    return VitalsTrendResponse(
        patient_id=patient_id,
        readings=[VitalsResponse.model_validate(r) for r in records],
        deterioration_flag=deterioration_flag,
        deterioration_reason=reason,
        systolic_trend=systolic_trend,
        glucose_trend="STABLE"
    )

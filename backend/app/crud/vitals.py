from typing import List, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.clinical import VitalsSeries
from app.schemas.clinical import VitalsCreate


async def record_vitals(db: AsyncSession, vitals_in: VitalsCreate, recorded_by: UUID = None) -> VitalsSeries:
    """Records a single vital observation into the TimescaleDB hypertable."""
    recorded_at = vitals_in.recorded_at or datetime.utcnow()
    vitals = VitalsSeries(
        recorded_at=recorded_at,
        patient_id=vitals_in.patient_id,
        encounter_id=vitals_in.encounter_id,
        systolic_bp=vitals_in.systolic_bp,
        diastolic_bp=vitals_in.diastolic_bp,
        blood_glucose=vitals_in.blood_glucose,
        glucose_context=vitals_in.glucose_context,
        pulse=vitals_in.pulse,
        spo2=vitals_in.spo2,
        temperature=vitals_in.temperature,
        recorded_by=recorded_by
    )
    db.add(vitals)
    await db.commit()
    return vitals


async def get_patient_vitals_trend(
    db: AsyncSession,
    patient_id: UUID,
    limit: int = 30
) -> Tuple[List[VitalsSeries], bool, str]:
    """
    Fetches vital time-series and evaluates clinical deterioration.
    Implements Objective O2: Flags deterioration in BP or blood glucose early.
    """
    stmt = (
        select(VitalsSeries)
        .where(VitalsSeries.patient_id == patient_id)
        .order_by(desc(VitalsSeries.recorded_at))
        .limit(limit)
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    if not records:
        return [], False, "No vitals recorded yet"

    # Analyze chronic trends across recent readings
    deterioration_flag = False
    reasons = []

    # Check Hypertension trend (e.g. Systolic BP >= 140 or Diastolic >= 90 consecutively)
    consecutive_high_bp = 0
    for r in records[:3]:
        if (r.systolic_bp and r.systolic_bp >= 140) or (r.diastolic_bp and r.diastolic_bp >= 90):
            consecutive_high_bp += 1
    
    if consecutive_high_bp >= 2:
        deterioration_flag = True
        reasons.append("Sustained elevated Blood Pressure (Stage 2 Hypertension trend)")

    # Check Diabetes trend (Fasting > 130 or Post-prandial > 180)
    consecutive_high_glucose = 0
    for r in records[:3]:
        if r.blood_glucose:
            if r.glucose_context == "FASTING" and r.blood_glucose > 130:
                consecutive_high_glucose += 1
            elif r.blood_glucose > 200:
                consecutive_high_glucose += 1

    if consecutive_high_glucose >= 2:
        deterioration_flag = True
        reasons.append("Persistent hyperglycemia detected across consecutive readings")

    # Check Hypoxia (SpO2 < 93%)
    if records[0].spo2 and records[0].spo2 < 93:
        deterioration_flag = True
        reasons.append("Critical SpO2 drop below 93%")

    reason_str = "; ".join(reasons) if reasons else "Vitals within stable chronic management limits"
    return records, deterioration_flag, reason_str

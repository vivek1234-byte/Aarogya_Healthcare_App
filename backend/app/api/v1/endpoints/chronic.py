from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.core.base_schema import BaseModel, Field
from app.models.clinical import VitalsSeries, MedicationAdherence
from app.models.patient import Patient
from app.models.user import User
from app.services.chronic_care import chronic_care_engine, DeteriorationRisk
from app.services.voice_checkin import voice_checkin_parser, ParsedCheckinData
from app.services.synthetic_cohort import cohort_benchmark
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()


class VoiceCheckinRequest(BaseModel):
    patient_id: UUID
    speech_transcript: str
    language: str = "hi"


class AdherenceLogCreate(BaseModel):
    patient_id: UUID
    medication_name: str
    status: str # TAKEN, MISSED, SKIPPED
    reason_for_miss: Optional[str] = None
    scheduled_time: Optional[datetime] = None


class VoiceCheckinResponse(BaseModel):
    parsed: ParsedCheckinData
    evaluation: DeteriorationRisk
    voice_feedback_text_hi: str
    voice_feedback_text_en: str


@router.post("/checkin/voice", response_model=VoiceCheckinResponse)
async def process_voice_checkin(
    request: VoiceCheckinRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ingests and parses spoken chronic check-in responses from patient or ASHA worker.
    Records vitals to TimescaleDB and logs adherence.
    """
    parsed = voice_checkin_parser.parse_checkin_speech(request.speech_transcript, default_language=request.language)
    now = datetime.utcnow()

    # 1. Record vitals if extracted
    if parsed.systolic_bp or parsed.blood_glucose:
        vitals_entry = VitalsSeries(
            recorded_at=now,
            patient_id=request.patient_id,
            systolic_bp=parsed.systolic_bp,
            diastolic_bp=parsed.diastolic_bp,
            blood_glucose=parsed.blood_glucose,
            glucose_context=parsed.glucose_context,
            recorded_by=current_user.id
        )
        db.add(vitals_entry)

    # 2. Record adherence if extracted
    if parsed.adherence_status:
        adh_entry = MedicationAdherence(
            patient_id=request.patient_id,
            medication_name=parsed.medication_name or "Prescribed Chronic Medication",
            scheduled_time=now,
            status=parsed.adherence_status,
            reason_for_miss=parsed.miss_reason
        )
        db.add(adh_entry)

    await db.commit()

    # 3. Fetch recent history for evaluation
    stmt_vitals = select(VitalsSeries).where(VitalsSeries.patient_id == request.patient_id).order_by(desc(VitalsSeries.recorded_at)).limit(30)
    res_vitals = await db.execute(stmt_vitals)
    vitals_history = [
        {"recorded_at": v.recorded_at, "systolic_bp": v.systolic_bp, "diastolic_bp": v.diastolic_bp, "blood_glucose": v.blood_glucose, "glucose_context": v.glucose_context}
        for v in res_vitals.scalars().all()
    ]

    stmt_adh = select(MedicationAdherence).where(MedicationAdherence.patient_id == request.patient_id).order_by(desc(MedicationAdherence.scheduled_time)).limit(30)
    res_adh = await db.execute(stmt_adh)
    adh_history = [
        {"scheduled_time": a.scheduled_time, "status": a.status, "reason_for_miss": a.reason_for_miss}
        for a in res_adh.scalars().all()
    ]

    eval_result = chronic_care_engine.evaluate_patient_deterioration(
        vitals_list=vitals_history,
        adherence_records=adh_history
    )

    # Generate feedback voice text
    if eval_result.risk_level in ["CRITICAL", "HIGH"]:
        feedback_hi = "सावधानी: आपकी रीडिंग बढ़ी हुई है। आशा कार्यकर्ता को सूचित कर दिया गया है।"
        feedback_en = "Warning: Your readings are elevated. Your community health worker has been notified."
    elif parsed.adherence_status == "MISSED":
        feedback_hi = "कृपया अपनी दवाई नियमित रूप से लें। स्वास्थ्य केंद्र से नई दवा प्राप्त करें।"
        feedback_en = "Please ensure your daily medication is taken regularly. Collect refill from health post."
    else:
        feedback_hi = "धन्यवाद, आपकी जानकारी दर्ज कर ली गई है। आपका स्वास्थ्य स्थिर है।"
        feedback_en = "Thank you, your records are saved. Your health trends appear stable."

    return VoiceCheckinResponse(
        parsed=parsed,
        evaluation=eval_result,
        voice_feedback_text_hi=feedback_hi,
        voice_feedback_text_en=feedback_en
    )


@router.post("/adherence", status_code=status.HTTP_201_CREATED)
async def log_medication_adherence(
    adherence_in: AdherenceLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Logs individual dose adherence (taken, missed, or skipped with reason)."""
    entry = MedicationAdherence(
        patient_id=adherence_in.patient_id,
        medication_name=adherence_in.medication_name,
        scheduled_time=adherence_in.scheduled_time or datetime.utcnow(),
        status=adherence_in.status,
        reason_for_miss=adherence_in.reason_for_miss
    )
    db.add(entry)
    await db.commit()
    return {"status": "SUCCESS", "message": "Adherence logged successfully"}


@router.get("/patients/{patient_id}/evaluation", response_model=DeteriorationRisk)
async def evaluate_patient_chronic_status(
    patient_id: UUID,
    days_back: int = Query(30, ge=7, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns full longitudinal evaluation for Hypertension & Diabetes.
    Calculates moving averages, velocity/slope, adherence score, and early warnings.
    """
    since_date = datetime.utcnow() - timedelta(days=days_back)
    
    # Query vitals
    stmt_vitals = select(VitalsSeries).where(
        VitalsSeries.patient_id == patient_id,
        VitalsSeries.recorded_at >= since_date
    ).order_by(desc(VitalsSeries.recorded_at))
    res_vitals = await db.execute(stmt_vitals)
    vitals_history = [
        {"recorded_at": v.recorded_at, "systolic_bp": v.systolic_bp, "diastolic_bp": v.diastolic_bp, "blood_glucose": v.blood_glucose, "glucose_context": v.glucose_context}
        for v in res_vitals.scalars().all()
    ]

    # Query adherence
    stmt_adh = select(MedicationAdherence).where(
        MedicationAdherence.patient_id == patient_id,
        MedicationAdherence.scheduled_time >= since_date
    ).order_by(desc(MedicationAdherence.scheduled_time))
    res_adh = await db.execute(stmt_adh)
    adh_history = [
        {"scheduled_time": a.scheduled_time, "status": a.status, "reason_for_miss": a.reason_for_miss}
        for a in res_adh.scalars().all()
    ]

    return chronic_care_engine.evaluate_patient_deterioration(
        vitals_list=vitals_history,
        adherence_records=adh_history
    )


@router.get("/village/{village_id}/action-queue")
async def get_asha_village_action_queue(
    village_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ASHA Daily Priority Action Queue:
    Ranks patients in the village based on clinical deterioration risk (CRITICAL -> HIGH -> MODERATE).
    Enables targeted home visits before severe complications occur.
    """
    stmt = select(Patient).where(Patient.village_id == village_id, Patient.is_active == True)
    res = await db.execute(stmt)
    patients = res.scalars().all()

    action_list = []
    for p in patients:
        # Fetch vitals
        stmt_v = select(VitalsSeries).where(VitalsSeries.patient_id == p.id).order_by(desc(VitalsSeries.recorded_at)).limit(10)
        res_v = await db.execute(stmt_v)
        vitals = [
            {"recorded_at": v.recorded_at, "systolic_bp": v.systolic_bp, "diastolic_bp": v.diastolic_bp, "blood_glucose": v.blood_glucose}
            for v in res_v.scalars().all()
        ]

        # Fetch adherence
        stmt_a = select(MedicationAdherence).where(MedicationAdherence.patient_id == p.id).order_by(desc(MedicationAdherence.scheduled_time)).limit(10)
        res_a = await db.execute(stmt_a)
        adh = [
            {"scheduled_time": a.scheduled_time, "status": a.status}
            for a in res_a.scalars().all()
        ]

        risk = chronic_care_engine.evaluate_patient_deterioration(vitals_list=vitals, adherence_records=adh)
        if risk.is_deteriorating:
            action_list.append({
                "patient_id": str(p.id),
                "pseudonym_id": p.pseudonym_id,
                "age": p.age,
                "gender": p.gender,
                "risk_level": risk.risk_level,
                "action_priority": risk.action_priority,
                "recommended_action": risk.recommended_action,
                "flags": risk.flags,
                "latest_systolic": risk.average_systolic,
                "adherence_rate_pct": risk.adherence_rate_pct
            })

    # Sort by priority (1=highest)
    action_list.sort(key=lambda x: x["action_priority"])
    return {
        "village_id": village_id,
        "total_requiring_action": len(action_list),
        "priority_roster": action_list
    }


@router.post("/synthetic/benchmark")
async def run_objective_o2_simulation_benchmark(
    cohort_size: int = Query(50, ge=10, le=200),
    current_user: User = Depends(get_current_user)
):
    """
    Executes the Synthea-style simulated chronic cohort benchmark.
    Verifies Objective O2 compliance (Deterioration flagged >= 7 days before next visit).
    """
    results = cohort_benchmark.run_objective_o2_benchmark(num_patients=cohort_size)
    return results

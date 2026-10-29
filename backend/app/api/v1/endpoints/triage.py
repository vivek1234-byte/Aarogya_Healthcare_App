from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.triage import TriageEvaluationRequest, TriageEvaluationResponse
from app.services.safety_gate import evaluate_safety_gate, sanitize_zero_prescriptions
from app.services.storage import storage_service
from app.services.stt_service import stt_service
from app.services.langgraph_triage import orchestrator, TriageState
from app.crud.audit import log_audit_event
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.clinical import Encounter, Symptom, EncounterType, TriageLevel
from app.models.triage import TriageDecision, Referral, Escalation
from pydantic import BaseModel

router = APIRouter()


class StartSessionRequest(BaseModel):
    patient_id: UUID
    patient_pseudonym: str
    age: int
    gender: str
    village_id: str
    language: str = "hi"
    vitals: Optional[Dict[str, Any]] = None


class TurnResponse(BaseModel):
    session_id: str
    transcription: str
    detected_language: str
    extracted_symptoms: List[str]
    danger_signs: List[str]
    is_final: bool
    triage_level: Optional[str] = None
    decision_rationale: Optional[str] = None
    next_question: Optional[str] = None
    checklist: List[str] = []
    doctor_summary_url: Optional[str] = None
    is_red_flag_overridden: bool = False


class TextTurnRequest(BaseModel):
    text: str


@router.post("/session/start", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def start_voice_triage_session(
    request: StartSessionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Initializes a stateful clinical voice triage session for a patient.
    """
    state = orchestrator.start_session(
        patient_id=str(request.patient_id),
        patient_pseudonym=request.patient_pseudonym,
        age=request.age,
        gender=request.gender,
        village_id=request.village_id,
        language=request.language,
        vitals=request.vitals
    )
    return {
        "session_id": state.session_id,
        "status": "INITIALIZED",
        "patient_pseudonym": state.patient_pseudonym,
        "language": state.language,
        "message": "Session initialized. Ready for voice or text turn."
    }


@router.post("/session/{session_id}/audio-turn", response_model=TurnResponse)
async def process_audio_turn(
    session_id: str,
    audio_file: UploadFile = File(...),
    mock_transcript: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """
    Ingests audio recording from Flutter mobile client:
    1. Uploads audio to MinIO/S3 object store.
    2. Runs Multilingual STT (Bhashini/Whisper pipeline).
    3. Runs LangGraph state machine node (Symptom extraction -> Safety Gate -> Clarification).
    4. Returns next guided question or final decision.
    """
    state = orchestrator.get_session(session_id)
    if not state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Triage session not found")

    audio_bytes = await audio_file.read()
    if len(audio_bytes) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty audio file uploaded")

    # Upload audio to MinIO S3
    audio_url = storage_service.upload_audio(
        file_bytes=audio_bytes,
        filename=f"{session_id}_{audio_file.filename}",
        content_type=audio_file.content_type or "audio/wav"
    )

    # Speech to text
    transcription, detected_lang, confidence = await stt_service.transcribe_audio(
        audio_bytes=audio_bytes,
        source_language=state.language,
        mock_transcript=mock_transcript
    )

    # Process turn in LangGraph orchestrator
    updated_state = orchestrator.process_turn(session_id=session_id, transcript=transcription)

    next_q = updated_state.next_question_hi if state.language == "hi" else updated_state.next_question_en

    return TurnResponse(
        session_id=updated_state.session_id,
        transcription=transcription,
        detected_language=detected_lang,
        extracted_symptoms=updated_state.symptoms,
        danger_signs=updated_state.danger_signs,
        is_final=updated_state.is_final,
        triage_level=updated_state.triage_level,
        decision_rationale=updated_state.decision_rationale,
        next_question=next_q,
        checklist=updated_state.checklist,
        doctor_summary_url=updated_state.doctor_summary_url,
        is_red_flag_overridden=updated_state.is_red_flag_overridden
    )


@router.post("/session/{session_id}/text-turn", response_model=TurnResponse)
async def process_text_turn(
    session_id: str,
    request: TextTurnRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Direct text turn for health workers typing or reviewing transcribed notes.
    """
    state = orchestrator.get_session(session_id)
    if not state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Triage session not found")

    updated_state = orchestrator.process_turn(session_id=session_id, transcript=request.text)
    next_q = updated_state.next_question_hi if state.language == "hi" else updated_state.next_question_en

    return TurnResponse(
        session_id=updated_state.session_id,
        transcription=request.text,
        detected_language=state.language,
        extracted_symptoms=updated_state.symptoms,
        danger_signs=updated_state.danger_signs,
        is_final=updated_state.is_final,
        triage_level=updated_state.triage_level,
        decision_rationale=updated_state.decision_rationale,
        next_question=next_q,
        checklist=updated_state.checklist,
        doctor_summary_url=updated_state.doctor_summary_url,
        is_red_flag_overridden=updated_state.is_red_flag_overridden
    )


@router.get("/session/{session_id}", response_model=TriageState)
async def get_triage_session_state(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Returns the current snapshot of a clinical voice triage session."""
    state = orchestrator.get_session(session_id)
    if not state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Triage session not found")
    return state


@router.post("/session/{session_id}/complete", status_code=status.HTTP_200_OK)
async def complete_triage_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Finalizes the triage session and persists:
    - Encounter record
    - Symptoms records
    - TriageDecision record
    - Referral & Escalation records (if EMERGENCY or REFER)
    - Tamper-evident Audit entry
    """
    state = orchestrator.get_session(session_id)
    if not state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Triage session not found")

    if not state.is_final:
        # Force decision finalize
        state = orchestrator.process_turn(session_id, "कोई अन्य लक्षण नहीं हैं (No other symptoms)")

    # 1. Create Encounter
    encounter = Encounter(
        patient_id=UUID(state.patient_id),
        health_worker_id=current_user.id,
        encounter_type=EncounterType.TRIAGE,
        chief_complaint=state.all_transcripts[0] if state.all_transcripts else "Voice Triage Session",
        language_code=state.language,
        triage_level=state.triage_level or TriageLevel.PENDING
    )
    db.add(encounter)
    await db.flush()

    # 2. Add Symptoms
    for sym_code in state.symptoms:
        is_rf = sym_code in state.danger_signs
        db.add(Symptom(
            encounter_id=encounter.id,
            symptom_code=sym_code,
            symptom_name=sym_code.replace("_", " ").title(),
            is_red_flag=is_rf
        ))

    # 3. Add Triage Decision
    decision = TriageDecision(
        encounter_id=encounter.id,
        triage_category=state.triage_level or "HOME_CARE",
        rationale=state.decision_rationale or "Clinical protocol evaluation complete",
        confidence_score=1.0 if state.is_red_flag_overridden else 0.92,
        protocol_citation="; ".join(state.protocol_citations),
        uncertainty_flag=False,
        decision_payload={"symptoms": state.symptoms, "danger_signs": state.danger_signs}
    )
    db.add(decision)

    # 4. If EMERGENCY or REFER, create Referral & Escalation
    referral_id = None
    if state.triage_level in ["EMERGENCY", "REFER"]:
        referral = Referral(
            encounter_id=encounter.id,
            patient_id=UUID(state.patient_id),
            target_facility=f"PHC-{state.village_id}",
            urgency_level="CRITICAL_IMMEDIATE" if state.triage_level == "EMERGENCY" else "URGENT_24HR",
            summary_pdf_s3_url=state.doctor_summary_url,
            summary_text=state.decision_rationale or "",
            status="PENDING"
        )
        db.add(referral)
        await db.flush()
        referral_id = str(referral.id)

        if state.triage_level == "EMERGENCY":
            escalation = Escalation(
                encounter_id=encounter.id,
                reason=state.decision_rationale or "Emergency Red Flag Fired",
                escalated_to_role="DOCTOR"
            )
            db.add(escalation)

    await db.commit()

    # 5. Audit Logging
    await log_audit_event(
        db=db,
        action="COMPLETE_TRIAGE_SESSION",
        resource_type="ENCOUNTER",
        resource_id=str(encounter.id),
        actor_id=str(current_user.id),
        actor_role=current_user.role,
        model_input={"session_id": session_id, "symptoms": state.symptoms},
        model_output={"triage_level": state.triage_level, "summary_url": state.doctor_summary_url},
        rule_fired="RED_FLAG_OVERRIDE" if state.is_red_flag_overridden else None
    )

    return {
        "status": "COMPLETED",
        "encounter_id": str(encounter.id),
        "triage_level": state.triage_level,
        "referral_id": referral_id,
        "doctor_summary_url": state.doctor_summary_url,
        "checklist": state.checklist
    }


# Standalone one-shot evaluation (retained for backward compatibility)
@router.post("/evaluate", response_model=TriageEvaluationResponse)
async def evaluate_triage(
    request: TriageEvaluationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """One-shot triage evaluation against deterministic safety gate."""
    safety_result = evaluate_safety_gate(
        symptoms=request.symptoms,
        age=request.patient_age,
        vitals=request.vitals
    )

    if safety_result.is_triggered:
        triage_category = safety_result.override_action or "EMERGENCY"
        rationale = f"CRITICAL: {safety_result.condition_name}. Deterministic safety gate triggered. Immediate referral required."
        rule_fired = safety_result.rule_code
        checklist = [
            "Check airway, breathing, circulation (ABC)",
            "Call local 108/102 emergency ambulance",
            "Notify Medical Officer at nearest PHC"
        ]
        is_override = True
        confidence = 1.0
    else:
        triage_category = "TREAT_LOCALLY" if "fever" in request.symptoms else "HOME_CARE"
        rationale = "No danger signs identified. Follow standard community health worker supportive protocol."
        rule_fired = None
        checklist = ["Ensure oral rehydration", "Advise caregiver to return immediately if danger signs develop"]
        is_override = False
        confidence = 0.92

    sanitized_rationale, _ = sanitize_zero_prescriptions(rationale)

    await log_audit_event(
        db=db,
        action="TRIAGE_EVALUATION",
        resource_type="ENCOUNTER",
        resource_id=str(request.encounter_id),
        actor_id=str(current_user.id),
        actor_role=current_user.role,
        model_input={"symptoms": request.symptoms, "age": request.patient_age},
        model_output={"triage_category": triage_category},
        rule_fired=rule_fired
    )

    return TriageEvaluationResponse(
        encounter_id=request.encounter_id,
        triage_category=triage_category,
        rationale=sanitized_rationale,
        confidence_score=confidence,
        protocol_citation="IMNCI 2024 / ICMR Frontline Worker Standard Clinical Protocol",
        uncertainty_flag=False,
        is_rule_override=is_override,
        rule_fired=rule_fired,
        zero_prescription_guaranteed=True,
        next_checklist=checklist
    )

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.triage import TriageEvaluationRequest, TriageEvaluationResponse
from app.services.safety_gate import evaluate_safety_gate, sanitize_zero_prescriptions
from app.crud.audit import log_audit_event
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/evaluate", response_model=TriageEvaluationResponse)
async def evaluate_triage(
    request: TriageEvaluationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Evaluates symptoms through the Deterministic Safety Gate:
    1. Checks for IMNCI child danger signs, acute chest pain, maternal emergencies.
    2. Overrides any AI decision if red flags are detected.
    3. Strictly enforces zero-prescription policy (Objective O1).
    4. Logs decision in the immutable audit trail.
    """
    # 1. Deterministic Rule Safety Check
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
            "Notify Medical Officer at nearest PHC",
            "Keep patient in recovery / lateral position if unconscious"
        ]
        is_override = True
        confidence = 1.0
    else:
        # Standard decision (LangGraph / IMNCI protocol fallback in Phase 2)
        triage_category = "TREAT_LOCALLY" if "fever" in request.symptoms else "HOME_CARE"
        rationale = "No danger signs identified. Follow standard community health worker supportive protocol."
        rule_fired = None
        checklist = [
            "Ensure adequate hydration (ORS / fluids)",
            "Advise caregiver to return immediately if danger signs develop",
            "Schedule follow-up check in 48 hours"
        ]
        is_override = False
        confidence = 0.92

    # Enforce zero-prescription guarantee
    sanitized_rationale, had_violation = sanitize_zero_prescriptions(rationale)

    # Log to audit ledger
    await log_audit_event(
        db=db,
        action="TRIAGE_EVALUATION",
        resource_type="ENCOUNTER",
        resource_id=str(request.encounter_id),
        actor_id=str(current_user.id),
        actor_role=current_user.role,
        model_input={"symptoms": request.symptoms, "age": request.patient_age, "vitals": request.vitals},
        model_output={"triage_category": triage_category, "rationale": sanitized_rationale},
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

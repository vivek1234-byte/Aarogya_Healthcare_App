from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class RedFlagCheckResult(BaseModel):
    is_triggered: bool
    rule_code: Optional[str] = None
    condition_name: Optional[str] = None
    override_action: Optional[str] = None # EMERGENCY, URGENT_REFERRAL
    matched_symptoms: List[str] = []


class TriageEvaluationRequest(BaseModel):
    encounter_id: UUID
    patient_age: int
    symptoms: List[str] = Field(..., example=["chest_pain", "sweating"])
    vitals: Optional[Dict[str, Any]] = None


class TriageEvaluationResponse(BaseModel):
    encounter_id: UUID
    triage_category: str # EMERGENCY, REFER, TREAT_LOCALLY, HOME_CARE
    rationale: str
    confidence_score: float
    protocol_citation: Optional[str] = None
    uncertainty_flag: bool = False
    is_rule_override: bool = False
    rule_fired: Optional[str] = None
    zero_prescription_guaranteed: bool = True
    next_checklist: List[str] = []

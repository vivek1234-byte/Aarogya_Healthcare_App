import uuid
from typing import Dict, Any, List, Optional
from app.core.base_schema import BaseModel, Field
from app.services.safety_gate import evaluate_safety_gate, sanitize_zero_prescriptions
from app.services.symptom_extractor import extract_clinical_symptoms
from app.services.referral_generator import generate_doctor_referral_summary


class TriageState(BaseModel):
    session_id: str
    patient_id: str
    patient_pseudonym: str
    age: int
    gender: str
    village_id: str
    language: str = "hi"
    all_transcripts: List[str] = Field(default_factory=list)
    symptoms: List[str] = Field(default_factory=list)
    danger_signs: List[str] = Field(default_factory=list)
    vitals: Dict[str, Any] = Field(default_factory=dict)
    duration_days: int = 1
    clarification_count: int = 0
    asked_questions: List[str] = Field(default_factory=list)
    is_final: bool = False
    triage_level: Optional[str] = None # EMERGENCY, REFER, TREAT_LOCALLY, HOME_CARE
    decision_rationale: Optional[str] = None
    next_question_hi: Optional[str] = None
    next_question_en: Optional[str] = None
    checklist: List[str] = Field(default_factory=list)
    doctor_summary_url: Optional[str] = None
    is_red_flag_overridden: bool = False
    protocol_citations: List[str] = Field(default_factory=list)


# Active in-memory session cache (can be persisted to Redis)
TRIAGE_SESSIONS: Dict[str, TriageState] = {}


class LangGraphClinicalOrchestrator:
    """
    Multi-Turn Clinical Voice Triage Orchestrator.
    Covers the 3 MVP conditions:
    1. Acute Chest Pain (Cardiovascular Red Flags)
    2. Child Danger Signs (IMNCI Under-5 Protocols)
    3. Fever (Uncomplicated vs Severe/Meningitis)
    """

    def start_session(
        self,
        patient_id: str,
        patient_pseudonym: str,
        age: int,
        gender: str,
        village_id: str,
        language: str = "hi",
        vitals: Optional[Dict[str, Any]] = None
    ) -> TriageState:
        session_id = f"SES-{uuid.uuid4().hex[:10].upper()}"
        state = TriageState(
            session_id=session_id,
            patient_id=patient_id,
            patient_pseudonym=patient_pseudonym,
            age=age,
            gender=gender,
            village_id=village_id,
            language=language,
            vitals=vitals or {}
        )
        TRIAGE_SESSIONS[session_id] = state
        return state

    def get_session(self, session_id: str) -> Optional[TriageState]:
        return TRIAGE_SESSIONS.get(session_id)

    def process_turn(self, session_id: str, transcript: str) -> TriageState:
        """
        Processes a turn of conversation from the health worker or patient.
        1. Extracts clinical symptoms and danger signs.
        2. Evaluates the deterministic safety gate.
        3. Identifies missing information and formulates next guided question.
        4. Finalizes triage decision when sufficient clinical evidence is gathered.
        """
        state = self.get_session(session_id)
        if not state:
            raise ValueError(f"Triage session {session_id} not found")

        state.all_transcripts.append(transcript)

        # 1. Symptom Extraction
        extracted = extract_clinical_symptoms(transcript, language=state.language)
        if extracted.duration_days and extracted.duration_days > 1:
            state.duration_days = max(state.duration_days, extracted.duration_days)
        for sym in extracted.symptoms:
            if sym not in state.symptoms:
                state.symptoms.append(sym)
        for ds in extracted.danger_signs:
            if ds not in state.danger_signs:
                state.danger_signs.append(ds)

        # 2. Evaluate Deterministic Safety Gate (100% Red-Flag Escalation)
        safety_eval = evaluate_safety_gate(
            symptoms=state.symptoms,
            age=state.age,
            vitals=state.vitals
        )

        if safety_eval.is_triggered:
            state.triage_level = safety_eval.override_action or "EMERGENCY"
            state.is_final = True
            state.is_red_flag_overridden = True
            state.decision_rationale = (
                f"CRITICAL RED FLAG DETECTED: {safety_eval.condition_name}. "
                f"Deterministic clinical safety gate triggered. AI bypassed. Immediate escalation initiated."
            )
            state.protocol_citations = [
                "National Health Mission (NHM) Emergency Triage Protocol",
                f"Rule Code: {safety_eval.rule_code}"
            ]
            state.checklist = [
                "Immediately arrange 108/102 emergency ambulance transport",
                "Notify Medical Officer at nearest Primary Health Centre",
                "Keep patient in stable resting / recovery position",
                "Hand over one-page clinical summary to transport team"
            ]

            # Generate 1-page doctor summary
            summary = generate_doctor_referral_summary(
                patient_id=state.patient_id,
                patient_pseudonym=state.patient_pseudonym,
                age=state.age,
                gender=state.gender,
                village_id=state.village_id,
                encounter_id=state.session_id,
                chief_complaint=state.all_transcripts[0] if state.all_transcripts else "Emergency Escalation",
                triage_category=state.triage_level,
                symptoms=state.symptoms,
                danger_signs=state.danger_signs + safety_eval.matched_symptoms,
                vitals=state.vitals,
                protocol_citations=state.protocol_citations,
                asha_actions=state.checklist
            )
            state.doctor_summary_url = summary.summary_document_url
            TRIAGE_SESSIONS[session_id] = state
            return state

        # 3. Non-Emergency Guided Clarification Logic
        state.clarification_count += 1

        # Condition A: Chest Pain clarification
        if "chest_pain" in state.symptoms and "Q_CHEST_RADIATION" not in state.asked_questions:
            state.asked_questions.append("Q_CHEST_RADIATION")
            state.next_question_hi = "क्या सीने का दर्द बाएं हाथ, गर्दन या जबड़े में जा रहा है, या पसीना आ रहा है?"
            state.next_question_en = "Does the chest pain radiate to the left arm, jaw, or shoulder, or is there cold sweating?"
            state.checklist = ["Check resting pulse and blood pressure", "Check for shortness of breath"]
            TRIAGE_SESSIONS[session_id] = state
            return state

        # Condition B: Child (< 5 yrs) general danger signs
        if state.age <= 5 and "Q_CHILD_DANGER" not in state.asked_questions:
            state.asked_questions.append("Q_CHILD_DANGER")
            state.next_question_hi = "क्या बच्चा मां का दूध या पानी पी पा रहा है? क्या झटके या लगातार उल्टी हुई है?"
            state.next_question_en = "Is the child able to drink or breastfeed? Have there been convulsions or non-stop vomiting?"
            state.checklist = ["Check child fontanelle (sunken/bulging)", "Look for chest indrawing while breathing"]
            TRIAGE_SESSIONS[session_id] = state
            return state

        # Condition C: Fever clarification
        if "fever" in state.symptoms and "Q_FEVER_DANGER" not in state.asked_questions:
            state.asked_questions.append("Q_FEVER_DANGER")
            state.next_question_hi = "बुखार कितने दिनों से है? क्या गर्दन में अकड़न है या शरीर पर लाल दाने हैं?"
            state.next_question_en = "How many days has the fever lasted? Is there any neck stiffness or skin rash?"
            state.checklist = ["Check body temperature using thermometer", "Check for neck stiffness"]
            TRIAGE_SESSIONS[session_id] = state
            return state

        # 4. Finalize Decision if no more critical questions remain
        state.is_final = True
        state.next_question_hi = None
        state.next_question_en = None

        if "chest_pain" in state.symptoms:
            state.triage_level = "REFER"
            state.decision_rationale = "Chest pain without red-flag signs still needs a same-day examination and ECG by a doctor."
            state.protocol_citations = ["NHM Emergency Triage Protocol: any chest pain requires physician evaluation"]
            state.checklist = [
                "Refer to PHC / CHC today for examination and ECG",
                "Check pulse and blood pressure before the patient leaves",
                "Call 108 at once if pain worsens, spreads to the arm or jaw, or sweating / breathlessness starts"
            ]
        elif "fever" in state.symptoms and state.duration_days >= 3:
            state.triage_level = "REFER"
            state.decision_rationale = "Prolonged fever (>= 3 days) without immediate danger signs. Non-emergency referral to PHC Medical Officer for lab tests."
            state.protocol_citations = ["IMNCI Protocol: Fever of > 3 days duration"]
            state.checklist = [
                "Refer patient to PHC within 24 hours for malaria / dengue rapid testing",
                "Ensure hydration with clean drinking water and ORS",
                "Advise caregiver to return immediately if child stops feeding or convulses"
            ]
        elif "fever" in state.symptoms:
            state.triage_level = "TREAT_LOCALLY"
            state.decision_rationale = "Uncomplicated acute fever (< 3 days) with zero danger signs. Manage under community health worker protocol."
            state.protocol_citations = ["NHM Frontline Worker Supportive Care Protocol"]
            state.checklist = [
                "Advise tepid sponging with normal temperature water",
                "Ensure frequent fluids and oral rehydration",
                "Follow up in 48 hours if fever does not subside"
            ]
        else:
            state.triage_level = "HOME_CARE"
            state.decision_rationale = "Mild symptoms with no physiological deterioration. Home care and observation."
            state.protocol_citations = ["Community Health Supportive Care"]
            state.checklist = ["Rest and balanced nutrition", "Observe for any new symptoms"]

        # If REFER, generate doctor summary
        if state.triage_level == "REFER":
            summary = generate_doctor_referral_summary(
                patient_id=state.patient_id,
                patient_pseudonym=state.patient_pseudonym,
                age=state.age,
                gender=state.gender,
                village_id=state.village_id,
                encounter_id=state.session_id,
                chief_complaint=state.all_transcripts[0] if state.all_transcripts else "Referral for clinical review",
                triage_category=state.triage_level,
                symptoms=state.symptoms,
                danger_signs=state.danger_signs,
                vitals=state.vitals,
                protocol_citations=state.protocol_citations,
                asha_actions=state.checklist
            )
            state.doctor_summary_url = summary.summary_document_url

        TRIAGE_SESSIONS[session_id] = state
        return state


orchestrator = LangGraphClinicalOrchestrator()

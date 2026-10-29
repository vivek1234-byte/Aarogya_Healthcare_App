from typing import List, Dict, Any, Optional
from app.schemas.triage import RedFlagCheckResult

# Deterministic safety rule matrix (Zero-AI-hallucination layer)
HARDCODED_RED_FLAGS = [
    {
        "rule_code": "RF-CHEST-PAIN-01",
        "condition_name": "Acute Coronary Syndrome / Myocardial Infarction Danger Sign",
        "required_symptoms": ["chest_pain"],
        "trigger_any_of": ["sweating", "radiating_pain", "breathlessness", "dizziness"],
        "override_action": "EMERGENCY"
    },
    {
        "rule_code": "RF-PEDIATRIC-DANGER-01",
        "condition_name": "IMNCI General Danger Sign in Child (< 5 yrs)",
        "max_age_years": 5,
        "trigger_any_of": ["convulsions", "cannot_drink_or_breastfeed", "vomiting_everything", "abnormally_sleepy"],
        "override_action": "EMERGENCY"
    },
    {
        "rule_code": "RF-RESPIRATORY-01",
        "condition_name": "Severe Respiratory Distress / Stridor",
        "trigger_any_of": ["severe_breathlessness", "stridor", "chest_indrawing", "cyanosis_blue_lips"],
        "override_action": "EMERGENCY"
    },
    {
        "rule_code": "RF-NEURO-FEVER-01",
        "condition_name": "Suspected Meningitis / Encephalitis",
        "required_symptoms": ["fever"],
        "trigger_any_of": ["stiff_neck", "altered_mental_status", "petechial_rash"],
        "override_action": "EMERGENCY"
    },
    {
        "rule_code": "RF-MATERNAL-01",
        "condition_name": "Maternal Obstetric Emergency",
        "trigger_any_of": ["severe_vaginal_bleeding", "severe_headache_blurred_vision", "labor_pain_premature"],
        "override_action": "EMERGENCY"
    }
]


def evaluate_safety_gate(
    symptoms: List[str],
    age: int,
    vitals: Optional[Dict[str, Any]] = None
) -> RedFlagCheckResult:
    """
    Deterministic rule-based safety gate.
    Evaluates raw symptoms against clinical red-flags.
    If matched, it strictly overrides any AI/LLM model decision.
    """
    normalized_symptoms = [s.strip().lower().replace(" ", "_") for s in symptoms]

    # Evaluate vital signs for physiological red flags
    if vitals:
        spo2 = vitals.get("spo2")
        if spo2 and float(spo2) < 90.0:
            return RedFlagCheckResult(
                is_triggered=True,
                rule_code="RF-VITALS-HYPOXIA",
                condition_name="Severe Hypoxemia (SpO2 < 90%)",
                override_action="EMERGENCY",
                matched_symptoms=["spo2_critically_low"]
            )

        systolic = vitals.get("systolic_bp")
        if systolic and int(systolic) >= 180:
            return RedFlagCheckResult(
                is_triggered=True,
                rule_code="RF-VITALS-HYPERTENSIVE-CRISIS",
                condition_name="Hypertensive Crisis (Systolic BP >= 180 mmHg)",
                override_action="EMERGENCY",
                matched_symptoms=["systolic_bp_crisis"]
            )

    # Evaluate symptom matrix
    for rule in HARDCODED_RED_FLAGS:
        # Check age constraint if present
        if "max_age_years" in rule and age > rule["max_age_years"]:
            continue

        # Check required baseline symptoms
        if "required_symptoms" in rule:
            has_required = any(req in normalized_symptoms for req in rule["required_symptoms"])
            if not has_required:
                continue

        # Check trigger modifiers
        matched_triggers = [trig for trig in rule["trigger_any_of"] if trig in normalized_symptoms]
        if matched_triggers:
            matched_all = (rule.get("required_symptoms", []) + matched_triggers)
            return RedFlagCheckResult(
                is_triggered=True,
                rule_code=rule["rule_code"],
                condition_name=rule["condition_name"],
                override_action=rule["override_action"],
                matched_symptoms=matched_all
            )

    return RedFlagCheckResult(is_triggered=False)


def sanitize_zero_prescriptions(text: str) -> Tuple[str, bool]:
    """
    Zero-prescription guardrail enforcement.
    Scans text output to ensure no unauthorized medication prescriptions or dosages are generated.
    """
    prohibited_keywords = [
        "prescribe", "take 500mg", "take 250mg", "amoxicillin", "ciprofloxacin",
        "azithromycin", "metformin", "amlodipine", "ibuprofen", "dispense"
    ]
    detected = []
    text_lower = text.lower()
    for kw in prohibited_keywords:
        if kw in text_lower:
            detected.append(kw)

    if detected:
        # Strip or redact prescription and flag
        sanitized = "[REDACTED: Direct medical prescription prohibited by ArogyaSaathi Safety Gate. Refer patient to Medical Officer.]"
        return sanitized, True

    return text, False

import sys
import os
import time

# Add backend directory to PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)

from app.services.storage import storage_service
from app.services.stt_service import stt_service
from app.services.symptom_extractor import extract_clinical_symptoms, extract_duration_days
from app.services.referral_generator import generate_doctor_referral_summary
from app.services.langgraph_triage import orchestrator, LangGraphClinicalOrchestrator
from app.services.safety_gate import evaluate_safety_gate, sanitize_zero_prescriptions


def test_storage_service():
    print("Testing Storage Service (Audio & Document Upload)...")
    # 1. Upload mock audio
    sample_wav = b"RIFF....WAVEfmt ...." + b"\x00" * 100
    audio_url = storage_service.upload_audio(sample_wav, filename="test_sample.wav")
    assert audio_url and ("arogya-audio-records" in audio_url or "file://" in audio_url)

    # 2. Upload referral document
    doc_content = "# Test Referral\nPatient exhibits chest pain."
    doc_url = storage_service.upload_document(doc_content, filename="test_ref.md")
    assert doc_url and ("arogya-referral-docs" in doc_url or "file://" in doc_url)
    print("  [PASSED] Storage service audio and document uploads verified.")


def test_multilingual_symptom_extraction():
    print("Testing Multilingual Clinical Symptom Extraction (Objective O5)...")

    # Test 1: Acute chest pain with cold sweat (Hindi)
    t1 = "सीने में तेज दर्द है और ठंडा पसीना आ रहा है"
    res1 = extract_clinical_symptoms(t1, language="hi")
    assert "chest_pain" in res1.symptoms, "Failed to extract chest_pain"
    assert "sweating" in res1.symptoms, "Failed to extract sweating"
    assert "chest_pain_sweating_cluster" in res1.danger_signs

    # Test 2: Pediatric danger sign (Hindi)
    t2 = "बच्चे को 2 दिन से तेज बुखार है, झटके आ रहे हैं और दूध नहीं पी पा रहा"
    res2 = extract_clinical_symptoms(t2, language="hi")
    assert "fever" in res2.symptoms
    assert "convulsions" in res2.symptoms
    assert "cannot_drink_or_breastfeed" in res2.symptoms
    assert res2.duration_days == 2
    assert "convulsions" in res2.danger_signs

    # Test 3: Meningitis danger sign (English)
    t3 = "Patient has high fever for 4 days with severe stiff neck and rash"
    res3 = extract_clinical_symptoms(t3, language="en")
    assert "fever" in res3.symptoms
    assert "stiff_neck" in res3.symptoms
    assert "rash" in res3.symptoms
    assert res3.duration_days == 4

    print("  [PASSED] Multilingual symptom extraction verified across Indic and English phrasing.")


def test_langgraph_chest_pain_flow():
    print("Testing LangGraph Triage Flow - Condition 1: Acute Chest Pain...")
    session = orchestrator.start_session(
        patient_id="p-001",
        patient_pseudonym="HASH-RAM-01",
        age=54,
        gender="Male",
        village_id="VILL-UP-01",
        language="hi",
        vitals={"systolic_bp": 150, "diastolic_bp": 95, "pulse": 98, "spo2": 95}
    )

    # Turn 1: Patient complains of chest pain only
    t1_state = orchestrator.process_turn(session.session_id, "कल से सीने में दर्द है")
    assert not t1_state.is_final, "Should ask clarification question before finalizing"
    assert t1_state.next_question_hi is not None
    assert "बाएं हाथ" in t1_state.next_question_hi or "पसीना" in t1_state.next_question_hi

    # Turn 2: Patient confirms radiating pain and sweating
    t2_state = orchestrator.process_turn(session.session_id, "हां, दर्द बाएं हाथ में जा रहा है और पसीना छूट रहा है")
    assert t2_state.is_final is True, "Emergency red flag must immediately finalize decision"
    assert t2_state.triage_level == "EMERGENCY"
    assert t2_state.is_red_flag_overridden is True
    assert t2_state.doctor_summary_url is not None
    assert len(t2_state.checklist) > 0
    print("  [PASSED] Condition 1 (Chest pain multi-turn red-flag escalation) verified.")


def test_langgraph_pediatric_danger_signs_flow():
    print("Testing LangGraph Triage Flow - Condition 2: Child Danger Signs (< 5 yrs)...")
    session = orchestrator.start_session(
        patient_id="p-002",
        patient_pseudonym="HASH-BABY-01",
        age=3,
        gender="Female",
        village_id="VILL-UP-02",
        language="hi",
        vitals={"temperature": 39.2, "spo2": 96}
    )

    # Turn 1: Child has convulsion and stopped breastfeeding
    state = orchestrator.process_turn(session.session_id, "बच्ची को तेज बुखार है और झटके आ रहे हैं, दूध नहीं पी रही")
    assert state.is_final is True, "Pediatric danger sign must trigger immediate EMERGENCY"
    assert state.triage_level == "EMERGENCY"
    assert "convulsions" in state.danger_signs
    assert state.doctor_summary_url is not None
    print("  [PASSED] Condition 2 (IMNCI pediatric danger signs) verified.")


def test_langgraph_fever_clarification_flow():
    print("Testing LangGraph Triage Flow - Condition 3: Fever (Uncomplicated vs Prolonged)...")

    # Subtest A: Acute uncomplicated fever (1 day, no danger signs) -> TREAT_LOCALLY
    session_a = orchestrator.start_session(
        patient_id="p-003",
        patient_pseudonym="HASH-FEVER-01",
        age=28,
        gender="Male",
        village_id="VILL-UP-03",
        language="hi"
    )
    # Turn 1: Mentions fever
    s1 = orchestrator.process_turn(session_a.session_id, "आज से हल्का बुखार है")
    assert not s1.is_final
    assert s1.next_question_hi is not None # Asks about duration and neck stiffness

    # Turn 2: Denies danger signs
    s2 = orchestrator.process_turn(session_a.session_id, "नहीं, केवल आज से है और गर्दन में कोई अकड़न नहीं है")
    assert s2.is_final is True
    assert s2.triage_level == "TREAT_LOCALLY"
    assert "Advise tepid sponging" in s2.checklist[0] or "fluids" in s2.checklist[1]

    # Subtest B: Prolonged fever (>= 3 days) -> REFER
    session_b = orchestrator.start_session(
        patient_id="p-004",
        patient_pseudonym="HASH-FEVER-02",
        age=32,
        gender="Female",
        village_id="VILL-UP-03",
        language="hi"
    )
    s_b1 = orchestrator.process_turn(session_b.session_id, "4 दिन से तेज बुखार है")
    s_b2 = orchestrator.process_turn(session_b.session_id, "गर्दन में अकड़न नहीं है लेकिन 4 दिन हो गए हैं")
    assert s_b2.is_final is True
    assert s_b2.triage_level == "REFER"
    assert s_b2.doctor_summary_url is not None
    print("  [PASSED] Condition 3 (Fever multi-turn triage and referral) verified.")


def test_doctor_referral_summary_generator():
    print("Testing Doctor Referral Summary Generator (Objective O6: <= 30s Target)...")
    start_time = time.time()
    
    summary = generate_doctor_referral_summary(
        patient_id="p-005",
        patient_pseudonym="HASH-REF-TEST",
        age=48,
        gender="Female",
        village_id="VILL-UP-05",
        encounter_id="ENC-TEST-001",
        chief_complaint="Severe retrosternal chest tightness and diaphoresis",
        triage_category="EMERGENCY",
        symptoms=["chest_pain", "sweating", "severe_breathlessness"],
        danger_signs=["chest_pain_sweating_cluster"],
        vitals={"systolic_bp": 165, "diastolic_bp": 102, "pulse": 110, "spo2": 94.0}
    )

    elapsed = time.time() - start_time
    assert elapsed < 30.0, f"Summary generation exceeded 30s limit: {elapsed}s"
    assert summary.generation_latency_seconds < 1.0, f"Generation took {summary.generation_latency_seconds}s"
    assert "AROGYASAATHI CLINICAL REFERRAL SUMMARY" in summary.summary_markdown
    assert summary.urgency_level == "CRITICAL_IMMEDIATE"
    assert summary.zero_prescription_guaranteed is True
    assert summary.summary_document_url is not None

    print(f"  [PASSED] Doctor summary generated in {summary.generation_latency_seconds}s (well within <= 30s limit).")


def test_zero_prescription_enforcement():
    print("Testing Zero-Prescription Enforcement on Summary Output...")
    unsafe_content = "Patient diagnosed with pneumonia. Prescribe azithromycin 500mg once daily."
    sanitized, was_sanitized = sanitize_zero_prescriptions(unsafe_content)
    assert was_sanitized is True
    assert "azithromycin" not in sanitized.lower()
    print("  [PASSED] Zero-prescription policy enforced.")


if __name__ == "__main__":
    print("=" * 65)
    print("ArogyaSaathi Backend Phase 2 Verification Suite")
    print("Voice Triage, LangGraph Orchestration, & Doctor Summaries")
    print("=" * 65)
    test_storage_service()
    test_multilingual_symptom_extraction()
    test_langgraph_chest_pain_flow()
    test_langgraph_pediatric_danger_signs_flow()
    test_langgraph_fever_clarification_flow()
    test_doctor_referral_summary_generator()
    test_zero_prescription_enforcement()
    print("=" * 65)
    print("ALL PHASE 2 VERIFICATIONS PASSED SUCCESSFULLY!")
    print("=" * 65)

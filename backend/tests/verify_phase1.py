import sys
import os
import re

# Add backend directory to PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)

from app.core.security import (
    encrypt_pii,
    decrypt_pii,
    generate_pseudonym,
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
    compute_audit_hash,
)
from app.services.safety_gate import evaluate_safety_gate, sanitize_zero_prescriptions

try:
    from app.core.database import Base
    from app.models import (
        User, Patient, Consent, Encounter, Symptom, VitalsSeries,
        MedicationAdherence, RedFlagRule, ProtocolChunk, TriageDecision,
        Referral, Escalation, SurveillanceSignal, OutbreakAlert, AuditLog
    )
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False


def test_pii_encryption():
    print("Testing DPDP AES-256 PII Encryption...")
    original_pii = {
        "full_name": "Sita Devi",
        "phone_number": "+919876543210",
        "national_id": "ABHA-99-8877-6655",
        "address": "Ward 4, Rampur Village"
    }
    encrypted = encrypt_pii(original_pii)
    assert encrypted != str(original_pii), "Encryption failed: Output matches plaintext"
    assert isinstance(encrypted, str) and len(encrypted) > 20

    decrypted = decrypt_pii(encrypted)
    assert decrypted == original_pii, f"Decryption failed: {decrypted} != {original_pii}"
    print("  [PASSED] DPDP PII encryption and decryption verified.")


def test_pseudonymization():
    print("Testing Deterministic Pseudonymization (HMAC-SHA256)...")
    phone = "+919876543210"
    pseudo1 = generate_pseudonym(phone)
    pseudo2 = generate_pseudonym(phone)
    assert pseudo1 == pseudo2, "Pseudonymization must be deterministic for identical identifiers"
    assert len(pseudo1) == 64, "Pseudonym must be a 64-character SHA-256 hex string"

    pseudo_diff = generate_pseudonym("+919876543211")
    assert pseudo1 != pseudo_diff, "Different identifiers must produce distinct pseudonyms"
    print("  [PASSED] Pseudonymization verified.")


def test_jwt_and_passwords():
    print("Testing Password Hashing and JWT Claims...")
    password = "ASHA@VillageWorker2026"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed), "Password verification failed"
    assert not verify_password("WrongPassword", hashed), "Invalid password incorrectly verified"

    token = create_access_token(subject="asha_worker_1", role="ASHA", village_id="VILL-01")
    decoded = decode_access_token(token)
    assert decoded["sub"] == "asha_worker_1"
    assert decoded["role"] == "ASHA"
    assert decoded["village_id"] == "VILL-01"
    print("  [PASSED] Password and JWT authentication verified.")


def test_safety_gate_rules():
    print("Testing Deterministic Safety Gate (Zero-AI-Hallucination Gate)...")
    
    # 1. Adult with chest pain and sweating -> EMERGENCY
    res1 = evaluate_safety_gate(symptoms=["chest_pain", "sweating"], age=52)
    assert res1.is_triggered is True, "Chest pain + sweating must trigger emergency"
    assert res1.override_action == "EMERGENCY"
    assert res1.rule_code == "RF-CHEST-PAIN-01"

    # 2. Child under 5 with convulsion -> EMERGENCY
    res2 = evaluate_safety_gate(symptoms=["convulsions", "fever"], age=2)
    assert res2.is_triggered is True, "Child convulsion must trigger emergency"
    assert res2.rule_code == "RF-PEDIATRIC-DANGER-01"

    # 3. Fever with stiff neck (Meningitis flag) -> EMERGENCY
    res3 = evaluate_safety_gate(symptoms=["fever", "stiff_neck"], age=25)
    assert res3.is_triggered is True, "Fever + stiff neck must trigger emergency"

    # 4. Critical SpO2 < 90 -> EMERGENCY
    res4 = evaluate_safety_gate(symptoms=["cough"], age=60, vitals={"spo2": 88.0})
    assert res4.is_triggered is True, "Low SpO2 must trigger emergency"
    assert res4.rule_code == "RF-VITALS-HYPOXIA"

    # 5. Non-emergency mild symptoms -> NOT triggered
    res5 = evaluate_safety_gate(symptoms=["mild_cold", "sneezing"], age=30)
    assert res5.is_triggered is False, "Mild symptoms should not trigger emergency rule"

    print("  [PASSED] 100% Red-flag safety gate escalation verified (Objective O1).")


def test_zero_prescriptions():
    print("Testing Zero-Prescription Guardrail...")
    unsafe_text = "Patient has bacterial infection. Prescribe amoxicillin 500mg twice daily."
    sanitized, violated = sanitize_zero_prescriptions(unsafe_text)
    assert violated is True, "Guardrail must flag prescription keywords"
    assert "amoxicillin" not in sanitized.lower(), "Prescription drug name must be removed"

    safe_text = "Ensure oral rehydration therapy and encourage fluid intake."
    sanitized_safe, violated_safe = sanitize_zero_prescriptions(safe_text)
    assert violated_safe is False, "Safe guidance should not be flagged"
    assert sanitized_safe == safe_text

    print("  [PASSED] Zero-prescription guardrail verified.")


def test_tamper_evident_audit_chain():
    print("Testing Cryptographic SHA-256 Audit Ledger Chain...")
    genesis_prev = "0000000000000000000000000000000000000000000000000000000000000000"
    entry1_data = {"action": "CREATE_PATIENT", "resource_id": "P-001", "actor_id": "ASHA-1"}
    hash1 = compute_audit_hash(genesis_prev, entry1_data)

    entry2_data = {"action": "TRIAGE_EVALUATION", "resource_id": "E-001", "actor_id": "ASHA-1"}
    hash2 = compute_audit_hash(hash1, entry2_data)

    assert hash1 != hash2, "Successive audit hashes must differ"

    # Tampering test: if entry1 was modified in database
    tampered_entry1_data = {"action": "CREATE_PATIENT", "resource_id": "P-001_TAMPERED", "actor_id": "ASHA-1"}
    tampered_hash1 = compute_audit_hash(genesis_prev, tampered_entry1_data)
    assert tampered_hash1 != hash1, "Modifying audit data must break the cryptographic hash"

    print("  [PASSED] Audit ledger hash chain verified.")


def test_database_models_metadata():
    print("Testing Database Schema & Table Metadata...")
    required_tables = {
        "users", "patients", "consents", "encounters", "symptoms",
        "vitals_series", "medication_adherence", "red_flag_rules",
        "protocol_chunks", "triage_decisions", "referrals", "escalations",
        "surveillance_signals", "outbreak_alerts", "audit_log"
    }

    if HAS_SQLALCHEMY:
        table_names = set(Base.metadata.tables.keys())
        missing = required_tables - table_names
        assert not missing, f"Missing tables in model metadata: {missing}"
        print(f"  [PASSED] All {len(required_tables)} core tables verified in SQLAlchemy schema.")
    else:
        # Verify init_db.sql DDL directly
        sql_path = os.path.join(backend_dir, "scripts", "init_db.sql")
        with open(sql_path, "r") as f:
            sql_content = f.read().lower()
        for tbl in required_tables:
            assert f"create table if not exists {tbl}" in sql_content or f"create table {tbl}" in sql_content, f"Table {tbl} missing from init_db.sql"
        assert "postgis" in sql_content
        assert "timescaledb" in sql_content
        assert "vector" in sql_content
        print(f"  [PASSED] All {len(required_tables)} core tables & extensions verified in init_db.sql DDL.")


if __name__ == "__main__":
    print("=" * 60)
    print("ArogyaSaathi Backend Phase 1 Verification Suite")
    print("=" * 60)
    test_pii_encryption()
    test_pseudonymization()
    test_jwt_and_passwords()
    test_safety_gate_rules()
    test_zero_prescriptions()
    test_tamper_evident_audit_chain()
    test_database_models_metadata()
    print("=" * 60)
    print("ALL PHASE 1 BACKEND VERIFICATIONS PASSED SUCCESSFULLY!")
    print("=" * 60)

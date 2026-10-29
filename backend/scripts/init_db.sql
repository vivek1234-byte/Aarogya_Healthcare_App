-- ====================================================================
-- ArogyaSaathi Database Initialization Script
-- PostgreSQL with PostGIS, TimescaleDB, and pgvector
-- Covers all 14 core tables specified in DEV_107.pdf
-- ====================================================================

-- 1. Enable Required Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";
CREATE EXTENSION IF NOT EXISTS "timescaledb" CASCADE;
CREATE EXTENSION IF NOT EXISTS "vector";

-- 2. Users and Roles (ASHA, ANM, Doctor, Health Officer, Admin)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('ASHA', 'ANM', 'DOCTOR', 'OFFICER', 'ADMIN')),
    assigned_village_id VARCHAR(100),
    phone_number VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Patients (DPDP-aligned: Encrypted PII & Pseudonymized IDs)
CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pseudonym_id VARCHAR(64) UNIQUE NOT NULL, -- SHA-256 HMAC for research/analytics
    encrypted_pii TEXT NOT NULL,              -- AES-256 encrypted (name, phone, national ID)
    village_id VARCHAR(100) NOT NULL,
    age INT NOT NULL,
    gender VARCHAR(20) NOT NULL,
    primary_language VARCHAR(50) DEFAULT 'hi',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_patients_village ON patients(village_id);
CREATE INDEX IF NOT EXISTS idx_patients_pseudonym ON patients(pseudonym_id);

-- 4. Consents (Voice/Written DPDP Consent)
CREATE TABLE IF NOT EXISTS consents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    consent_type VARCHAR(50) NOT NULL CHECK (consent_type IN ('VOICE', 'WRITTEN', 'MISSED_CALL')),
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'REVOKED', 'EXPIRED')),
    audio_s3_url TEXT,                         -- Voice recording verifying verbal consent
    purpose VARCHAR(255) DEFAULT 'PRIMARY_HEALTHCARE_AND_SURVEILLANCE',
    granted_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_consents_patient ON consents(patient_id, status);

-- 5. Encounters (Health Worker Triage or Follow-up Session)
CREATE TABLE IF NOT EXISTS encounters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    health_worker_id UUID REFERENCES users(id),
    encounter_type VARCHAR(50) NOT NULL CHECK (encounter_type IN ('TRIAGE', 'CHRONIC_FOLLOWUP', 'ROUTINE')),
    chief_complaint TEXT,
    audio_recording_url TEXT,
    language_code VARCHAR(20) DEFAULT 'hi',
    triage_level VARCHAR(50) CHECK (triage_level IN ('EMERGENCY', 'REFER', 'TREAT_LOCALLY', 'HOME_CARE', 'PENDING')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_encounters_patient ON encounters(patient_id);
CREATE INDEX IF NOT EXISTS idx_encounters_created ON encounters(created_at DESC);

-- 6. Symptoms (Extracted from speech or checklist)
CREATE TABLE IF NOT EXISTS symptoms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    encounter_id UUID NOT NULL REFERENCES encounters(id) ON DELETE CASCADE,
    symptom_code VARCHAR(100) NOT NULL,
    symptom_name VARCHAR(255) NOT NULL,
    severity VARCHAR(50) DEFAULT 'MODERATE',
    duration_days INT,
    is_red_flag BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_symptoms_encounter ON symptoms(encounter_id);
CREATE INDEX IF NOT EXISTS idx_symptoms_code ON symptoms(symptom_code);

-- 7. Vitals Series (TimescaleDB Hypertable)
CREATE TABLE IF NOT EXISTS vitals_series (
    recorded_at TIMESTAMPTZ NOT NULL,
    patient_id UUID NOT NULL,
    encounter_id UUID,
    systolic_bp INT,
    diastolic_bp INT,
    blood_glucose NUMERIC(6, 2), -- mg/dL
    glucose_context VARCHAR(20) CHECK (glucose_context IN ('FASTING', 'POST_PRANDIAL', 'RANDOM')),
    pulse INT,
    spo2 NUMERIC(5, 2),          -- %
    temperature NUMERIC(4, 1),   -- °C / °F
    recorded_by UUID
);
-- Create TimescaleDB hypertable partitioned by recorded_at
SELECT create_hypertable('vitals_series', 'recorded_at', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_vitals_patient_time ON vitals_series(patient_id, recorded_at DESC);

-- 8. Medication Adherence
CREATE TABLE IF NOT EXISTS medication_adherence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    medication_name VARCHAR(255) NOT NULL,
    prescribed_dosage VARCHAR(100),
    scheduled_time TIMESTAMPTZ NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('TAKEN', 'MISSED', 'SKIPPED')),
    reason_for_miss TEXT,
    reported_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_adherence_patient ON medication_adherence(patient_id, scheduled_time DESC);

-- 9. Red Flag Rules (Deterministic Safety Gate)
CREATE TABLE IF NOT EXISTS red_flag_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_code VARCHAR(50) UNIQUE NOT NULL,
    condition_name VARCHAR(150) NOT NULL,
    criteria JSONB NOT NULL,                   -- e.g. {"symptoms": ["chest_pain", "sweating"]}
    override_action VARCHAR(50) NOT NULL DEFAULT 'EMERGENCY' CHECK (override_action IN ('EMERGENCY', 'URGENT_REFERRAL')),
    priority INT DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 10. Protocol Chunks (pgvector for RAG Guidelines)
CREATE TABLE IF NOT EXISTS protocol_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_guideline VARCHAR(150) NOT NULL,    -- e.g. 'IMNCI', 'NVBDCP', 'ICMR_HTN'
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),                    -- OpenAI/IndicBERT/Bhashini clinical vector space
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_protocol_chunks_embedding 
ON protocol_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 11. Triage Decisions (LangGraph Outputs + Rule Overrides)
CREATE TABLE IF NOT EXISTS triage_decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    encounter_id UUID NOT NULL REFERENCES encounters(id) ON DELETE CASCADE,
    triage_category VARCHAR(50) NOT NULL CHECK (triage_category IN ('EMERGENCY', 'REFER', 'TREAT_LOCALLY', 'HOME_CARE')),
    rationale TEXT NOT NULL,
    confidence_score NUMERIC(4, 3),
    protocol_citation TEXT,
    uncertainty_flag BOOLEAN DEFAULT FALSE,
    rule_override_id UUID REFERENCES red_flag_rules(id),
    decision_payload JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_triage_encounter ON triage_decisions(encounter_id);

-- 12. Referrals & Escalations
CREATE TABLE IF NOT EXISTS referrals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    encounter_id UUID NOT NULL REFERENCES encounters(id) ON DELETE CASCADE,
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    target_facility VARCHAR(255) NOT NULL,
    urgency_level VARCHAR(50) NOT NULL CHECK (urgency_level IN ('CRITICAL_IMMEDIATE', 'URGENT_24HR', 'ROUTINE')),
    summary_pdf_s3_url TEXT,
    summary_text TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'ACCEPTED', 'COMPLETED', 'CANCELLED')),
    doctor_id UUID REFERENCES users(id),
    doctor_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS escalations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    encounter_id UUID NOT NULL REFERENCES encounters(id) ON DELETE CASCADE,
    reason TEXT NOT NULL,
    escalated_to_role VARCHAR(50) NOT NULL DEFAULT 'DOCTOR',
    escalated_at TIMESTAMPTZ DEFAULT NOW(),
    acknowledged_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ
);

-- 13. Surveillance Signals (TimescaleDB Hypertable for Outbreak Warning)
CREATE TABLE IF NOT EXISTS surveillance_signals (
    timestamp TIMESTAMPTZ NOT NULL,
    village_id VARCHAR(100) NOT NULL,
    signal_type VARCHAR(100) NOT NULL CHECK (signal_type IN ('CLINIC_FEVER', 'PHARMACY_ORS_SALES', 'SCHOOL_ABSENTEEISM', 'ACUTE_DIARRHEA', 'RASH_ILLNESS')),
    count INT NOT NULL,
    source VARCHAR(100) DEFAULT 'COMMUNITY_HEALTH_POST',
    metadata JSONB
);
SELECT create_hypertable('surveillance_signals', 'timestamp', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_surveillance_village_time ON surveillance_signals(village_id, timestamp DESC);

-- 14. Outbreak Alerts (PostGIS Geospatial Cluster Polygons)
CREATE TABLE IF NOT EXISTS outbreak_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    syndrome VARCHAR(100) NOT NULL,
    affected_villages JSONB NOT NULL,           -- Array of village IDs
    cluster_geom GEOMETRY(Geometry, 4326),     -- PostGIS polygon/multipolygon of outbreak cluster
    z_score NUMERIC(5, 2) NOT NULL,
    confidence NUMERIC(4, 3) NOT NULL,
    baseline_expected_cases INT,
    observed_cases INT,
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INVESTIGATING', 'CONTAINED', 'FALSE_ALARM')),
    notes TEXT
);
CREATE INDEX IF NOT EXISTS idx_outbreak_alerts_geom ON outbreak_alerts USING GIST (cluster_geom);

-- 15. Audit Log (Cryptographically Chained Tamper-Evident Ledger)
CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    actor_id VARCHAR(100),
    actor_role VARCHAR(50),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(100),
    model_input JSONB,
    model_output JSONB,
    rule_fired VARCHAR(100),
    human_override BOOLEAN DEFAULT FALSE,
    previous_hash VARCHAR(64) NOT NULL,         -- SHA-256 of the prior log entry
    entry_hash VARCHAR(64) NOT NULL             -- SHA-256 of current entry + previous_hash
);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_log(resource_type, resource_id);

-- ====================================================================
-- Initial Seed Data
-- ====================================================================

-- 1. Default Admin User (Password: Arogya@Admin2026)
-- bcrypt hash of 'Arogya@Admin2026'
INSERT INTO users (id, username, email, hashed_password, full_name, role, is_active)
VALUES (
    'a0000000-0000-0000-0000-000000000001',
    'admin',
    'admin@arogyasaathi.gov.in',
    '$2b$12$4Lp5N9b9yYQj8fL8pLqG3e4DkV6wZ1tF4jB7cD0eH3aK6sV8xY2uI',
    'System Administrator',
    'ADMIN',
    TRUE
) ON CONFLICT (username) DO NOTHING;

-- 2. Seed Deterministic Red-Flag Rules (Objective O1: 100% Red-Flag Escalation)
INSERT INTO red_flag_rules (rule_code, condition_name, criteria, override_action, priority)
VALUES 
(
    'RF-CHEST-PAIN-01',
    'Acute Coronary / Chest Pain Red Flag',
    '{"symptoms": ["chest_pain"], "modifiers": ["radiating_to_arm", "sweating", "breathlessness"]}'::jsonb,
    'EMERGENCY',
    1
),
(
    'RF-PEDIATRIC-01',
    'IMNCI Child Danger Signs (Convulsion / Inability to Feed)',
    '{"age_max_years": 5, "symptoms": ["convulsions", "cannot_drink_or_breastfeed", "vomiting_everything", "lethargic"]}'::jsonb,
    'EMERGENCY',
    1
),
(
    'RF-RESP-01',
    'Severe Respiratory Distress / Strider',
    '{"symptoms": ["severe_breathlessness", "stridor_in_calm_child", "chest_indrawing"]}'::jsonb,
    'EMERGENCY',
    1
),
(
    'RF-MATERNAL-01',
    'Maternal Antepartum / Postpartum Red Flag',
    '{"symptoms": ["severe_headache_with_blurring_vision", "severe_vaginal_bleeding", "high_fever_chills"]}'::jsonb,
    'EMERGENCY',
    1
)
ON CONFLICT (rule_code) DO NOTHING;

-- 3. Initial Audit Ledger Genesis Block
INSERT INTO audit_log (id, timestamp, actor_id, actor_role, action, resource_type, resource_id, previous_hash, entry_hash)
VALUES (
    1,
    NOW(),
    'SYSTEM',
    'SYSTEM',
    'GENESIS',
    'SYSTEM_AUDIT_LOG',
    'GENESIS_0',
    '0000000000000000000000000000000000000000000000000000000000000000',
    'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
) ON CONFLICT (id) DO NOTHING;

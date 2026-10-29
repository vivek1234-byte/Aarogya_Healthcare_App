# ArogyaSaathi Backend Gateway

Voice-First Triage, Chronic Care Follow-up, and Village-Level Outbreak Early Warning for Frontline Health Workers.

---

## 🏗️ Architecture Overview

The backend is built with **FastAPI**, **PostgreSQL** (with **PostGIS**, **TimescaleDB**, and **pgvector** extensions), **Redis**, and **MinIO**. It is strictly compliant with India's **Digital Personal Data Protection (DPDP) Act 2023** and enforces a **deterministic clinical safety gate** with a zero-prescription guarantee.

```
Flutter Mobile App (ASHA / ANM)
        │
        │ HTTPS / WebSockets
        ▼
FastAPI Gateway & Auth (Port 8000)
        │
        ├──▶ Deterministic Safety Gate (100% Red-Flag Escalation)
        ├──▶ AES-256 PII Encryption & Pseudonymization Engine
        ├──▶ TimescaleDB Hypertables (Vitals Series & Surveillance Streams)
        ├──▶ PostGIS Geometries (Village Clusters & Outbreak Alert Polygons)
        ├──▶ pgvector IVFFlat (Clinical Protocol Guidelines RAG)
        └──▶ Tamper-Evident SHA-256 Chained Audit Ledger
```

---

## 📦 What Was Built in Phase 1

### 1. Database Architecture (`backend/scripts/init_db.sql`)
Initializes PostgreSQL with all required extensions and creates all **14 core tables** specified in `DEV_107.pdf`:
1. `users`: ASHA, ANM, Doctor, Officer, Admin with bcrypt passwords & role-based access.
2. `patients`: Encrypted PII at rest + deterministic SHA-256 HMAC pseudonym ID.
3. `consents`: Voice, written, and missed-call consent records with audio URLs.
4. `encounters`: Triage and chronic follow-up sessions.
5. `symptoms`: Extracted symptoms, duration, and red-flag indicators.
6. `vitals_series`: **TimescaleDB Hypertable** partitioned by `recorded_at` for continuous BP, glucose, SpO2 tracking.
7. `medication_adherence`: Taken/missed dose logs for chronic hypertension & diabetes patients.
8. `red_flag_rules`: Deterministic safety rules that strictly override LLMs.
9. `protocol_chunks`: **pgvector** table with 1536-dim vector embeddings for standard IMNCI/ICMR guidelines.
10. `triage_decisions`: Decisions with protocol citations and uncertainty flags.
11. `referrals`: One-page structured summaries for PHC doctors.
12. `escalations`: Real-time emergency escalation queue.
13. `surveillance_signals`: **TimescaleDB Hypertable** aggregating clinic fever cases, pharmacy ORS sales, and school absenteeism.
14. `outbreak_alerts`: **PostGIS Geometry** cluster polygons with spatio-temporal $Z$-scores.
15. `audit_log`: Append-only, cryptographically chained SHA-256 tamper-evident ledger.

### 2. Security & DPDP Compliance (`backend/app/core/security.py`)
- **AES-256 PII Encryption**: Name, phone, ABHA ID, and address are encrypted before writing to disk.
- **HMAC Pseudonymization**: Deterministic pseudonym hash for de-identified epidemiological analytics without leaking PII.
- **Right to Erasure**: `DELETE /api/v1/patients/{id}` executes DPDP-compliant data erasure and logs an immutable audit trail.
- **Audit Hash Chaining**: Every log entry computes `entry_hash = SHA256(previous_hash + entry_data)`, preventing silent database tampering.

### 3. Deterministic Safety Gate (`backend/app/services/safety_gate.py`)
- **100% Danger-Sign Escalation (Objective O1)**:
  - Chest pain + sweating/radiating pain $\to$ Immediate `EMERGENCY`
  - Child under 5 with convulsions / inability to feed $\to$ Immediate `EMERGENCY`
  - Fever with stiff neck / altered mental status $\to$ Immediate `EMERGENCY`
  - Severe respiratory distress / SpO2 < 90% $\to$ Immediate `EMERGENCY`
- **Zero-Prescription Guarantee**: Sanitizer strips and blocks any medication names or dosages.

### 4. API Endpoints (`backend/app/api/v1/endpoints/`)
- `POST /api/v1/auth/login` & `POST /api/v1/auth/register`: JWT authentication with role and village scope.
- `GET /api/v1/health`: Deep health probe checking database connectivity and extensions.
- `POST /api/v1/patients/`: Registers patient with encrypted PII and voice consent.
- `GET /api/v1/patients/`: Scoped patient listing by assigned village.
- `DELETE /api/v1/patients/{id}`: DPDP Right to Erasure.
- `POST /api/v1/vitals/`: Ingests vital observations into TimescaleDB.
- `GET /api/v1/vitals/{patient_id}/trends`: Chronic deterioration analysis (flagging deteriorating BP/glucose trends $\ge 7$ days early).
- `POST /api/v1/triage/evaluate`: Deterministic safety gate evaluation.
- `GET /api/v1/audit/`: Audit trail inspection.
- `GET /api/v1/audit/verify-chain`: Mathematically validates the cryptographic integrity of the entire ledger.

---

## 🚀 How to Run

### Option A: Using Docker (Recommended for complete stack)
```bash
cd backend
docker compose up --build -d
```
FastAPI Swagger documentation will be available at:
`http://localhost:8000/docs`

### Option B: Local Python Development
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./run_backend.sh
```

### Running the Phase 1 Verification Suite:
```bash
python3 backend/tests/verify_phase1.py
```

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
        ├──▶ Multilingual STT & Clinical Symptom Extractor (Indic + English)
        ├──▶ LangGraph Multi-Turn Clinical Triage Orchestrator (Chest Pain, Child Danger Signs, Fever)
        ├──▶ Doctor Referral Summary Generator (<= 30s target)
        ├──▶ Chronic Care & Deterioration Early Warning Engine (BP & Glucose)
        ├──▶ Syndromic Surveillance & Spatio-Temporal Outbreak Early Warning (PostGIS + TimescaleDB)
        ├──▶ AES-256 PII Encryption & Pseudonymization Engine
        └──▶ Tamper-Evident SHA-256 Chained Audit Ledger
```

---

## 📦 Project Implementation Progress

### Phase 1: Database Foundation & Security Architecture
* **14 Core Tables**: Initialized PostgreSQL with `postgis`, `timescaledb`, and `vector` extensions.
* **DPDP Compliance**: AES-256 encryption for PII, deterministic HMAC-SHA256 pseudonym IDs, and Right-to-Erasure.
* **Deterministic Safety Gate**: 100% danger-sign escalation (Objective O1) and zero-prescription policy.
* **TimescaleDB Hypertables**: `vitals_series` and `surveillance_signals` partitioned by timestamp.
* **Audit Ledger**: Cryptographically chained SHA-256 tamper-evident log.

### Phase 2: Voice Triage Pipeline & Doctor Referral Generator
* **Storage Service**: Audio and markdown document storage via MinIO/S3 (`arogya-audio-records`, `arogya-referral-docs`).
* **Multilingual STT Pipeline**: Bhashini Indian Language Gateway adapter with fallback transcription.
* **Clause-Aware Symptom Extractor**: Extracts standardized clinical symptom codes with negation awareness (e.g. *"गर्दन में अकड़न नहीं है"* $\to$ neck stiffness negated).
* **LangGraph Clinical Triage Orchestrator**: Multi-turn stateful graph handling:
  1. Acute Chest Pain (Coronary red flags $\to$ `EMERGENCY`)
  2. Child Danger Signs (IMNCI under-5: convulsions, inability to drink $\to$ `EMERGENCY`)
  3. Fever (Acute uncomplicated $\to$ `TREAT_LOCALLY`; Prolonged $\ge 3$ days $\to$ `REFER`)
* **Doctor Referral Summary Generator**: Generates structured 1-page clinical reports in $< 0.1\text{ s}$ (Objective O6 $\le 30\text{ s}$ target) with zero unauthorized prescriptions.

### Phase 3: Chronic Care Engine & Early Deterioration Detection
* **Clinical Trend Analytics**: Moving averages, systolic velocity/slope ($\Delta \text{mmHg/week}$), sustained Stage 2 Hypertension, and Hypoglycemia/Hyperglycemia detection.
* **Medication Adherence Scoring**: Tracks compliance and flags critical dropouts ($\ge 3$ consecutive missed doses).
* **Conversational Voice Check-in Parser**: Spoken reporting of BP, sugar, and pill adherence in Hindi and English with localized voice feedback.
* **Synthea-Style Simulated Cohort Benchmark (Objective O2)**: Injected progressive deterioration into 50 chronic patients $\to$ **100% compliance** with an average lead time of **12.0 days** before scheduled clinical visit ($\ge 7$ days target).
* **ASHA Village Action Roster**: Prioritized daily action queue for frontline workers (Priority 1: Critical $\to$ Priority 4: Routine).

### Phase 4: Syndromic Surveillance & Village Outbreak Early Warning
* **Multi-Source Signal Fusion**: Combines clinic triage encounters, village pharmacy OTC ORS sales, and primary school absenteeism.
* **Anomaly Detection Algorithm**: Rolling baseline mean/standard deviation with multi-stream fused $Z$-score and confidence mapping.
* **PostGIS Geospatial Clustering**: Computes convex hull bounding polygons for affected village clusters.
* **Live GeoJSON Map Feed**: Village boundaries color-coded by risk level (`NORMAL`, `WATCH`, `WARNING`, `OUTBREAK`) for Flutter Map widgets.
* **Simulated Outbreak Injection Benchmark (Objective O4)**:
  * Injected waterborne outbreak in rural block: Detected at **Day 25** vs. conventional clinic baseline at **Day 28** (**3 days earlier**).
  * Pre-outbreak false alarm rate: **0 false alarms / month / block** ($\le 1$ target).

---

## 🧪 Verification Test Suites

Run any verification suite natively using Python:

```bash
# Phase 2: Voice Triage, LangGraph & Doctor Summaries
python3 backend/tests/verify_phase2.py

# Phase 3: Chronic Care, Adherence & Objective O2 Benchmark
python3 backend/tests/verify_phase3.py

# Phase 4: Syndromic Surveillance, GeoJSON Map & Objective O4 Benchmark
python3 backend/tests/verify_phase4.py

# Run all verification suites in sequence:
python3 backend/tests/verify_phase2.py && python3 backend/tests/verify_phase3.py && python3 backend/tests/verify_phase4.py
```

---

## 🚀 Running the Services with Docker

```bash
cd backend
docker compose up --build -d
```
* **Interactive OpenAPI Swagger Docs**: `http://localhost:8000/docs`
* **MinIO Object Storage Console**: `http://localhost:9001`
* **PostgreSQL (PostGIS + TimescaleDB + pgvector)**: Port `5432`
* **Redis**: Port `6379`

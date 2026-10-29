from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.patient import Patient, Consent, ConsentType, ConsentStatus
from app.schemas.patient import PatientCreate, PatientPII
from app.core.security import encrypt_pii, decrypt_pii, generate_pseudonym
from app.crud.audit import log_audit_event


async def create_patient(
    db: AsyncSession,
    patient_in: PatientCreate,
    actor_id: str = "SYSTEM",
    actor_role: str = "ASHA"
) -> Patient:
    """
    Creates a new patient with DPDP compliance:
    1. Deterministically hashes the patient's phone/national ID into a pseudonym_id.
    2. Encrypts the PII block using AES-256 before writing to disk.
    3. Records the initial voice/written consent record.
    4. Records an immutable audit log entry.
    """
    unique_key = patient_in.pii.national_id or patient_in.pii.phone_number
    pseudonym_id = generate_pseudonym(unique_key)

    # Encrypt PII
    pii_dict = patient_in.pii.model_dump()
    encrypted_pii = encrypt_pii(pii_dict)

    patient = Patient(
        pseudonym_id=pseudonym_id,
        encrypted_pii=encrypted_pii,
        village_id=patient_in.village_id,
        age=patient_in.age,
        gender=patient_in.gender,
        primary_language=patient_in.primary_language,
        is_active=True
    )
    db.add(patient)
    await db.flush() # Populate patient.id

    # Create initial consent record
    consent = Consent(
        patient_id=patient.id,
        consent_type=patient_in.consent_type,
        status=ConsentStatus.ACTIVE,
        audio_s3_url=patient_in.consent_audio_s3_url,
        purpose="PRIMARY_HEALTHCARE_AND_SURVEILLANCE"
    )
    db.add(consent)
    await db.commit()
    await db.refresh(patient)

    # Audit log
    await log_audit_event(
        db=db,
        action="CREATE_PATIENT",
        resource_type="PATIENT",
        resource_id=str(patient.id),
        actor_id=actor_id,
        actor_role=actor_role,
        model_input={"village_id": patient_in.village_id, "age": patient_in.age, "gender": patient_in.gender}
    )

    return patient


async def get_patient_by_id(
    db: AsyncSession,
    patient_id: UUID,
    include_pii: bool = False
) -> Optional[Tuple[Patient, Optional[Dict[str, Any]]]]:
    """Retrieve patient by UUID, optionally decrypting PII for authorized roles."""
    stmt = select(Patient).where(Patient.id == patient_id, Patient.is_active == True)
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()
    if not patient:
        return None

    decrypted = None
    if include_pii and patient.encrypted_pii:
        try:
            decrypted = decrypt_pii(patient.encrypted_pii)
        except Exception:
            decrypted = {"error": "Decryption failed or invalid key"}

    return patient, decrypted


async def get_patients_by_village(
    db: AsyncSession,
    village_id: str,
    skip: int = 0,
    limit: int = 50
) -> List[Patient]:
    """Retrieve patients for an ASHA/ANM worker's assigned village."""
    stmt = (
        select(Patient)
        .where(Patient.village_id == village_id, Patient.is_active == True)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def dpdp_erase_patient(
    db: AsyncSession,
    patient_id: UUID,
    reason: str,
    actor_id: str,
    actor_role: str
) -> bool:
    """
    Executes Right-to-be-Forgotten under DPDP Act 2023:
    1. Overwrites encrypted PII with anonymized redaction marker.
    2. Revokes all active consents.
    3. Sets is_active to False.
    4. Logs tamper-evident audit record of erasure.
    """
    stmt = select(Patient).where(Patient.id == patient_id)
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()
    if not patient:
        return False

    patient.encrypted_pii = encrypt_pii({"status": "REDACTED_UNDER_DPDP_RIGHT_TO_ERASURE"})
    patient.is_active = False

    # Revoke consent
    consent_stmt = (
        update(Consent)
        .where(Consent.patient_id == patient_id)
        .values(status=ConsentStatus.REVOKED)
    )
    await db.execute(consent_stmt)
    await db.commit()

    await log_audit_event(
        db=db,
        action="DPDP_ERASURE",
        resource_type="PATIENT",
        resource_id=str(patient_id),
        actor_id=actor_id,
        actor_role=actor_role,
        model_input={"reason": reason}
    )

    return True

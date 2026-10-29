from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class PatientPII(BaseModel):
    """
    Personally Identifiable Information.
    Never stored in plaintext; encrypted with AES-256 before database write.
    """
    full_name: str = Field(..., example="Radha Devi")
    phone_number: str = Field(..., example="+919876543210")
    national_id: Optional[str] = Field(None, example="ABHA-12-3456-7890")
    address: Optional[str] = Field(None, example="House 14, Ward 2, Rampur Village")


class PatientCreate(BaseModel):
    pii: PatientPII
    village_id: str = Field(..., example="VILL-UP-RAMPUR-01")
    age: int = Field(..., ge=0, le=125, example=45)
    gender: str = Field(..., example="Female")
    primary_language: str = Field("hi", example="hi")
    consent_type: str = Field("VOICE", example="VOICE")
    consent_audio_s3_url: Optional[str] = None


class PatientResponse(BaseModel):
    id: UUID
    pseudonym_id: str
    village_id: str
    age: int
    gender: str
    primary_language: str
    is_active: bool
    created_at: datetime
    # Only decrypted and populated if requested by authorized role (ASHA / Doctor)
    pii: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class ConsentResponse(BaseModel):
    id: UUID
    patient_id: UUID
    consent_type: str
    status: str
    audio_s3_url: Optional[str] = None
    purpose: str
    granted_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DPDPErasureRequest(BaseModel):
    """Right to erasure request under DPDP Act 2023."""
    reason: str = Field(..., example="Patient withdrew consent and moved out of district")

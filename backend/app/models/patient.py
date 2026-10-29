import enum
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class ConsentType(str, enum.Enum):
    VOICE = "VOICE"
    WRITTEN = "WRITTEN"
    MISSED_CALL = "MISSED_CALL"


class ConsentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class Patient(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "patients"

    # Deterministic SHA-256 HMAC pseudonym for DPDP-compliant de-identified analytics & surveillance
    pseudonym_id = Column(String(64), unique=True, nullable=False, index=True)
    
    # AES-256 encrypted JSON string containing Name, Phone Number, National/ABHA ID, and Address
    encrypted_pii = Column(Text, nullable=False)
    
    # Village identifier for geographic routing and local ASHA worker matching
    village_id = Column(String(100), nullable=False, index=True)
    
    age = Column(Integer, nullable=False)
    gender = Column(String(20), nullable=False)
    primary_language = Column(String(50), default="hi")
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    consents = relationship("Consent", back_populates="patient", cascade="all, delete-orphan")
    encounters = relationship("Encounter", back_populates="patient", cascade="all, delete-orphan")
    adherence_records = relationship("MedicationAdherence", back_populates="patient", cascade="all, delete-orphan")


class Consent(Base, UUIDMixin):
    __tablename__ = "consents"

    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    consent_type = Column(String(50), nullable=False, default=ConsentType.VOICE)
    status = Column(String(50), nullable=False, default=ConsentStatus.ACTIVE)
    
    # URL to the MinIO/S3 stored audio recording where the patient gave verbal consent
    audio_s3_url = Column(Text, nullable=True)
    purpose = Column(String(255), default="PRIMARY_HEALTHCARE_AND_SURVEILLANCE")
    
    granted_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    patient = relationship("Patient", back_populates="consents")

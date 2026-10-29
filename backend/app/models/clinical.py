import enum
from datetime import datetime
from sqlalchemy import Column, String, Integer, Numeric, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class EncounterType(str, enum.Enum):
    TRIAGE = "TRIAGE"
    CHRONIC_FOLLOWUP = "CHRONIC_FOLLOWUP"
    ROUTINE = "ROUTINE"


class TriageLevel(str, enum.Enum):
    EMERGENCY = "EMERGENCY"
    REFER = "REFER"
    TREAT_LOCALLY = "TREAT_LOCALLY"
    HOME_CARE = "HOME_CARE"
    PENDING = "PENDING"


class Encounter(Base, UUIDMixin):
    __tablename__ = "encounters"

    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    health_worker_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    encounter_type = Column(String(50), nullable=False, default=EncounterType.TRIAGE)
    chief_complaint = Column(Text, nullable=True)
    audio_recording_url = Column(Text, nullable=True)
    language_code = Column(String(20), default="hi")
    triage_level = Column(String(50), default=TriageLevel.PENDING)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    patient = relationship("Patient", back_populates="encounters")
    health_worker = relationship("User")
    symptoms = relationship("Symptom", back_populates="encounter", cascade="all, delete-orphan")
    triage_decision = relationship("TriageDecision", back_populates="encounter", uselist=False, cascade="all, delete-orphan")
    referral = relationship("Referral", back_populates="encounter", uselist=False, cascade="all, delete-orphan")
    escalation = relationship("Escalation", back_populates="encounter", uselist=False, cascade="all, delete-orphan")


class Symptom(Base, UUIDMixin):
    __tablename__ = "symptoms"

    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id", ondelete="CASCADE"), nullable=False, index=True)
    symptom_code = Column(String(100), nullable=False, index=True)
    symptom_name = Column(String(255), nullable=False)
    severity = Column(String(50), default="MODERATE")
    duration_days = Column(Integer, nullable=True)
    is_red_flag = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    encounter = relationship("Encounter", back_populates="symptoms")


class VitalsSeries(Base):
    """
    TimescaleDB Hypertable partitioned by recorded_at.
    Stores continuous vital signs for chronic care tracking (BP, Blood Glucose, SpO2).
    """
    __tablename__ = "vitals_series"

    recorded_at = Column(DateTime(timezone=True), primary_key=True, default=datetime.utcnow, nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, index=True)
    encounter_id = Column(UUID(as_uuid=True), nullable=True)
    
    systolic_bp = Column(Integer, nullable=True)     # mmHg
    diastolic_bp = Column(Integer, nullable=True)    # mmHg
    blood_glucose = Column(Numeric(6, 2), nullable=True) # mg/dL
    glucose_context = Column(String(20), nullable=True)   # FASTING, POST_PRANDIAL, RANDOM
    pulse = Column(Integer, nullable=True)           # bpm
    spo2 = Column(Numeric(5, 2), nullable=True)      # %
    temperature = Column(Numeric(4, 1), nullable=True) # °C
    recorded_by = Column(UUID(as_uuid=True), nullable=True)


class MedicationAdherence(Base, UUIDMixin):
    __tablename__ = "medication_adherence"

    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    medication_name = Column(String(255), nullable=False)
    prescribed_dosage = Column(String(100), nullable=True)
    scheduled_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(50), nullable=False) # TAKEN, MISSED, SKIPPED
    reason_for_miss = Column(Text, nullable=True)
    reported_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    patient = relationship("Patient", back_populates="adherence_records")

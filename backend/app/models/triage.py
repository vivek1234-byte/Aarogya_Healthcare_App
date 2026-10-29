import enum
from datetime import datetime
from sqlalchemy import Column, String, Integer, Numeric, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    from sqlalchemy.types import NullType as Vector


class RedFlagRule(Base, UUIDMixin):
    """
    Deterministic safety rules that strictly override the LLM.
    Guarantees 100% escalation of danger signs and prevents unsafe AI hallucinations.
    """
    __tablename__ = "red_flag_rules"

    rule_code = Column(String(50), unique=True, nullable=False, index=True)
    condition_name = Column(String(150), nullable=False)
    criteria = Column(JSONB, nullable=False) # e.g. {"symptoms": ["chest_pain", "sweating"]}
    override_action = Column(String(50), default="EMERGENCY", nullable=False)
    priority = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class ProtocolChunk(Base, UUIDMixin):
    """
    Standard Clinical Guidelines (IMNCI, ICMR, NVBDCP) chunked and embedded
    using pgvector for Retrieval-Augmented Generation (RAG).
    """
    __tablename__ = "protocol_chunks"

    source_guideline = Column(String(150), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=True)
    metadata_json = Column("metadata", JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class TriageDecision(Base, UUIDMixin):
    """
    Clinical decision output from either the deterministic safety gate or LangGraph.
    """
    __tablename__ = "triage_decisions"

    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id", ondelete="CASCADE"), nullable=False, index=True)
    triage_category = Column(String(50), nullable=False) # EMERGENCY, REFER, TREAT_LOCALLY, HOME_CARE
    rationale = Column(Text, nullable=False)
    confidence_score = Column(Numeric(4, 3), nullable=True)
    protocol_citation = Column(Text, nullable=True)
    uncertainty_flag = Column(Boolean, default=False, nullable=False)
    rule_override_id = Column(UUID(as_uuid=True), ForeignKey("red_flag_rules.id"), nullable=True)
    decision_payload = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    encounter = relationship("Encounter", back_populates="triage_decision")
    rule_override = relationship("RedFlagRule")


class Referral(Base, UUIDMixin, TimestampMixin):
    """
    One-page structured summary sent to the PHC or telemedicine doctor.
    """
    __tablename__ = "referrals"

    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    target_facility = Column(String(255), nullable=False)
    urgency_level = Column(String(50), nullable=False) # CRITICAL_IMMEDIATE, URGENT_24HR, ROUTINE
    summary_pdf_s3_url = Column(Text, nullable=True)
    summary_text = Column(Text, nullable=False)
    status = Column(String(50), default="PENDING", nullable=False) # PENDING, ACCEPTED, COMPLETED, CANCELLED
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    doctor_notes = Column(Text, nullable=True)

    encounter = relationship("Encounter", back_populates="referral")
    patient = relationship("Patient")
    doctor = relationship("User")


class Escalation(Base, UUIDMixin):
    """
    Urgent clinical escalation alerts pushed to supervisory staff / PHC doctors.
    """
    __tablename__ = "escalations"

    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id", ondelete="CASCADE"), nullable=False, index=True)
    reason = Column(Text, nullable=False)
    escalated_to_role = Column(String(50), default="DOCTOR", nullable=False)
    escalated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    encounter = relationship("Encounter", back_populates="escalation")

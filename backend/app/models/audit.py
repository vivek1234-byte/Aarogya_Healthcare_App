from datetime import datetime
from sqlalchemy import Column, String, BigInteger, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from app.core.database import Base


class AuditLog(Base):
    """
    Append-only, cryptographically chained tamper-evident audit ledger.
    Every clinical decision, rule firing, model output, and human override is recorded.
    """
    __tablename__ = "audit_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    actor_id = Column(String(100), nullable=True)
    actor_role = Column(String(50), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(String(100), nullable=True)
    
    model_input = Column(JSONB, nullable=True)
    model_output = Column(JSONB, nullable=True)
    rule_fired = Column(String(100), nullable=True)
    human_override = Column(Boolean, default=False, nullable=False)
    
    # Cryptographic SHA-256 chain: entry_hash = SHA256(previous_hash + entry_data)
    previous_hash = Column(String(64), nullable=False)
    entry_hash = Column(String(64), nullable=False)

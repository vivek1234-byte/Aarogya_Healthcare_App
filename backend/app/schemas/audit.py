from typing import Optional, Any
from pydantic import BaseModel
from datetime import datetime


class AuditLogResponse(BaseModel):
    id: int
    timestamp: datetime
    actor_id: Optional[str] = None
    actor_role: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    rule_fired: Optional[str] = None
    human_override: bool
    previous_hash: str
    entry_hash: str

    class Config:
        from_attributes = True


class AuditChainVerificationResponse(BaseModel):
    is_valid: bool
    total_entries_verified: int
    broken_entry_id: Optional[int] = None
    message: str

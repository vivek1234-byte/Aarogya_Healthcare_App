from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime


class ComponentStatus(BaseModel):
    status: str # "UP", "DOWN", "DEGRADED"
    latency_ms: Optional[float] = None
    details: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    project: str
    version: str
    timestamp: datetime
    components: Dict[str, ComponentStatus]

from datetime import datetime
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base
from app.models.base import UUIDMixin

try:
    from geoalchemy2 import Geometry
except ImportError:
    from sqlalchemy.types import Text as Geometry


class SurveillanceSignal(Base):
    """
    TimescaleDB Hypertable for syndromic surveillance streams:
    - Pharmacy ORS/anti-pyretic sales
    - Clinic acute fever/diarrhea encounters
    - Village school absenteeism
    """
    __tablename__ = "surveillance_signals"

    timestamp = Column(DateTime(timezone=True), primary_key=True, default=datetime.utcnow, nullable=False, index=True)
    village_id = Column(String(100), primary_key=True, nullable=False, index=True)
    signal_type = Column(String(100), primary_key=True, nullable=False, index=True) # CLINIC_FEVER, PHARMACY_ORS_SALES, etc.
    count = Column(Integer, nullable=False)
    source = Column(String(100), default="COMMUNITY_HEALTH_POST")
    metadata_json = Column("metadata", JSONB, nullable=True)


class OutbreakAlert(Base, UUIDMixin):
    """
    Spatial-temporal outbreak cluster alerts flagged by the surveillance engine.
    Uses PostGIS Geometry for village polygons and affected boundaries.
    """
    __tablename__ = "outbreak_alerts"

    detected_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    syndrome = Column(String(100), nullable=False)
    affected_villages = Column(JSONB, nullable=False) # List of village IDs
    cluster_geom = Column(Geometry(geometry_type="GEOMETRY", srid=4326), nullable=True) # PostGIS geometry
    z_score = Column(Numeric(5, 2), nullable=False)
    confidence = Column(Numeric(4, 3), nullable=False)
    baseline_expected_cases = Column(Integer, nullable=True)
    observed_cases = Column(Integer, nullable=True)
    status = Column(String(50), default="ACTIVE", nullable=False) # ACTIVE, INVESTIGATING, CONTAINED, FALSE_ALARM
    notes = Column(Text, nullable=True)

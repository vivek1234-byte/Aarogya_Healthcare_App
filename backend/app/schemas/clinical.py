from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class VitalsCreate(BaseModel):
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    systolic_bp: Optional[int] = Field(None, ge=40, le=300, example=138)
    diastolic_bp: Optional[int] = Field(None, ge=30, le=200, example=88)
    blood_glucose: Optional[Decimal] = Field(None, ge=20, le=800, example=165.5)
    glucose_context: Optional[str] = Field("RANDOM", example="FASTING") # FASTING, POST_PRANDIAL, RANDOM
    pulse: Optional[int] = Field(None, ge=30, le=250, example=76)
    spo2: Optional[Decimal] = Field(None, ge=50, le=100, example=98.0)
    temperature: Optional[Decimal] = Field(None, ge=30, le=45, example=37.2)
    recorded_at: Optional[datetime] = None


class VitalsResponse(BaseModel):
    recorded_at: datetime
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    blood_glucose: Optional[Decimal] = None
    glucose_context: Optional[str] = None
    pulse: Optional[int] = None
    spo2: Optional[Decimal] = None
    temperature: Optional[Decimal] = None

    class Config:
        from_attributes = True


class VitalsTrendResponse(BaseModel):
    patient_id: UUID
    readings: List[VitalsResponse]
    deterioration_flag: bool = False
    deterioration_reason: Optional[str] = None
    systolic_trend: str = "STABLE" # RISING, STABLE, FALLING
    glucose_trend: str = "STABLE"


class SymptomInput(BaseModel):
    symptom_code: str = Field(..., example="fever")
    symptom_name: str = Field(..., example="High Fever")
    severity: str = Field("MODERATE", example="SEVERE")
    duration_days: Optional[int] = Field(1, ge=0, example=3)
    is_red_flag: bool = False
    notes: Optional[str] = None


class SymptomResponse(BaseModel):
    id: UUID
    symptom_code: str
    symptom_name: str
    severity: str
    duration_days: Optional[int] = None
    is_red_flag: bool
    created_at: datetime

    class Config:
        from_attributes = True


class EncounterCreate(BaseModel):
    patient_id: UUID
    encounter_type: str = Field("TRIAGE", example="TRIAGE")
    chief_complaint: Optional[str] = Field(None, example="Chest discomfort and sweating")
    audio_recording_url: Optional[str] = None
    language_code: str = Field("hi", example="hi")
    symptoms: List[SymptomInput] = []


class EncounterResponse(BaseModel):
    id: UUID
    patient_id: UUID
    encounter_type: str
    chief_complaint: Optional[str] = None
    triage_level: str
    language_code: str
    created_at: datetime
    symptoms: List[SymptomResponse] = []

    class Config:
        from_attributes = True

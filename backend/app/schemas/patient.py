from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class PatientCreate(BaseModel):
    name: str
    age: Optional[int] = None
    sex: Optional[str] = None
    conditions: str = ""
    medical_history: str = ""
    diet_notes: str = ""
    hydration_habits: str = ""
    smoking: str = ""


class PatientUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    sex: Optional[str] = None
    conditions: Optional[str] = None
    medical_history: Optional[str] = None
    diet_notes: Optional[str] = None
    hydration_habits: Optional[str] = None
    smoking: Optional[str] = None


class PatientRead(BaseModel):
    id: int
    name: str
    age: Optional[int] = None
    sex: Optional[str] = None
    conditions: str
    medical_history: str
    diet_notes: str
    hydration_habits: str
    smoking: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MedicationCreate(BaseModel):
    name: str
    dosage: str = ""
    frequency: str = ""
    time_of_day: str = ""
    instructions: str = ""
    conditions_not_to_take: str = ""


class MedicationRead(BaseModel):
    id: int
    patient_id: int
    name: str
    dosage: str
    frequency: str
    time_of_day: str
    instructions: str
    conditions_not_to_take: str
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MedicationLogCreate(BaseModel):
    medication_id: Optional[int] = None
    skipped: bool = False
    note: str = ""


class MedicationLogRead(BaseModel):
    id: int
    patient_id: int
    medication_id: Optional[int]
    taken_at: datetime
    skipped: bool
    note: str

    model_config = {"from_attributes": True}


class SymptomLogCreate(BaseModel):
    symptoms: str
    severity: str = ""
    notes: str = ""


class SymptomLogRead(BaseModel):
    id: int
    patient_id: int
    logged_at: datetime
    symptoms: str
    severity: str
    notes: str

    model_config = {"from_attributes": True}


class VitalsLogCreate(BaseModel):
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    heart_rate: Optional[int] = None
    weight_kg: Optional[float] = None
    temperature_c: Optional[float] = None


class VitalsLogRead(BaseModel):
    id: int
    patient_id: int
    logged_at: datetime
    systolic_bp: Optional[int]
    diastolic_bp: Optional[int]
    heart_rate: Optional[int]
    weight_kg: Optional[float]
    temperature_c: Optional[float]
    triage_flag: str
    triage_note: str

    model_config = {"from_attributes": True}


class RiskEventRead(BaseModel):
    id: int
    patient_id: int
    created_at: datetime
    event_type: str
    severity: str
    description: str
    acknowledged: bool

    model_config = {"from_attributes": True}

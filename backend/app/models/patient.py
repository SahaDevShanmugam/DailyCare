from datetime import datetime
from sqlalchemy import String, Text, Float, Integer, Boolean, DateTime, ForeignKey, Column
from sqlalchemy.orm import relationship
from app.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    age = Column(Integer, nullable=True)  # optional, for HF risk score
    sex = Column(String(10), nullable=True)  # optional, e.g. "M", "F"

    conditions = Column(Text, default="")
    medical_history = Column(Text, default="")
    diet_notes = Column(Text, default="")
    hydration_habits = Column(Text, default="")
    smoking = Column(String(50), default="")

    medications = relationship("Medication", back_populates="patient", cascade="all, delete-orphan")
    medication_logs = relationship("MedicationLog", back_populates="patient", cascade="all, delete-orphan")
    symptom_logs = relationship("SymptomLog", back_populates="patient", cascade="all, delete-orphan")
    vitals_logs = relationship("VitalsLog", back_populates="patient", cascade="all, delete-orphan")
    risk_events = relationship("RiskEvent", back_populates="patient", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="patient", cascade="all, delete-orphan")


class Medication(Base):
    __tablename__ = "medications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    name = Column(String(255), nullable=False)
    dosage = Column(String(100), default="")
    frequency = Column(String(100), default="")
    time_of_day = Column(String(100), default="")  # e.g. "Morning", "08:00", "After breakfast"
    instructions = Column(Text, default="")  # Clinical-grade: e.g. "Take 2 tablets after every meal"
    conditions_not_to_take = Column(Text, default="")  # e.g. "Do not take multiple doses within 4 hours"
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="medications")
    logs = relationship("MedicationLog", back_populates="medication", cascade="all, delete-orphan")


class MedicationLog(Base):
    __tablename__ = "medication_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=True)
    taken_at = Column(DateTime, default=datetime.utcnow)
    skipped = Column(Boolean, default=False)
    note = Column(Text, default="")

    patient = relationship("Patient", back_populates="medication_logs")
    medication = relationship("Medication", back_populates="logs")


class SymptomLog(Base):
    __tablename__ = "symptom_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    logged_at = Column(DateTime, default=datetime.utcnow)
    symptoms = Column(Text, nullable=False)
    severity = Column(String(20), default="")
    notes = Column(Text, default="")

    patient = relationship("Patient", back_populates="symptom_logs")


class VitalsLog(Base):
    __tablename__ = "vitals_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    logged_at = Column(DateTime, default=datetime.utcnow)
    systolic_bp = Column(Integer, nullable=True)
    diastolic_bp = Column(Integer, nullable=True)
    heart_rate = Column(Integer, nullable=True)
    weight_kg = Column(Float, nullable=True)
    temperature_c = Column(Float, nullable=True)
    triage_flag = Column(String(50), default="")
    triage_note = Column(Text, default="")

    patient = relationship("Patient", back_populates="vitals_logs")


class RiskEvent(Base):
    __tablename__ = "risk_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String(50), nullable=False)
    severity = Column(String(20), default="")
    description = Column(Text, nullable=False)
    acknowledged = Column(Boolean, default=False)

    patient = relationship("Patient", back_populates="risk_events")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    role = Column(String(20), nullable=False)  # "user" | "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="chat_messages")

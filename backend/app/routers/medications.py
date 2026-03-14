from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.database import get_db
from app.models.patient import Patient, Medication, MedicationLog
from app.schemas.patient import (
    MedicationCreate,
    MedicationRead,
    MedicationLogCreate,
    MedicationLogRead,
)

router = APIRouter(prefix="/patients/{patient_id}/medications", tags=["medications"])


@router.post("/", response_model=MedicationRead)
async def add_medication(
    patient_id: int, data: MedicationCreate, db: AsyncSession = Depends(get_db)
):
    r = await db.execute(select(Patient).where(Patient.id == patient_id))
    if not r.scalar_one_or_none():
        raise HTTPException(404, "Patient not found")
    med = Medication(
        patient_id=patient_id,
        name=data.name,
        dosage=data.dosage or "",
        frequency=data.frequency or "",
        time_of_day=data.time_of_day or "",
        instructions=data.instructions or "",
        conditions_not_to_take=getattr(data, "conditions_not_to_take", "") or "",
    )
    db.add(med)
    await db.commit()
    await db.refresh(med)
    return med


@router.get("/", response_model=list[MedicationRead])
async def list_medications(patient_id: int, db: AsyncSession = Depends(get_db)):
    r = await db.execute(
        select(Medication).where(Medication.patient_id == patient_id).order_by(Medication.id)
    )
    return list(r.scalars().all())


@router.post("/log", response_model=MedicationLogRead)
async def log_medication(
    patient_id: int, data: MedicationLogCreate, db: AsyncSession = Depends(get_db)
):
    r = await db.execute(select(Patient).where(Patient.id == patient_id))
    if not r.scalar_one_or_none():
        raise HTTPException(404, "Patient not found")
    log = MedicationLog(
        patient_id=patient_id,
        medication_id=data.medication_id,
        skipped=data.skipped,
        note=data.note or "",
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


@router.get("/log", response_model=list[MedicationLogRead])
async def list_medication_logs(
    patient_id: int, limit: int = 50, db: AsyncSession = Depends(get_db)
):
    r = await db.execute(
        select(MedicationLog)
        .where(MedicationLog.patient_id == patient_id)
        .order_by(MedicationLog.taken_at.desc())
        .limit(limit)
    )
    return list(r.scalars().all())

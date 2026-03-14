from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.patient import Patient, SymptomLog
from app.schemas.patient import SymptomLogCreate, SymptomLogRead

router = APIRouter(prefix="/patients/{patient_id}/symptoms", tags=["symptoms"])


@router.post("/", response_model=SymptomLogRead)
async def log_symptom(
    patient_id: int, data: SymptomLogCreate, db: AsyncSession = Depends(get_db)
):
    r = await db.execute(select(Patient).where(Patient.id == patient_id))
    if not r.scalar_one_or_none():
        raise HTTPException(404, "Patient not found")
    log = SymptomLog(
        patient_id=patient_id,
        symptoms=data.symptoms,
        severity=data.severity or "",
        notes=data.notes or "",
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


@router.get("/", response_model=list[SymptomLogRead])
async def list_symptom_logs(
    patient_id: int, limit: int = 50, db: AsyncSession = Depends(get_db)
):
    r = await db.execute(
        select(SymptomLog)
        .where(SymptomLog.patient_id == patient_id)
        .order_by(SymptomLog.logged_at.desc())
        .limit(limit)
    )
    return list(r.scalars().all())

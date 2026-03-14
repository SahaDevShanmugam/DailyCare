from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database import get_db
from app.models.patient import Patient, VitalsLog, RiskEvent
from app.triage.vitals import triage_vitals
from app.schemas.patient import VitalsLogCreate, VitalsLogRead

router = APIRouter(prefix="/patients/{patient_id}/vitals", tags=["vitals"])


@router.post("/", response_model=VitalsLogRead)
async def log_vitals(
    patient_id: int, data: VitalsLogCreate, db: AsyncSession = Depends(get_db)
):
    r = await db.execute(select(Patient).where(Patient.id == patient_id))
    if not r.scalar_one_or_none():
        raise HTTPException(404, "Patient not found")

    # Previous weight for triage (weight gain alert)
    previous_weight_kg = None
    if data.weight_kg is not None:
        prev = await db.execute(
            select(VitalsLog.weight_kg)
            .where(VitalsLog.patient_id == patient_id, VitalsLog.weight_kg.isnot(None))
            .order_by(desc(VitalsLog.logged_at))
            .limit(1)
        )
        previous_weight_kg = prev.scalar_one_or_none()

    triage = triage_vitals(
        systolic_bp=data.systolic_bp,
        diastolic_bp=data.diastolic_bp,
        heart_rate=data.heart_rate,
        weight_kg=data.weight_kg,
        previous_weight_kg=previous_weight_kg,
        temperature_c=data.temperature_c,
    )

    log = VitalsLog(
        patient_id=patient_id,
        systolic_bp=data.systolic_bp,
        diastolic_bp=data.diastolic_bp,
        heart_rate=data.heart_rate,
        weight_kg=data.weight_kg,
        temperature_c=data.temperature_c,
        triage_flag=triage.flag,
        triage_note=triage.note,
    )
    db.add(log)

    # Always clear previous vitals-based alerts when new vitals are logged, so alerts
    # reflect the latest reading (e.g. high HR alert goes away after a normal HR entry).
    prev_vitals_alerts = await db.execute(
        select(RiskEvent).where(
            RiskEvent.patient_id == patient_id,
            RiskEvent.event_type == "vitals",
            RiskEvent.acknowledged == False,
        )
    )
    for event in prev_vitals_alerts.scalars().all():
        event.acknowledged = True

    if triage.should_escalate:
        risk = RiskEvent(
            patient_id=patient_id,
            event_type="vitals",
            severity="critical",
            description=triage.note,
        )
        db.add(risk)
    await db.commit()
    await db.refresh(log)
    return log


@router.get("/", response_model=list[VitalsLogRead])
async def list_vitals(
    patient_id: int, limit: int = 50, db: AsyncSession = Depends(get_db)
):
    r = await db.execute(
        select(VitalsLog)
        .where(VitalsLog.patient_id == patient_id)
        .order_by(VitalsLog.logged_at.desc())
        .limit(limit)
    )
    return list(r.scalars().all())

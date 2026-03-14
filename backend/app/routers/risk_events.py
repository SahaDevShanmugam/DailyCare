from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.patient import Patient, RiskEvent
from app.schemas.patient import RiskEventRead

router = APIRouter(prefix="/patients/{patient_id}/risk-events", tags=["risk-events"])


@router.get("/", response_model=list[RiskEventRead])
async def list_risk_events(
    patient_id: int,
    limit: int = 50,
    acknowledged: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    r = await db.execute(select(Patient).where(Patient.id == patient_id))
    if not r.scalar_one_or_none():
        raise HTTPException(404, "Patient not found")
    q = select(RiskEvent).where(RiskEvent.patient_id == patient_id)
    if acknowledged is not None:
        q = q.where(RiskEvent.acknowledged == acknowledged)
    q = q.order_by(RiskEvent.created_at.desc()).limit(limit)
    r = await db.execute(q)
    return list(r.scalars().all())


@router.patch("/{event_id}/acknowledge", response_model=RiskEventRead)
async def acknowledge_risk_event(
    patient_id: int, event_id: int, db: AsyncSession = Depends(get_db)
):
    r = await db.execute(
        select(RiskEvent).where(
            RiskEvent.id == event_id, RiskEvent.patient_id == patient_id
        )
    )
    event = r.scalar_one_or_none()
    if not event:
        raise HTTPException(404, "Risk event not found")
    event.acknowledged = True
    await db.commit()
    await db.refresh(event)
    return event

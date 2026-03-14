import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database import get_db
from app.models.patient import Patient, Medication, MedicationLog, VitalsLog, SymptomLog, ChatMessage
from app.schemas.chat import ChatRequest, ChatResponse, ChatMessageRead
from app.services.agent import get_agent_response
from app.utils.patient_context import format_patient_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/patients/{patient_id}/chat", tags=["chat"])

VITALS_HISTORY_LIMIT = 14
SYMPTOM_HISTORY_LIMIT = 10
MED_LOG_LIMIT = 30
CHAT_HISTORY_LIMIT = 20


@router.post("/", response_model=ChatResponse)
async def chat(
    patient_id: int, body: ChatRequest, db: AsyncSession = Depends(get_db)
):
    r = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = r.scalar_one_or_none()
    if not patient:
        raise HTTPException(404, "Patient not found")

    meds_r = await db.execute(
        select(Medication).where(
            Medication.patient_id == patient_id, Medication.active == True
        )
    )
    meds = list(meds_r.scalars().all())
    med_id_to_name = {m.id: m.name for m in meds}

    vitals_r = await db.execute(
        select(VitalsLog)
        .where(VitalsLog.patient_id == patient_id)
        .order_by(desc(VitalsLog.logged_at))
        .limit(VITALS_HISTORY_LIMIT)
    )
    vitals_history = list(vitals_r.scalars().all())

    symptoms_r = await db.execute(
        select(SymptomLog)
        .where(SymptomLog.patient_id == patient_id)
        .order_by(desc(SymptomLog.logged_at))
        .limit(SYMPTOM_HISTORY_LIMIT)
    )
    symptom_history = list(symptoms_r.scalars().all())

    med_logs_r = await db.execute(
        select(MedicationLog)
        .where(MedicationLog.patient_id == patient_id)
        .order_by(desc(MedicationLog.taken_at))
        .limit(MED_LOG_LIMIT)
    )
    med_logs = list(med_logs_r.scalars().all())

    chat_r = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.patient_id == patient_id)
        .order_by(desc(ChatMessage.created_at))
        .limit(CHAT_HISTORY_LIMIT)
    )
    chat_history_reversed = list(chat_r.scalars().all())
    chat_history = list(reversed(chat_history_reversed))

    patient_context = format_patient_context(
        patient, meds, vitals_history, symptom_history, med_logs, med_id_to_name, chat_history
    )
    try:
        response = await get_agent_response(
            patient_id=patient_id,
            patient_context=patient_context,
            user_message=body.message,
            recent_summary=body.recent_summary or "",
        )
        # Persist so "Full chat & history" shows this exchange
        user_msg = ChatMessage(patient_id=patient_id, role="user", content=body.message)
        assistant_msg = ChatMessage(patient_id=patient_id, role="assistant", content=response)
        db.add(user_msg)
        db.add(assistant_msg)
        await db.commit()
        return ChatResponse(response=response)
    except Exception as e:
        logger.exception("Chat/LLM error")
        raw = str(e).strip() or "The assistant is temporarily unavailable."
        raw_lower = raw.lower()
        if "api_key" in raw_lower or "authentication" in raw_lower or "incorrect api key" in raw_lower or "invalid" in raw_lower and "key" in raw_lower:
            msg = "DailyCare is not connected. Set POE_API_KEY in backend/.env (get a key at https://poe.com/api_key) and restart the server."
        elif "429" in raw or "quota" in raw_lower or "exceeded your current quota" in raw_lower or "billing" in raw_lower or "insufficient_credits" in raw_lower or "resource_exhausted" in raw_lower:
            msg = (
                "Your Poe quota or credits have been used. "
                "Add credits at https://poe.com/api_key or try again later when your quota resets."
            )
        elif "rate" in raw_lower and "limit" in raw_lower:
            msg = "Rate limit reached. Please wait a moment and try again."
        elif "connection" in raw_lower or "timeout" in raw_lower or "network" in raw_lower:
            msg = "Could not reach the AI service. Check your internet connection and try again."
        elif "model" in raw_lower and ("not found" in raw_lower or "unknown" in raw_lower):
            msg = "The AI model is not available. Try setting POE_MODEL in backend/.env (e.g. Claude-Sonnet-4, GPT-4o)."
        else:
            msg = raw[:180] + ("…" if len(raw) > 180 else "")
        return ChatResponse(response=msg)


@router.get("/history", response_model=list[ChatMessageRead])
async def chat_history(
    patient_id: int, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    r = await db.execute(
        select(Patient).where(Patient.id == patient_id)
    )
    if not r.scalar_one_or_none():
        raise HTTPException(404, "Patient not found")
    r = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.patient_id == patient_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
    )
    return list(r.scalars().all())

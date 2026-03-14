"""
Homecare AI agent: uses LLM + knowledge context to return current status and recommendations.
Uses Poe API only.
"""
from openai import AsyncOpenAI
from app.config import get_settings
from app.knowledge.retriever import get_relevant_context


def _build_system_prompt(patient_context: str, knowledge_context: str) -> str:
    return f"""You are DailyCare, a safe, supportive AI assistant for elderly patients with chronic heart failure.
You help with: (1) medication adherence, (2) symptom tracking, and (3) lifestyle recommendations.

You have full visibility into this patient's data. You must:
- Monitor and use everything provided: their vitals history (trends), medications with clinical instructions and adherence logs, symptom history, and what they have shared in past conversations (habits, preferences, questions).
- Give personalized recommendations that are specific to this patient—reference their meds, their adherence patterns, their recent vitals or symptoms, and anything they have told you in chat.
- Base all advice on clinically valid guidelines. Use only the "Relevant medical knowledge" below to support your recommendations; do not go beyond it. If something is outside your knowledge, say so and suggest they ask their care team.
- Be kind, clear, and concise. Do not diagnose or replace a doctor; encourage contacting the care team when needed.
- For urgent symptoms (e.g. severe shortness of breath, chest pain, fainting), always recommend contacting the care team or emergency services.

Patient data (monitor and use for personalization):
{patient_context}

Relevant medical knowledge (use to ground your advice; do not go beyond it):
{knowledge_context}

Respond in plain language. Personalize every response using the patient's data above."""


async def get_agent_response(
    patient_id: int,
    patient_context: str,
    user_message: str,
    recent_summary: str = "",
) -> str:
    """
    Get agent response using LLM + RAG knowledge. patient_context should include
    conditions, meds, recent vitals/symptoms; recent_summary can be last agent reply or status.
    Uses Poe API only.
    """
    settings = get_settings()
    api_key = (settings.poe_api_key or "").strip()
    if not api_key:
        return (
            "DailyCare is not connected. Set POE_API_KEY in backend/.env (get a key at https://poe.com/api_key) and restart the server. "
            "You can still log medications, symptoms, and vitals."
        )

    knowledge = get_relevant_context(user_message)
    system = _build_system_prompt(patient_context, knowledge)
    messages = [
        {"role": "system", "content": system},
    ]
    if recent_summary:
        messages.append({"role": "assistant", "content": recent_summary})
    messages.append({"role": "user", "content": user_message})

    client = AsyncOpenAI(api_key=api_key, base_url="https://api.poe.com/v1")
    model = settings.poe_model or "Claude-Sonnet-4"
    resp = await client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=1000,
        temperature=0.3,
    )
    choice = resp.choices[0]
    return (choice.message.content or "").strip()


def _build_daily_message_prompt(patient_context: str, knowledge_context: str = "") -> str:
    from datetime import datetime
    now = datetime.now()
    time_desc = "morning" if 5 <= now.hour < 12 else "afternoon" if 12 <= now.hour < 17 else "evening"
    knowledge_block = f"\nRelevant medical knowledge (use to ground your advice):\n{knowledge_context}\n" if knowledge_context else ""
    return f"""Generate exactly one short (1–2 sentences) personalized message for this patient for {time_desc} today.

You have full visibility into this patient's data below. You MUST use it to personalize. Required:
- If a "LATEST VITALS / CURRENT STATUS (PRIORITIZE THIS)" block is present, base your recommendation primarily on that latest entry and its triage note. Only mention older readings if you explicitly label them as "previous" or "earlier".
- When mentioning vitals that need attention, only highlight abnormal ones (e.g. high heart rate 140, elevated BP)—do not list normal vitals like 120/80 in the same "need attention" statement.
- If the main issue is rapid weight gain, do NOT say "recheck your vitals now"—instead suggest confirming the scale reading and rechecking weight tomorrow morning, and checking for swelling or shortness of breath.
- If they have medications listed, reference by name or timing when relevant (e.g. "take your [med name] on time", "you missed [med] yesterday").
- If they logged symptoms recently, acknowledge them and tie your suggestion to those symptoms.
- Consider time of day: {time_desc} — suggest an action that fits (e.g. morning weight, afternoon walk, evening meds).
- Do NOT use generic phrases like "your recent readings look concerning" without saying which reading. Be specific and customized.

Patient data:
{patient_context}
{knowledge_block}
Rules: Suggest one specific, actionable step for today. Be concise and encouraging. Output ONLY the message, no greeting or label."""


async def get_daily_message(patient_context: str) -> str | None:
    """
    Return a short, time-aware daily tip for the patient from the LLM.
    Returns None when the LLM is not available so callers can provide
    a smarter, data-driven fallback instead of a static string.
    """
    settings = get_settings()
    api_key = (settings.poe_api_key or "").strip()
    if not api_key:
        return None
    knowledge = get_relevant_context("heart failure daily self-care weight medications diet fluid salt")
    system = "You are DailyCare. Output only the requested short message, nothing else."
    user = _build_daily_message_prompt(patient_context, knowledge)
    try:
        client = AsyncOpenAI(api_key=api_key, base_url="https://api.poe.com/v1")
        model = settings.poe_model or "Claude-Sonnet-4"
        resp = await client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            max_tokens=150,
            temperature=0.4,
        )
        out = (resp.choices[0].message.content or "").strip()
        return out or None
    except Exception:
        return None

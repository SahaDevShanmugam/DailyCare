DailyCare – Homecare AI for Elderly Chronic Heart Failure

Monitoring and assistance for elderly patients with chronic heart failure.

Core Functions

1. **Medication adherence** – Reminders, logging, and safety checks (indications, contraindications, side effects).
2. **Symptom tracking** – Daily symptom and vitals input (BP, heart rate, weight, temperature) with triage for abnormal values.
3. **Lifestyle recommendations** – Evidence-based advice from a curated heart-failure knowledge base.

Architecture

- **User interface** – Medication reminders/logging, symptom and vitals input (elderly-friendly).
- **Backend API** – Receives logs and messages, returns agent responses.
- **Patient database** – User info, medication schedule, vitals, risk events.
- **Triage engine** – Flags severe/abnormal vitals and suggests escalation.
- **RAG + knowledge layer** – Curated HF and medication safety content.
- **Cloud LLM** – Status summaries and next-step recommendations.

## Quick start

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # Set OPENAI_API_KEY and optional DB path
uvicorn app.main:app --reload
```

API: http://localhost:8000  
Docs: http://localhost:8000/docs  

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Then open http://localhost:5173 (or the port shown). The dev server proxies `/api` to the backend; for a different backend URL set `VITE_API_URL` in `.env`.

### Environment

**Backend** (in `backend/.env`):

- **Poe** (takes precedence if set): `POE_API_KEY` – get at [poe.com/api_key](https://poe.com/api_key). `POE_MODEL` – optional; default `Claude-Sonnet-4` (or `GPT-4o`, `Gemini-3-Pro`, etc.).
- **OpenAI**: `OPENAI_API_KEY` – used if Poe is not set. `OPENAI_BASE_URL` – optional; default `https://api.openai.com/v1`.
- `DATABASE_URL` – Optional; defaults to SQLite `./dailycare.db`.

**Frontend** (in `frontend/.env`):

- `VITE_API_URL` – Optional; default `/api` (proxied to backend in dev).

**If the assistant says "DailyCare is not connected":** Set either `POE_API_KEY` or `OPENAI_API_KEY` in `backend/.env`. Restart the backend after changing `.env`. Check `GET http://localhost:8000/config/status` — it returns `{"poe_configured": true}` or `{"openai_configured": true}` when a key is loaded.

## Data (from proposal)

- **Medical knowledge**: HF definitions/stages, symptom patterns, lifestyle advice, medication indications/contraindications/side effects/frequency.
- **Patient data**: Conditions, history, diet/hydration/smoking, vitals (BP, HR, weight, temperature).

## Evaluation (from proposal)

- HF clinical dataset – risk classification accuracy.
- Heart failure knowledge / NCLEX-style – response accuracy.

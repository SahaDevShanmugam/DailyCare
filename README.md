# DailyCare – Homecare AI for Elderly Chronic Heart Failure

**DailyCare** is a homecare AI assistant for elderly patients with chronic heart failure. It supports day‑to‑day monitoring and guidance through:

- **Medication adherence**: reminders, logging, and basic safety checks (indications, contraindications, side effects).
- **Symptom and vitals tracking**: daily input of blood pressure, heart rate, weight, temperature with triage for abnormal values.
- **Lifestyle recommendations**: evidence-based advice from a curated heart‑failure knowledge base.
- **Risk scoring**: ML-based heart‑failure risk estimate adjusted by current vitals.
- **Conversational agent**: RAG‑augmented cloud LLM for personalized, context‑aware responses.

---

## 1. Installation

### 1.1 Prerequisites

- **Python** ≥ 3.10 (backend)
- **Node.js** ≥ 18 and **npm** (frontend)
- **Git** (optional but recommended)

### 1.2 Clone the repository

```bash
git clone https://github.com/SahaDevShanmugam/DailyCare.git
cd DailyCare
```

### 1.3 Backend dependencies

From the project root:

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate        # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

Create your backend environment file:

```bash
cp .env.example .env
```

Then edit `.env` to set at least one LLM provider:

- **Poe (takes precedence if set):**
  - `POE_API_KEY` – get from `poe.com/api_key`
  - `POE_MODEL` (optional) – e.g. `Claude-Sonnet-4`, `gpt-4o`, `Gemini-1.5-Pro`
- **OpenAI (used if Poe is not set):**
  - `OPENAI_API_KEY`
  - `OPENAI_BASE_URL` (optional, default `https://api.openai.com/v1`)
- **Database (optional):**
  - `DATABASE_URL` (defaults to `sqlite:///./dailycare.db`)

### 1.4 Frontend dependencies

From the project root:

```bash
cd frontend
npm install
```

Optional `frontend/.env`:

```bash
# default is /api, proxied to backend in dev
VITE_API_URL=/api
```

---

## 2. Running the system

### 2.1 Start the backend (FastAPI)

From `backend/` with the virtual environment activated:

```bash
uvicorn app.main:app --reload
```

- API base URL: `http://localhost:8000`
- Docs (OpenAPI/Swagger): `http://localhost:8000/docs`
- LLM configuration status: `http://localhost:8000/config/status`  
  (returns `{"poe_configured": true}` or `{"openai_configured": true}` when a key is loaded)

If the assistant says **“DailyCare is not connected”**:

- Ensure `POE_API_KEY` **or** `OPENAI_API_KEY` is set in `backend/.env`.
- Restart the backend after editing `.env`.

### 2.2 Start the frontend (React/Vite)

In a separate terminal:

```bash
cd frontend
npm run dev
```

By default Vite runs at `http://localhost:5173` (or another port if 5173 is taken; the URL is printed in the terminal).

- `/api` is proxied to `http://localhost:8000` in development.
- If your backend runs elsewhere, set `VITE_API_URL` in `frontend/.env`.

Open the printed URL in your browser to access the DailyCare dashboard.

---

## 3. Example usage

### 3.1 First‑time setup

1. Start the **backend** (`uvicorn`) and **frontend** (`npm run dev`).
2. Open the dashboard in a browser (e.g. `http://localhost:5173`).
3. Verify LLM configuration via `http://localhost:8000/config/status`.

### 3.2 Typical patient workflow

- **Medication adherence**
  - Add HF medications (e.g. furosemide, ACE inhibitor) with time‑of‑day labels such as “after breakfast” or “evening”.
  - The dashboard:
    - Shows upcoming doses.
    - Highlights doses that are currently due.
    - Displays an in‑app **medication reminder banner** at the appropriate time window.

- **Vitals and symptom tracking**
  - Enter:
    - Blood pressure (systolic/diastolic)
    - Heart rate
    - Weight
    - Temperature
  - Optionally add free‑text symptoms (e.g. shortness of breath, swelling).
  - The **triage engine** classifies each reading as *normal*, *warning*, or *critical* and creates alerts for severe abnormalities.

- **Risk score and health status**
  - A logistic regression model trained on the UCI Heart Failure dataset produces a 0–100 risk score.
  - The score is adjusted using the latest vitals via the triage engine and categorized as **low**, **moderate**, or **high**.
  - The **Health Status** panel shows:
    - Current risk tier.
    - A short, personalized daily recommendation grounded in vitals, symptoms, meds, and guideline-based knowledge.

- **Conversational assistant**
  - Use the chat interface to ask about:
    - Medications (interactions, side effects).
    - Symptoms (“Should I worry about this weight gain?”).
    - Lifestyle (sodium, fluids, exercise).
  - The backend:
    - Retrieves relevant clinical content from the **RAG + knowledge layer**.
    - Builds a structured **patient context**.
    - Calls the configured **cloud LLM** to generate grounded, personalized replies.

- **Data export for clinicians**
  - Export the patient’s history as a password‑protected ZIP of CSV files:
    - Vitals, symptoms, medications, adherence logs.
  - Intended for clinician review, research, or import into external tools.

---

## 4. Evaluation (summary)

- **Heart failure risk score**  
  Logistic regression trained on the UCI Heart Failure Clinical Records dataset, evaluated with 80/20 train–test split and standard accuracy on the held‑out test set.

- **Knowledge and reasoning**  
  Heart‑failure knowledge / NCLEX‑style questions evaluated via response accuracy and explanation quality in a small benchmark of HF management questions.


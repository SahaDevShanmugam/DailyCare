DailyCare – Homecare AI for Elderly Chronic Heart Failure
DailyCare is a homecare AI assistant for elderly patients with chronic heart failure. It supports day‑to‑day monitoring and guidance through:

Medication adherence: reminders, logging, and basic safety checks (indications, contraindications, side effects).
Symptom and vitals tracking: daily input of BP, heart rate, weight, temperature with triage for abnormal values.
Lifestyle recommendations: evidence-based advice from a curated heart‑failure knowledge base.
Risk scoring: ML-based heart‑failure risk estimate adjusted by current vitals.
Conversational agent: RAG‑augmented cloud LLM for personalized, context‑aware responses.
1. Installation
1.1 Prerequisites
Python ≥ 3.10 (for the backend)
Node.js ≥ 18 and npm (for the frontend)
Git (optional but recommended)
1.2 Clone the repository
git clone https://github.com/SahaDevShanmugam/DailyCare.git
cd DailyCare
1.3 Backend dependencies
From the project root:

cd backend
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate        # On Windows: .venv\Scripts\activate
# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
Create your backend environment file:

cp .env.example .env
Edit .env to set at least one LLM provider:

Poe (takes precedence if set):
POE_API_KEY – get from poe.com/api_key
POE_MODEL (optional) – e.g. Claude-Sonnet-4, gpt-4o, Gemini-1.5-Pro
OpenAI (used if Poe is not set):
OPENAI_API_KEY
OPENAI_BASE_URL (optional, default https://api.openai.com/v1)
Database (optional):
DATABASE_URL (defaults to sqlite:///./dailycare.db)
1.4 Frontend dependencies
From the project root:

cd frontend
npm install
You can optionally create frontend/.env:

# default is /api, proxied to backend in dev
VITE_API_URL=/api
2. Running the system
2.1 Start the backend (FastAPI)
From backend/ with the virtual environment activated:

uvicorn app.main:app --reload
API base URL: http://localhost:8000
Interactive docs (OpenAPI/Swagger): http://localhost:8000/docs
LLM configuration status: http://localhost:8000/config/status
Returns e.g. {"poe_configured": true} or {"openai_configured": true}.
If the assistant says “DailyCare is not connected”, make sure:

POE_API_KEY or OPENAI_API_KEY is set in backend/.env.
You have restarted the backend after editing .env.
2.2 Start the frontend (React/Vite)
In a separate terminal:

cd frontend
npm run dev
By default Vite will run at http://localhost:5173 (or another port if 5173 is taken; the URL is printed in the terminal).

All calls to /api are proxied to http://localhost:8000 in development.
If your backend runs elsewhere, set VITE_API_URL in frontend/.env.
Open the printed URL in your browser to access the DailyCare dashboard.

3. Example usage
3.1 First‑time setup
Start backend (uvicorn) and frontend (npm run dev).
Open the dashboard in a browser (e.g. http://localhost:5173).
Ensure your LLM key is configured (/config/status shows at least one provider as true).
3.2 Typical patient workflow
Log medications and schedule

Add HF medications (e.g. furosemide, ACE inhibitor) with time‑of‑day labels such as “after breakfast” or “evening”.
The dashboard will:
Show upcoming doses.
Highlight doses that are currently due.
Display an in‑app medication reminder banner at the appropriate time (e.g. morning meds).
Enter vitals and symptoms

On the dashboard, enter:
Blood pressure (systolic/diastolic)
Heart rate
Weight
Temperature
Optionally add free‑text symptoms (e.g. shortness of breath, swelling).
The triage engine classifies each new reading as normal, warning, or critical and creates alerts for severe abnormalities.
View risk score and health status

The heart‑failure risk score (0–100) is computed from:
A logistic regression model trained on the UCI Heart Failure dataset.
Adjustments based on the latest vitals (via the triage engine).
The dashboard shows:
A colored risk circle (low, moderate, high) when vitals exist.
“Unavailable” when no vitals have been logged yet.
The Health Status panel summarizes whether the patient is stable or needs attention and shows a short, personalized daily recommendation.
Ask questions via the conversational agent

Use the chat interface to ask:
Medication questions (e.g. interactions, side effects).
Symptom questions (“Should I be worried about this weight gain?”).
Lifestyle questions (sodium restriction, fluid intake, exercise).
The backend:
Retrieves relevant clinical content from the RAG + knowledge layer (HF guidelines, medication references, etc.).
Builds a structured patient context from vitals, symptoms, medications, logs, and prior chat.
Calls the configured cloud LLM to generate a grounded, personalized reply.
Export data for clinicians

From the dashboard, export the patient’s history:
Vitals, symptoms, medications, adherence logs.
Data is packaged as a password‑protected ZIP of CSV files, suitable for:
Clinician review.
Import into other analysis tools.
Research or documentation.

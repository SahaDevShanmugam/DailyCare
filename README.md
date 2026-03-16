DailyCare – Homecare AI for Elderly Chronic Heart Failure

DailyCare is a homecare AI assistant designed to support elderly patients with chronic heart failure (HF).
It provides daily monitoring, medication adherence support, and personalized guidance through a conversational AI interface.

The system combines machine learning risk prediction, clinical triage rules, and a retrieval-augmented LLM assistant grounded in heart-failure medical guidelines.

Key Features
Medication Adherence

Medication reminders and logging

Safety checks (indications, contraindications, side effects)

Adherence tracking and history

Vitals & Symptom Monitoring

Daily input of:

Blood pressure

Heart rate

Weight

Temperature

Free-text symptom tracking

Automatic triage of abnormal values

Lifestyle Guidance

Evidence-based recommendations

Low-sodium diet suggestions

Fluid management guidance

Lifestyle advice from a curated HF knowledge base

Risk Scoring

ML-based heart-failure risk score

Logistic regression model trained on the UCI Heart Failure dataset

Risk score adjusted using current vital signs

Conversational AI Agent

RAG-augmented cloud LLM

Personalized responses based on patient history

Medication questions

Symptom monitoring advice

Lifestyle recommendations

System Architecture

DailyCare consists of:

Frontend: React + Vite dashboard

Backend: FastAPI service

Database: SQLite (default)

Machine Learning: Scikit-learn logistic regression model

AI Assistant: Cloud LLM via Poe API or OpenAI

Knowledge Layer: Heart failure guidelines and medication references

Installation
Prerequisites

Python ≥ 3.10 (backend)

Node.js ≥ 18 and npm (frontend)

Git (optional but recommended)

Clone the Repository
git clone https://github.com/SahaDevShanmugam/DailyCare.git
cd DailyCare
Backend Setup

Navigate to the backend folder:

cd backend
Create Virtual Environment
python -m venv .venv

Activate it:

Mac/Linux:

source .venv/bin/activate

Windows:

.venv\Scripts\activate
Install Dependencies
pip install --upgrade pip
pip install -r requirements.txt
Backend Environment Variables

Create an environment file:

cp .env.example .env

Edit .env and configure at least one LLM provider.

Poe API (recommended)
POE_API_KEY=your_key_here
POE_MODEL=Claude-Sonnet-4
OpenAI (fallback if Poe is not configured)
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
Database (optional)
DATABASE_URL=sqlite:///./dailycare.db
Frontend Setup

Navigate to the frontend folder:

cd frontend
npm install

Optional environment file:

frontend/.env

VITE_API_URL=/api

This proxies requests to the backend during development.

Running the System
Start the Backend

From backend/ with the virtual environment activated:

uvicorn app.main:app --reload

Backend URLs:

Service	URL
API	http://localhost:8000

Swagger Docs	http://localhost:8000/docs

LLM Config Status	http://localhost:8000/config/status

Example response:

{"poe_configured": true}

If the assistant reports "DailyCare is not connected", ensure:

POE_API_KEY or OPENAI_API_KEY is set

Backend was restarted after editing .env

Start the Frontend

In another terminal:

cd frontend
npm run dev

Default URL:

http://localhost:5173

All /api calls are automatically proxied to the backend.

Example Usage
First-Time Setup

Start the backend (uvicorn)

Start the frontend (npm run dev)

Open the dashboard in your browser

Confirm an LLM provider is configured (/config/status)

Typical Patient Workflow
1. Log Medications

Add heart failure medications such as:

Furosemide

ACE inhibitors

Beta blockers

Features:

Time-of-day labels (morning / evening / night)

Medication reminder banners

Dose confirmation logging

2. Enter Vitals & Symptoms

Patients enter:

Blood pressure

Heart rate

Weight

Temperature

Optional symptom entry:

shortness of breath
leg swelling
fatigue

The triage engine classifies readings as:

Normal

Warning

Critical

Severe abnormalities generate alerts.

3. View Risk Score & Health Status

The system calculates a 0–100 heart failure risk score using:

Logistic regression ML model

Latest vital signs

Triage rule adjustments

The dashboard shows:

Colored risk indicator

Health status summary

Personalized daily recommendations

4. Ask the AI Assistant

Patients can ask questions such as:

“Can I take these medications together?”

“Should I worry about my weight gain?”

“What foods should I avoid with heart failure?”

The backend:

Retrieves medical context from the RAG knowledge base

Builds a structured patient context

Calls the configured cloud LLM

Returns a grounded, personalized response

5. Export Data for Clinicians

Patient data can be exported as:

Password-protected ZIP

Contains CSV files for:

vitals

symptoms

medications

adherence logs

Use cases:

Clinician review

Research analysis

Clinical documentation

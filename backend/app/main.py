from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import init_db
from app.routers import patients, medications, symptoms, vitals, risk_events, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="DailyCare API",
    description="Homecare AI for elderly chronic heart failure: medication adherence, symptom tracking, lifestyle recommendations.",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(patients.router)
app.include_router(medications.router)
app.include_router(symptoms.router)
app.include_router(vitals.router)
app.include_router(risk_events.router)
app.include_router(chat.router)


@app.get("/")
async def root():
    return {
        "name": "DailyCare API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/config/status")
async def config_status():
    """Check if Poe is configured (for debugging). Does not expose keys."""
    s = get_settings()
    return {"poe_configured": bool(s.poe_api_key and s.poe_api_key.strip())}

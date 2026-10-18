"""Run with:  uvicorn app.main:app --reload"""
import os
from pathlib import Path

import psycopg
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.ai.provider import AIError, get_provider
from app.db import get_conn
from app.routers import ai, doctor, logs, medications, parent, patients, slips

PARENT_APP_DIR = Path(__file__).resolve().parent / "static" / "parent"

app = FastAPI(
    title="Clinic assistant API",
    version="0.3.0",
    description="Backend for a pediatric neurology clinic assistant. The bot records and "
    "reminds; only the doctor changes doses. The parent app is served at /app/.",
)

origins = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization", "X-Doctor-Key", "X-Bot-Key"],
)

for router in (patients.router, medications.router, logs.router, doctor.router, slips.router, parent.router,
               ai.parent_router, ai.doctor_router):
    app.include_router(router)


def _ai_banner() -> None:
    """One line in the backend terminal saying whether the AI is on."""
    try:
        p = get_provider()
    except AIError as e:
        print(f"[AI] Not available: {e}", flush=True)
        return
    if p.name == "offline":
        print("[AI] OFF: no GEMINI_API_KEY, using simple rules only.", flush=True)
    else:
        print(f"[AI] ON: {p.name}, model {p.model}, embeddings {p.embed_model}", flush=True)


_ai_banner()


@app.exception_handler(psycopg.errors.IntegrityError)
async def integrity_error(_request, _exc):
    # Do not echo the database message back; it can contain other people's data.
    return JSONResponse(status_code=409, content={"detail": "This conflicts with data that already exists"})


@app.get("/health", tags=["health"])
def health(conn=Depends(get_conn)):
    conn.execute("SELECT 1")
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/app/")


# The parent app: plain HTML, CSS and JavaScript, no build step.
app.mount("/app", StaticFiles(directory=PARENT_APP_DIR, html=True), name="parent-app")

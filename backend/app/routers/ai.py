"""AI endpoints for the parent app, and the doctor's view of prescription photos.

Every AI answer here is a suggestion shown back to a person: the parent confirms a
seizure draft before saving it, sees an approved answer only if it matches, and the
doctor approves medicines read from a photo. See app/ai/__init__.py.
"""
import base64
import binascii
import json
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app import queries as q
from app.ai import faq_match, seizure_text
from app.ai.provider import AIError, get_provider, report_fallback
from app.ai.slip import read_slip
from app.auth import require_doctor
from app.clock import clinic_tz
from app.common import ensure_patient_and_guardian, one_or_404
from app.db import get_conn
from app.parent_auth import require_parent
from app.schemas import QuestionMatchIn, SeizureTextIn, SlipPhotoIn

parent_router = APIRouter(prefix="/parent", tags=["parent app: AI"])
doctor_router = APIRouter(tags=["slips"], dependencies=[Depends(require_doctor)])

EXT = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
MIME = {v: k for k, v in EXT.items()}
SAFE_NAME = re.compile(r"^[0-9a-f]{32}\.(jpg|png|webp)$")
MAX_BYTES = 4 * 1024 * 1024


def upload_dir() -> Path:
    d = Path(os.environ.get("UPLOAD_DIR") or Path(__file__).resolve().parents[2] / "uploads")
    d.mkdir(parents=True, exist_ok=True)
    return d


def _provider():
    try:
        return get_provider()
    except AIError as e:
        raise HTTPException(503, str(e)) from e


def _names(conn, patient_id: UUID, parent: dict) -> list[str]:
    child = conn.execute(q.PATIENT_NAME, {"id": patient_id}).fetchone()
    return [n for n in ((child or {}).get("full_name"), parent.get("full_name")) if n]


# ---------------------------------------------------------------- seizure in the parent's words

@parent_router.post("/children/{patient_id}/ai/seizure-draft")
def seizure_draft(patient_id: UUID, body: SeizureTextIn, parent: dict = Depends(require_parent), conn=Depends(get_conn)):
    """Reads a free-text message into a draft. Nothing is saved: the parent confirms
    the draft in the seizure form, and the red-flag rules run when it is saved."""
    ensure_patient_and_guardian(conn, patient_id, parent["id"])
    now = datetime.now(clinic_tz())
    result = seizure_text.extract(body.text, now, _provider(), _names(conn, patient_id, parent))
    draft = result["draft"]
    if draft["occurred_at"] is not None:
        draft["occurred_at"] = draft["occurred_at"].isoformat()
    return result


# ---------------------------------------------------------------- questions in the parent's words

@parent_router.post("/children/{patient_id}/ai/match-question")
def match_question(patient_id: UUID, body: QuestionMatchIn, parent: dict = Depends(require_parent), conn=Depends(get_conn)):
    """The doctor's approved answer that fits the question, word for word, or null."""
    ensure_patient_and_guardian(conn, patient_id, parent["id"])
    faqs = conn.execute(q.FAQ_FOR_PATIENT, {"patient_id": patient_id}).fetchall()
    found = faq_match.match(conn, faqs, body.question, _provider(), _names(conn, patient_id, parent))
    conn.commit()  # keeps any embeddings computed on the way
    return {"match": found}


# ---------------------------------------------------------------- prescription photos

@parent_router.post("/children/{patient_id}/slips", status_code=201)
def upload_slip(patient_id: UUID, body: SlipPhotoIn, parent: dict = Depends(require_parent), conn=Depends(get_conn)):
    ensure_patient_and_guardian(conn, patient_id, parent["id"])
    try:
        data = base64.b64decode(body.image_base64, validate=True)
    except (binascii.Error, ValueError) as e:
        raise HTTPException(422, "The photo could not be read") from e
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "The photo is too large")
    if not _looks_like(data, body.mime_type):
        raise HTTPException(422, "This file is not a JPEG, PNG or WebP photo")

    name = f"{uuid.uuid4().hex}.{EXT[body.mime_type]}"
    (upload_dir() / name).write_bytes(data)

    reading, note = None, None
    try:
        reading = read_slip(data, body.mime_type, _provider())
    except (AIError, HTTPException) as e:
        note = getattr(e, "detail", None) or str(e)
        report_fallback("prescription photo", e)

    row = conn.execute(q.INSERT_UPLOAD, {
        "patient_id": patient_id, "image_url": f"local:{name}", "guardian_id": parent["id"],
        "extracted_json": json.dumps(reading) if reading is not None else None,
    }).fetchone()
    conn.commit()
    return {
        "id": row["id"], "status": row["status"], "reading": reading,
        # Without AI the photo still reaches the doctor, who reads it directly.
        "note": None if reading is not None else "The photo is saved. The doctor will read it.",
        "ai_error": note,
    }


@parent_router.post("/children/{patient_id}/slips/{upload_id}/confirm")
def confirm_slip(patient_id: UUID, upload_id: UUID, parent: dict = Depends(require_parent), conn=Depends(get_conn)):
    ensure_patient_and_guardian(conn, patient_id, parent["id"])
    upload = conn.execute(q.GET_UPLOAD_FOR_UPDATE, {"id": upload_id}).fetchone()
    if upload is None or upload["patient_id"] != patient_id:
        raise HTTPException(404, "Slip not found")
    if upload["status"] != "pending":
        raise HTTPException(409, f"This slip is already {upload['status']}")
    row = conn.execute(q.SET_UPLOAD_STATUS, {"id": upload_id, "status": "parent_confirmed", "note": None}).fetchone()
    conn.commit()
    return {"id": row["id"], "status": row["status"]}


@parent_router.get("/children/{patient_id}/slips")
def my_slips(patient_id: UUID, parent: dict = Depends(require_parent), conn=Depends(get_conn)):
    ensure_patient_and_guardian(conn, patient_id, parent["id"])
    return conn.execute(q.LIST_UPLOADS_FOR_PARENT, {"patient_id": patient_id}).fetchall()


@doctor_router.get("/patients/{patient_id}/prescription-uploads")
def open_slips(patient_id: UUID, conn=Depends(get_conn)):
    """Slips waiting for the doctor: the AI's reading is a suggestion to check against the photo."""
    one_or_404(conn, q.PATIENT_EXISTS, {"id": patient_id}, "Patient")
    return conn.execute(q.LIST_UPLOADS_OPEN, {"patient_id": patient_id}).fetchall()


@doctor_router.get("/prescription-uploads/{upload_id}/image")
def slip_image(upload_id: UUID, conn=Depends(get_conn)):
    upload = one_or_404(conn, q.GET_UPLOAD, {"id": upload_id}, "Slip")
    url = upload["image_url"] or ""
    name = url.removeprefix("local:")
    if not url.startswith("local:") or not SAFE_NAME.match(name):
        raise HTTPException(404, "No stored photo for this slip")
    path = upload_dir() / name
    if not path.is_file():
        raise HTTPException(404, "Photo file is missing")
    return FileResponse(path, media_type=MIME[name.rsplit(".", 1)[1]], headers={"Cache-Control": "private, no-store"})


def _looks_like(data: bytes, mime: str) -> bool:
    if mime == "image/jpeg":
        return data[:3] == b"\xff\xd8\xff"
    if mime == "image/png":
        return data[:8] == b"\x89PNG\r\n\x1a\n"
    return data[:4] == b"RIFF" and data[8:12] == b"WEBP"

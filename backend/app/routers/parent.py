"""The parent app's API. A parent logs in with a code sent to their phone and can
only see and log things for their own children.
"""
import secrets
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app import queries as q
from app import services
from app.clock import clinic_today, clinic_tz
from app.common import ensure_patient_and_guardian
from app.db import get_conn
from app.parent_auth import (
    MAX_ATTEMPTS_PER_CODE,
    MAX_CODES_PER_HOUR,
    code_hash,
    new_code,
    new_token,
    require_parent,
    send_code,
    sha256,
)
from app.schedule import day_bounds, dose_slots, normalize_phone
from app.schemas import (
    CodeRequestIn,
    CodeVerifyIn,
    ParentDoseIn,
    QuestionIn,
    SeizureFields,
    SideEffectFields,
)

router = APIRouter(prefix="/parent", tags=["parent app"])

GENERIC_SENT = {"sent": True, "message": "If this number is registered with the clinic, a code has been sent."}


# ---------------------------------------------------------------- login

@router.post("/auth/request-code")
def request_code(body: CodeRequestIn, conn=Depends(get_conn)):
    phone = normalize_phone(body.phone)
    if phone is None:
        raise HTTPException(422, "Please enter a valid phone number")
    recent = conn.execute(q.COUNT_RECENT_CODES, {"phone": phone}).fetchone()["n"]
    if recent >= MAX_CODES_PER_HOUR:
        raise HTTPException(429, "Too many codes requested. Please try again in an hour")
    guardian = conn.execute(q.GUARDIAN_BY_PHONE, {"phone": phone}).fetchone()
    if guardian is not None:
        code = new_code()
        conn.execute(q.INSERT_LOGIN_CODE, {"phone": phone, "code_hash": code_hash(phone, code)})
        conn.commit()
        send_code(phone, code)
    # Same answer either way, so nobody can find out which numbers are registered.
    return GENERIC_SENT


@router.post("/auth/verify")
def verify_code(body: CodeVerifyIn, conn=Depends(get_conn)):
    phone = normalize_phone(body.phone)
    if phone is None:
        raise HTTPException(422, "Please enter a valid phone number")
    row = conn.execute(q.LATEST_LOGIN_CODE, {"phone": phone}).fetchone()
    if row is None:
        raise HTTPException(400, "The code is wrong or has expired. Please ask for a new one")
    if row["attempts"] >= MAX_ATTEMPTS_PER_CODE:
        conn.execute(q.USE_LOGIN_CODE, {"id": row["id"]})
        conn.commit()
        raise HTTPException(429, "Too many wrong tries. Please ask for a new code")
    if not secrets.compare_digest(row["code_hash"], code_hash(phone, body.code)):
        conn.execute(q.BUMP_CODE_ATTEMPTS, {"id": row["id"]})
        conn.commit()
        raise HTTPException(400, "The code is wrong or has expired. Please ask for a new one")

    guardian = conn.execute(q.GUARDIAN_BY_PHONE, {"phone": phone}).fetchone()
    conn.execute(q.USE_LOGIN_CODE, {"id": row["id"]})
    if guardian is None:  # removed after the code was sent
        conn.commit()
        raise HTTPException(400, "This number is not registered with the clinic")
    token = new_token()
    conn.execute(q.INSERT_SESSION, {"token_hash": sha256(token), "guardian_id": guardian["id"]})
    conn.commit()
    return {"token": token, "guardian": {"id": guardian["id"], "full_name": guardian["full_name"]}}


@router.post("/auth/logout")
def logout(parent: dict = Depends(require_parent), conn=Depends(get_conn)):
    conn.execute(q.REVOKE_SESSION, {"token_hash": parent["token_hash"]})
    conn.commit()
    return {"logged_out": True}


# ---------------------------------------------------------------- the parent's view

@router.get("/me")
def me(parent: dict = Depends(require_parent), conn=Depends(get_conn)):
    children = conn.execute(q.GUARDIAN_CHILDREN, {"guardian_id": parent["id"]}).fetchall()
    return {"guardian": {"id": parent["id"], "full_name": parent["full_name"]}, "children": children}


def _child(conn, parent: dict, patient_id: UUID) -> None:
    ensure_patient_and_guardian(conn, patient_id, parent["id"])


@router.get("/children/{patient_id}/today")
def today(patient_id: UUID, parent: dict = Depends(require_parent), conn=Depends(get_conn)):
    """Today's doses for each active medicine, with what has been logged so far."""
    _child(conn, parent, patient_id)
    tz = clinic_tz()
    day = clinic_today()
    start, end = day_bounds(day, tz)
    now = datetime.now(tz)
    logs = conn.execute(q.DOSE_LOGS_BETWEEN, {"patient_id": patient_id, "a": start, "b": end}).fetchall()
    logged = {(row["medication_id"], row["scheduled_for"]): row["status"] for row in logs}

    medicines = []
    for med in conn.execute(q.ACTIVE_MEDS_FOR_SCHEDULE, {"patient_id": patient_id}).fetchall():
        if med["started_on"] > day:
            continue
        slots = [
            {"at": slot, "status": logged.get((med["id"], slot)), "due": slot <= now}
            for slot in dose_slots(med["dose_times"], med["times_per_day"], day, tz)
        ]
        medicines.append(
            {
                "id": med["id"],
                "drug_name": med["drug_name"],
                "dose_amount": med["dose_amount"],
                "dose_unit": med["dose_unit"],
                "times_per_day": med["times_per_day"],
                "slots": slots,
            }
        )
    return {"date": day, "medicines": medicines}


@router.post("/children/{patient_id}/doses", status_code=201)
def log_dose(patient_id: UUID, body: ParentDoseIn, parent: dict = Depends(require_parent), conn=Depends(get_conn)):
    _child(conn, parent, patient_id)
    med = conn.execute(q.GET_MEDICATION, {"id": body.medication_id}).fetchone()
    if med is None or med["patient_id"] != patient_id:
        raise HTTPException(404, "Medicine not found")
    if med["status"] != "active":
        raise HTTPException(409, "This medicine is not active")
    row = conn.execute(
        q.UPSERT_ADHERENCE,
        {
            "medication_id": body.medication_id,
            "scheduled_for": body.scheduled_for,
            "status": body.status,
            "guardian_id": parent["id"],
            "note": body.note,
        },
    ).fetchone()
    conn.commit()
    return row


@router.post("/children/{patient_id}/seizures", status_code=201)
def log_seizure(patient_id: UUID, body: SeizureFields, parent: dict = Depends(require_parent), conn=Depends(get_conn)):
    _child(conn, parent, patient_id)
    result = services.log_seizure(conn, patient_id, parent["id"], body)
    conn.commit()
    return result


@router.post("/children/{patient_id}/side-effects", status_code=201)
def log_side_effect(patient_id: UUID, body: SideEffectFields, parent: dict = Depends(require_parent), conn=Depends(get_conn)):
    _child(conn, parent, patient_id)
    effect = services.log_side_effect(conn, patient_id, parent["id"], body)
    conn.commit()
    return effect


@router.get("/children/{patient_id}/faq")
def faq(patient_id: UUID, parent: dict = Depends(require_parent), conn=Depends(get_conn)):
    """Only answers the doctor has approved and published."""
    _child(conn, parent, patient_id)
    return conn.execute(q.FAQ_FOR_PATIENT, {"patient_id": patient_id}).fetchall()


@router.get("/children/{patient_id}/questions")
def my_questions(patient_id: UUID, parent: dict = Depends(require_parent), conn=Depends(get_conn)):
    _child(conn, parent, patient_id)
    return conn.execute(q.LIST_QUESTIONS_FOR_PARENT, {"patient_id": patient_id}).fetchall()


@router.post("/children/{patient_id}/questions", status_code=201)
def ask(patient_id: UUID, body: QuestionIn, parent: dict = Depends(require_parent), conn=Depends(get_conn)):
    _child(conn, parent, patient_id)
    row = conn.execute(
        q.INSERT_QUESTION, {"patient_id": patient_id, "guardian_id": parent["id"], "question": body.question}
    ).fetchone()
    conn.commit()
    return row

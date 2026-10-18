"""Medicines, dose changes and the daily 'dose given / missed' log."""
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app import queries as q
from app import services
from app.auth import require_doctor, require_service
from app.clock import clinic_today
from app.common import audit, ensure_patient_and_guardian, one_or_404
from app.db import get_conn
from app.schemas import AdherenceIn, MedicationChangeIn, MedicationIn

router = APIRouter(tags=["medicines"])


@router.post("/patients/{patient_id}/medications", status_code=201)
def add_medication(
    patient_id: UUID,
    body: MedicationIn,
    actor: str = Depends(require_doctor),
    conn=Depends(get_conn),
):
    one_or_404(conn, q.PATIENT_EXISTS, {"id": patient_id}, "Patient")
    medication = services.create_medication(conn, patient_id, body, source="doctor")
    audit(conn, actor, "create", "medications", medication["id"])
    conn.commit()
    return medication


@router.get("/patients/{patient_id}/medications")
def list_medications(
    patient_id: UUID,
    status: Literal["active", "all"] = "active",
    _actor: str = Depends(require_service),
    conn=Depends(get_conn),
):
    one_or_404(conn, q.PATIENT_EXISTS, {"id": patient_id}, "Patient")
    sql = q.LIST_MEDICATIONS_ACTIVE if status == "active" else q.LIST_MEDICATIONS_ALL
    return conn.execute(sql, {"patient_id": patient_id}).fetchall()


@router.post("/medications/{medication_id}/changes", status_code=201)
def change_medication(
    medication_id: UUID,
    body: MedicationChangeIn,
    actor: str = Depends(require_doctor),
    conn=Depends(get_conn),
):
    """Only the doctor can change a dose. The bot never calls this."""
    med = one_or_404(conn, q.GET_MEDICATION_FOR_UPDATE, {"id": medication_id}, "Medicine")
    if med["status"] == "stopped":
        raise HTTPException(409, "This medicine is stopped. Add it again as a new medicine to restart it.")

    changed_on = body.changed_on or clinic_today()
    if changed_on < med["started_on"] or changed_on > clinic_today():
        raise HTTPException(422, "changed_on must be between the start date and today")

    kind = body.change_type
    new_dose = None
    new_freq = None

    if kind in ("dose_increased", "dose_decreased"):
        higher = kind == "dose_increased"
        if higher and body.new_dose_amount <= med["dose_amount"]:
            raise HTTPException(422, "new_dose_amount must be higher than the current dose")
        if not higher and body.new_dose_amount >= med["dose_amount"]:
            raise HTTPException(422, "new_dose_amount must be lower than the current dose")
        updated = conn.execute(
            q.UPDATE_MEDICATION_DOSE, {"id": medication_id, "dose_amount": body.new_dose_amount}
        ).fetchone()
        new_dose = body.new_dose_amount
    elif kind == "frequency_changed":
        if body.new_times_per_day == med["times_per_day"]:
            raise HTTPException(422, "new_times_per_day is the same as the current value")
        updated = conn.execute(
            q.UPDATE_MEDICATION_FREQUENCY,
            {"id": medication_id, "times_per_day": body.new_times_per_day},
        ).fetchone()
        new_freq = body.new_times_per_day
    elif kind == "paused":
        if med["status"] != "active":
            raise HTTPException(409, "Only an active medicine can be paused")
        updated = conn.execute(
            q.UPDATE_MEDICATION_STATUS,
            {"id": medication_id, "status": "paused", "ended_on": None},
        ).fetchone()
    elif kind == "resumed":
        if med["status"] != "paused":
            raise HTTPException(409, "Only a paused medicine can be resumed")
        updated = conn.execute(
            q.UPDATE_MEDICATION_STATUS,
            {"id": medication_id, "status": "active", "ended_on": None},
        ).fetchone()
    else:  # stopped or switched
        updated = conn.execute(
            q.UPDATE_MEDICATION_STATUS,
            {"id": medication_id, "status": "stopped", "ended_on": changed_on},
        ).fetchone()

    doctor = conn.execute(q.DOCTOR_NAME_FOR_PATIENT, {"patient_id": med["patient_id"]}).fetchone()
    change = conn.execute(
        q.INSERT_CHANGE,
        {
            "medication_id": medication_id,
            "changed_on": changed_on,
            "change_type": kind,
            "old_dose_amount": med["dose_amount"] if new_dose is not None else None,
            "new_dose_amount": new_dose,
            "old_times_per_day": med["times_per_day"] if new_freq is not None else None,
            "new_times_per_day": new_freq,
            "reason": body.reason,
            "changed_by": doctor["full_name"] if doctor else None,
        },
    ).fetchone()
    audit(conn, actor, kind, "medications", medication_id)
    conn.commit()
    return {"medication": updated, "change": change}


@router.post("/medications/{medication_id}/adherence", status_code=201)
def log_dose(
    medication_id: UUID,
    body: AdherenceIn,
    actor: str = Depends(require_service),
    conn=Depends(get_conn),
):
    med = one_or_404(conn, q.GET_MEDICATION, {"id": medication_id}, "Medicine")
    ensure_patient_and_guardian(conn, med["patient_id"], body.guardian_id)
    if med["status"] != "active":
        raise HTTPException(409, "Doses can only be logged for an active medicine")
    log = conn.execute(
        q.UPSERT_ADHERENCE,
        {
            "medication_id": medication_id,
            "scheduled_for": body.scheduled_for,
            "status": body.status,
            "guardian_id": body.guardian_id,
            "note": body.note,
        },
    ).fetchone()
    conn.commit()
    return log

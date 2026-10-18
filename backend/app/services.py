"""Logic used by more than one router."""
from uuid import UUID

from fastapi import HTTPException

from app import queries as q
from app.common import one_or_404
from app.redflags import check_seizure
from app.schemas import MedicationIn, SeizureFields, SideEffectFields


def create_medication(conn, patient_id: UUID, item: MedicationIn, source: str) -> dict:
    """Add a medicine and write its 'started' line in the change history.

    Only call this for entries the doctor has checked (the doctor adds it directly,
    or approves a slip), because it marks the medicine as verified.
    """
    doctor = conn.execute(q.DOCTOR_NAME_FOR_PATIENT, {"patient_id": patient_id}).fetchone()
    doctor_name = doctor["full_name"] if doctor else None
    params = item.model_dump()
    params.update(
        patient_id=patient_id,
        source=source,
        prescribed_by=item.prescribed_by or doctor_name,
    )
    medication = conn.execute(q.INSERT_MEDICATION, params).fetchone()
    conn.execute(
        q.INSERT_CHANGE,
        {
            "medication_id": medication["id"],
            "changed_on": item.started_on,
            "change_type": "started",
            "old_dose_amount": None,
            "new_dose_amount": item.dose_amount,
            "old_times_per_day": None,
            "new_times_per_day": item.times_per_day,
            "reason": item.reason,
            "changed_by": doctor_name,
        },
    )
    return medication


def log_seizure(conn, patient_id: UUID, guardian_id: UUID, body: SeizureFields) -> dict:
    """Save a seizure and apply the doctor's red-flag rules to it. Caller commits."""
    params = body.model_dump(exclude={"guardian_id"})
    params.update(patient_id=patient_id, guardian_id=guardian_id)
    seizure = conn.execute(q.INSERT_SEIZURE, params).fetchone()
    red_flags = check_seizure(conn, patient_id, seizure)
    return {"seizure": seizure, "red_flags": red_flags, "emergency_advice": bool(red_flags)}


def log_side_effect(conn, patient_id: UUID, guardian_id: UUID, body: SideEffectFields) -> dict:
    """Save a side effect after checking the medicine belongs to this child. Caller commits."""
    if body.medication_id is not None:
        med = one_or_404(conn, q.GET_MEDICATION, {"id": body.medication_id}, "Medicine")
        if med["patient_id"] != patient_id:
            raise HTTPException(422, "That medicine belongs to a different patient")
    params = body.model_dump(exclude={"guardian_id"})
    params.update(patient_id=patient_id, guardian_id=guardian_id)
    return conn.execute(q.INSERT_SIDE_EFFECT, params).fetchone()

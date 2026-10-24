"""Doctors, patients and guardians. Doctor key only."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app import queries as q
from app.schedule import normalize_phone
from app.auth import require_doctor
from app.clock import clinic_today
from app.common import audit, one_or_404
from app.db import get_conn
from app.redflags import DEFAULT_RULE, condition_json
from app.schemas import DoctorIn, GuardianIn, PatientIn

router = APIRouter(tags=["patients"], dependencies=[Depends(require_doctor)])


@router.post("/doctors", status_code=201)
def create_doctor(body: DoctorIn, conn=Depends(get_conn)):
    doctor = conn.execute(q.INSERT_DOCTOR, body.model_dump()).fetchone()
    conn.execute(
        q.INSERT_RULE,
        {
            "doctor_id": doctor["id"],
            "name": DEFAULT_RULE["name"],
            "condition": condition_json(DEFAULT_RULE["condition"]),
            "message_ur": DEFAULT_RULE["message_ur"],
            "message_en": DEFAULT_RULE["message_en"],
        },
    )
    audit(conn, "doctor", "create", "doctors", doctor["id"])
    conn.commit()
    return doctor


@router.get("/doctors")
def list_doctors(conn=Depends(get_conn)):
    return conn.execute(q.LIST_DOCTORS).fetchall()


@router.post("/patients", status_code=201)
def create_patient(body: PatientIn, conn=Depends(get_conn)):
    one_or_404(conn, q.DOCTOR_EXISTS, {"id": body.doctor_id}, "Doctor")
    params = body.model_dump()
    params["weight_updated_on"] = clinic_today() if body.weight_kg is not None else None
    patient = conn.execute(q.INSERT_PATIENT, params).fetchone()
    audit(conn, "doctor", "create", "patients", patient["id"])
    conn.commit()
    return patient


@router.get("/patients")
def list_patients(doctor_id: UUID | None = None, conn=Depends(get_conn)):
    if doctor_id is None:
        return conn.execute(q.LIST_PATIENTS).fetchall()
    return conn.execute(q.LIST_PATIENTS_BY_DOCTOR, {"doctor_id": doctor_id}).fetchall()


@router.get("/patients/{patient_id}")
def get_patient(patient_id: UUID, conn=Depends(get_conn)):
    return one_or_404(conn, q.GET_PATIENT, {"id": patient_id}, "Patient")


@router.post("/patients/{patient_id}/guardians", status_code=201)
def add_guardian(patient_id: UUID, body: GuardianIn, conn=Depends(get_conn)):
    one_or_404(conn, q.PATIENT_EXISTS, {"id": patient_id}, "Patient")
    # Stored as digits only (923001234567) so the parent app finds it at login.
    phone = normalize_phone(body.phone)
    if phone is None:
        raise HTTPException(422, "Please enter a valid phone number")
    guardian = conn.execute(
        q.UPSERT_GUARDIAN,
        {"full_name": body.full_name, "phone": phone, "relation": body.relation},
    ).fetchone()
    link = {
        "patient_id": patient_id,
        "guardian_id": guardian["id"],
        "is_primary": body.is_primary,
    }
    conn.execute(q.LINK_GUARDIAN, link)
    if body.is_primary:
        conn.execute(q.CLEAR_OTHER_PRIMARY, link)
    audit(conn, "doctor", "link_guardian", "patient_guardians", guardian["id"])
    conn.commit()
    return guardian

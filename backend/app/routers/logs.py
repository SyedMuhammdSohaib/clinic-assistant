"""Things a parent logs: seizures, drips, hospital visits, side effects.

Everything a parent logs starts as 'not verified' until the doctor checks it.
"""
from uuid import UUID

from fastapi import APIRouter, Depends

from app import queries as q
from app import notifications, services
from app.auth import require_doctor, require_service
from app.common import audit, ensure_patient_and_guardian, one_or_404
from app.db import get_conn
from app.schemas import AllergyIn, HospitalVisitIn, IVInfusionIn, SeizureIn, SideEffectIn

router = APIRouter(tags=["logs"])


@router.post("/patients/{patient_id}/seizures", status_code=201)
def log_seizure(
    patient_id: UUID,
    body: SeizureIn,
    actor: str = Depends(require_service),
    conn=Depends(get_conn),
):
    ensure_patient_and_guardian(conn, patient_id, body.guardian_id)
    result = services.log_seizure(conn, patient_id, body.guardian_id, body)
    conn.commit()
    notifications.alert_doctor(conn, patient_id, result["red_flags"])
    return result


@router.post("/patients/{patient_id}/iv-infusions", status_code=201)
def log_iv(
    patient_id: UUID,
    body: IVInfusionIn,
    actor: str = Depends(require_service),
    conn=Depends(get_conn),
):
    ensure_patient_and_guardian(conn, patient_id, body.guardian_id)
    params = body.model_dump()
    params["patient_id"] = patient_id
    infusion = conn.execute(q.INSERT_IV, params).fetchone()
    conn.commit()
    return infusion


@router.post("/patients/{patient_id}/hospital-visits", status_code=201)
def log_visit(
    patient_id: UUID,
    body: HospitalVisitIn,
    actor: str = Depends(require_service),
    conn=Depends(get_conn),
):
    ensure_patient_and_guardian(conn, patient_id, body.guardian_id)
    params = body.model_dump()
    params["patient_id"] = patient_id
    visit = conn.execute(q.INSERT_VISIT, params).fetchone()
    conn.commit()
    return visit


@router.post("/patients/{patient_id}/side-effects", status_code=201)
def log_side_effect(
    patient_id: UUID,
    body: SideEffectIn,
    actor: str = Depends(require_service),
    conn=Depends(get_conn),
):
    ensure_patient_and_guardian(conn, patient_id, body.guardian_id)
    effect = services.log_side_effect(conn, patient_id, body.guardian_id, body)
    conn.commit()
    return effect


@router.post("/patients/{patient_id}/allergies", status_code=201)
def add_allergy(
    patient_id: UUID,
    body: AllergyIn,
    actor: str = Depends(require_doctor),
    conn=Depends(get_conn),
):
    one_or_404(conn, q.PATIENT_EXISTS, {"id": patient_id}, "Patient")
    params = body.model_dump()
    params["patient_id"] = patient_id
    allergy = conn.execute(q.INSERT_ALLERGY, params).fetchone()
    audit(conn, actor, "create", "allergies", allergy["id"])
    conn.commit()
    return allergy

"""Prescription and discharge slips.

Flow: the parent sends a photo (the bot stores what it read from it), the parent
confirms the reading, and the doctor approves or rejects. Nothing reaches the
medicine list until the doctor approves.
"""
import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app import queries as q
from app import services
from app.auth import require_doctor, require_service
from app.common import audit, ensure_patient_and_guardian, one_or_404
from app.db import get_conn
from app.schemas import UploadApproveIn, UploadConfirmIn, UploadIn, UploadRejectIn

router = APIRouter(tags=["slips"])


@router.post("/patients/{patient_id}/prescription-uploads", status_code=201)
def create_upload(
    patient_id: UUID,
    body: UploadIn,
    actor: str = Depends(require_service),
    conn=Depends(get_conn),
):
    ensure_patient_and_guardian(conn, patient_id, body.guardian_id)
    upload = conn.execute(
        q.INSERT_UPLOAD,
        {
            "patient_id": patient_id,
            "image_url": body.image_url,
            "guardian_id": body.guardian_id,
            "extracted_json": json.dumps(body.extracted_json) if body.extracted_json is not None else None,
        },
    ).fetchone()
    conn.commit()
    return upload


@router.post("/prescription-uploads/{upload_id}/confirm")
def confirm_upload(
    upload_id: UUID,
    body: UploadConfirmIn,
    actor: str = Depends(require_service),
    conn=Depends(get_conn),
):
    upload = one_or_404(conn, q.GET_UPLOAD_FOR_UPDATE, {"id": upload_id}, "Slip")
    ensure_patient_and_guardian(conn, upload["patient_id"], body.guardian_id)
    if upload["status"] != "pending":
        raise HTTPException(409, f"This slip is already {upload['status']}")
    updated = conn.execute(
        q.SET_UPLOAD_STATUS, {"id": upload_id, "status": "parent_confirmed", "note": None}
    ).fetchone()
    conn.commit()
    return updated


@router.post("/prescription-uploads/{upload_id}/approve")
def approve_upload(
    upload_id: UUID,
    body: UploadApproveIn,
    actor: str = Depends(require_doctor),
    conn=Depends(get_conn),
):
    upload = one_or_404(conn, q.GET_UPLOAD_FOR_UPDATE, {"id": upload_id}, "Slip")
    if upload["status"] not in ("pending", "parent_confirmed"):
        raise HTTPException(409, f"This slip is already {upload['status']}")
    created = [
        services.create_medication(conn, upload["patient_id"], item, source="prescription_photo")
        for item in body.items
    ]
    updated = conn.execute(
        q.SET_UPLOAD_STATUS,
        {"id": upload_id, "status": "doctor_verified", "note": body.reviewer_note},
    ).fetchone()
    audit(conn, actor, "approve", "prescription_uploads", upload_id)
    conn.commit()
    return {"upload": updated, "medications_created": created}


@router.post("/prescription-uploads/{upload_id}/reject")
def reject_upload(
    upload_id: UUID,
    body: UploadRejectIn,
    actor: str = Depends(require_doctor),
    conn=Depends(get_conn),
):
    upload = one_or_404(conn, q.GET_UPLOAD_FOR_UPDATE, {"id": upload_id}, "Slip")
    if upload["status"] not in ("pending", "parent_confirmed"):
        raise HTTPException(409, f"This slip is already {upload['status']}")
    updated = conn.execute(
        q.SET_UPLOAD_STATUS,
        {"id": upload_id, "status": "rejected", "note": body.reviewer_note},
    ).fetchone()
    audit(conn, actor, "reject", "prescription_uploads", upload_id)
    conn.commit()
    return updated

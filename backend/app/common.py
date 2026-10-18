"""Small helpers shared by the routers."""
from uuid import UUID

from fastapi import HTTPException

from app import queries as q


def one_or_404(conn, sql: str, params: dict, what: str) -> dict:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        raise HTTPException(404, f"{what} not found")
    return row


def ensure_patient_and_guardian(conn, patient_id: UUID, guardian_id: UUID) -> None:
    one_or_404(conn, q.PATIENT_EXISTS, {"id": patient_id}, "Patient")
    link = conn.execute(
        q.IS_GUARDIAN_OF, {"patient_id": patient_id, "guardian_id": guardian_id}
    ).fetchone()
    if link is None:
        raise HTTPException(403, "This guardian is not linked to this patient")


def audit(conn, actor: str, action: str, table_name: str, row_id: UUID | None) -> None:
    conn.execute(
        q.INSERT_AUDIT,
        {"actor": actor, "action": action, "table_name": table_name, "row_id": row_id},
    )

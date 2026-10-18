"""What the doctor dashboard reads and acts on. Doctor key only."""
from datetime import date, datetime, time, timedelta
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app import queries as q
from app.auth import require_doctor
from app.clock import clinic_tz
from app.common import audit, one_or_404
from app.db import get_conn
from app.redflags import condition_json
from app.schemas import AnswerIn, RuleIn

router = APIRouter(tags=["doctor"], dependencies=[Depends(require_doctor)])

# The timeline names events one way; the verify route names them another.
VERIFY_KIND = {
    "seizure": "seizures",
    "medicine_change": "medication-changes",
    "iv_drip": "iv-infusions",
    "hospital_visit": "hospital-visits",
}


@router.get("/patients/{patient_id}/timeline")
def timeline(
    patient_id: UUID,
    limit: int = Query(default=50, ge=1, le=200),
    before: datetime | None = None,
    conn=Depends(get_conn),
):
    """Seizures, medicine changes, drips and hospital visits, newest first.

    Each row has row_id and verify_kind so the dashboard can call
    POST /verify/{verify_kind}/{row_id}. To load more, pass the last
    happened_at you received as `before`.
    """
    one_or_404(conn, q.PATIENT_EXISTS, {"id": patient_id}, "Patient")
    params = {"patient_id": patient_id, "limit": limit}
    if before is None:
        rows = conn.execute(q.TIMELINE, params).fetchall()
    else:
        params["before"] = before
        rows = conn.execute(q.TIMELINE_BEFORE, params).fetchall()
    for row in rows:
        row["verify_kind"] = VERIFY_KIND[row["event_type"]]
    return rows


@router.post("/verify/{kind}/{row_id}")
def verify(
    kind: Literal[
        "seizures", "medications", "medication-changes", "iv-infusions",
        "hospital-visits", "side-effects", "allergies",
    ],
    row_id: UUID,
    conn=Depends(get_conn),
):
    row = one_or_404(conn, q.VERIFY[kind], {"id": row_id}, "Entry")
    audit(conn, "doctor", "verify", kind, row_id)
    conn.commit()
    return {"id": row["id"], "verified_by_doctor": True}


@router.get("/patients/{patient_id}/red-flags")
def list_red_flags(patient_id: UUID, unseen_only: bool = True, conn=Depends(get_conn)):
    one_or_404(conn, q.PATIENT_EXISTS, {"id": patient_id}, "Patient")
    sql = q.LIST_RED_FLAGS_UNSEEN if unseen_only else q.LIST_RED_FLAGS_ALL
    return conn.execute(sql, {"patient_id": patient_id}).fetchall()


@router.post("/red-flag-events/{event_id}/seen")
def mark_seen(event_id: UUID, conn=Depends(get_conn)):
    event = one_or_404(conn, q.MARK_RED_FLAG_SEEN, {"id": event_id}, "Red-flag event")
    audit(conn, "doctor", "seen", "red_flag_events", event_id)
    conn.commit()
    return event


@router.post("/doctors/{doctor_id}/red-flag-rules", status_code=201)
def add_rule(doctor_id: UUID, body: RuleIn, conn=Depends(get_conn)):
    one_or_404(conn, q.DOCTOR_EXISTS, {"id": doctor_id}, "Doctor")
    rule = conn.execute(
        q.INSERT_RULE,
        {
            "doctor_id": doctor_id,
            "name": body.name,
            "condition": condition_json(body.condition.model_dump()),
            "message_ur": body.message_ur,
            "message_en": body.message_en,
        },
    ).fetchone()
    audit(conn, "doctor", "create", "red_flag_rules", rule["id"])
    conn.commit()
    return rule


@router.get("/patients/{patient_id}/questions")
def list_questions(patient_id: UUID, open_only: bool = True, conn=Depends(get_conn)):
    """Questions parents asked that the approved answers did not cover."""
    one_or_404(conn, q.PATIENT_EXISTS, {"id": patient_id}, "Patient")
    sql = q.LIST_QUESTIONS_OPEN if open_only else q.LIST_QUESTIONS_ALL
    return conn.execute(sql, {"patient_id": patient_id}).fetchall()


@router.post("/questions/{question_id}/answer")
def answer_question(question_id: UUID, body: AnswerIn, conn=Depends(get_conn)):
    """The doctor's own reply. The parent sees it in the app."""
    row = one_or_404(conn, q.ANSWER_QUESTION, {"id": question_id, "answer": body.answer}, "Question")
    audit(conn, "doctor", "answer", "parent_questions", question_id)
    conn.commit()
    return row


def _window(since: date | None) -> tuple[datetime, datetime]:
    tz = clinic_tz()
    until = datetime.now(tz)
    start = datetime.combine(since, time.min, tzinfo=tz) if since else until - timedelta(days=28)
    if start >= until:
        raise HTTPException(422, "since must be a date in the past")
    return start, until


@router.get("/patients/{patient_id}/previsit")
def previsit(patient_id: UUID, since: date | None = None, conn=Depends(get_conn)):
    """Everything the one-page pre-visit summary needs, as data.

    `since` is the date of the last visit; it defaults to 28 days ago. Writing the
    summary as readable text is a separate step (an LLM can do it from this JSON).
    """
    patient = one_or_404(
        conn,
        "SELECT id, full_name, date_of_birth, weight_kg FROM patients WHERE id = %(id)s",
        {"id": patient_id},
        "Patient",
    )
    start, until = _window(since)
    previous_start = start - (until - start)
    base = {"patient_id": patient_id}
    window = {**base, "a": start, "b": until, "a_date": start.date(), "b_date": until.date()}

    seizures = conn.execute(q.SEIZURE_STATS, window).fetchone()
    previous = conn.execute(q.SEIZURE_STATS, {**base, "a": previous_start, "b": start}).fetchone()
    unverified = conn.execute(q.UNVERIFIED_COUNT, base).fetchone()

    return {
        "patient": patient,
        "period": {"from": start, "to": until},
        "seizures": {**seizures, "previous_period_total": previous["total"]},
        "red_flags": conn.execute(q.RED_FLAGS_IN_PERIOD, window).fetchall(),
        "medicines_now": conn.execute(q.LIST_MEDICATIONS_ACTIVE, base).fetchall(),
        "medicine_changes": conn.execute(q.CHANGES_IN_PERIOD, window).fetchall(),
        "adherence": conn.execute(q.ADHERENCE_IN_PERIOD, window).fetchall(),
        "iv_infusions": conn.execute(q.IV_IN_PERIOD, window).fetchall(),
        "hospital_visits": conn.execute(q.VISITS_IN_PERIOD, window).fetchall(),
        "side_effects": conn.execute(q.SIDE_EFFECTS_IN_PERIOD, window).fetchall(),
        "allergies": conn.execute(q.LIST_ALLERGIES, base).fetchall(),
        "unverified_entries": unverified["n"],
    }

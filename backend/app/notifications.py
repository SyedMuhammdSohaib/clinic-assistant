"""SMS notices: red flags to the doctor, answered questions to the parent.

They go out in the background after the change is saved (app/sms.py), so a slow or
switched-off phone never holds up or breaks the request.
"""
import os
from uuid import UUID

from app import queries as q
from app.schedule import normalize_phone
from app.sms import notify

ANSWERED = {
    "ur": "ڈاکٹر نے آپ کے سوال کا جواب دے دیا ہے۔ کلینک ایپ کھول کر دیکھیں۔",
    "roman_ur": "Doctor ne aap ke sawal ka jawab de diya hai. Clinic app khol kar dekhein.",
    "en": "The doctor has answered your question. Open the clinic app to read it.",
}


def _doctor_phone(stored: str | None) -> str | None:
    """The doctor's own number, or DOCTOR_ALERT_PHONE when the doctor has none saved."""
    return normalize_phone(stored or os.environ.get("DOCTOR_ALERT_PHONE", ""))


def alert_doctor(conn, patient_id: UUID, red_flags: list[dict]) -> None:
    """Text the doctor once for each red flag a newly logged seizure raised."""
    if not red_flags:
        return
    row = conn.execute(q.PATIENT_AND_DOCTOR_PHONE, {"patient_id": patient_id}).fetchone()
    phone = _doctor_phone(row["doctor_phone"]) if row else None
    if phone is None:
        return
    short_id = str(row["id"])[:8].upper()
    for flag in red_flags:
        notify(phone, f"RED FLAG: {row['full_name']} (ID {short_id}). {flag['rule_name']}. Please check the clinic dashboard.")


def tell_parent_answered(conn, question_id: UUID) -> None:
    """Text the parent who asked that the doctor has answered."""
    row = conn.execute(q.QUESTION_ASKER, {"question_id": question_id}).fetchone()
    if row is None or not row["phone"]:
        return
    text = ANSWERED.get(row["preferred_language"], ANSWERED["en"])
    app_url = os.environ.get("PARENT_APP_URL", "").strip()
    notify(row["phone"], f"{text} {app_url}".strip())

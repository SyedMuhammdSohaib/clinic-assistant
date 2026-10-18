"""Red-flag rules. The doctor writes the rules; the code only applies them.

A rule's condition is stored as JSON in red_flag_rules.condition_json. Two kinds:

  threshold  {"kind": "threshold", "event": "seizure", "field": "duration_seconds",
              "op": ">=", "value": 300}
  cluster    {"kind": "cluster", "event": "seizure", "count_gte": 3, "within_hours": 24}

A threshold rule never fires when the field is missing (for example the parent did not
know how long the seizure lasted). The chat layer should ask for the duration instead.
"""
import json

from app import queries as q

# Every new doctor gets this one rule so the safety net is never empty. The name says
# "please confirm" on purpose: the doctor decides the real threshold.
DEFAULT_RULE = {
    "name": "Seizure of 5 minutes or longer (default, please confirm)",
    "condition": {
        "kind": "threshold",
        "event": "seizure",
        "field": "duration_seconds",
        "op": ">=",
        "value": 300,
    },
    "message_en": (
        "This seizure lasted 5 minutes or longer. "
        "Please take the child to the nearest emergency room now."
    ),
    "message_ur": (
        "یہ دورہ 5 منٹ یا اس سے زیادہ چلا۔ "
        "براہ مہربانی بچے کو ابھی قریبی ایمرجنسی میں لے جائیں۔"
    ),
}


def condition_hit(condition: dict, seizure: dict, count_in_window: int | None = None) -> bool:
    """Does this seizure trigger this rule? Pure function, no database."""
    if condition.get("event") != "seizure":
        return False
    kind = condition.get("kind")
    if kind == "threshold":
        actual = seizure.get(condition["field"])
        if actual is None:
            return False
        if condition["op"] == ">=":
            return actual >= condition["value"]
        return actual > condition["value"]
    if kind == "cluster":
        return count_in_window is not None and count_in_window >= condition["count_gte"]
    return False


def check_seizure(conn, patient_id, seizure: dict) -> list[dict]:
    """Apply every active rule of the patient's doctor to a freshly saved seizure.

    Call this after the seizure row is inserted (in the same transaction) so a
    cluster rule counts the new seizure too. Returns what the parent should be told.
    """
    rules = conn.execute(q.RULES_FOR_PATIENT, {"patient_id": patient_id}).fetchall()
    hits = []
    for rule in rules:
        condition = rule["condition_json"]
        count = None
        if condition.get("kind") == "cluster":
            row = conn.execute(
                q.COUNT_SEIZURES_WINDOW,
                {
                    "patient_id": patient_id,
                    "at": seizure["occurred_at"],
                    "hours": condition["within_hours"],
                },
            ).fetchone()
            count = row["n"]
        if not condition_hit(condition, seizure, count):
            continue
        duration = seizure.get("duration_seconds")
        trigger_text = seizure.get("description") or (
            f"Seizure of {duration} seconds" if duration is not None else "Seizure"
        )
        event = conn.execute(
            q.INSERT_RED_FLAG_EVENT,
            {"patient_id": patient_id, "rule_id": rule["id"], "trigger_text": trigger_text},
        ).fetchone()
        hits.append(
            {
                "event_id": event["id"],
                "rule_name": rule["name"],
                "message_ur": rule["message_ur"],
                "message_en": rule["message_en"],
            }
        )
    return hits


def condition_json(condition: dict) -> str:
    return json.dumps(condition)

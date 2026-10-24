"""End-to-end tests against a real PostgreSQL database (see conftest.py)."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest

DOC = {"X-Doctor-Key": "test-doctor-key"}
BOT = {"X-Bot-Key": "test-bot-key"}

LEVETIRACETAM = {
    "drug_name": "Levetiracetam", "dose_amount": "5", "dose_unit": "ml",
    "times_per_day": 2, "started_on": "2026-06-03", "reason": "seizures",
}


def ago(**kwargs) -> str:
    return (datetime.now(timezone.utc) - timedelta(**kwargs)).isoformat()


def ok(response, status=200):
    assert response.status_code == status, f"{response.status_code}: {response.text}"
    return response.json()


@pytest.fixture
def world(client):
    doctor = ok(client.post("/doctors", json={"full_name": "Dr Test", "email": "dr@example.com"}, headers=DOC), 201)
    patient = ok(client.post("/patients", json={
        "doctor_id": doctor["id"], "full_name": "Sample Child",
        "date_of_birth": "2020-05-01", "weight_kg": "21",
    }, headers=DOC), 201)
    guardian = ok(client.post(f"/patients/{patient['id']}/guardians", json={
        "full_name": "Sample Mother", "phone": "923001234567", "is_primary": True,
    }, headers=DOC), 201)
    return {"doctor": doctor, "patient": patient, "guardian": guardian,
            "pid": patient["id"], "gid": guardian["id"]}


@pytest.fixture
def med(client, world):
    return ok(client.post(f"/patients/{world['pid']}/medications", json=LEVETIRACETAM, headers=DOC), 201)


def seizure(client, world, **overrides):
    body = {"guardian_id": world["gid"], "occurred_at": ago(hours=1), "duration_seconds": 60}
    body.update(overrides)
    return client.post(f"/patients/{world['pid']}/seizures", json=body, headers=BOT)


# ---------------------------------------------------------------- basics and access

def test_health_and_openapi(client):
    assert ok(client.get("/health")) == {"status": "ok"}
    assert ok(client.get("/openapi.json"))["info"]["title"] == "Clinic assistant API"


def test_keys_are_required_and_roles_are_separated(client, world):
    pid = world["pid"]
    assert client.get("/patients").status_code == 401
    assert client.get("/patients", headers={"X-Doctor-Key": "wrong"}).status_code == 401
    assert client.get("/patients", headers=BOT).status_code == 401            # bot cannot list patients
    assert client.get(f"/patients/{pid}", headers=BOT).status_code == 401     # nor read doctor notes
    assert client.post(f"/patients/{pid}/medications", json=LEVETIRACETAM, headers=BOT).status_code == 401
    assert client.get(f"/patients/{pid}/medications", headers=BOT).status_code == 200  # bot may read for reminders
    assert client.get(f"/patients/{pid}/medications", headers=DOC).status_code == 200  # doctor key works everywhere


def test_doctors_are_listed_for_the_doctor_key_only(client, world):
    doctors = ok(client.get("/doctors", headers=DOC))
    assert [d["id"] for d in doctors] == [world["doctor"]["id"]]
    assert set(doctors[0]) == {"id", "full_name", "email", "clinic_name"}
    assert client.get("/doctors", headers=BOT).status_code == 401


def test_duplicate_doctor_email_is_a_conflict(client, world):
    response = client.post("/doctors", json={"full_name": "Other", "email": "dr@example.com"}, headers=DOC)
    assert response.status_code == 409


def test_patient_checks(client, world):
    base = {"doctor_id": world["doctor"]["id"], "full_name": "X", "date_of_birth": "2020-01-01"}
    assert client.post("/patients", json={**base, "date_of_birth": "2999-01-01"}, headers=DOC).status_code == 422
    assert client.post("/patients", json={**base, "doctor_notes": "nope"}, headers=DOC).status_code == 422
    assert client.post("/patients", json={**base, "doctor_id": str(uuid.uuid4())}, headers=DOC).status_code == 404
    listed = ok(client.get("/patients", headers=DOC))
    assert [p["full_name"] for p in listed] == ["Sample Child"]
    assert listed[0]["unseen_red_flags"] == 0


def test_guardian_phone_is_reused_and_primary_moves(client, world):
    pid = world["pid"]
    again = ok(client.post(f"/patients/{pid}/guardians", json={
        "full_name": "Different Name", "phone": "923001234567"}, headers=DOC), 201)
    assert again["id"] == world["gid"]
    second = ok(client.post(f"/patients/{pid}/guardians", json={
        "full_name": "Sample Father", "phone": "923007654321", "is_primary": True}, headers=DOC), 201)
    assert second["id"] != world["gid"]


# ---------------------------------------------------------------- medicines

def test_medicine_lifecycle(client, world, med):
    pid, mid = world["pid"], med["id"]
    assert med["verified_by_doctor"] is True
    assert med["prescribed_by"] == "Dr Test"
    assert med["source"] == "doctor"

    active = ok(client.get(f"/patients/{pid}/medications", headers=BOT))
    assert [m["drug_name"] for m in active] == ["Levetiracetam"]

    up = ok(client.post(f"/medications/{mid}/changes", json={
        "change_type": "dose_increased", "new_dose_amount": "7", "reason": "more seizures"}, headers=DOC), 201)
    assert float(up["medication"]["dose_amount"]) == 7
    assert float(up["change"]["old_dose_amount"]) == 5 and float(up["change"]["new_dose_amount"]) == 7

    # A "decrease" that is really an increase, and an "increase" that is really a decrease, are refused.
    for kind, value in (("dose_increased", "6"), ("dose_decreased", "9")):
        r = client.post(f"/medications/{mid}/changes", json={"change_type": kind, "new_dose_amount": value}, headers=DOC)
        assert r.status_code == 422

    freq = ok(client.post(f"/medications/{mid}/changes", json={
        "change_type": "frequency_changed", "new_times_per_day": 3}, headers=DOC), 201)
    assert freq["medication"]["times_per_day"] == 3 and freq["medication"]["dose_times"] is None

    paused = ok(client.post(f"/medications/{mid}/changes", json={"change_type": "paused"}, headers=DOC), 201)
    assert paused["medication"]["status"] == "paused"
    blocked = client.post(f"/medications/{mid}/adherence", headers=BOT, json={
        "guardian_id": world["gid"], "scheduled_for": ago(hours=2), "status": "taken"})
    assert blocked.status_code == 409
    assert client.post(f"/medications/{mid}/changes", json={"change_type": "paused"}, headers=DOC).status_code == 409

    resumed = ok(client.post(f"/medications/{mid}/changes", json={"change_type": "resumed"}, headers=DOC), 201)
    assert resumed["medication"]["status"] == "active"

    stopped = ok(client.post(f"/medications/{mid}/changes", json={"change_type": "stopped"}, headers=DOC), 201)
    assert stopped["medication"]["status"] == "stopped" and stopped["medication"]["ended_on"]
    assert client.post(f"/medications/{mid}/changes", json={"change_type": "resumed"}, headers=DOC).status_code == 409

    assert ok(client.get(f"/patients/{pid}/medications", headers=BOT)) == []
    assert len(ok(client.get(f"/patients/{pid}/medications?status=all", headers=BOT))) == 1


def test_changes_cannot_be_dated_before_the_start(client, world, med):
    r = client.post(f"/medications/{med['id']}/changes", headers=DOC, json={
        "change_type": "dose_increased", "new_dose_amount": "7", "changed_on": "2026-01-01"})
    assert r.status_code == 422


def test_dose_log_updates_the_same_slot_and_feeds_the_adherence_numbers(client, world, med):
    mid = med["id"]
    slot_a, slot_b = ago(hours=30), ago(hours=18)

    def log(slot, status, **extra):
        return client.post(f"/medications/{mid}/adherence", headers=BOT, json={
            "guardian_id": world["gid"], "scheduled_for": slot, "status": status, **extra})

    first = ok(log(slot_a, "taken"), 201)
    corrected = ok(log(slot_a, "missed", note="actually she refused"), 201)
    assert corrected["id"] == first["id"] and corrected["status"] == "missed"

    row = ok(client.get(f"/patients/{world['pid']}/medications", headers=BOT))[0]
    assert (row["doses_given"], row["doses_missed"], float(row["adherence_pct"])) == (0, 1, 0.0)

    ok(log(slot_b, "late"), 201)
    row = ok(client.get(f"/patients/{world['pid']}/medications", headers=BOT))[0]
    assert (row["doses_given"], row["doses_missed"], float(row["adherence_pct"])) == (1, 1, 50.0)

    assert log("2026-10-12T08:00:00", "taken").status_code == 422          # no timezone
    other = ok(client.post("/patients", headers=DOC, json={
        "doctor_id": world["doctor"]["id"], "full_name": "Other", "date_of_birth": "2019-01-01"}), 201)
    stranger = ok(client.post(f"/patients/{other['id']}/guardians", headers=DOC, json={
        "full_name": "Stranger", "phone": "923111111111"}), 201)
    assert client.post(f"/medications/{mid}/adherence", headers=BOT, json={
        "guardian_id": stranger["id"], "scheduled_for": ago(hours=1), "status": "taken"}).status_code == 403


# ---------------------------------------------------------------- seizures and red flags

def test_long_seizure_triggers_the_default_red_flag(client, world):
    short = ok(seizure(client, world, duration_seconds=120), 201)
    assert short["emergency_advice"] is False and short["red_flags"] == []
    assert ok(seizure(client, world, duration_seconds=None), 201)["emergency_advice"] is False  # unknown duration

    long = ok(seizure(client, world, duration_seconds=360, fever_present=True, seizure_type="shaking"), 201)
    assert long["emergency_advice"] is True
    flag = long["red_flags"][0]
    assert "emergency" in flag["message_en"].lower() and flag["message_ur"]
    assert long["seizure"]["verified_by_doctor"] is False

    pid = world["pid"]
    assert ok(client.get("/patients", headers=DOC))[0]["unseen_red_flags"] == 1
    unseen = ok(client.get(f"/patients/{pid}/red-flags", headers=DOC))
    assert len(unseen) == 1 and unseen[0]["doctor_seen_at"] is None
    seen = ok(client.post(f"/red-flag-events/{flag['event_id']}/seen", headers=DOC))
    assert seen["doctor_seen_at"] is not None
    assert ok(client.get(f"/patients/{pid}/red-flags", headers=DOC)) == []
    assert len(ok(client.get(f"/patients/{pid}/red-flags?unseen_only=false", headers=DOC))) == 1


def test_seizure_input_checks(client, world):
    assert seizure(client, world, occurred_at=ago(hours=-5)).status_code == 422       # future
    assert seizure(client, world, occurred_at="2026-10-12T02:10:00").status_code == 422  # no timezone
    assert seizure(client, world, duration_seconds=-1).status_code == 422
    stranger = ok(client.post("/patients", headers=DOC, json={
        "doctor_id": world["doctor"]["id"], "full_name": "Other", "date_of_birth": "2019-01-01"}), 201)
    r = client.post(f"/patients/{stranger['id']}/seizures", headers=BOT, json={
        "guardian_id": world["gid"], "occurred_at": ago(hours=1)})
    assert r.status_code == 403  # this guardian is not linked to that child


def test_doctor_can_add_a_cluster_rule(client, world):
    rule = ok(client.post(f"/doctors/{world['doctor']['id']}/red-flag-rules", headers=DOC, json={
        "name": "Three seizures in a day",
        "condition": {"kind": "cluster", "event": "seizure", "count_gte": 3, "within_hours": 24},
        "message_ur": "ur", "message_en": "Three seizures in 24 hours. Call the clinic now.",
    }), 201)
    assert rule["name"] == "Three seizures in a day"

    first = ok(seizure(client, world, occurred_at=ago(hours=5), duration_seconds=30), 201)
    second = ok(seizure(client, world, occurred_at=ago(hours=3), duration_seconds=30), 201)
    third = ok(seizure(client, world, occurred_at=ago(hours=1), duration_seconds=30), 201)
    assert not first["red_flags"] and not second["red_flags"]
    assert [f["rule_name"] for f in third["red_flags"]] == ["Three seizures in a day"]


def test_bad_rule_is_refused(client, world):
    r = client.post(f"/doctors/{world['doctor']['id']}/red-flag-rules", headers=DOC, json={
        "name": "x", "message_ur": "u", "message_en": "e",
        "condition": {"kind": "threshold", "event": "seizure", "field": "duration_seconds", "op": "<", "value": 5}})
    assert r.status_code == 422
    assert client.post(f"/doctors/{uuid.uuid4()}/red-flag-rules", headers=DOC, json={
        "name": "x", "message_ur": "u", "message_en": "e",
        "condition": {"kind": "cluster", "event": "seizure", "count_gte": 3, "within_hours": 24}}).status_code == 404


# ---------------------------------------------------------------- timeline and verify

def test_timeline_lists_everything_and_verify_works(client, world, med):
    pid, gid = world["pid"], world["gid"]
    ok(seizure(client, world, duration_seconds=90), 201)
    ok(client.post(f"/patients/{pid}/iv-infusions", headers=BOT, json={
        "guardian_id": gid, "given_on": datetime.now(timezone.utc).date().isoformat(),
        "fluid_or_drug": "Normal saline", "given_at": "Test hospital", "duration_minutes": 60}), 201)
    ok(client.post(f"/patients/{pid}/hospital-visits", headers=BOT, json={
        "guardian_id": gid, "visit_type": "emergency",
        "visited_on": datetime.now(timezone.utc).date().isoformat(), "facility": "Test hospital"}), 201)

    rows = ok(client.get(f"/patients/{pid}/timeline", headers=DOC))
    assert {r["event_type"] for r in rows} == {"seizure", "medicine_change", "iv_drip", "hospital_visit"}
    times = [datetime.fromisoformat(r["happened_at"]) for r in rows]
    assert times == sorted(times, reverse=True)
    assert all(r["row_id"] and r["verify_kind"] for r in rows)

    target = next(r for r in rows if r["event_type"] == "seizure")
    assert target["verified_by_doctor"] is False
    ok(client.post(f"/verify/{target['verify_kind']}/{target['row_id']}", headers=DOC))
    after = ok(client.get(f"/patients/{pid}/timeline", headers=DOC))
    assert next(r for r in after if r["row_id"] == target["row_id"])["verified_by_doctor"] is True

    assert client.post(f"/verify/seizures/{uuid.uuid4()}", headers=DOC).status_code == 404
    assert client.post(f"/verify/nonsense/{target['row_id']}", headers=DOC).status_code == 422
    assert client.post(f"/verify/seizures/{target['row_id']}", headers=BOT).status_code == 401

    first_page = ok(client.get(f"/patients/{pid}/timeline", params={"limit": 1}, headers=DOC))
    second_page = ok(client.get(f"/patients/{pid}/timeline", headers=DOC,
                                params={"limit": 50, "before": first_page[0]["happened_at"]}))
    assert len(first_page) == 1 and first_page[0]["row_id"] not in {r["row_id"] for r in second_page}


# ---------------------------------------------------------------- pre-visit summary

def test_previsit_summary(client, world, med):
    pid, gid, mid = world["pid"], world["gid"], med["id"]
    ok(seizure(client, world, occurred_at=ago(days=3), duration_seconds=400, fever_present=True), 201)  # also a red flag
    ok(seizure(client, world, occurred_at=ago(days=2), duration_seconds=45), 201)
    ok(seizure(client, world, occurred_at=ago(days=35), duration_seconds=30), 201)  # in the period before

    for hours, status in ((70, "taken"), (46, "missed"), (22, "vomited")):
        ok(client.post(f"/medications/{mid}/adherence", headers=BOT, json={
            "guardian_id": gid, "scheduled_for": ago(hours=hours), "status": status}), 201)
    ok(client.post(f"/patients/{pid}/iv-infusions", headers=BOT, json={
        "guardian_id": gid, "given_on": datetime.now(timezone.utc).date().isoformat(), "fluid_or_drug": "Saline"}), 201)
    ok(client.post(f"/patients/{pid}/allergies", headers=DOC, json={"substance": "Penicillin", "reaction": "rash"}), 201)
    ok(client.post(f"/patients/{pid}/side-effects", headers=BOT, json={
        "guardian_id": gid, "medication_id": mid, "observed_on": datetime.now(timezone.utc).date().isoformat(),
        "description": "Sleepy after the dose", "severity": "mild"}), 201)

    s = ok(client.get(f"/patients/{pid}/previsit", headers=DOC))
    assert s["seizures"]["total"] == 2
    assert s["seizures"]["longest_seconds"] == 400
    assert s["seizures"]["with_fever"] == 1
    assert s["seizures"]["previous_period_total"] == 1
    assert len(s["red_flags"]) == 1
    assert [(a["given"], a["missed"], a["vomited"]) for a in s["adherence"]] == [(1, 1, 1)]
    assert len(s["iv_infusions"]) == 1 and len(s["allergies"]) == 1 and len(s["side_effects"]) == 1
    assert [m["drug_name"] for m in s["medicines_now"]] == ["Levetiracetam"]
    assert s["medicine_changes"] == [] or all(c["drug_name"] == "Levetiracetam" for c in s["medicine_changes"])
    assert s["unverified_entries"] == 5  # 3 seizures + 1 drip + 1 side effect; the medicine was added by the doctor

    assert client.get(f"/patients/{pid}/previsit", params={"since": "2999-01-01"}, headers=DOC).status_code == 422
    assert client.get(f"/patients/{uuid.uuid4()}/previsit", headers=DOC).status_code == 404
    assert client.get(f"/patients/{pid}/previsit", headers=BOT).status_code == 401


# ---------------------------------------------------------------- prescription slips

def test_slip_flow(client, world):
    pid, gid = world["pid"], world["gid"]
    upload = ok(client.post(f"/patients/{pid}/prescription-uploads", headers=BOT, json={
        "guardian_id": gid, "image_url": "https://example.com/slip.jpg",
        "extracted_json": {"items": [{"drug_name": "Levetiracetam", "dose": "7 ml"}]}}), 201)
    assert upload["status"] == "pending"
    uid = upload["id"]

    stranger = ok(client.post(f"/patients/{pid}/guardians", headers=DOC, json={
        "full_name": "Other Parent", "phone": "923222222222"}), 201)
    other_child = ok(client.post("/patients", headers=DOC, json={
        "doctor_id": world["doctor"]["id"], "full_name": "Other", "date_of_birth": "2019-01-01"}), 201)
    unlinked = ok(client.post(f"/patients/{other_child['id']}/guardians", headers=DOC, json={
        "full_name": "Not Linked", "phone": "923333333333"}), 201)
    assert client.post(f"/prescription-uploads/{uid}/confirm", headers=BOT,
                       json={"guardian_id": unlinked["id"]}).status_code == 403
    assert ok(client.post(f"/prescription-uploads/{uid}/confirm", headers=BOT,
                          json={"guardian_id": stranger["id"]}))["status"] == "parent_confirmed"
    assert client.post(f"/prescription-uploads/{uid}/confirm", headers=BOT,
                       json={"guardian_id": gid}).status_code == 409

    assert client.post(f"/prescription-uploads/{uid}/approve", headers=BOT, json={"items": []}).status_code == 401
    approved = ok(client.post(f"/prescription-uploads/{uid}/approve", headers=DOC, json={
        "items": [LEVETIRACETAM], "reviewer_note": "Checked against the photo"}))
    assert approved["upload"]["status"] == "doctor_verified" and approved["upload"]["reviewed_at"]
    created = approved["medications_created"]
    assert len(created) == 1 and created[0]["source"] == "prescription_photo" and created[0]["verified_by_doctor"]
    assert [m["drug_name"] for m in ok(client.get(f"/patients/{pid}/medications", headers=BOT))] == ["Levetiracetam"]
    assert client.post(f"/prescription-uploads/{uid}/approve", headers=DOC, json={"items": []}).status_code == 409

    second = ok(client.post(f"/patients/{pid}/prescription-uploads", headers=BOT, json={
        "guardian_id": gid, "image_url": "https://example.com/blurry.jpg"}), 201)
    assert client.post(f"/prescription-uploads/{second['id']}/reject", headers=DOC, json={}).status_code == 422
    rejected = ok(client.post(f"/prescription-uploads/{second['id']}/reject", headers=DOC,
                              json={"reviewer_note": "Photo is too blurry"}))
    assert rejected["status"] == "rejected" and rejected["reviewer_note"] == "Photo is too blurry"
    assert client.post(f"/prescription-uploads/{uuid.uuid4()}/reject", headers=DOC,
                       json={"reviewer_note": "x"}).status_code == 404

"""The parent app's API, end to end against the test database (see conftest.py)."""
import base64
import json
import pathlib
import uuid
from datetime import datetime, timedelta, timezone

import psycopg
import pytest

from app import queries as q
from app.routers import parent as parent_router

DOC = {"X-Doctor-Key": "test-doctor-key"}
FAQ = json.loads((pathlib.Path(__file__).resolve().parents[1] / "db" / "faq.json").read_text(encoding="utf-8"))


def ok(response, status=200):
    assert response.status_code == status, f"{response.status_code}: {response.text}"
    return response.json()


def ago(**kwargs) -> str:
    return (datetime.now(timezone.utc) - timedelta(**kwargs)).isoformat()


@pytest.fixture
def sent_codes(monkeypatch):
    codes = []
    monkeypatch.setattr(parent_router, "send_code", lambda phone, code: codes.append((phone, code)))
    return codes


@pytest.fixture
def family(client, database):
    doctor = ok(client.post("/doctors", json={"full_name": "Dr Test", "email": "dr@example.com"}, headers=DOC), 201)
    child = ok(client.post("/patients", headers=DOC, json={
        "doctor_id": doctor["id"], "full_name": "Sample Child", "date_of_birth": "2020-05-01"}), 201)
    other = ok(client.post("/patients", headers=DOC, json={
        "doctor_id": doctor["id"], "full_name": "Not Theirs", "date_of_birth": "2019-01-01"}), 201)
    mother = ok(client.post(f"/patients/{child['id']}/guardians", headers=DOC, json={
        "full_name": "Sample Mother", "phone": "03001234567", "is_primary": True}), 201)
    med = ok(client.post(f"/patients/{child['id']}/medications", headers=DOC, json={
        "drug_name": "Levetiracetam", "dose_amount": "5", "dose_unit": "ml", "times_per_day": 2,
        "dose_times": ["08:00", "20:00"], "started_on": "2026-06-03"}), 201)
    with psycopg.connect(database) as conn:
        for i, e in enumerate(FAQ):
            conn.execute(q.UPSERT_FAQ, {
                "doctor_id": doctor["id"], "topic": e["topic"], "question_en": e["question_en"],
                "question_ur": e["question_ur"], "answer_en": e["answer_en"], "answer_ur": e["answer_ur"],
                "is_published": e["published"], "sort_order": i})
        conn.commit()
    return {"doctor": doctor, "child": child, "other": other, "mother": mother, "med": med}


def login(client, sent_codes, phone="0300 1234567"):
    ok(client.post("/parent/auth/request-code", json={"phone": phone}))
    code = sent_codes[-1][1]
    body = ok(client.post("/parent/auth/verify", json={"phone": phone, "code": code}))
    return {"Authorization": f"Bearer {body['token']}"}


def test_phone_is_stored_as_digits(family):
    assert family["mother"]["phone"] == "923001234567"


def test_login_flow(client, family, sent_codes):
    # Unknown number: same answer, but no code is made.
    unknown = ok(client.post("/parent/auth/request-code", json={"phone": "03119999999"}))
    assert unknown["sent"] is True and sent_codes == []
    assert client.post("/parent/auth/request-code", json={"phone": "12"}).status_code == 422

    ok(client.post("/parent/auth/request-code", json={"phone": "+92 300 1234567"}))
    phone, code = sent_codes[-1]
    assert phone == "923001234567" and len(code) == 6
    wrong = "000000" if code != "000000" else "111111"
    assert client.post("/parent/auth/verify", json={"phone": "03001234567", "code": wrong}).status_code == 400
    body = ok(client.post("/parent/auth/verify", json={"phone": "03001234567", "code": code}))
    headers = {"Authorization": f"Bearer {body['token']}"}
    assert body["guardian"]["full_name"] == "Sample Mother"

    # A used code does not work twice.
    assert client.post("/parent/auth/verify", json={"phone": "03001234567", "code": code}).status_code == 400

    me = ok(client.get("/parent/me", headers=headers))
    assert [c["full_name"] for c in me["children"]] == ["Sample Child"]
    assert "diagnosis" not in me["children"][0]

    ok(client.post("/parent/auth/logout", headers=headers))
    assert client.get("/parent/me", headers=headers).status_code == 401


def test_no_token_or_bad_token(client, family):
    assert client.get("/parent/me").status_code == 401
    assert client.get("/parent/me", headers={"Authorization": "Bearer nonsense"}).status_code == 401
    assert client.get("/parent/me", headers=DOC).status_code == 401  # the doctor key is not a parent login


def test_too_many_wrong_codes_burns_the_code(client, family, sent_codes):
    ok(client.post("/parent/auth/request-code", json={"phone": "03001234567"}))
    code = sent_codes[-1][1]
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(5):
        assert client.post("/parent/auth/verify", json={"phone": "03001234567", "code": wrong}).status_code == 400
    assert client.post("/parent/auth/verify", json={"phone": "03001234567", "code": code}).status_code == 429
    assert client.post("/parent/auth/verify", json={"phone": "03001234567", "code": code}).status_code == 400


def test_code_requests_are_limited(client, family, sent_codes):
    for _ in range(5):
        ok(client.post("/parent/auth/request-code", json={"phone": "03001234567"}))
    assert client.post("/parent/auth/request-code", json={"phone": "03001234567"}).status_code == 429


def test_parent_cannot_reach_another_child(client, family, sent_codes):
    h = login(client, sent_codes)
    other = family["other"]["id"]
    assert client.get(f"/parent/children/{other}/today", headers=h).status_code == 403
    assert client.post(f"/parent/children/{other}/seizures", headers=h,
                       json={"occurred_at": ago(hours=1), "duration_seconds": 30}).status_code == 403
    assert client.get(f"/parent/children/{uuid.uuid4()}/faq", headers=h).status_code == 404
    # Doctor-only routes stay closed to a parent token.
    assert client.get("/patients", headers=h).status_code == 401


def test_today_and_dose_logging(client, family, sent_codes):
    h = login(client, sent_codes)
    child = family["child"]["id"]
    today = ok(client.get(f"/parent/children/{child}/today", headers=h))
    med = today["medicines"][0]
    assert med["drug_name"] == "Levetiracetam" and len(med["slots"]) == 2
    assert all(s["status"] is None for s in med["slots"])
    assert med["slots"][0]["at"].endswith("08:00:00+05:00")

    first = med["slots"][0]["at"]
    if med["slots"][0]["due"]:
        ok(client.post(f"/parent/children/{child}/doses", headers=h,
                       json={"medication_id": med["id"], "scheduled_for": first, "status": "taken"}), 201)
        again = ok(client.get(f"/parent/children/{child}/today", headers=h))
        assert again["medicines"][0]["slots"][0]["status"] == "taken"
    else:  # run before 07:00: a dose more than an hour ahead cannot be logged yet
        assert client.post(f"/parent/children/{child}/doses", headers=h, json={
            "medication_id": med["id"], "scheduled_for": first, "status": "taken"}).status_code == 422

    other_med = ok(client.post(f"/patients/{family['other']['id']}/medications", headers=DOC, json={
        "drug_name": "X", "dose_amount": "1", "dose_unit": "ml", "times_per_day": 1, "started_on": "2026-01-01"}), 201)
    assert client.post(f"/parent/children/{child}/doses", headers=h, json={
        "medication_id": other_med["id"], "scheduled_for": first, "status": "taken"}).status_code == 404


def test_seizure_from_the_app_raises_the_red_flag(client, family, sent_codes):
    h = login(client, sent_codes)
    child = family["child"]["id"]
    short = ok(client.post(f"/parent/children/{child}/seizures", headers=h,
                           json={"occurred_at": ago(minutes=30), "duration_seconds": 90}), 201)
    assert short["emergency_advice"] is False
    long = ok(client.post(f"/parent/children/{child}/seizures", headers=h,
                          json={"occurred_at": ago(minutes=5), "duration_seconds": 300, "fever_present": True}), 201)
    assert long["emergency_advice"] is True and long["red_flags"][0]["message_ur"]
    assert long["seizure"]["logged_by"] == family["mother"]["id"]
    row = next(p for p in ok(client.get("/patients", headers=DOC)) if p["id"] == child)
    assert row["unseen_red_flags"] == 1


def test_side_effect(client, family, sent_codes):
    h = login(client, sent_codes)
    child = family["child"]["id"]
    today = datetime.now(timezone.utc).date().isoformat()
    ok(client.post(f"/parent/children/{child}/side-effects", headers=h, json={
        "observed_on": today, "description": "Very sleepy", "medication_id": family["med"]["id"]}), 201)
    assert client.post(f"/parent/children/{child}/side-effects", headers=h, json={
        "observed_on": "2999-01-01", "description": "x"}).status_code == 422


def test_faq_shows_only_published_answers(client, family, sent_codes):
    h = login(client, sent_codes)
    faq = ok(client.get(f"/parent/children/{family['child']['id']}/faq", headers=h))
    topics = [f["topic"] for f in faq]
    assert topics[0] == "first-aid" and len(topics) == 8
    assert "missed-dose" not in topics and "fever" not in topics
    assert all("[Doctor" not in f["answer_en"] and "[ڈاکٹر" not in f["answer_ur"] for f in faq)


def test_question_goes_to_the_doctor_and_back(client, family, sent_codes):
    h = login(client, sent_codes)
    child = family["child"]["id"]
    asked = ok(client.post(f"/parent/children/{child}/questions", headers=h,
                           json={"question": "Kya is hafte school bhej sakte hain?"}), 201)
    assert asked["answer"] is None
    assert client.post(f"/parent/children/{child}/questions", headers=h, json={"question": "a"}).status_code == 422

    row = next(p for p in ok(client.get("/patients", headers=DOC)) if p["id"] == child)
    assert row["open_questions"] == 1
    open_q = ok(client.get(f"/patients/{child}/questions", headers=DOC))
    assert open_q[0]["guardian_name"] == "Sample Mother"
    ok(client.post(f"/questions/{asked['id']}/answer", headers=DOC, json={"answer": "Haan, Monday se."}))
    assert ok(client.get(f"/patients/{child}/questions", headers=DOC)) == []
    assert len(ok(client.get(f"/patients/{child}/questions?open_only=false", headers=DOC))) == 1

    mine = ok(client.get(f"/parent/children/{child}/questions", headers=h))
    assert mine[0]["answer"] == "Haan, Monday se." and mine[0]["answered_at"]
    assert client.post(f"/questions/{asked['id']}/answer", headers=h, json={"answer": "x"}).status_code == 401


def test_parent_app_page_is_served(client):
    page = client.get("/app/")
    assert page.status_code == 200 and "<html" in page.text.lower()
    assert client.get("/", follow_redirects=False).headers["location"] == "/app/"


# ---------------------------------------------------------------- AI features (offline provider)

TINY_JPEG = base64.b64encode(b"\xff\xd8\xff\xe0" + b"\x00" * 200).decode()


def test_seizure_draft_from_free_text(client, family, sent_codes):
    h = login(client, sent_codes)
    child = family["child"]["id"]
    r = ok(client.post(f"/parent/children/{child}/ai/seizure-draft", headers=h,
                       json={"text": "kal raat 3 minute dora para, bukhar bhi tha"}))
    assert r["source"] == "rules"  # no AI key in tests
    assert r["draft"]["duration_seconds"] == 180 and r["draft"]["fever_present"] is True
    assert r["draft"]["occurred_at"].endswith("22:00:00+05:00")
    # Nothing was saved: the parent still has to confirm in the form.
    timeline = ok(client.get(f"/patients/{child}/timeline", headers=DOC))
    assert not any(row["event_type"] == "seizure" for row in timeline)
    assert client.post(f"/parent/children/{family['other']['id']}/ai/seizure-draft", headers=h,
                       json={"text": "kal dora para"}).status_code == 403


def test_question_match(client, family, sent_codes):
    h = login(client, sent_codes)
    child = family["child"]["id"]
    hit = ok(client.post(f"/parent/children/{child}/ai/match-question", headers=h,
                         json={"question": "What should I do during a seizure?"}))["match"]
    assert hit["topic"] == "first-aid" and hit["answer_ur"]
    miss = ok(client.post(f"/parent/children/{child}/ai/match-question", headers=h,
                          json={"question": "Doctor sahab ki fees kitni hai?"}))["match"]
    assert miss is None
    # Unpublished answers are never matched.
    blank = ok(client.post(f"/parent/children/{child}/ai/match-question", headers=h,
                           json={"question": "What if a dose is missed?"}))["match"]
    assert blank is None or blank["topic"] != "missed-dose"


def test_slip_photo_flow(client, family, sent_codes):
    h = login(client, sent_codes)
    child = family["child"]["id"]
    assert client.post(f"/parent/children/{child}/slips", headers=h,
                       json={"mime_type": "image/png", "image_base64": TINY_JPEG}).status_code == 422
    assert client.post(f"/parent/children/{child}/slips", headers=h,
                       json={"mime_type": "image/jpeg", "image_base64": "%%%" * 50}).status_code == 422
    up = ok(client.post(f"/parent/children/{child}/slips", headers=h,
                        json={"mime_type": "image/jpeg", "image_base64": TINY_JPEG}), 201)
    assert up["reading"] is None and up["note"]  # no AI: the doctor reads the photo
    assert [s["id"] for s in ok(client.get(f"/parent/children/{child}/slips", headers=h))] == [up["id"]]

    ok(client.post(f"/parent/children/{child}/slips/{up['id']}/confirm", headers=h))
    assert client.post(f"/parent/children/{child}/slips/{up['id']}/confirm", headers=h).status_code == 409

    waiting = ok(client.get(f"/patients/{child}/prescription-uploads", headers=DOC))
    assert waiting[0]["status"] == "parent_confirmed" and waiting[0]["guardian_name"] == "Sample Mother"
    img = client.get(f"/prescription-uploads/{up['id']}/image", headers=DOC)
    assert img.status_code == 200 and img.headers["content-type"] == "image/jpeg" and img.content[:3] == b"\xff\xd8\xff"
    assert client.get(f"/prescription-uploads/{up['id']}/image", headers=h).status_code == 401

    ok(client.post(f"/prescription-uploads/{up['id']}/approve", headers=DOC, json={"items": [{
        "drug_name": "Levetiracetam", "dose_amount": "5", "dose_unit": "ml", "times_per_day": 2,
        "started_on": "2026-06-03"}]}))
    assert ok(client.get(f"/patients/{child}/prescription-uploads", headers=DOC)) == []

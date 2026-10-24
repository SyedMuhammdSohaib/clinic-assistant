"""Tests that need no database and no web server."""
import base64
import json
import re
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app import parent_auth, queries
from app.redflags import DEFAULT_RULE, condition_hit
from app.schemas import (
    AdherenceIn,
    GuardianIn,
    HospitalVisitIn,
    MedicationChangeIn,
    MedicationIn,
    PatientIn,
    RuleIn,
    SeizureIn,
    ThresholdCondition,
)

GUARDIAN = "7b1f5c7e-3f0a-4d0e-9f27-2f3a3c6b9a11"
PATIENT_BASE = {"doctor_id": GUARDIAN, "full_name": "Sample Child", "date_of_birth": "2020-05-01"}
MED_BASE = {
    "drug_name": "Levetiracetam", "dose_amount": "5", "dose_unit": "ml",
    "times_per_day": 2, "started_on": "2026-06-03",
}


# ---------------------------------------------------------------- request models

def test_medication_accepts_valid_body():
    med = MedicationIn(**MED_BASE, dose_times=["08:00", "20:00"])
    assert med.route == "oral"
    assert len(med.dose_times) == 2


def test_medication_rejects_wrong_number_of_dose_times():
    with pytest.raises(ValidationError):
        MedicationIn(**MED_BASE, dose_times=["08:00"])


def test_medication_rejects_zero_negative_and_too_precise_doses():
    for bad in ("0", "-1", "5.123"):
        with pytest.raises(ValidationError):
            MedicationIn(**{**MED_BASE, "dose_amount": bad})


def test_unknown_fields_are_rejected():
    with pytest.raises(ValidationError):
        MedicationIn(**MED_BASE, doses_per_day=3)
    with pytest.raises(ValidationError):
        PatientIn(**PATIENT_BASE, doctor_notes="should not be settable here")


def test_patient_birth_date_cannot_be_in_the_future():
    with pytest.raises(ValidationError):
        PatientIn(**{**PATIENT_BASE, "date_of_birth": "2999-01-01"})


def test_guardian_phone_format():
    GuardianIn(full_name="Sample Mother", phone="923001234567")
    GuardianIn(full_name="Sample Mother", phone="+923001234567")
    with pytest.raises(ValidationError):
        GuardianIn(full_name="Sample Mother", phone="0300-1234567")


def test_seizure_time_needs_timezone_and_cannot_be_future():
    now = datetime.now(timezone.utc)
    SeizureIn(guardian_id=GUARDIAN, occurred_at=now - timedelta(hours=1))
    with pytest.raises(ValidationError):
        SeizureIn(guardian_id=GUARDIAN, occurred_at=datetime.now())  # no timezone
    with pytest.raises(ValidationError):
        SeizureIn(guardian_id=GUARDIAN, occurred_at=now + timedelta(days=1))
    with pytest.raises(ValidationError):
        SeizureIn(guardian_id=GUARDIAN, occurred_at=now - timedelta(hours=1), duration_seconds=-5)


def test_dose_log_cannot_be_far_in_the_future():
    now = datetime.now(timezone.utc)
    AdherenceIn(guardian_id=GUARDIAN, scheduled_for=now, status="taken")
    with pytest.raises(ValidationError):
        AdherenceIn(guardian_id=GUARDIAN, scheduled_for=now + timedelta(hours=3), status="taken")


def test_dose_change_needs_the_new_value():
    with pytest.raises(ValidationError):
        MedicationChangeIn(change_type="dose_increased")
    with pytest.raises(ValidationError):
        MedicationChangeIn(change_type="frequency_changed")
    MedicationChangeIn(change_type="stopped")
    MedicationChangeIn(change_type="dose_decreased", new_dose_amount="3")


def test_hospital_discharge_cannot_be_before_visit():
    base = {"guardian_id": GUARDIAN, "visit_type": "admission", "visited_on": "2026-10-12"}
    HospitalVisitIn(**base, discharged_on="2026-10-14")
    with pytest.raises(ValidationError):
        HospitalVisitIn(**base, discharged_on="2026-10-10")


def test_rule_conditions_are_checked():
    ok = {"name": "x", "message_ur": "u", "message_en": "e"}
    RuleIn(**ok, condition={"kind": "threshold", "event": "seizure",
                            "field": "duration_seconds", "op": ">=", "value": 180})
    RuleIn(**ok, condition={"kind": "cluster", "event": "seizure", "count_gte": 3, "within_hours": 24})
    for bad in (
        {"kind": "threshold", "event": "seizure", "field": "duration_seconds", "op": "<", "value": 5},
        {"kind": "cluster", "event": "seizure", "count_gte": 1, "within_hours": 24},
        {"kind": "mystery", "event": "seizure"},
    ):
        with pytest.raises(ValidationError):
            RuleIn(**ok, condition=bad)


# ---------------------------------------------------------------- red-flag logic

def test_threshold_rule():
    rule = {"kind": "threshold", "event": "seizure", "field": "duration_seconds", "op": ">=", "value": 300}
    assert condition_hit(rule, {"duration_seconds": 300})
    assert condition_hit(rule, {"duration_seconds": 301})
    assert not condition_hit(rule, {"duration_seconds": 299})
    assert not condition_hit({**rule, "op": ">"}, {"duration_seconds": 300})


def test_threshold_rule_does_not_fire_when_duration_unknown():
    rule = {"kind": "threshold", "event": "seizure", "field": "duration_seconds", "op": ">=", "value": 300}
    assert not condition_hit(rule, {"duration_seconds": None})
    assert not condition_hit(rule, {})


def test_cluster_rule():
    rule = {"kind": "cluster", "event": "seizure", "count_gte": 3, "within_hours": 24}
    assert condition_hit(rule, {}, count_in_window=3)
    assert not condition_hit(rule, {}, count_in_window=2)
    assert not condition_hit(rule, {}, count_in_window=None)


def test_other_events_and_unknown_kinds_never_fire():
    assert not condition_hit({"kind": "threshold", "event": "iv_drip", "field": "x", "op": ">=", "value": 1}, {"x": 5})
    assert not condition_hit({"kind": "mystery", "event": "seizure"}, {})


def test_default_rule_is_valid_and_fires_at_five_minutes():
    ThresholdCondition(**DEFAULT_RULE["condition"])  # same shape the API accepts
    assert condition_hit(DEFAULT_RULE["condition"], {"duration_seconds": 300})
    assert not condition_hit(DEFAULT_RULE["condition"], {"duration_seconds": 120})
    assert "please confirm" in DEFAULT_RULE["name"]


# ---------------------------------------------------------------- SQL hygiene

def test_sql_has_no_stray_percent_signs():
    """psycopg reads a bare % as the start of a placeholder, so none may sneak in."""
    statements = {
        name: value for name, value in vars(queries).items()
        if name.isupper() and isinstance(value, str)
    }
    statements.update({f"VERIFY[{k}]": v for k, v in queries.VERIFY.items()})
    assert statements, "no queries found"
    for name, sql in statements.items():
        stray = re.findall(r"%(?!\(\w+\)s)", sql)
        assert not stray, f"{name} contains a stray percent sign"


# ---------------------------------------------------------------- login code by SMS

class FakeGateway:
    """Stands in for the SMS Gateway for Android app and records what it was sent."""

    def __init__(self, status=200):
        import http.server
        import threading

        self.requests = []
        gateway = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                body = self.rfile.read(int(self.headers["Content-Length"]))
                gateway.requests.append((self.headers["Authorization"], json.loads(body)))
                self.send_response(status)
                self.end_headers()
                self.wfile.write(b"{}")

            def log_message(self, *args):
                pass

        self.server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_port}/3rdparty/v1/message"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self):
        self.server.shutdown()


@pytest.fixture
def gateway(monkeypatch):
    fake = FakeGateway()
    monkeypatch.setenv("SMS_GATEWAY_URL", fake.url)
    monkeypatch.setenv("SMS_GATEWAY_USER", "clinic")
    monkeypatch.setenv("SMS_GATEWAY_PASSWORD", "secret")
    yield fake
    fake.close()


def test_login_code_goes_by_sms_when_gateway_is_set(gateway, capsys):
    parent_auth.send_code("923001234567", "123456")
    assert len(gateway.requests) == 1
    auth, body = gateway.requests[0]
    assert auth == "Basic " + base64.b64encode(b"clinic:secret").decode()
    assert body["phoneNumbers"] == ["+923001234567"]
    assert "123456" in body["textMessage"]["text"]
    assert "123456" not in capsys.readouterr().out


def test_login_code_is_printed_when_sms_is_off(monkeypatch, capsys):
    monkeypatch.delenv("SMS_GATEWAY_URL", raising=False)
    parent_auth.send_code("923001234567", "123456")
    assert "123456" in capsys.readouterr().out


def test_login_code_is_printed_when_sms_fails(monkeypatch, capsys):
    fake = FakeGateway(status=500)
    monkeypatch.setenv("SMS_GATEWAY_URL", fake.url)
    try:
        parent_auth.send_code("923001234567", "654321")
    finally:
        fake.close()
    assert "654321" in capsys.readouterr().out


def test_login_code_is_printed_when_phone_is_offline(monkeypatch, capsys):
    monkeypatch.setenv("SMS_GATEWAY_URL", "http://127.0.0.1:9/message")
    parent_auth.send_code("923001234567", "111222")
    assert "111222" in capsys.readouterr().out


def test_login_code_is_printed_when_gateway_url_is_malformed(monkeypatch, capsys):
    monkeypatch.setenv("SMS_GATEWAY_URL", "192.168.10.10:8080/message")  # http:// missing
    parent_auth.send_code("923001234567", "333444")
    assert "333444" in capsys.readouterr().out


def test_phone_on_local_wifi_is_reached_without_the_computers_proxy(gateway, monkeypatch, capsys):
    monkeypatch.setenv("HTTP_PROXY", "http://proxy.invalid:3128")
    monkeypatch.setenv("http_proxy", "http://proxy.invalid:3128")
    monkeypatch.delenv("NO_PROXY", raising=False)
    monkeypatch.delenv("no_proxy", raising=False)
    parent_auth.send_code("923001234567", "555666")
    assert len(gateway.requests) == 1
    assert "555666" not in capsys.readouterr().out


def test_notice_goes_by_sms_or_is_printed(gateway, monkeypatch, capsys):
    from app import sms

    monkeypatch.setattr(sms, "_dispatch", lambda job: job())   # run the background send right away
    sms.notify("923001234567", "Doctor ne jawab de diya")
    assert gateway.requests[0][1]["textMessage"]["text"] == "Doctor ne jawab de diya"
    monkeypatch.delenv("SMS_GATEWAY_URL")
    sms.notify("923001234567", "printed instead")
    assert "printed instead" in capsys.readouterr().out

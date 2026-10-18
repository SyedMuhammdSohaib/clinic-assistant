"""Tests that need no database and no web server."""
import re
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app import queries
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

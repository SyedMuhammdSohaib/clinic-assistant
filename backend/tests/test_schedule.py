"""Dose slots and phone numbers. No database needed."""
from datetime import date, time
from zoneinfo import ZoneInfo

from app.parent_auth import code_hash, new_code, new_token, sha256
from app.schedule import day_bounds, default_times, dose_slots, normalize_phone

TZ = ZoneInfo("Asia/Karachi")


def test_default_times_spread_over_waking_hours():
    assert default_times(1) == [time(8, 0)]
    assert default_times(2) == [time(8, 0), time(22, 0)]
    assert default_times(3) == [time(8, 0), time(15, 0), time(22, 0)]
    assert default_times(4)[1] == time(12, 40)


def test_dose_slots_use_the_doctors_times_when_set():
    slots = dose_slots([time(20, 0), time(8, 0)], 2, date(2026, 10, 14), TZ)
    assert [s.isoformat() for s in slots] == ["2026-10-14T08:00:00+05:00", "2026-10-14T20:00:00+05:00"]


def test_dose_slots_fall_back_to_default_times():
    slots = dose_slots(None, 2, date(2026, 10, 14), TZ)
    assert [s.hour for s in slots] == [8, 22]


def test_day_bounds():
    start, end = day_bounds(date(2026, 10, 14), TZ)
    assert start.isoformat() == "2026-10-14T00:00:00+05:00"
    assert (end - start).days == 1


def test_normalize_phone():
    assert normalize_phone("0300-1234567") == "923001234567"
    assert normalize_phone("0300 123 4567") == "923001234567"
    assert normalize_phone("+92 300 1234567") == "923001234567"
    assert normalize_phone("00923001234567") == "923001234567"
    assert normalize_phone("923001234567") == "923001234567"
    assert normalize_phone("12345") is None
    assert normalize_phone("") is None


def test_codes_and_tokens():
    codes = {new_code() for _ in range(200)}
    assert all(len(c) == 6 and c.isdigit() for c in codes)
    assert len(codes) > 150
    assert len(new_token()) >= 40
    assert code_hash("923001234567", "123456") != code_hash("923001234568", "123456")
    assert len(sha256("x")) == 64

"""Clinic-local date and time. Kept free of web imports so it is easy to test."""
import os
from datetime import date, datetime
from zoneinfo import ZoneInfo


def clinic_tz() -> ZoneInfo:
    return ZoneInfo(os.environ.get("CLINIC_TZ", "Asia/Karachi"))


def clinic_today() -> date:
    return datetime.now(clinic_tz()).date()

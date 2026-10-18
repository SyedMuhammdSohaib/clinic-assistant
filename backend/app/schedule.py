"""Daily dose slots and phone numbers. Pure functions, easy to test."""
import re
from datetime import date, datetime, time, timedelta, tzinfo

# Waking hours used when the doctor did not set exact dose times.
DAY_START = time(8, 0)
DAY_END = time(22, 0)


def default_times(times_per_day: int) -> list[time]:
    """Spread the doses over waking hours: 1 -> 08:00, 2 -> 08:00 and 22:00, 3 -> 08:00, 15:00, 22:00."""
    if times_per_day <= 1:
        return [DAY_START]
    start = DAY_START.hour * 60 + DAY_START.minute
    span = (DAY_END.hour * 60 + DAY_END.minute) - start
    step = span / (times_per_day - 1)
    minutes = [round(start + i * step) for i in range(times_per_day)]
    return [time(m // 60, m % 60) for m in minutes]


def dose_slots(dose_times: list[time] | None, times_per_day: int, day: date, tz: tzinfo) -> list[datetime]:
    """The moments a dose is due on `day`, in the clinic's time zone."""
    times = sorted(dose_times) if dose_times else default_times(times_per_day)
    return [datetime.combine(day, t, tzinfo=tz) for t in times]


def day_bounds(day: date, tz: tzinfo) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min, tzinfo=tz)
    return start, start + timedelta(days=1)


def normalize_phone(raw: str) -> str | None:
    """Digits only, Pakistani local numbers turned into 92...: '0300-1234567' -> '923001234567'.

    Returns None when it cannot be a phone number.
    """
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("00"):
        digits = digits[2:]
    if len(digits) == 11 and digits.startswith("03"):
        digits = "92" + digits[1:]
    if not 9 <= len(digits) <= 15:
        return None
    return digits

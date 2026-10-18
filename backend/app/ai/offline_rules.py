"""A no-AI baseline: keyword rules for Roman Urdu, Urdu and English, and a simple
text embedding. Used when no AI key is set, in tests, and as the baseline the
evaluation compares the AI against.
"""
import hashlib
import math
import re
from datetime import datetime, time, timedelta

URDU_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

NUMBER_WORDS = {
    # Roman Urdu
    "aadha": 0.5, "adha": 0.5, "dedh": 1.5, "dhai": 2.5, "dhaai": 2.5,
    "ek": 1, "aik": 1, "do": 2, "teen": 3, "tin": 3, "char": 4, "chaar": 4, "panch": 5, "paanch": 5,
    "chay": 6, "chhe": 6, "che": 6, "saat": 7, "sat": 7, "aath": 8, "ath": 8, "nau": 9, "das": 10,
    "bees": 20, "tees": 30, "pandrah": 15,
    # English
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "fifteen": 15, "twenty": 20, "thirty": 30, "half": 0.5,
    # Urdu
    "آدھا": 0.5, "آدھے": 0.5, "ڈیڑھ": 1.5, "ڈھائی": 2.5, "ایک": 1, "دو": 2, "تین": 3, "چار": 4,
    "پانچ": 5, "چھ": 6, "سات": 7, "آٹھ": 8, "نو": 9, "دس": 10, "بیس": 20, "تیس": 30,
}
SECONDS = ("sec", "second", "seconds", "secs", "sekand", "saikand", "سیکنڈ")
MINUTES = ("min", "mins", "minute", "minutes", "mint", "minat", "منٹ")
HOURS = ("ghanta", "ghante", "ghantay", "hour", "hours", "hr", "hrs", "گھنٹہ", "گھنٹے")

_NUM = r"(\d+(?:\.\d+)?|" + "|".join(sorted(map(re.escape, NUMBER_WORDS), key=len, reverse=True)) + r")"
_UNIT = r"(" + "|".join(map(re.escape, SECONDS + MINUTES)) + r")"
_DURATION = re.compile(r"(?<!\w)" + _NUM + r"\s*[- ]?\s*" + _UNIT + r"(?![a-z])", re.IGNORECASE)
_HOURS_AGO = re.compile(r"(?<!\w)" + _NUM + r"\s*(" + "|".join(map(re.escape, HOURS)) + r")\s*(pehle|pehlay|ago|پہلے)", re.IGNORECASE)

NEGATION = ("nahi", "nahin", "nai", "na tha", "nahi tha", "no", "not", "without", "بغیر", "نہیں")
FEVER = ("bukhar", "bukhaar", "bokhar", "fever", "temperature", "temp", "بخار")
ER = ("emergency", "hospital", "aspatal", "haspatal", "1122", "ambulance", "ایمرجنسی", "ہسپتال", "اسپتال")
KINDS = {
    "shaking": ("jhatk", "jhatak", "jerk", "shaking", "shook", "kanp", "convuls", "fits", "جھٹک", "کانپ"),
    "staring": ("ghoor", "ghur", "staring", "stare", "blank", "gum sum", "gumsum", "khoya", "گھور", "گم سم", "کھویا"),
    "stiffening": ("akar", "akad", "stiff", "sakht", "اکڑ", "سخت"),
}


def _number(token: str) -> float | None:
    token = token.lower()
    if re.fullmatch(r"\d+(?:\.\d+)?", token):
        return float(token)
    return NUMBER_WORDS.get(token)


def _mentions(text: str, words) -> int | None:
    """Position of the first mention, or None."""
    positions = [text.find(w) for w in words if w in text]
    return min(positions) if positions else None


_CLAUSE_END = re.compile(r"[,.;!?\n،۔]")


def _negated(text: str, at: int) -> bool:
    """A negation word in the same clause: just before the mention ("no fever",
    "بغیر بخار") or shortly after it ("bukhar nahi tha")."""
    before = text[max(0, at - 10): at]
    before = _CLAUSE_END.split(before)[-1]
    after = _CLAUSE_END.split(text[at: at + 25])[0]
    window = before + after
    return any(re.search(rf"(?<!\w){re.escape(n)}(?!\w)", window) for n in NEGATION)


def extract_seizure(text: str, now: datetime) -> dict:
    """Best-effort reading of a parent's message. Unknown fields stay None."""
    t = text.translate(URDU_DIGITS).lower()
    out = {"occurred_at": None, "duration_seconds": None, "seizure_type": None,
           "fever_present": None, "went_to_er": None}

    m = _DURATION.search(t)
    if m:
        n = _number(m.group(1))
        if n is not None:
            unit = m.group(2).lower()
            out["duration_seconds"] = int(round(n * (60 if unit in MINUTES else 1)))

    at = _mentions(t, FEVER)
    if at is not None:
        out["fever_present"] = not _negated(t, at)

    at = _mentions(t, ER)
    if at is not None:
        out["went_to_er"] = not _negated(t, at)

    for kind, words in KINDS.items():
        if _mentions(t, words) is not None:
            out["seizure_type"] = kind
            break

    out["occurred_at"] = _when(t, now)
    return out


def _when(t: str, now: datetime) -> datetime | None:
    tz = now.tzinfo
    today = now.date()
    yesterday = today - timedelta(days=1)

    def at(day, hh, mm=0):
        return min(datetime.combine(day, time(hh, mm), tzinfo=tz), now)

    m = _HOURS_AGO.search(t)
    if m and _number(m.group(1)) is not None:
        return now - timedelta(hours=_number(m.group(1)))
    if any(w in t for w in ("abhi", "just now", "right now", "ابھی")):
        return now
    yday = any(w in t for w in ("kal", "yesterday", "last night", "کل"))
    night = any(w in t for w in ("raat", "night", "رات"))
    morning = any(w in t for w in ("subah", "morning", "صبح"))
    evening = any(w in t for w in ("shaam", "sham", "evening", "شام"))
    noon = any(w in t for w in ("dopehar", "dopahar", "afternoon", "دوپہر"))
    hour = 22 if night else 8 if morning else 18 if evening else 14 if noon else None
    if yday or "last night" in t:
        return at(yesterday, hour if hour is not None else 12)
    if any(w in t for w in ("aaj", "today", "this morning", "آج")) or hour is not None:
        if hour is None:
            return None
        # "raat ko" said at 4 pm means last night: a time later than now is yesterday's.
        if datetime.combine(today, time(hour), tzinfo=tz) > now:
            return at(yesterday, hour)
        return at(today, hour)
    return None


# ---------------------------------------------------------------- embedding

DIM = 512


def embed(text: str) -> list[float]:
    """Hashed character trigrams plus words, normalised. Crude, but needs no AI."""
    t = re.sub(r"\s+", " ", text.translate(URDU_DIGITS).lower()).strip()
    vec = [0.0] * DIM
    grams = [t[i:i + 3] for i in range(max(len(t) - 2, 0))] + t.split(" ")
    for g in grams:
        h = int(hashlib.md5(g.encode()).hexdigest(), 16)
        vec[h % DIM] += 1.0 if (h >> 8) % 2 else -1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]

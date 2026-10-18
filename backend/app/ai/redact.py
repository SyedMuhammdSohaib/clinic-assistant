"""Remove personal details before text leaves the server for an AI service."""
import re

_CNIC = re.compile(r"\b\d{5}-\d{7}-\d\b")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
# A run of digits, spaces, dashes and an optional leading +; only treated as a phone
# number when it holds 10 or more digits, so dates and doses are left alone.
_DIGIT_RUN = re.compile(r"\+?\d[\d\s-]*\d")


def _phone(match: re.Match) -> str:
    text = match.group(0)
    return "[PHONE]" if sum(c.isdigit() for c in text) >= 10 else text


def redact(text: str, names: list[str] | None = None) -> str:
    """Replace ID numbers, emails, phone numbers and the given names.

    `names` are the child's and parent's names; each word of 3+ letters is replaced,
    so "Ayaan Khan" also catches "Ayaan" on its own.
    """
    out = _CNIC.sub("[ID]", text)
    out = _EMAIL.sub("[EMAIL]", out)
    out = _DIGIT_RUN.sub(_phone, out)
    words = set()
    for name in names or []:
        for part in re.split(r"\s+", name.strip()):
            if len(part) >= 3:
                words.add(part)
    for word in sorted(words, key=len, reverse=True):
        out = re.sub(rf"(?<!\w){re.escape(word)}(?!\w)", "[NAME]", out, flags=re.IGNORECASE)
    return out

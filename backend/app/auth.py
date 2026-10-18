"""Two shared keys, one per caller.

  X-Doctor-Key  the doctor dashboard. Can do everything.
  X-Bot-Key     the parent-facing chatbot service. Can only log things for a
                guardian, read the medicine list for reminders, and upload slips.

Both are declared as API-key security schemes, so the /docs page shows an
Authorize button where each key is entered once.

This is a starting point, not finished security. Before real patient data goes in:
add real logins for doctors and a proper way to identify each parent (for example
an OTP sent to their phone), use HTTPS only, and rotate the keys.
"""
import os
import secrets

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

# auto_error=False: a missing key reaches our own check, which answers 401.
doctor_key_header = APIKeyHeader(
    name="X-Doctor-Key",
    scheme_name="DoctorKey",
    description="Key for the doctor dashboard (full access).",
    auto_error=False,
)
bot_key_header = APIKeyHeader(
    name="X-Bot-Key",
    scheme_name="BotKey",
    description="Key for the parent chatbot (logging and reading medicines only).",
    auto_error=False,
)


def _matches(provided: str | None, env_name: str) -> bool:
    expected = os.environ.get(env_name)
    if not expected or not provided:
        return False
    return secrets.compare_digest(provided.encode(), expected.encode())


def _require_configured() -> None:
    if not os.environ.get("DOCTOR_API_KEY"):
        # Fail closed: a server without a key must not accept anyone.
        raise HTTPException(503, "Server is missing DOCTOR_API_KEY")


def require_doctor(x_doctor_key: str | None = Security(doctor_key_header)) -> str:
    _require_configured()
    if not _matches(x_doctor_key, "DOCTOR_API_KEY"):
        raise HTTPException(401, "Doctor key missing or wrong")
    return "doctor"


def require_service(
    x_doctor_key: str | None = Security(doctor_key_header),
    x_bot_key: str | None = Security(bot_key_header),
) -> str:
    _require_configured()
    if _matches(x_doctor_key, "DOCTOR_API_KEY"):
        return "doctor"
    if _matches(x_bot_key, "BOT_API_KEY"):
        return "bot"
    raise HTTPException(401, "Key missing or wrong")

"""Parent login with a one-time code sent to their phone.

For the pilot there is no SMS service yet, so `send_code` prints the code in the
backend terminal (the doctor or you read it out to the parent). Replace send_code
with a real SMS or WhatsApp sender before going live.
"""
import hashlib
import logging
import secrets

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app import queries as q
from app.db import get_conn

log = logging.getLogger("clinic.parent_login")

MAX_CODES_PER_HOUR = 5
MAX_ATTEMPTS_PER_CODE = 5

bearer = HTTPBearer(auto_error=False, scheme_name="ParentToken", description="Token from /parent/auth/verify")


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def code_hash(phone: str, code: str) -> str:
    return sha256(f"{phone}:{code}")


def new_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def new_token() -> str:
    return secrets.token_urlsafe(32)


def send_code(phone: str, code: str) -> None:
    """Pilot delivery: print to the backend terminal. Swap for SMS/WhatsApp later.

    print() is used on purpose: logging output can be swallowed depending on how
    uvicorn configures logging, and the code must always be visible here.
    """
    print(f"\n>>> Parent login code for {phone}: {code} (valid 10 minutes)\n", flush=True)
    log.info("Login code sent to %s", phone)


def require_parent(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer),
    conn=Depends(get_conn),
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise HTTPException(401, "Please log in")
    guardian = conn.execute(q.SESSION_GUARDIAN, {"token_hash": sha256(credentials.credentials)}).fetchone()
    if guardian is None:
        raise HTTPException(401, "Your login has expired. Please log in again")
    guardian["token_hash"] = sha256(credentials.credentials)
    return guardian

"""Parent login with a one-time code sent to their phone.

The code goes out as an SMS (see app/sms.py). Without SMS set up, or if the phone
cannot be reached, the code is printed in the backend terminal instead.
"""
import hashlib
import logging
import secrets

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app import queries as q
from app.db import get_conn
from app.sms import enabled as sms_enabled
from app.sms import send_sms

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


def sms_text(code: str) -> str:
    return f"Clinic login code: {code}. Valid for 10 minutes. Do not share it with anyone."


def send_code(phone: str, code: str) -> None:
    """Send the code by SMS, or print it in the backend terminal when SMS is off or fails.

    print() is used on purpose: logging output can be swallowed depending on how
    uvicorn configures logging, and the code must always be visible here.
    """
    if sms_enabled():
        try:
            send_sms(phone, sms_text(code))
            log.info("Login code sent by SMS to %s", phone)
            return
        except Exception as e:  # a bad URL or an SMS problem must never break the login page
            log.error("Could not send the login code by SMS to %s: %s", phone, e)
    print(f"\n>>> Parent login code for {phone}: {code} (valid 10 minutes)\n", flush=True)
    log.info("Login code printed for %s", phone)


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

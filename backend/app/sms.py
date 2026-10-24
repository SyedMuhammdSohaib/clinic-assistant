"""SMS through the clinic's own Android phone, using the free SMS Gateway for Android
app (https://sms-gate.app). Set SMS_GATEWAY_URL, SMS_GATEWAY_USER and
SMS_GATEWAY_PASSWORD to turn it on. Without them, messages are printed in the backend
terminal instead.
"""
import base64
import ipaddress
import json
import logging
import os
import threading
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable

log = logging.getLogger("clinic.sms")


def enabled() -> bool:
    return bool(os.environ.get("SMS_GATEWAY_URL"))


def _opener_for(url: str) -> urllib.request.OpenerDirector:
    """A phone on the clinic's Wi-Fi is reached directly, never through a proxy set on the computer."""
    host = urllib.parse.urlsplit(url).hostname or ""
    try:
        local = ipaddress.ip_address(host).is_private
    except ValueError:
        local = host == "localhost"
    return urllib.request.build_opener(urllib.request.ProxyHandler({})) if local else urllib.request.build_opener()


def send_sms(phone: str, text: str) -> None:
    """Send one SMS and wait for the phone to take it. Raises OSError on failure."""
    url = os.environ["SMS_GATEWAY_URL"]
    user = os.environ.get("SMS_GATEWAY_USER", "")
    password = os.environ.get("SMS_GATEWAY_PASSWORD", "")
    auth = base64.b64encode(f"{user}:{password}".encode()).decode()
    req = urllib.request.Request(
        url,
        data=json.dumps({"textMessage": {"text": text}, "phoneNumbers": [f"+{phone}"]}).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Basic {auth}"},
        method="POST",
    )
    try:
        with _opener_for(url).open(req, timeout=15) as resp:
            resp.read()
    except urllib.error.HTTPError as e:
        raise OSError(f"SMS gateway error {e.code}: {e.read().decode(errors='replace')[:300]}") from e


def _dispatch(job: Callable[[], None]) -> None:
    """Run a send in the background so a slow phone never holds up the request. Tests replace this."""
    threading.Thread(target=job, daemon=True).start()


def notify(phone: str, text: str) -> None:
    """Send a notice by SMS without waiting for it; it never raises.

    When SMS is off or sending fails, the message is printed in the backend terminal.
    """
    def job() -> None:
        if enabled():
            try:
                send_sms(phone, text)
                log.info("SMS sent to %s", phone)
                return
            except Exception as e:  # an SMS problem must never break the request that caused it
                log.error("Could not send an SMS to %s: %s", phone, e)
        print(f"\n>>> SMS for {phone} (not sent): {text}\n", flush=True)

    _dispatch(job)

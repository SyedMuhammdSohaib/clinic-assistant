"""One-time local setup, run by setup.bat. Safe to run again.

    python scripts/setup_local.py ../run-backend.bat [--phone 03001234567]

Reads the settings from run-backend.bat, creates the database and its tables if they
are missing, writes dashboard/.env.local with the same doctor key, and, when a phone
number is given, registers it as a parent of a demo child so you can log in to the
parent app straight away.
"""
import argparse
import os
import pathlib
import re
import sys

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

BACKEND = pathlib.Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

SCHEMA = BACKEND / "db" / "schema.sql"
MIGRATIONS = sorted((BACKEND / "db" / "migrations").glob("*.sql"))
PLACEHOLDERS = ("YOUR_DB_PASSWORD", "choose-a-long-random-key", "choose-another-long-random-key")


def fail(message: str) -> None:
    print(f"\nXXX {message}\n")
    sys.exit(1)


def read_bat(path: pathlib.Path) -> dict[str, str]:
    """The values of the `set "NAME=value"` lines in a .bat file."""
    if not path.exists():
        fail(f"{path.name} nahi mili. Pehle run-backend.example.bat se run-backend.bat banayein.")
    values = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r'\s*set\s+"([A-Z_]+)=(.*)"\s*$', line, re.IGNORECASE)
        if m:
            # cmd turns %% into %, so a password written as abc%%401 reaches the app as abc%401.
            values[m.group(1).upper()] = m.group(2).replace("%%", "%")
    return values


def check_settings(settings: dict[str, str]) -> None:
    for name in ("DATABASE_URL", "DOCTOR_API_KEY", "BOT_API_KEY"):
        value = settings.get(name, "")
        if not value:
            fail(f"run-backend.bat mein {name} khaali hai. Use bhar ke setup.bat dobara chalayein.")
        if any(p in value for p in PLACEHOLDERS):
            fail(f"run-backend.bat mein {name} abhi namune wali value hai. Apni value likhein.")


def create_database(url: str) -> None:
    try:
        info = conninfo_to_dict(url)
    except psycopg.ProgrammingError:
        fail("DATABASE_URL theek nahi likha. Password mein @ ho to run-backend.bat mein us ki jagah %%40 likhein.")
    dbname = info.get("dbname") or "clinic"
    admin_url = make_conninfo(url, dbname="postgres")
    try:
        with psycopg.connect(admin_url, autocommit=True) as conn:
            exists = conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,)).fetchone()
            if exists:
                print(f"OK  Database '{dbname}' pehle se bana hua hai")
            else:
                conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
                print(f"OK  Database '{dbname}' bana diya")
    except psycopg.OperationalError as e:
        text = str(e)
        if "password authentication failed" in text:
            fail("Database ka password ghalat hai. run-backend.bat mein DATABASE_URL ka password theek karein.")
        if "Connection refused" in text or "could not connect" in text or "connection failed" in text:
            fail("Database band hai. Windows + R -> services.msc -> postgresql -> Start dabayein.")
        fail(f"Database se rabta nahi ho saka: {text}")


def create_tables(url: str) -> None:
    with psycopg.connect(url, autocommit=True) as conn:
        has_tables = conn.execute("SELECT to_regclass('public.doctors') IS NOT NULL AS ok").fetchone()[0]
        if not has_tables:
            conn.execute(SCHEMA.read_text(encoding="utf-8"))
            print("OK  Tables bana diye")
        for migration in MIGRATIONS:
            conn.execute(migration.read_text(encoding="utf-8"))
        if has_tables:
            print("OK  Tables pehle se bane hue the, naye hisse jod diye")


def write_dashboard_env(doctor_key: str) -> None:
    env = ROOT / "dashboard" / ".env.local"
    example = ROOT / "dashboard" / ".env.local.example"
    text = env.read_text(encoding="utf-8") if env.exists() else example.read_text(encoding="utf-8")
    new_text = re.sub(r"(?m)^DOCTOR_API_KEY=.*$", f"DOCTOR_API_KEY={doctor_key}", text)
    if env.exists() and new_text == text:
        print("OK  dashboard\\.env.local pehle se theek hai")
        return
    env.write_text(new_text, encoding="utf-8")
    print("OK  dashboard\\.env.local mein doctor key likh di")


def register_phone(phone: str) -> None:
    """Make sure the phone belongs to a parent of some child, adding a demo doctor and child if needed."""
    from fastapi.testclient import TestClient

    from app.main import app

    headers = {"X-Doctor-Key": os.environ["DOCTOR_API_KEY"]}
    with TestClient(app) as client:
        patients = client.get("/patients", headers=headers).json()
        if patients:
            child = patients[0]
        else:
            doctor = client.post("/doctors", headers=headers, json={
                "full_name": "Demo Doctor", "email": "demo-doctor@example.com"})
            if doctor.status_code != 201:
                fail(f"Demo doctor nahi ban saka: {doctor.text}")
            child = client.post("/patients", headers=headers, json={
                "doctor_id": doctor.json()["id"], "full_name": "Demo Child", "date_of_birth": "2020-05-01"})
            if child.status_code != 201:
                fail(f"Demo bacha nahi ban saka: {child.text}")
            child = child.json()
            print("OK  Demo doctor aur 'Demo Child' bana diye")
        guardian = client.post(f"/patients/{child['id']}/guardians", headers=headers, json={
            "full_name": "Test Parent", "phone": phone, "relation": "parent", "is_primary": True})
        if guardian.status_code == 422:
            fail("Phone number theek nahi. Is tarah likhein: 03001234567")
        if guardian.status_code != 201:
            fail(f"Number save nahi ho saka: {guardian.text}")
        print(f"OK  Number {phone} '{child['full_name']}' ke parent ke taur par save ho gaya")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bat_file")
    parser.add_argument("--phone", default="")
    args = parser.parse_args()

    settings = read_bat(pathlib.Path(args.bat_file))
    check_settings(settings)
    os.environ.update({k: v for k, v in settings.items() if v})

    create_database(settings["DATABASE_URL"])
    create_tables(settings["DATABASE_URL"])
    write_dashboard_env(settings["DOCTOR_API_KEY"])
    phone = re.sub(r"[\s()-]", "", args.phone)  # "0300-123 4567" -> "03001234567"
    if phone:
        register_phone(phone)


if __name__ == "__main__":
    main()

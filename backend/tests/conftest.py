"""Test setup.

The API tests need a real PostgreSQL database. Point TEST_DATABASE_URL at an empty,
throwaway database whose name ends in _test. The tests wipe it. Example:

    createdb clinic_test
    export TEST_DATABASE_URL=postgresql://localhost/clinic_test
    pytest

The unit tests (test_unit.py) need no database.
"""
import os
import pathlib
import tempfile

import psycopg
import pytest
from psycopg.conninfo import conninfo_to_dict

SCHEMA = pathlib.Path(__file__).resolve().parents[1] / "db" / "schema.sql"

os.environ["DOCTOR_API_KEY"] = "test-doctor-key"
os.environ["BOT_API_KEY"] = "test-bot-key"
os.environ.setdefault("CLINIC_TZ", "Asia/Karachi")
# API tests never call a real AI service; the AI layer itself is tested in test_ai.py.
os.environ["AI_PROVIDER"] = "offline"
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp(prefix="clinic-test-uploads-")


def _test_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        raise pytest.UsageError(
            "Set TEST_DATABASE_URL to a throwaway database whose name ends in _test"
        )
    if not conninfo_to_dict(url).get("dbname", "").endswith("_test"):
        # The tests drop everything in the database. Refuse anything that is not clearly a test one.
        raise pytest.UsageError("TEST_DATABASE_URL must point at a database whose name ends in _test")
    return url


@pytest.fixture(scope="session")
def database():
    url = _test_url()
    os.environ["DATABASE_URL"] = url
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute("DROP SCHEMA public CASCADE")
        conn.execute("CREATE SCHEMA public")
        conn.execute(SCHEMA.read_text())
    return url


@pytest.fixture
def client(database):
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
    with psycopg.connect(database, autocommit=True) as conn:
        conn.execute("TRUNCATE doctors, guardians, login_codes, audit_log RESTART IDENTITY CASCADE")

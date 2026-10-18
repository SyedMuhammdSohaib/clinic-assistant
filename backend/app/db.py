"""Database connection: one connection per request.

Routes call conn.commit() themselves when they want to save. If a route raises
before that, the connection is closed and PostgreSQL throws the half-done work
away, so a failed request never leaves partial data behind.

For more traffic later, swap this for psycopg_pool.ConnectionPool.
"""
import os
from collections.abc import Iterator

import psycopg
from psycopg.rows import dict_row


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return url


def get_conn() -> Iterator[psycopg.Connection]:
    conn = psycopg.connect(database_url(), row_factory=dict_row)
    try:
        yield conn
    finally:
        conn.close()

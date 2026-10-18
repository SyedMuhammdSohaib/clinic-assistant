"""Load the doctor's approved answers (db/faq.json) into the database.

    python scripts/load_faq.py --doctor-email test2@example.com

Only entries with "published": true are shown to parents. Run it again after
editing faq.json; existing answers are updated, not duplicated.
"""
import argparse
import json
import pathlib
import sys

import psycopg
from psycopg.rows import dict_row

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import queries as q  # noqa: E402
from app.db import database_url  # noqa: E402

PLACEHOLDER_MARKERS = ("[Doctor", "[ڈاکٹر")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    who = parser.add_mutually_exclusive_group(required=True)
    who.add_argument("--doctor-email")
    who.add_argument("--doctor-id")
    parser.add_argument("--file", default=str(ROOT / "db" / "faq.json"))
    args = parser.parse_args()

    entries = json.loads(pathlib.Path(args.file).read_text(encoding="utf-8"))
    with psycopg.connect(database_url(), row_factory=dict_row) as conn:
        if args.doctor_email:
            row = conn.execute(q.DOCTOR_BY_EMAIL, {"email": args.doctor_email}).fetchone()
            if row is None:
                print(f"No doctor with email {args.doctor_email}")
                return 1
            doctor_id = row["id"]
        else:
            doctor_id = args.doctor_id

        for order, e in enumerate(entries):
            text = e["answer_en"] + e["answer_ur"]
            published = bool(e.get("published"))
            if published and any(m in text for m in PLACEHOLDER_MARKERS):
                # A blank the doctor has not filled must never reach a parent.
                print(f"  {e['topic']}: still has a [Doctor: ...] blank, kept hidden")
                published = False
            saved = conn.execute(
                q.UPSERT_FAQ,
                {
                    "doctor_id": doctor_id,
                    "topic": e["topic"],
                    "question_en": e["question_en"],
                    "question_ur": e["question_ur"],
                    "answer_en": e["answer_en"],
                    "answer_ur": e["answer_ur"],
                    "is_published": published,
                    "sort_order": order,
                },
            ).fetchone()
            print(f"  {saved['topic']}: {'shown to parents' if saved['is_published'] else 'hidden'}")
        conn.commit()
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

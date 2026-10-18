"""Check that the Gemini key and model work, without starting the app.

    python scripts/check_ai.py

Uses the same settings as the app (GEMINI_API_KEY, GEMINI_MODEL, GEMINI_EMBED_MODEL).
Sends only a made-up sentence, never patient data.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.ai.provider import AIError, get_provider  # noqa: E402


def main() -> int:
    try:
        p = get_provider()
    except AIError as e:
        print("FAIL:", e)
        return 1
    if p.name == "offline":
        print("AI is OFF: GEMINI_API_KEY is not set in this window.")
        print("Run the 'set GEMINI_API_KEY=...' line from run-backend.bat here first.")
        return 1
    print(f"Key found ({len(p.api_key)} characters). Model: {p.model}. Embeddings: {p.embed_model}")

    ok = True
    try:
        reply = p.generate_json('Reply with JSON {"ok": true}', {"type": "OBJECT", "properties": {"ok": {"type": "BOOLEAN"}}, "required": ["ok"]})
        print("1. Text model:  OK", reply)
    except AIError as e:
        ok = False
        print("1. Text model:  FAIL ->", e)
    try:
        v = p.embed(["Should I record the seizure on video?"], kind="query")[0]
        print(f"2. Embeddings:  OK ({len(v)} numbers)")
    except AIError as e:
        ok = False
        print("2. Embeddings:  FAIL ->", e)
    print("All good. Restart the backend and try the app." if ok else "Something failed; send the FAIL line(s).")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

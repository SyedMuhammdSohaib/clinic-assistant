"""Measure how well the AI reads parents' messages and matches their questions.

    python -m evals.run                      # uses Gemini if GEMINI_API_KEY is set, else offline rules
    python -m evals.run --provider offline   # the keyword-rules baseline
    python -m evals.run --provider gemini

Writes evals/reports/<provider>.md. No database needed.

Seizure messages: each field is scored separately against the expected value; a
duration counts as right within 10 percent (at least 5 seconds).
Questions: the safety number is "wrong answers shown", an approved answer shown for a
question it does not answer. A missed match is less serious: the question goes to the doctor.
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.ai import faq_match, seizure_text  # noqa: E402
from app.ai.provider import get_provider  # noqa: E402

NOW = datetime(2026, 10, 14, 16, 0, tzinfo=ZoneInfo("Asia/Karachi"))
FIELDS = ("is_report", "date", "duration_seconds", "seizure_type", "fever_present", "went_to_er")


def load(name: str) -> list[dict]:
    with open(ROOT / "evals" / name, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def duration_ok(got, want) -> bool:
    if want is None or got is None:
        return got is want
    return abs(got - want) <= max(5, 0.1 * want)


def run_seizures(provider, pause: float) -> dict:
    cases = load("seizure_cases.jsonl")
    scores = {f: 0 for f in FIELDS}
    failures = []
    for case in cases:
        exp = case["expect"]
        res = seizure_text.extract(case["text"], NOW, provider)
        d = res["draft"]
        report = exp.get("report", True)
        got = {
            "is_report": res["is_seizure_report"],
            "date": d["occurred_at"].date().isoformat() if d["occurred_at"] else None,
            "duration_seconds": d["duration_seconds"],
            # "Seizure of unknown kind" and "kind not given" mean the same to the form.
            "seizure_type": (d["seizure_type"] or "unknown") if report else d["seizure_type"],
            "fever_present": d["fever_present"],
            "went_to_er": d["went_to_er"],
        }
        want = {"is_report": report, **{k: exp[k] for k in FIELDS if k != "is_report"}}
        if report and want["seizure_type"] is None:
            want["seizure_type"] = "unknown"
        wrong = []
        for f in FIELDS:
            ok = duration_ok(got[f], want[f]) if f == "duration_seconds" else got[f] == want[f]
            if not report and f != "is_report":
                ok = True  # for non-reports only the "is it a report" call matters
            scores[f] += ok
            if not ok:
                wrong.append(f"{f}: got {got[f]!r}, expected {want[f]!r}")
        if wrong:
            failures.append((case["id"], case["text"], wrong, res["source"]))
        time.sleep(pause)
    n = len(cases)
    return {"n": n, "per_field": {f: scores[f] / n for f in FIELDS},
            "all_fields_right": (n - len(failures)) / n, "failures": failures}


def run_faq(provider, pause: float) -> dict:
    faqs = [{**e, "id": e["topic"]} for e in json.loads((ROOT / "db" / "faq.json").read_text(encoding="utf-8"))
            if e["published"]]
    cases = load("faq_cases.jsonl")
    right = wrong_shown = missed = 0
    failures = []
    for case in cases:
        found = faq_match.match(None, faqs, case["question"], provider)
        got = found["topic"] if found else None
        want = case["expect"]
        if got == want:
            right += 1
        elif got is None:
            missed += 1
            failures.append((case["id"], case["question"], f"missed (expected {want})"))
        else:
            wrong_shown += 1
            failures.append((case["id"], case["question"], f"WRONG ANSWER SHOWN: {got} (expected {want})"))
        time.sleep(pause)
    n = len(cases)
    return {"n": n, "accuracy": right / n, "wrong_shown": wrong_shown, "missed": missed, "failures": failures}


def pct(x: float) -> str:
    return f"{100 * x:.0f}%"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", choices=["auto", "gemini", "offline"], default="auto")
    ap.add_argument("--suite", choices=["all", "seizure", "faq"], default="all")
    ap.add_argument("--pause", type=float, default=None, help="seconds between AI calls (free-tier limits)")
    args = ap.parse_args()
    if args.provider != "auto":
        os.environ["AI_PROVIDER"] = args.provider
    provider = get_provider()
    pause = args.pause if args.pause is not None else (0 if provider.name == "offline" else 4.0)
    model = getattr(provider, "model", "keyword rules")

    lines = [f"# Evaluation: {provider.name} ({model})", "",
             f"Run {datetime.now().strftime('%Y-%m-%d %H:%M')}. Reference time for the messages: {NOW.isoformat()}.", ""]

    if args.suite in ("all", "seizure"):
        r = run_seizures(provider, pause)
        lines += [f"## Reading seizure messages ({r['n']} messages: Roman Urdu, Urdu, English)", "",
                  "| Field | Right |", "|---|---|"]
        lines += [f"| {f} | {pct(v)} |" for f, v in r["per_field"].items()]
        lines += [f"| **every field right** | **{pct(r['all_fields_right'])}** |", ""]
        if r["failures"]:
            lines += ["Misses:", ""] + [f"- `{i}` {t} ({src}): " + "; ".join(w) for i, t, w, src in r["failures"]] + [""]
        print(f"seizure: every field right {pct(r['all_fields_right'])}; " +
              ", ".join(f"{f} {pct(v)}" for f, v in r["per_field"].items()))

    if args.suite in ("all", "faq"):
        r = run_faq(provider, pause)
        lines += [f"## Matching questions to approved answers ({r['n']} questions, 10 with no approved answer)", "",
                  "| Measure | Result |", "|---|---|",
                  f"| Right (answer or correctly sent to doctor) | {pct(r['accuracy'])} |",
                  f"| **Wrong answer shown (safety)** | **{r['wrong_shown']}** |",
                  f"| Missed, sent to doctor instead | {r['missed']} |", ""]
        if r["failures"]:
            lines += ["Misses:", ""] + [f"- `{i}` {q}: {w}" for i, q, w in r["failures"]] + [""]
        print(f"faq: right {pct(r['accuracy'])}, wrong answers shown {r['wrong_shown']}, missed {r['missed']}")

    out = ROOT / "evals" / "reports" / f"{provider.name}.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"report: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Evaluations

How well does the AI read parents' messages and match their questions? These sets
measure it, so a change of model or prompt is judged by numbers, not by feel.

```
python -m evals.run --provider offline   # keyword-rules baseline, no key needed
python -m evals.run --provider gemini    # needs GEMINI_API_KEY; about 2 minutes on the free tier
```

Reports are written to `evals/reports/<provider>.md`.

## The sets

| File | Cases | What is checked |
|---|---|---|
| `seizure_cases.jsonl` | 30 messages in Roman Urdu, Urdu and English, incl. negations ("bukhar nahi"), ranges ("2-3 minute"), messages that are not seizure reports, and a prompt-injection attempt | date, duration (within 10%), kind, fever, emergency visit, "is this a report" |
| `faq_cases.jsonl` | 30 questions: 20 that an approved answer covers, 10 that none does (including topics whose answers the doctor has not approved yet) | the right answer, or correctly none |

For questions the key safety number is **wrong answers shown**: an approved answer shown
for a question it does not answer. It must stay at 0. A miss is less serious: the
question goes to the doctor.

## Offline baseline

| Measure | Result |
|---|---|
| Seizure messages, every field right | 83% |
| Questions answered or correctly routed | 57% |
| Wrong answers shown | 0 |
| Questions missed (sent to doctor) | 13 of 20 |

Read these with care: the keyword rules and the matching threshold were written while
looking at these same cases, so the baseline is flattering. The baseline mostly misses
questions phrased differently from the approved ones; that gap is what the AI is for.
Run the Gemini evaluation and add its numbers here.

## Adding cases

Add real-sounding messages, especially the ones the system got wrong. Never put real
patient data in these files.

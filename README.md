# Clinic Assistant: pediatric epilepsy care

A two-sided app for a child neurology clinic. Parents log seizures and medicine doses from
their phone in Urdu or English. The doctor sees each child's history, red-flag alerts
and a pre-visit summary on a dashboard. AI helps with the slow parts: turning a parent's
message into a form, finding the doctor's approved answer to a question, and reading a
prescription photo. The doctor keeps control of every medical decision.

> **Portfolio project.** Built as a working demo with made-up data. It is not deployed
> and has never held real patient records.

![Parent app home](docs/screenshots/02-parent-home.png)

## What it does

**Parent app** (mobile web, Urdu RTL and English, served by the backend at `/app/`)
- Log a seizure: when, how long, what it looked like, fever, ER visit.
- **AI:** write it in your own words ("kal raat 2 minute jhatke aaye, bukhar bhi tha") and the form fills itself. The parent checks it and saves.
- Today's medicines: mark each dose as given, late, missed or vomited.
- Questions: shows only answers the doctor approved. **AI** matches a question in the parent's own words to an approved answer; anything else goes to the doctor.
- **AI:** photo of a prescription slip. Medicines are read from it and sent to the doctor to approve.
- "Seizure happening now" screen with first aid and a 1122 call button.
- Phone number + one-time code login (code sent by SMS from the clinic's Android phone).

**Doctor dashboard** (Next.js)
- Patient list, children with unseen red flags first.
- Per-child timeline: seizures, medicine changes, drips (IV infusions), hospital visits.
- Red-flag rules, e.g. a seizure of 5 minutes or longer, or N seizures in H hours.
- 12-week seizure chart with medicine changes, 30-day dose adherence.
- Change a dose (the only place doses change), answer parents' questions, review slip photos.
- Printable pre-visit summary.

| AI form fill | Question → approved answer | Prescription photo |
|---|---|---|
| ![](docs/screenshots/03-ai-fill-form.png) | ![](docs/screenshots/05-ai-question-match.png) | ![](docs/screenshots/07-ai-slip-reading.png) |

| Dashboard | Slip review |
|---|---|
| ![](docs/screenshots/10-dashboard-timeline.png) | ![](docs/screenshots/08-dashboard-slip-review.png) |

## How it is built

```mermaid
flowchart LR
  P[Parent app<br/>HTML/JS, Urdu + English] -->|Bearer session| API
  D[Doctor dashboard<br/>Next.js 15, server components] -->|doctor key, server side only| API
  API[FastAPI backend] --> DB[(PostgreSQL)]
  API -->|redacted text, photos| G[Google Gemini<br/>free tier]
  API -.->|no key or AI fails| R[Keyword rules +<br/>local embeddings]
```

| Part | Tech |
|---|---|
| Backend | Python, FastAPI, Pydantic v2, psycopg 3 |
| Database | PostgreSQL (views for timeline and adherence) |
| Doctor dashboard | Next.js 15, React 19, TypeScript |
| Parent app | Plain HTML, CSS, JavaScript, no build step |
| AI | Google Gemini: structured JSON output, vision, embeddings |
| Tests | pytest, 65 tests including a fake Gemini server |

## AI design: where it helps and where it is not allowed

| Feature | AI does | AI never does |
|---|---|---|
| Seizure message → form | Extracts time, duration, type, fever into a fixed JSON schema | Saves anything. The parent reviews the draft; the doctor's rules run on the saved values |
| Question → answer (RAG) | Embeds the question, finds the 3 closest approved answers, picks one or none | Writes an answer. The parent sees the doctor's text word for word |
| Prescription photo | Reads drug, dose and frequency (OD/BD/TDS) | Changes the medicine list. The doctor compares with the photo and approves each item |

Safety measures:
- **Redaction:** names, phone numbers, CNIC and emails are removed before text is sent to the model.
- **Prompt-injection fencing:** parent text is wrapped in markers and marked as data; outputs must match a schema, and impossible values (future times, negative durations) are dropped.
- **Graceful fallback:** with no key, a reached rate limit or any error, the app falls back to keyword rules or sends the item to the doctor, and logs the reason.
- **Unsure means "ask the doctor":** a question is only matched when the model is confident; otherwise it is routed to the doctor.

## Evaluation

Two test sets in `backend/evals/`: 30 seizure messages (Roman Urdu, Urdu, English,
including negations, ranges and a prompt-injection attempt) and 30 parent questions
(20 covered by an approved answer, 10 not). The key safety number is **wrong answers
shown**, which must stay at 0.

| Measure | Keyword rules (baseline) |
|---|---|
| Seizure messages, every field right | 83% |
| Questions answered or correctly routed | 57% |
| Wrong answers shown | 0 |

The baseline is flattering: its rules were written while looking at these same cases.
Run `python -m evals.run --provider gemini` to score the AI; see
[`backend/evals/README.md`](backend/evals/README.md).

## Run it locally

Needs Python 3.11+, Node 20+, PostgreSQL 16+.

```bash
# 1. Database
createdb clinic
psql -d clinic -f backend/db/schema.sql

# 2. Backend
cd backend
python -m venv .venv && .venv\Scripts\activate      # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
# set DATABASE_URL, DOCTOR_API_KEY, BOT_API_KEY (and optionally GEMINI_API_KEY); see .env.example
uvicorn app.main:app --reload                        # parent app: http://127.0.0.1:8000/app/

# 3. Dashboard (new terminal)
cd dashboard
npm install
copy .env.local.example .env.local                   # same DOCTOR_API_KEY as the backend
npm run dev                                          # http://localhost:3000
```

On Windows, copy `run-backend.example.bat` to `run-backend.bat`, fill in your values, and
double-click `start.bat` to start everything. Details: [`backend/README.md`](backend/README.md),
[`dashboard/README.md`](dashboard/README.md).

Tests (need a throwaway database whose name ends in `_test`):

```bash
cd backend
createdb clinic_test
set TEST_DATABASE_URL=postgresql://postgres:PASSWORD@localhost/clinic_test
pytest
```

## Limits (what a real deployment would still need)

- Login codes go by SMS from the clinic's own Android phone (free, see [`backend/README.md`](backend/README.md#login-codes-by-sms-free)); that phone must stay on. A paid SMS or WhatsApp service would be more reliable at scale.
- The doctor side uses a shared API key, not individual logins.
- No hosting, HTTPS, backups or encryption at rest.
- On Gemini's free tier, Google may use the data to improve its products, so only demo data should be sent. Real patients would need a paid plan with a data agreement and the clinic's consent.

## License

MIT

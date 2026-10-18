# Clinic assistant API

Backend for a pediatric neurology clinic assistant (FastAPI + PostgreSQL). It stores a
child's seizures, medicines, dose changes, drips and hospital visits, applies the doctor's
red-flag rules, and feeds the doctor dashboard. The bot only records and reminds. Only the
doctor changes doses.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

createdb clinic
psql clinic -f db/schema.sql

cp .env.example .env        # fill in DATABASE_URL and the two keys, then load it:
set -a && source .env && set +a

uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for the interactive API. Click Authorize (top right) and enter the doctor key once.

## Run the tests

```bash
createdb clinic_test        # the name must end in _test; the tests wipe it
export TEST_DATABASE_URL=postgresql://localhost/clinic_test
pytest
```

`tests/test_unit.py` needs no database. `tests/test_api.py` runs the whole API against the
test database.

## Who can call what

| Key (header)       | Used by                 | Allowed |
|--------------------|-------------------------|---------|
| `X-Doctor-Key`     | the doctor dashboard    | everything |
| `X-Bot-Key`        | the parent chatbot      | log seizures, drips, visits, side effects and doses; read the medicine list; upload and confirm slips |

Anything a parent logs starts as `verified_by_doctor = false` until the doctor verifies it.
`doctor_notes` and the diagnosis are never reachable with the bot key.

## Endpoints

| Method and path | Key | What it does |
|---|---|---|
| `GET /health` | none | server and database check |
| `POST /doctors` | doctor | create a doctor (also adds the default red-flag rule) |
| `POST /patients`, `GET /patients`, `GET /patients/{id}` | doctor | patients; the list shows unseen red flags |
| `POST /patients/{id}/guardians` | doctor | add a parent (a phone number identifies a guardian) |
| `POST /patients/{id}/medications` | doctor | add a medicine (also writes its "started" history line) |
| `GET /patients/{id}/medications?status=active\|all` | doctor or bot | medicines with 30-day adherence |
| `POST /medications/{id}/changes` | doctor | dose up or down, frequency, pause, resume, stop |
| `POST /medications/{id}/adherence` | doctor or bot | dose taken, late, missed or vomited (same slot updates) |
| `POST /patients/{id}/seizures` | doctor or bot | log a seizure; the reply says if a red flag fired |
| `POST /patients/{id}/iv-infusions`, `/hospital-visits`, `/side-effects` | doctor or bot | parent-logged events |
| `POST /patients/{id}/allergies` | doctor | allergy (saved as verified) |
| `GET /patients/{id}/timeline?limit=&before=` | doctor | seizures, medicine changes, drips and visits, newest first |
| `POST /verify/{kind}/{row_id}` | doctor | mark an entry as checked; `kind` comes from the timeline row |
| `GET /patients/{id}/red-flags`, `POST /red-flag-events/{id}/seen` | doctor | review red flags |
| `POST /doctors/{id}/red-flag-rules` | doctor | add a rule: a duration threshold or a cluster |
| `GET /patients/{id}/previsit?since=YYYY-MM-DD` | doctor | data for the pre-visit summary |
| `POST /patients/{id}/prescription-uploads` | doctor or bot | store a slip photo link and what was read from it |
| `POST /prescription-uploads/{id}/confirm` | doctor or bot | the parent confirms the reading |
| `POST /prescription-uploads/{id}/approve`, `/reject` | doctor | approve (creates the medicines you list) or reject with a reason |

## Red-flag rules

Every new doctor gets one default rule, "Seizure of 5 minutes or longer (default, please
confirm)". The doctor should confirm or change it, and add their own with
`POST /doctors/{id}/red-flag-rules`:

```json
{"name": "Three seizures in a day",
 "condition": {"kind": "cluster", "event": "seizure", "count_gte": 3, "within_hours": 24},
 "message_ur": "...", "message_en": "..."}
```

A duration rule does not fire when the duration is missing, so the chat layer should ask the
parent how long it lasted.

## Parent app

The parent app is served by this same server at http://127.0.0.1:8000/app/ (plain HTML and
JavaScript in `app/static/parent/`, no build step). Urdu and English.

- **Login:** the parent enters the phone number the doctor saved; a 6-digit code is sent.
  For the pilot there is no SMS service, so the code is **printed in the backend terminal**
  (`Parent login code for 923001234567: 123456`). Replace `send_code` in
  `app/parent_auth.py` with an SMS or WhatsApp sender before going live. Codes last 10
  minutes, 5 codes per hour per number, 5 wrong tries per code. Sessions last 30 days.
- **Screens:** seizure happening now (first aid + 1122), record a seizure (red flag screen
  when a rule fires), today's medicines (given / late / not given / vomited), questions
  (only published answers; anything else goes to the doctor), side effects.
- **Approved answers:** `db/faq.json`. Load them with
  `python scripts/load_faq.py --doctor-email <doctor's email>`. Only entries with
  `"published": true` and no `[Doctor: ...]` blank are shown to parents.

Existing database from the first version: run `db/migrations/002_parent_app.sql` once.

| Method and path | Auth | What it does |
|---|---|---|
| `POST /parent/auth/request-code`, `/parent/auth/verify`, `/parent/auth/logout` | none / token | login |
| `GET /parent/me` | parent token | the parent and their children (no diagnosis or notes) |
| `GET /parent/children/{id}/today` | parent token | today's dose times and what was logged |
| `POST /parent/children/{id}/doses`, `/seizures`, `/side-effects` | parent token | log |
| `GET /parent/children/{id}/faq` | parent token | published approved answers |
| `GET`/`POST /parent/children/{id}/questions` | parent token | ask the doctor, see answers |
| `GET /patients/{id}/questions`, `POST /questions/{id}/answer` | doctor | answer parents' questions |

To open it on a phone on the same Wi-Fi, start the server with
`uvicorn app.main:app --host 0.0.0.0 --port 8000` and open `http://<computer's IP>:8000/app/`.
That is for testing only: real parents need it online over HTTPS.

## AI features

All optional: without `GEMINI_API_KEY` the app uses simple keyword rules and still works.
Get a free key at https://aistudio.google.com/apikey and set `GEMINI_API_KEY` (see `.env.example`).

| Feature | Endpoint | Safety design |
|---|---|---|
| Seizure in the parent's own words (Urdu, Roman Urdu, English) | `POST /parent/children/{id}/ai/seizure-draft` | Returns a draft only. The parent checks it in the form and saves; the doctor's red-flag rules run on the saved values. Unclear fields stay empty. Impossible values (future time, negative duration) are dropped. |
| Question to approved answer (retrieval) | `POST /parent/children/{id}/ai/match-question` | Embeddings find the closest approved answers, the model only picks one or none. The parent sees the doctor's text word for word; nothing is generated. No match: the question goes to the doctor. |
| Prescription photo | `POST /parent/children/{id}/slips` (+ `/confirm`), doctor: `GET /patients/{id}/prescription-uploads`, `GET /prescription-uploads/{id}/image` | The reading is a suggestion. The parent confirms, the doctor compares it with the photo on the dashboard and approves each medicine. |

Also:
- **Redaction:** names, phone numbers, CNIC and emails are removed before text goes to the AI (`app/ai/redact.py`). Photos cannot be redacted.
- **Prompt injection:** parent text is fenced and marked as data in every prompt; outputs are validated with fixed schemas.
- **Fallbacks:** if the AI fails or the free limit is reached, the app falls back to the rules or sends things to the doctor.
- **Evaluation:** `python -m evals.run` scores the AI on 30 seizure messages and 30 questions; see `evals/README.md`.
- **Privacy:** on Gemini's free tier, Google may use what you send to improve its products. Use made-up demo data only.

Existing database: run `db/migrations/003_ai.sql` once.

## What is not here yet

- Medicine reminders sent to the phone (the app shows today's doses, but does not notify).
- SMS delivery of login codes (printed in the terminal for now).
- Real security for the doctor side. Two shared keys are a start, not enough for real patient
  data. Add doctor logins, HTTPS only, key rotation, backups and encrypted storage. Check the
  data-protection and medical-record rules that apply to the clinic before storing real
  children's records.
- Image storage. Slips are stored as a link; you host the photos.
- Several clinics. Right now one doctor key sees every patient.

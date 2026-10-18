-- =====================================================================
-- Pediatric Neurology Clinic Assistant: database schema (PostgreSQL 13+)
-- Covers: patients, medicines, medicine changes, adherence, IV drips,
-- hospital visits, seizures, prescription photos, safety red flags,
-- and the doctor-approved answers the chatbot is allowed to use.
--
-- Design rules:
--   1. The bot only RECORDS and REMINDS. It never writes a dose on its own.
--   2. Every clinical row has verified_by_doctor so wrong data is visible.
--   3. Nothing is hard-deleted from clinical tables (use status/ended_on).
-- =====================================================================

BEGIN;

-- ---------- People ---------------------------------------------------

CREATE TABLE doctors (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name       text NOT NULL,
    email           text UNIQUE NOT NULL,
    phone           text,
    clinic_name     text,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE patients (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    doctor_id           uuid NOT NULL REFERENCES doctors(id),
    full_name           text NOT NULL,
    date_of_birth       date NOT NULL,
    sex                 text CHECK (sex IN ('male', 'female', 'other')),
    weight_kg           numeric(5,2),
    weight_updated_on   date,
    diagnosis           text,                 -- entered by the doctor only
    doctor_notes        text,                 -- private to the doctor
    preferred_language  text NOT NULL DEFAULT 'ur'
                        CHECK (preferred_language IN ('ur', 'roman_ur', 'en')),
    is_active           boolean NOT NULL DEFAULT true,
    created_at          timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE guardians (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name       text NOT NULL,
    phone           text UNIQUE NOT NULL,     -- used to log in / chat
    relation        text,                     -- mother, father, grandmother...
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE patient_guardians (
    patient_id      uuid NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    guardian_id     uuid NOT NULL REFERENCES guardians(id) ON DELETE CASCADE,
    is_primary      boolean NOT NULL DEFAULT false,
    PRIMARY KEY (patient_id, guardian_id)
);

-- ---------- Medicines ------------------------------------------------

CREATE TABLE medications (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id          uuid NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    drug_name           text NOT NULL,
    dose_amount         numeric(8,2) NOT NULL,
    dose_unit           text NOT NULL,        -- mg, ml, tablet, drops...
    times_per_day       smallint NOT NULL CHECK (times_per_day BETWEEN 1 AND 12),
    dose_times          time[],               -- e.g. {08:00, 20:00} for reminders
    route               text DEFAULT 'oral',  -- oral, IV, IM, rectal...
    reason              text,                 -- why it was prescribed
    prescribed_by       text,                 -- doctor name (can be another doctor)
    started_on          date NOT NULL,
    ended_on            date,
    status              text NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'stopped', 'paused')),
    source              text NOT NULL DEFAULT 'doctor'
                        CHECK (source IN ('doctor', 'parent', 'prescription_photo')),
    verified_by_doctor  boolean NOT NULL DEFAULT false,
    verified_at         timestamptz,
    created_at          timestamptz NOT NULL DEFAULT now(),
    CHECK (ended_on IS NULL OR ended_on >= started_on)
);

-- Full history of every start / dose change / stop for a medicine.
CREATE TABLE medication_changes (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    medication_id       uuid NOT NULL REFERENCES medications(id) ON DELETE CASCADE,
    changed_on          date NOT NULL,
    change_type         text NOT NULL
                        CHECK (change_type IN
                          ('started', 'dose_increased', 'dose_decreased',
                           'frequency_changed', 'paused', 'resumed',
                           'stopped', 'switched')),
    old_dose_amount     numeric(8,2),
    new_dose_amount     numeric(8,2),
    old_times_per_day   smallint,
    new_times_per_day   smallint,
    reason              text,
    changed_by          text,                 -- doctor who decided
    verified_by_doctor  boolean NOT NULL DEFAULT false,
    created_at          timestamptz NOT NULL DEFAULT now()
);

-- Daily "dose given / missed" confirmations from the parent chat.
CREATE TABLE adherence_logs (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    medication_id   uuid NOT NULL REFERENCES medications(id) ON DELETE CASCADE,
    scheduled_for   timestamptz NOT NULL,
    status          text NOT NULL CHECK (status IN ('taken', 'late', 'missed', 'vomited')),
    logged_by       uuid REFERENCES guardians(id),
    logged_at       timestamptz NOT NULL DEFAULT now(),
    note            text,
    UNIQUE (medication_id, scheduled_for)
);

CREATE TABLE side_effects (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      uuid NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    medication_id   uuid REFERENCES medications(id) ON DELETE SET NULL,
    observed_on     date NOT NULL,
    description     text NOT NULL,            -- sleepiness, rash, dizziness...
    severity        text CHECK (severity IN ('mild', 'moderate', 'severe')),
    logged_by       uuid REFERENCES guardians(id),
    verified_by_doctor boolean NOT NULL DEFAULT false
);

CREATE TABLE allergies (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      uuid NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    substance       text NOT NULL,            -- drug or food
    reaction        text,
    severity        text CHECK (severity IN ('mild', 'moderate', 'severe')),
    verified_by_doctor boolean NOT NULL DEFAULT false
);

-- ---------- Drips and hospital visits -------------------------------

CREATE TABLE iv_infusions (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id          uuid NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    given_on            date NOT NULL,
    fluid_or_drug       text NOT NULL,        -- e.g. normal saline, levetiracetam IV
    given_at            text,                 -- hospital / clinic name
    duration_minutes    integer CHECK (duration_minutes > 0),
    reason              text,
    reaction_noted      boolean NOT NULL DEFAULT false,
    reaction_details    text,
    logged_by           uuid REFERENCES guardians(id),
    verified_by_doctor  boolean NOT NULL DEFAULT false
);

CREATE TABLE hospital_visits (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id          uuid NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    visit_type          text NOT NULL
                        CHECK (visit_type IN ('emergency', 'admission', 'opd', 'follow_up')),
    visited_on          date NOT NULL,
    discharged_on       date,
    facility            text,
    reason              text,
    discharge_summary   text,
    discharge_medicines text,                 -- free text, parsed into medications later
    verified_by_doctor  boolean NOT NULL DEFAULT false
);

-- ---------- Seizures -------------------------------------------------

CREATE TABLE seizure_logs (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id          uuid NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    occurred_at         timestamptz NOT NULL,
    duration_seconds    integer CHECK (duration_seconds >= 0),
    seizure_type        text,                 -- shaking, staring, stiffening, unknown
    possible_trigger    text,                 -- fever, missed dose, lack of sleep...
    fever_present       boolean,
    description         text,                 -- what it looked like, in parent's words
    went_to_er          boolean NOT NULL DEFAULT false,
    logged_by           uuid REFERENCES guardians(id),
    verified_by_doctor  boolean NOT NULL DEFAULT false,
    created_at          timestamptz NOT NULL DEFAULT now()
);

-- ---------- Prescription / discharge slip photos ---------------------

CREATE TABLE prescription_uploads (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id          uuid NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    image_url           text NOT NULL,
    uploaded_by         uuid REFERENCES guardians(id),
    uploaded_at         timestamptz NOT NULL DEFAULT now(),
    extracted_json      jsonb,                -- AI reading of the slip
    status              text NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'parent_confirmed',
                                          'doctor_verified', 'rejected')),
    reviewed_at         timestamptz,
    reviewer_note       text
);

-- ---------- Safety ---------------------------------------------------

-- Red-flag rules are written by the doctor, not by the model.
CREATE TABLE red_flag_rules (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    doctor_id       uuid NOT NULL REFERENCES doctors(id),
    name            text NOT NULL,            -- "Seizure longer than 5 minutes"
    condition_json  jsonb NOT NULL,           -- machine-readable rule
    message_ur      text NOT NULL,
    message_en      text NOT NULL,
    is_active       boolean NOT NULL DEFAULT true
);

CREATE TABLE red_flag_events (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      uuid NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    rule_id         uuid REFERENCES red_flag_rules(id),
    triggered_at    timestamptz NOT NULL DEFAULT now(),
    trigger_text    text,                     -- what the parent wrote
    doctor_seen_at  timestamptz
);

-- Answers the doctor has approved. Parents only ever see published ones.
CREATE TABLE approved_answers (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    doctor_id       uuid NOT NULL REFERENCES doctors(id),
    topic           text NOT NULL,            -- short key, e.g. "first-aid"
    question_examples text[],
    question_en     text,
    question_ur     text,
    answer_ur       text,
    answer_en       text,
    is_published    boolean NOT NULL DEFAULT false,
    sort_order      integer NOT NULL DEFAULT 0,
    updated_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT approved_answers_doctor_topic_key UNIQUE (doctor_id, topic)
    -- add an embedding column (pgvector) when RAG is wired up:
    -- embedding vector(1536)
);

-- ---------- Parent app: login and questions --------------------------

-- One-time login codes. Phone is stored as digits only (923001234567).
CREATE TABLE login_codes (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    phone           text NOT NULL,
    code_hash       text NOT NULL,
    expires_at      timestamptz NOT NULL,
    attempts        smallint NOT NULL DEFAULT 0,
    used_at         timestamptz,
    created_at      timestamptz NOT NULL DEFAULT now()
);

-- Parent sessions. Only a hash of the token is stored.
CREATE TABLE parent_sessions (
    token_hash      text PRIMARY KEY,
    guardian_id     uuid NOT NULL REFERENCES guardians(id) ON DELETE CASCADE,
    created_at      timestamptz NOT NULL DEFAULT now(),
    expires_at      timestamptz NOT NULL,
    revoked_at      timestamptz
);

-- Cached embeddings of the approved answers, one row per answer and embedding model.
CREATE TABLE faq_embeddings (
    answer_id       uuid NOT NULL REFERENCES approved_answers(id) ON DELETE CASCADE,
    model_key       text NOT NULL,            -- "gemini:gemini-embedding-001", "offline:local"
    content_hash    text NOT NULL,            -- re-embed when the answer text changes
    vector          double precision[] NOT NULL,
    updated_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (answer_id, model_key)
);

-- Questions a parent asks that are not in the approved answers.
CREATE TABLE parent_questions (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      uuid NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    guardian_id     uuid REFERENCES guardians(id) ON DELETE SET NULL,
    question        text NOT NULL,
    asked_at        timestamptz NOT NULL DEFAULT now(),
    answer          text,
    answered_at     timestamptz
);

-- ---------- Chat + pre-visit summaries -------------------------------

CREATE TABLE chat_messages (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      uuid NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    guardian_id     uuid REFERENCES guardians(id),
    role            text NOT NULL CHECK (role IN ('guardian', 'bot')),
    content         text NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE visit_summaries (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      uuid NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    for_visit_on    date NOT NULL,
    summary_text    text NOT NULL,            -- one-page summary for the doctor
    generated_at    timestamptz NOT NULL DEFAULT now(),
    opened_by_doctor_at timestamptz
);

-- ---------- Audit ----------------------------------------------------

CREATE TABLE audit_log (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    actor           text NOT NULL,            -- doctor id, guardian id, or 'bot'
    action          text NOT NULL,
    table_name      text NOT NULL,
    row_id          uuid,
    at              timestamptz NOT NULL DEFAULT now()
);

-- ---------- Indexes --------------------------------------------------

CREATE INDEX idx_patients_doctor        ON patients (doctor_id) WHERE is_active;
CREATE INDEX idx_meds_patient_status    ON medications (patient_id, status);
CREATE INDEX idx_medchanges_med_date    ON medication_changes (medication_id, changed_on);
CREATE INDEX idx_adherence_med_time     ON adherence_logs (medication_id, scheduled_for DESC);
CREATE INDEX idx_iv_patient_date        ON iv_infusions (patient_id, given_on DESC);
CREATE INDEX idx_visits_patient_date    ON hospital_visits (patient_id, visited_on DESC);
CREATE INDEX idx_seizures_patient_time  ON seizure_logs (patient_id, occurred_at DESC);
CREATE INDEX idx_uploads_status         ON prescription_uploads (status) WHERE status <> 'doctor_verified';
CREATE INDEX idx_redflags_unseen        ON red_flag_events (patient_id) WHERE doctor_seen_at IS NULL;
CREATE INDEX idx_chat_patient_time      ON chat_messages (patient_id, created_at DESC);
CREATE INDEX idx_login_codes_phone      ON login_codes (phone, created_at DESC);
CREATE INDEX idx_sessions_guardian      ON parent_sessions (guardian_id);
CREATE INDEX idx_questions_open         ON parent_questions (patient_id) WHERE answered_at IS NULL;

-- ---------- The doctor's timeline view -------------------------------
-- One list of everything that happened to a child, newest first.
-- This powers the dashboard's main screen: seizures and medicine
-- changes side by side, so the doctor sees cause and effect.

CREATE VIEW patient_timeline AS
    SELECT s.patient_id,
           s.id                                  AS row_id,
           s.occurred_at                         AS happened_at,
           'seizure'                             AS event_type,
           concat_ws(' | ',
               coalesce(s.seizure_type, 'seizure'),
               CASE WHEN s.duration_seconds IS NOT NULL
                    THEN s.duration_seconds || ' sec' END,
               s.possible_trigger)               AS summary,
           s.verified_by_doctor
    FROM seizure_logs s
  UNION ALL
    SELECT m.patient_id,
           c.id,
           c.changed_on::timestamptz,
           'medicine_change',
           concat_ws(' ', m.drug_name, replace(c.change_type, '_', ' '),
               CASE WHEN c.new_dose_amount IS NOT NULL
                    THEN '-> ' || c.new_dose_amount || ' ' || m.dose_unit END),
           c.verified_by_doctor
    FROM medication_changes c
    JOIN medications m ON m.id = c.medication_id
  UNION ALL
    SELECT i.patient_id,
           i.id,
           i.given_on::timestamptz,
           'iv_drip',
           concat_ws(' | ', i.fluid_or_drug, i.given_at,
               CASE WHEN i.reaction_noted THEN 'REACTION' END),
           i.verified_by_doctor
    FROM iv_infusions i
  UNION ALL
    SELECT h.patient_id,
           h.id,
           h.visited_on::timestamptz,
           'hospital_visit',
           concat_ws(' | ', h.visit_type, h.facility, h.reason),
           h.verified_by_doctor
    FROM hospital_visits h;

-- Adherence per medicine over the last 30 days (for the dashboard).
CREATE VIEW medication_adherence_30d AS
    SELECT m.patient_id,
           m.id AS medication_id,
           m.drug_name,
           count(*) FILTER (WHERE a.status IN ('taken', 'late')) AS doses_given,
           count(*) FILTER (WHERE a.status IN ('missed', 'vomited')) AS doses_missed,
           round(100.0 * count(*) FILTER (WHERE a.status IN ('taken', 'late'))
                 / nullif(count(*), 0), 1) AS adherence_pct
    FROM medications m
    LEFT JOIN adherence_logs a
           ON a.medication_id = m.id
          AND a.scheduled_for >= now() - interval '30 days'
    WHERE m.status = 'active'
    GROUP BY m.patient_id, m.id, m.drug_name;

COMMIT;

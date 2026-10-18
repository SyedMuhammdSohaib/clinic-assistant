-- Adds the parent app tables to a database created from the first schema.sql.
-- Run once:  psql -U postgres -d clinic -f db\migrations\002_parent_app.sql
-- (A fresh database made from the current schema.sql already has all of this.)

BEGIN;

ALTER TABLE approved_answers ADD COLUMN IF NOT EXISTS question_en text;
ALTER TABLE approved_answers ADD COLUMN IF NOT EXISTS question_ur text;
ALTER TABLE approved_answers ADD COLUMN IF NOT EXISTS sort_order integer NOT NULL DEFAULT 0;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'approved_answers_doctor_topic_key') THEN
        ALTER TABLE approved_answers
            ADD CONSTRAINT approved_answers_doctor_topic_key UNIQUE (doctor_id, topic);
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS login_codes (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    phone           text NOT NULL,
    code_hash       text NOT NULL,
    expires_at      timestamptz NOT NULL,
    attempts        smallint NOT NULL DEFAULT 0,
    used_at         timestamptz,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS parent_sessions (
    token_hash      text PRIMARY KEY,
    guardian_id     uuid NOT NULL REFERENCES guardians(id) ON DELETE CASCADE,
    created_at      timestamptz NOT NULL DEFAULT now(),
    expires_at      timestamptz NOT NULL,
    revoked_at      timestamptz
);

CREATE TABLE IF NOT EXISTS parent_questions (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      uuid NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    guardian_id     uuid REFERENCES guardians(id) ON DELETE SET NULL,
    question        text NOT NULL,
    asked_at        timestamptz NOT NULL DEFAULT now(),
    answer          text,
    answered_at     timestamptz
);

CREATE INDEX IF NOT EXISTS idx_login_codes_phone ON login_codes (phone, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_guardian ON parent_sessions (guardian_id);
CREATE INDEX IF NOT EXISTS idx_questions_open    ON parent_questions (patient_id) WHERE answered_at IS NULL;

COMMIT;

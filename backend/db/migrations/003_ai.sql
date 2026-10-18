-- Adds the AI tables to an existing database. Run once:
--   psql -U postgres -d clinic -f db\migrations\003_ai.sql

CREATE TABLE IF NOT EXISTS faq_embeddings (
    answer_id       uuid NOT NULL REFERENCES approved_answers(id) ON DELETE CASCADE,
    model_key       text NOT NULL,
    content_hash    text NOT NULL,
    vector          double precision[] NOT NULL,
    updated_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (answer_id, model_key)
);

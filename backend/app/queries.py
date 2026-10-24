"""All SQL in one place. Placeholders look like %(name)s (psycopg style).

Keep literal percent signs out of these strings; psycopg would read them as placeholders.
"""

# ---------------------------------------------------------------- doctors, rules

INSERT_DOCTOR = """
INSERT INTO doctors (full_name, email, phone, clinic_name)
VALUES (%(full_name)s, %(email)s, %(phone)s, %(clinic_name)s)
RETURNING *"""

DOCTOR_EXISTS = "SELECT id FROM doctors WHERE id = %(id)s"
LIST_DOCTORS = "SELECT id, full_name, email, clinic_name FROM doctors ORDER BY created_at"

INSERT_RULE = """
INSERT INTO red_flag_rules (doctor_id, name, condition_json, message_ur, message_en)
VALUES (%(doctor_id)s, %(name)s, %(condition)s::jsonb, %(message_ur)s, %(message_en)s)
RETURNING *"""

RULES_FOR_PATIENT = """
SELECT r.id, r.name, r.condition_json, r.message_ur, r.message_en
FROM red_flag_rules r
JOIN patients p ON p.doctor_id = r.doctor_id
WHERE p.id = %(patient_id)s AND r.is_active
ORDER BY r.name"""

# ---------------------------------------------------------------- patients, guardians

INSERT_PATIENT = """
INSERT INTO patients (doctor_id, full_name, date_of_birth, sex, weight_kg,
                      weight_updated_on, preferred_language)
VALUES (%(doctor_id)s, %(full_name)s, %(date_of_birth)s, %(sex)s, %(weight_kg)s,
        %(weight_updated_on)s, %(preferred_language)s)
RETURNING *"""

_LIST_PATIENTS = """
SELECT p.id, p.full_name, p.date_of_birth, p.sex, p.weight_kg, p.preferred_language,
       (SELECT count(*) FROM red_flag_events e
         WHERE e.patient_id = p.id AND e.doctor_seen_at IS NULL) AS unseen_red_flags,
       (SELECT count(*) FROM parent_questions pq
         WHERE pq.patient_id = p.id AND pq.answered_at IS NULL) AS open_questions
FROM patients p
WHERE p.is_active"""

LIST_PATIENTS = _LIST_PATIENTS + "\nORDER BY p.full_name"
LIST_PATIENTS_BY_DOCTOR = _LIST_PATIENTS + "\n  AND p.doctor_id = %(doctor_id)s\nORDER BY p.full_name"
# Doctor's search box: the start of the patient id, part of the name, or a parent's phone.
SEARCH_PATIENTS = _LIST_PATIENTS + """
  AND ((%(id_prefix)s::text IS NOT NULL AND starts_with(p.id::text, %(id_prefix)s))
       OR (%(name)s::text IS NOT NULL AND strpos(lower(p.full_name), %(name)s) > 0)
       OR EXISTS (SELECT 1 FROM patient_guardians pg JOIN guardians g ON g.id = pg.guardian_id
                  WHERE pg.patient_id = p.id AND g.phone = %(phone)s))
ORDER BY p.full_name"""

GET_PATIENT = "SELECT * FROM patients WHERE id = %(id)s"
PATIENT_GUARDIANS = """
SELECT g.id, g.full_name, g.phone, g.relation, pg.is_primary
FROM patient_guardians pg JOIN guardians g ON g.id = pg.guardian_id
WHERE pg.patient_id = %(patient_id)s
ORDER BY pg.is_primary DESC, g.full_name"""
PATIENT_EXISTS = "SELECT id FROM patients WHERE id = %(id)s"
# Who to text about a patient: their doctor, and the parent who asked a question.
PATIENT_AND_DOCTOR_PHONE = """
SELECT p.id, p.full_name, d.phone AS doctor_phone
FROM patients p JOIN doctors d ON d.id = p.doctor_id
WHERE p.id = %(patient_id)s"""
QUESTION_ASKER = """
SELECT g.phone, p.preferred_language
FROM parent_questions pq
JOIN patients p ON p.id = pq.patient_id
LEFT JOIN guardians g ON g.id = pq.guardian_id
WHERE pq.id = %(question_id)s"""
DOCTOR_NAME_FOR_PATIENT = """
SELECT d.full_name
FROM doctors d JOIN patients p ON p.doctor_id = d.id
WHERE p.id = %(patient_id)s"""

# A phone number identifies a guardian; the same parent can have several children.
UPSERT_GUARDIAN = """
INSERT INTO guardians (full_name, phone, relation)
VALUES (%(full_name)s, %(phone)s, %(relation)s)
ON CONFLICT (phone) DO UPDATE SET phone = EXCLUDED.phone
RETURNING *"""

LINK_GUARDIAN = """
INSERT INTO patient_guardians (patient_id, guardian_id, is_primary)
VALUES (%(patient_id)s, %(guardian_id)s, %(is_primary)s)
ON CONFLICT (patient_id, guardian_id) DO UPDATE SET is_primary = EXCLUDED.is_primary"""

CLEAR_OTHER_PRIMARY = """
UPDATE patient_guardians SET is_primary = false
WHERE patient_id = %(patient_id)s AND guardian_id <> %(guardian_id)s"""

IS_GUARDIAN_OF = """
SELECT 1 AS ok FROM patient_guardians
WHERE patient_id = %(patient_id)s AND guardian_id = %(guardian_id)s"""

# ---------------------------------------------------------------- medicines

INSERT_MEDICATION = """
INSERT INTO medications (patient_id, drug_name, dose_amount, dose_unit, times_per_day,
                         dose_times, route, reason, prescribed_by, started_on, source,
                         verified_by_doctor, verified_at)
VALUES (%(patient_id)s, %(drug_name)s, %(dose_amount)s, %(dose_unit)s, %(times_per_day)s,
        %(dose_times)s, %(route)s, %(reason)s, %(prescribed_by)s, %(started_on)s, %(source)s,
        true, now())
RETURNING *"""

INSERT_CHANGE = """
INSERT INTO medication_changes (medication_id, changed_on, change_type,
                                old_dose_amount, new_dose_amount,
                                old_times_per_day, new_times_per_day,
                                reason, changed_by, verified_by_doctor)
VALUES (%(medication_id)s, %(changed_on)s, %(change_type)s,
        %(old_dose_amount)s, %(new_dose_amount)s,
        %(old_times_per_day)s, %(new_times_per_day)s,
        %(reason)s, %(changed_by)s, true)
RETURNING *"""

GET_MEDICATION = "SELECT * FROM medications WHERE id = %(id)s"
GET_MEDICATION_FOR_UPDATE = "SELECT * FROM medications WHERE id = %(id)s FOR UPDATE"

UPDATE_MEDICATION_DOSE = """
UPDATE medications SET dose_amount = %(dose_amount)s WHERE id = %(id)s RETURNING *"""

# New frequency means the old reminder times no longer fit, so they are cleared.
UPDATE_MEDICATION_FREQUENCY = """
UPDATE medications SET times_per_day = %(times_per_day)s, dose_times = NULL
WHERE id = %(id)s RETURNING *"""

UPDATE_MEDICATION_STATUS = """
UPDATE medications SET status = %(status)s, ended_on = %(ended_on)s
WHERE id = %(id)s RETURNING *"""

_LIST_MEDICATIONS = """
SELECT m.id, m.drug_name, m.dose_amount, m.dose_unit, m.times_per_day, m.dose_times,
       m.route, m.reason, m.prescribed_by, m.started_on, m.ended_on, m.status,
       m.verified_by_doctor,
       a.doses_given, a.doses_missed, a.adherence_pct
FROM medications m
LEFT JOIN medication_adherence_30d a ON a.medication_id = m.id
WHERE m.patient_id = %(patient_id)s"""

LIST_MEDICATIONS_ACTIVE = _LIST_MEDICATIONS + "\n  AND m.status = 'active'\nORDER BY m.started_on DESC, m.drug_name"
LIST_MEDICATIONS_ALL = _LIST_MEDICATIONS + "\nORDER BY m.started_on DESC, m.drug_name"

# Logging the same dose slot twice updates it, so a parent can correct a mistake.
UPSERT_ADHERENCE = """
INSERT INTO adherence_logs (medication_id, scheduled_for, status, logged_by, note)
VALUES (%(medication_id)s, %(scheduled_for)s, %(status)s, %(guardian_id)s, %(note)s)
ON CONFLICT (medication_id, scheduled_for)
DO UPDATE SET status = EXCLUDED.status, logged_by = EXCLUDED.logged_by,
              logged_at = now(), note = EXCLUDED.note
RETURNING *"""

# ---------------------------------------------------------------- seizures, drips, visits

INSERT_SEIZURE = """
INSERT INTO seizure_logs (patient_id, occurred_at, duration_seconds, seizure_type,
                          possible_trigger, fever_present, description, went_to_er, logged_by)
VALUES (%(patient_id)s, %(occurred_at)s, %(duration_seconds)s, %(seizure_type)s,
        %(possible_trigger)s, %(fever_present)s, %(description)s, %(went_to_er)s, %(guardian_id)s)
RETURNING *"""

COUNT_SEIZURES_WINDOW = """
SELECT count(*) AS n
FROM seizure_logs
WHERE patient_id = %(patient_id)s
  AND occurred_at <= %(at)s
  AND occurred_at > %(at)s - make_interval(hours => %(hours)s)"""

INSERT_RED_FLAG_EVENT = """
INSERT INTO red_flag_events (patient_id, rule_id, trigger_text)
VALUES (%(patient_id)s, %(rule_id)s, %(trigger_text)s)
RETURNING id, triggered_at"""

_LIST_RED_FLAGS = """
SELECT e.id, e.triggered_at, e.trigger_text, e.doctor_seen_at, r.name AS rule_name
FROM red_flag_events e
LEFT JOIN red_flag_rules r ON r.id = e.rule_id
WHERE e.patient_id = %(patient_id)s"""

LIST_RED_FLAGS_UNSEEN = _LIST_RED_FLAGS + "\n  AND e.doctor_seen_at IS NULL\nORDER BY e.triggered_at DESC"
LIST_RED_FLAGS_ALL = _LIST_RED_FLAGS + "\nORDER BY e.triggered_at DESC"

MARK_RED_FLAG_SEEN = """
UPDATE red_flag_events SET doctor_seen_at = COALESCE(doctor_seen_at, now())
WHERE id = %(id)s RETURNING *"""

INSERT_IV = """
INSERT INTO iv_infusions (patient_id, given_on, fluid_or_drug, given_at, duration_minutes,
                          reason, reaction_noted, reaction_details, logged_by)
VALUES (%(patient_id)s, %(given_on)s, %(fluid_or_drug)s, %(given_at)s, %(duration_minutes)s,
        %(reason)s, %(reaction_noted)s, %(reaction_details)s, %(guardian_id)s)
RETURNING *"""

INSERT_VISIT = """
INSERT INTO hospital_visits (patient_id, visit_type, visited_on, discharged_on, facility,
                             reason, discharge_summary, discharge_medicines)
VALUES (%(patient_id)s, %(visit_type)s, %(visited_on)s, %(discharged_on)s, %(facility)s,
        %(reason)s, %(discharge_summary)s, %(discharge_medicines)s)
RETURNING *"""

INSERT_SIDE_EFFECT = """
INSERT INTO side_effects (patient_id, medication_id, observed_on, description, severity, logged_by)
VALUES (%(patient_id)s, %(medication_id)s, %(observed_on)s, %(description)s, %(severity)s,
        %(guardian_id)s)
RETURNING *"""

INSERT_ALLERGY = """
INSERT INTO allergies (patient_id, substance, reaction, severity, verified_by_doctor)
VALUES (%(patient_id)s, %(substance)s, %(reaction)s, %(severity)s, true)
RETURNING *"""

# ---------------------------------------------------------------- doctor views

_TIMELINE = """
SELECT row_id, happened_at, event_type, summary, verified_by_doctor
FROM patient_timeline
WHERE patient_id = %(patient_id)s"""

TIMELINE = _TIMELINE + "\nORDER BY happened_at DESC\nLIMIT %(limit)s"
TIMELINE_BEFORE = _TIMELINE + "\n  AND happened_at < %(before)s\nORDER BY happened_at DESC\nLIMIT %(limit)s"

# One UPDATE per kind. The table names come from this fixed list, never from the request.
VERIFY = {
    "seizures": "UPDATE seizure_logs SET verified_by_doctor = true WHERE id = %(id)s RETURNING id",
    "medications": (
        "UPDATE medications SET verified_by_doctor = true, verified_at = now() "
        "WHERE id = %(id)s RETURNING id"
    ),
    "medication-changes": "UPDATE medication_changes SET verified_by_doctor = true WHERE id = %(id)s RETURNING id",
    "iv-infusions": "UPDATE iv_infusions SET verified_by_doctor = true WHERE id = %(id)s RETURNING id",
    "hospital-visits": "UPDATE hospital_visits SET verified_by_doctor = true WHERE id = %(id)s RETURNING id",
    "side-effects": "UPDATE side_effects SET verified_by_doctor = true WHERE id = %(id)s RETURNING id",
    "allergies": "UPDATE allergies SET verified_by_doctor = true WHERE id = %(id)s RETURNING id",
}

# Pre-visit summary pieces. "a" is the start of the period, "b" the end.
SEIZURE_STATS = """
SELECT count(*) AS total,
       max(duration_seconds) AS longest_seconds,
       count(*) FILTER (WHERE fever_present) AS with_fever,
       count(*) FILTER (WHERE went_to_er) AS went_to_er
FROM seizure_logs
WHERE patient_id = %(patient_id)s AND occurred_at >= %(a)s AND occurred_at < %(b)s"""

RED_FLAGS_IN_PERIOD = """
SELECT e.id, e.triggered_at, e.trigger_text, e.doctor_seen_at, r.name AS rule_name
FROM red_flag_events e
LEFT JOIN red_flag_rules r ON r.id = e.rule_id
WHERE e.patient_id = %(patient_id)s AND e.triggered_at >= %(a)s AND e.triggered_at < %(b)s
ORDER BY e.triggered_at"""

CHANGES_IN_PERIOD = """
SELECT c.id, c.changed_on, m.drug_name, m.dose_unit, c.change_type,
       c.old_dose_amount, c.new_dose_amount, c.old_times_per_day, c.new_times_per_day,
       c.reason, c.verified_by_doctor
FROM medication_changes c
JOIN medications m ON m.id = c.medication_id
WHERE m.patient_id = %(patient_id)s AND c.changed_on >= %(a_date)s AND c.changed_on <= %(b_date)s
ORDER BY c.changed_on"""

ADHERENCE_IN_PERIOD = """
SELECT m.id AS medication_id, m.drug_name,
       count(*) FILTER (WHERE a.status IN ('taken', 'late')) AS given,
       count(*) FILTER (WHERE a.status = 'missed') AS missed,
       count(*) FILTER (WHERE a.status = 'vomited') AS vomited
FROM medications m
JOIN adherence_logs a ON a.medication_id = m.id
WHERE m.patient_id = %(patient_id)s AND a.scheduled_for >= %(a)s AND a.scheduled_for < %(b)s
GROUP BY m.id, m.drug_name
ORDER BY m.drug_name"""

IV_IN_PERIOD = """
SELECT id, given_on, fluid_or_drug, given_at, duration_minutes, reaction_noted,
       reaction_details, verified_by_doctor
FROM iv_infusions
WHERE patient_id = %(patient_id)s AND given_on >= %(a_date)s AND given_on <= %(b_date)s
ORDER BY given_on"""

VISITS_IN_PERIOD = """
SELECT id, visit_type, visited_on, discharged_on, facility, reason, verified_by_doctor
FROM hospital_visits
WHERE patient_id = %(patient_id)s AND visited_on >= %(a_date)s AND visited_on <= %(b_date)s
ORDER BY visited_on"""

SIDE_EFFECTS_IN_PERIOD = """
SELECT s.id, s.observed_on, s.description, s.severity, s.verified_by_doctor, m.drug_name
FROM side_effects s
LEFT JOIN medications m ON m.id = s.medication_id
WHERE s.patient_id = %(patient_id)s AND s.observed_on >= %(a_date)s AND s.observed_on <= %(b_date)s
ORDER BY s.observed_on"""

LIST_ALLERGIES = """
SELECT id, substance, reaction, severity, verified_by_doctor
FROM allergies WHERE patient_id = %(patient_id)s ORDER BY substance"""

UNVERIFIED_COUNT = """
SELECT (SELECT count(*) FROM seizure_logs      WHERE patient_id = %(patient_id)s AND NOT verified_by_doctor)
     + (SELECT count(*) FROM medications       WHERE patient_id = %(patient_id)s AND NOT verified_by_doctor)
     + (SELECT count(*) FROM iv_infusions      WHERE patient_id = %(patient_id)s AND NOT verified_by_doctor)
     + (SELECT count(*) FROM hospital_visits   WHERE patient_id = %(patient_id)s AND NOT verified_by_doctor)
     + (SELECT count(*) FROM side_effects      WHERE patient_id = %(patient_id)s AND NOT verified_by_doctor)
       AS n"""

# ---------------------------------------------------------------- prescription slips

INSERT_UPLOAD = """
INSERT INTO prescription_uploads (patient_id, image_url, uploaded_by, extracted_json)
VALUES (%(patient_id)s, %(image_url)s, %(guardian_id)s, %(extracted_json)s::jsonb)
RETURNING *"""

GET_UPLOAD_FOR_UPDATE = "SELECT * FROM prescription_uploads WHERE id = %(id)s FOR UPDATE"

SET_UPLOAD_STATUS = """
UPDATE prescription_uploads
SET status = %(status)s,
    reviewed_at = CASE WHEN %(status)s IN ('doctor_verified', 'rejected') THEN now() ELSE reviewed_at END,
    reviewer_note = COALESCE(%(note)s, reviewer_note)
WHERE id = %(id)s
RETURNING *"""

# ---------------------------------------------------------------- parent login

# Guardians may have been saved as +92..., 0300-..., or 92...; compare digits only.
GUARDIAN_BY_PHONE = """
SELECT id, full_name, phone, relation
FROM guardians
WHERE regexp_replace(phone, '[^0-9]', '', 'g') = %(phone)s
ORDER BY created_at
LIMIT 1"""

COUNT_RECENT_CODES = """
SELECT count(*) AS n FROM login_codes
WHERE phone = %(phone)s AND created_at > now() - interval '1 hour'"""

INSERT_LOGIN_CODE = """
INSERT INTO login_codes (phone, code_hash, expires_at)
VALUES (%(phone)s, %(code_hash)s, now() + interval '10 minutes')"""

LATEST_LOGIN_CODE = """
SELECT id, code_hash, attempts
FROM login_codes
WHERE phone = %(phone)s AND used_at IS NULL AND expires_at > now()
ORDER BY created_at DESC
LIMIT 1
FOR UPDATE"""

BUMP_CODE_ATTEMPTS = "UPDATE login_codes SET attempts = attempts + 1 WHERE id = %(id)s RETURNING attempts"
USE_LOGIN_CODE = "UPDATE login_codes SET used_at = now() WHERE id = %(id)s"

INSERT_SESSION = """
INSERT INTO parent_sessions (token_hash, guardian_id, expires_at)
VALUES (%(token_hash)s, %(guardian_id)s, now() + interval '30 days')"""

SESSION_GUARDIAN = """
SELECT g.id, g.full_name, g.relation
FROM parent_sessions s
JOIN guardians g ON g.id = s.guardian_id
WHERE s.token_hash = %(token_hash)s AND s.revoked_at IS NULL AND s.expires_at > now()"""

REVOKE_SESSION = "UPDATE parent_sessions SET revoked_at = now() WHERE token_hash = %(token_hash)s"

# ---------------------------------------------------------------- parent app

# Only what a parent needs: never the diagnosis or the doctor's notes.
GUARDIAN_CHILDREN = """
SELECT p.id, p.full_name, p.date_of_birth, p.preferred_language
FROM patient_guardians pg
JOIN patients p ON p.id = pg.patient_id
WHERE pg.guardian_id = %(guardian_id)s AND p.is_active
ORDER BY p.full_name"""

ACTIVE_MEDS_FOR_SCHEDULE = """
SELECT id, drug_name, dose_amount, dose_unit, times_per_day, dose_times, started_on
FROM medications
WHERE patient_id = %(patient_id)s AND status = 'active'
ORDER BY drug_name"""

DOSE_LOGS_BETWEEN = """
SELECT a.medication_id, a.scheduled_for, a.status
FROM adherence_logs a
JOIN medications m ON m.id = a.medication_id
WHERE m.patient_id = %(patient_id)s AND a.scheduled_for >= %(a)s AND a.scheduled_for < %(b)s"""

FAQ_FOR_PATIENT = """
SELECT aa.id, aa.topic, aa.question_en, aa.question_ur, aa.answer_en, aa.answer_ur
FROM approved_answers aa
JOIN patients p ON p.doctor_id = aa.doctor_id
WHERE p.id = %(patient_id)s AND aa.is_published
ORDER BY aa.sort_order, aa.topic"""

INSERT_QUESTION = """
INSERT INTO parent_questions (patient_id, guardian_id, question)
VALUES (%(patient_id)s, %(guardian_id)s, %(question)s)
RETURNING id, question, asked_at, answer, answered_at"""

LIST_QUESTIONS_FOR_PARENT = """
SELECT id, question, asked_at, answer, answered_at
FROM parent_questions
WHERE patient_id = %(patient_id)s
ORDER BY asked_at DESC
LIMIT 50"""

_LIST_QUESTIONS = """
SELECT q.id, q.question, q.asked_at, q.answer, q.answered_at, g.full_name AS guardian_name
FROM parent_questions q
LEFT JOIN guardians g ON g.id = q.guardian_id
WHERE q.patient_id = %(patient_id)s"""

LIST_QUESTIONS_OPEN = _LIST_QUESTIONS + "\n  AND q.answered_at IS NULL\nORDER BY q.asked_at"
LIST_QUESTIONS_ALL = _LIST_QUESTIONS + "\nORDER BY q.asked_at DESC\nLIMIT 100"

ANSWER_QUESTION = """
UPDATE parent_questions SET answer = %(answer)s, answered_at = now()
WHERE id = %(id)s
RETURNING id, patient_id, question, asked_at, answer, answered_at"""

# Used by scripts/load_faq.py.
UPSERT_FAQ = """
INSERT INTO approved_answers (doctor_id, topic, question_en, question_ur, answer_en, answer_ur,
                              is_published, sort_order, updated_at)
VALUES (%(doctor_id)s, %(topic)s, %(question_en)s, %(question_ur)s, %(answer_en)s, %(answer_ur)s,
        %(is_published)s, %(sort_order)s, now())
ON CONFLICT (doctor_id, topic) DO UPDATE
SET question_en = EXCLUDED.question_en, question_ur = EXCLUDED.question_ur,
    answer_en = EXCLUDED.answer_en, answer_ur = EXCLUDED.answer_ur,
    is_published = EXCLUDED.is_published, sort_order = EXCLUDED.sort_order, updated_at = now()
RETURNING id, topic, is_published"""

DOCTOR_BY_EMAIL = "SELECT id FROM doctors WHERE lower(email) = lower(%(email)s)"

# ---------------------------------------------------------------- AI

FAQ_EMBEDDINGS_FOR = """
SELECT answer_id, content_hash, vector
FROM faq_embeddings
WHERE model_key = %(model_key)s AND answer_id = ANY(%(ids)s)"""

UPSERT_FAQ_EMBEDDING = """
INSERT INTO faq_embeddings (answer_id, model_key, content_hash, vector)
VALUES (%(answer_id)s, %(model_key)s, %(content_hash)s, %(vector)s)
ON CONFLICT (answer_id, model_key)
DO UPDATE SET content_hash = EXCLUDED.content_hash, vector = EXCLUDED.vector, updated_at = now()"""

PATIENT_NAME = "SELECT full_name FROM patients WHERE id = %(id)s"

GET_UPLOAD = "SELECT * FROM prescription_uploads WHERE id = %(id)s"

LIST_UPLOADS_OPEN = """
SELECT u.id, u.uploaded_at, u.status, u.extracted_json, u.reviewer_note, g.full_name AS guardian_name
FROM prescription_uploads u
LEFT JOIN guardians g ON g.id = u.uploaded_by
WHERE u.patient_id = %(patient_id)s AND u.status IN ('pending', 'parent_confirmed')
ORDER BY u.uploaded_at DESC"""

LIST_UPLOADS_FOR_PARENT = """
SELECT id, uploaded_at, status, extracted_json, reviewer_note
FROM prescription_uploads
WHERE patient_id = %(patient_id)s
ORDER BY uploaded_at DESC
LIMIT 10"""

# ---------------------------------------------------------------- audit

INSERT_AUDIT = """
INSERT INTO audit_log (actor, action, table_name, row_id)
VALUES (%(actor)s, %(action)s, %(table_name)s, %(row_id)s)"""

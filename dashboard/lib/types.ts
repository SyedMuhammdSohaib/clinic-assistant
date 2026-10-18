// Shapes returned by the clinic API. Numbers from numeric columns can arrive as
// number or string, so they are typed loosely and converted with Number().

export type Num = number | string;

export interface PatientListItem {
  id: string;
  full_name: string;
  date_of_birth: string;
  sex: string | null;
  weight_kg: Num | null;
  preferred_language: string;
  unseen_red_flags: number;
  open_questions?: number;
}

export interface ParentQuestion {
  id: string;
  question: string;
  asked_at: string;
  answer: string | null;
  answered_at: string | null;
  guardian_name: string | null;
}

export interface Patient {
  id: string;
  doctor_id: string;
  full_name: string;
  date_of_birth: string;
  sex: string | null;
  weight_kg: Num | null;
  weight_updated_on: string | null;
  diagnosis: string | null;
  preferred_language: string;
}

export type EventType = "seizure" | "medicine_change" | "iv_drip" | "hospital_visit";

export interface TimelineRow {
  row_id: string;
  happened_at: string;
  event_type: EventType;
  summary: string;
  verified_by_doctor: boolean;
  verify_kind: string;
}

export interface RedFlag {
  id: string;
  triggered_at: string;
  trigger_text: string | null;
  doctor_seen_at: string | null;
  rule_name: string | null;
}

export interface Medication {
  id: string;
  drug_name: string;
  dose_amount: Num;
  dose_unit: string;
  times_per_day: number;
  dose_times: string[] | null;
  route: string | null;
  reason: string | null;
  prescribed_by: string | null;
  started_on: string;
  ended_on: string | null;
  status: "active" | "paused" | "stopped";
  verified_by_doctor: boolean;
  doses_given: number | null;
  doses_missed: number | null;
  adherence_pct: Num | null;
}

export interface Previsit {
  patient: { id: string; full_name: string; date_of_birth: string; weight_kg: Num | null };
  period: { from: string; to: string };
  seizures: {
    total: number;
    longest_seconds: number | null;
    with_fever: number;
    went_to_er: number;
    previous_period_total: number;
  };
  red_flags: RedFlag[];
  medicines_now: Medication[];
  medicine_changes: {
    id: string;
    changed_on: string;
    drug_name: string;
    dose_unit: string;
    change_type: string;
    old_dose_amount: Num | null;
    new_dose_amount: Num | null;
    old_times_per_day: number | null;
    new_times_per_day: number | null;
    reason: string | null;
    verified_by_doctor: boolean;
  }[];
  adherence: { medication_id: string; drug_name: string; given: number; missed: number; vomited: number }[];
  iv_infusions: {
    id: string;
    given_on: string;
    fluid_or_drug: string;
    given_at: string | null;
    duration_minutes: number | null;
    reaction_noted: boolean;
    reaction_details: string | null;
    verified_by_doctor: boolean;
  }[];
  hospital_visits: {
    id: string;
    visit_type: string;
    visited_on: string;
    discharged_on: string | null;
    facility: string | null;
    reason: string | null;
    verified_by_doctor: boolean;
  }[];
  side_effects: {
    id: string;
    observed_on: string;
    description: string;
    severity: string | null;
    verified_by_doctor: boolean;
    drug_name: string | null;
  }[];
  allergies: { id: string; substance: string; reaction: string | null; severity: string | null; verified_by_doctor: boolean }[];
  unverified_entries: number;
}

export interface SlipItem {
  drug_name: string;
  dose_amount: number | null;
  dose_unit: string | null;
  times_per_day: number | null;
  instructions: string | null;
  legible: boolean;
}

export interface SlipUpload {
  id: string;
  uploaded_at: string;
  status: "pending" | "parent_confirmed" | "doctor_verified" | "rejected";
  extracted_json: { is_prescription: boolean; items: SlipItem[] } | null;
  reviewer_note: string | null;
  guardian_name: string | null;
}

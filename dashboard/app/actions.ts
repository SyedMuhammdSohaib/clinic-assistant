"use server";
// Form actions. They run on the server, so the doctor key never reaches the browser.
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { ApiError, apiPost, seg } from "@/lib/api";

const VERIFY_KINDS = new Set([
  "seizures",
  "medications",
  "medication-changes",
  "iv-infusions",
  "hospital-visits",
  "side-effects",
  "allergies",
]);

const CHANGE_TYPES = new Set([
  "dose_increased",
  "dose_decreased",
  "frequency_changed",
  "paused",
  "resumed",
  "stopped",
  "switched",
]);

function field(formData: FormData, name: string): string {
  const value = formData.get(name);
  return typeof value === "string" ? value.trim() : "";
}

export async function verifyEntry(formData: FormData): Promise<void> {
  const patientId = field(formData, "patient_id");
  const kind = field(formData, "kind");
  const rowId = field(formData, "row_id");
  if (!VERIFY_KINDS.has(kind) || !rowId) throw new Error("Unknown entry");
  await apiPost(`/verify/${kind}/${seg(rowId)}`);
  revalidatePath(`/patients/${patientId}`, "layout");
}

export async function markRedFlagSeen(formData: FormData): Promise<void> {
  const patientId = field(formData, "patient_id");
  const eventId = field(formData, "event_id");
  if (!eventId) throw new Error("Unknown red flag");
  await apiPost(`/red-flag-events/${seg(eventId)}/seen`);
  revalidatePath("/");
  revalidatePath(`/patients/${patientId}`, "layout");
}

export async function answerQuestion(formData: FormData): Promise<void> {
  const patientId = field(formData, "patient_id");
  const questionId = field(formData, "question_id");
  const answer = field(formData, "answer");
  if (!questionId || !answer) throw new Error("Write an answer first");
  await apiPost(`/questions/${seg(questionId)}/answer`, { answer });
  revalidatePath("/");
  revalidatePath(`/patients/${patientId}`, "layout");
}

export async function changeMedicine(formData: FormData): Promise<void> {
  const patientId = field(formData, "patient_id");
  const medicationId = field(formData, "medication_id");
  const changeType = field(formData, "change_type");
  const back = `/patients/${seg(patientId)}/medicines`;

  let message = "";
  if (!CHANGE_TYPES.has(changeType) || !medicationId) {
    message = "Choose what changes";
  } else {
    const body: Record<string, unknown> = { change_type: changeType };
    const dose = field(formData, "new_dose_amount");
    const times = field(formData, "new_times_per_day");
    const reason = field(formData, "reason");
    if ((changeType === "dose_increased" || changeType === "dose_decreased") && dose) body.new_dose_amount = dose;
    if (changeType === "frequency_changed" && times) body.new_times_per_day = Number(times);
    if (reason) body.reason = reason;
    try {
      await apiPost(`/medications/${seg(medicationId)}/changes`, body);
    } catch (e) {
      message = e instanceof ApiError ? e.message : "Could not save the change. Is the backend running?";
    }
  }

  revalidatePath(`/patients/${patientId}`, "layout");
  // redirect() works by throwing, so it stays outside the try block above.
  redirect(message ? `${back}?error=${encodeURIComponent(message)}` : `${back}?saved=1`);
}

// ---------------------------------------------------------------- prescription slips

export async function approveSlip(formData: FormData): Promise<void> {
  const patientId = field(formData, "patient_id");
  const uploadId = field(formData, "upload_id");
  const rows = Math.min(Number(field(formData, "rows")) || 0, 30);
  const back = `/patients/${seg(patientId)}/slips`;
  const items: Record<string, unknown>[] = [];
  let message = "";
  for (let i = 0; i < rows; i++) {
    if (formData.get(`add_${i}`) !== "on") continue;
    const name = field(formData, `drug_name_${i}`);
    const dose = field(formData, `dose_amount_${i}`);
    const unit = field(formData, `dose_unit_${i}`);
    const times = field(formData, `times_per_day_${i}`);
    const start = field(formData, `started_on_${i}`);
    if (!name || !dose || !unit || !times || !start) {
      message = `Row ${i + 1}: fill in name, dose, unit, times a day and start date, or untick it`;
      break;
    }
    items.push({ drug_name: name, dose_amount: dose, dose_unit: unit, times_per_day: Number(times), started_on: start });
  }
  if (!message) {
    const note = field(formData, "reviewer_note");
    try {
      await apiPost(`/prescription-uploads/${seg(uploadId)}/approve`, { items, ...(note ? { reviewer_note: note } : {}) });
    } catch (e) {
      message = e instanceof ApiError ? e.message : "Could not approve. Is the backend running?";
    }
  }
  revalidatePath(`/patients/${patientId}`, "layout");
  redirect(message ? `${back}?error=${encodeURIComponent(message)}` : `${back}?saved=${items.length}`);
}

export async function rejectSlip(formData: FormData): Promise<void> {
  const patientId = field(formData, "patient_id");
  const uploadId = field(formData, "upload_id");
  const note = field(formData, "reviewer_note");
  const back = `/patients/${seg(patientId)}/slips`;
  let message = "";
  if (!note) message = "Write a reason for the parent";
  else {
    try {
      await apiPost(`/prescription-uploads/${seg(uploadId)}/reject`, { reviewer_note: note });
    } catch (e) {
      message = e instanceof ApiError ? e.message : "Could not reject. Is the backend running?";
    }
  }
  revalidatePath(`/patients/${patientId}`, "layout");
  redirect(message ? `${back}?error=${encodeURIComponent(message)}` : `${back}?rejected=1`);
}

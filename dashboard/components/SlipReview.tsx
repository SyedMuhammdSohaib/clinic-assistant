import { fmtDateTime } from "@/lib/format";
import type { SlipItem, SlipUpload } from "@/lib/types";

type Action = (formData: FormData) => Promise<void>;

const STATUS: Record<SlipUpload["status"], string> = {
  pending: "Parent has not confirmed yet",
  parent_confirmed: "Parent confirmed",
  doctor_verified: "Approved",
  rejected: "Rejected",
};

// One extra empty row lets the doctor add a medicine the AI missed.
const BLANK: SlipItem = { drug_name: "", dose_amount: null, dose_unit: null, times_per_day: null, instructions: null, legible: true };

export function SlipReview({ slips, patientId, today, approve, reject }: {
  slips: SlipUpload[]; patientId: string; today: string; approve: Action; reject: Action;
}) {
  if (slips.length === 0) {
    return (
      <section className="card">
        <p className="muted">No prescription photos are waiting. Parents send them from the app.</p>
      </section>
    );
  }
  return (
    <div className="stack-lg">
      {slips.map((s) => {
        const items = s.extracted_json?.items ?? [];
        const rows = [...items, BLANK];
        return (
          <section key={s.id} className="card slip" aria-label="Prescription photo">
            <div className="slip-photo">
              <a href={`/api/slips/${encodeURIComponent(s.id)}/image`} target="_blank" rel="noreferrer">
                <img src={`/api/slips/${encodeURIComponent(s.id)}/image`} alt="Prescription photo sent by the parent" />
              </a>
              <span className="muted small">
                {fmtDateTime(s.uploaded_at)}
                {s.guardian_name ? ` · ${s.guardian_name}` : ""} · {STATUS[s.status]}
              </span>
            </div>
            <div className="stack-md grow">
              <div className="stack-xs">
                <h2>{items.length ? `AI read ${items.length} medicine${items.length > 1 ? "s" : ""}` : "AI could not read this photo"}</h2>
                <p className="muted small">
                  A suggestion only. Check every line against the photo. Only ticked lines are added to the medicine list.
                </p>
              </div>
              <form action={approve} className="stack-sm">
                <input type="hidden" name="patient_id" value={patientId} />
                <input type="hidden" name="upload_id" value={s.id} />
                <input type="hidden" name="rows" value={rows.length} />
                <div className="scroll-x">
                  <table className="slip-table">
                    <thead>
                      <tr>
                        <th scope="col">Add</th>
                        <th scope="col">Medicine</th>
                        <th scope="col">Dose</th>
                        <th scope="col">Unit</th>
                        <th scope="col">Times a day</th>
                        <th scope="col">Start</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map((it, i) => {
                        const id = `${s.id}-${i}`;
                        const blank = i === items.length;
                        return (
                          <tr key={id} className={!it.legible ? "slip-unclear" : undefined}>
                            <td>
                              <input type="checkbox" name={`add_${i}`} aria-label={`Add row ${i + 1}`}
                                defaultChecked={!blank && it.legible && it.times_per_day !== null && it.dose_amount !== null} />
                            </td>
                            <td>
                              <input name={`drug_name_${i}`} defaultValue={it.drug_name} aria-label="Medicine name" placeholder={blank ? "Add a medicine" : undefined} />
                              {it.instructions && <span className="muted small">{it.instructions}</span>}
                              {!it.legible && <span className="badge badge-warn">Not clearly read</span>}
                            </td>
                            <td><input name={`dose_amount_${i}`} type="number" step="0.01" min="0.01" defaultValue={it.dose_amount ?? ""} aria-label="Dose" /></td>
                            <td><input name={`dose_unit_${i}`} defaultValue={it.dose_unit ?? ""} aria-label="Unit" size={5} /></td>
                            <td><input name={`times_per_day_${i}`} type="number" min="1" max="12" step="1" defaultValue={it.times_per_day ?? ""} aria-label="Times a day" /></td>
                            <td><input name={`started_on_${i}`} type="date" defaultValue={today} aria-label="Start date" /></td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
                <label htmlFor={`note-${s.id}`}>Note for the record (optional)</label>
                <input id={`note-${s.id}`} name="reviewer_note" maxLength={1000} />
                <div className="row-gap">
                  <button type="submit" className="btn">Approve ticked medicines</button>
                </div>
              </form>
              <form action={reject} className="reject-form">
                <input type="hidden" name="patient_id" value={patientId} />
                <input type="hidden" name="upload_id" value={s.id} />
                <label htmlFor={`rej-${s.id}`}>Or reject, with a reason the parent will see</label>
                <div className="row-gap">
                  <input id={`rej-${s.id}`} name="reviewer_note" required maxLength={1000} placeholder="e.g. Photo too blurry, please send again" />
                  <button type="submit" className="btn btn-alert">Reject</button>
                </div>
              </form>
            </div>
          </section>
        );
      })}
    </div>
  );
}

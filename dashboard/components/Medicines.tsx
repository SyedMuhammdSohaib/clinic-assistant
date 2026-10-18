import { StatusBadge, VerifiedBadge } from "@/components/Badge";
import { fmtDateTime, fmtDay, fmtNum, num, timesPerDayText } from "@/lib/format";
import type { Medication, TimelineRow } from "@/lib/types";

type Action = (formData: FormData) => Promise<void>;

function Adherence({ med }: { med: Medication }) {
  const pct = num(med.adherence_pct);
  if (pct === null) return <span className="muted">No doses logged</span>;
  return (
    <div className="meter-row">
      <div className="meter" aria-hidden="true">
        <div className="meter-fill" style={{ width: `${Math.min(Math.max(pct, 0), 100)}%` }} />
      </div>
      <span>
        <strong>{fmtNum(pct)}%</strong>{" "}
        <span className="muted small">({med.doses_given ?? 0} given, {med.doses_missed ?? 0} missed)</span>
      </span>
    </div>
  );
}

function ChangeForm({ med, patientId, action }: { med: Medication; patientId: string; action: Action }) {
  const idp = `chg-${med.id}`;
  const options =
    med.status === "paused"
      ? [{ value: "resumed", label: "Resume" }, { value: "stopped", label: "Stop" }]
      : [
          { value: "dose_increased", label: "Increase dose" },
          { value: "dose_decreased", label: "Decrease dose" },
          { value: "frequency_changed", label: "Change times per day" },
          { value: "paused", label: "Pause" },
          { value: "stopped", label: "Stop" },
          { value: "switched", label: "Stop (switched to another medicine)" },
        ];
  return (
    <details className="change-form">
      <summary>Change this medicine</summary>
      <form action={action} className="form-grid">
        <input type="hidden" name="patient_id" value={patientId} />
        <input type="hidden" name="medication_id" value={med.id} />
        <label htmlFor={`${idp}-type`}>What changes</label>
        <select id={`${idp}-type`} name="change_type" required defaultValue={options[0].value}>
          {options.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <label htmlFor={`${idp}-dose`}>New dose ({med.dose_unit}), for a dose change</label>
        <input id={`${idp}-dose`} name="new_dose_amount" type="number" step="0.01" min="0.01" inputMode="decimal" />
        <label htmlFor={`${idp}-times`}>New times per day, for a frequency change</label>
        <input id={`${idp}-times`} name="new_times_per_day" type="number" min="1" max="12" step="1" />
        <label htmlFor={`${idp}-reason`}>Reason (optional)</label>
        <input id={`${idp}-reason`} name="reason" type="text" maxLength={500} />
        <div className="form-actions">
          <button type="submit" className="btn">Save change</button>
        </div>
      </form>
    </details>
  );
}

export function MedicineTable({ meds, patientId, changeAction }: { meds: Medication[]; patientId: string; changeAction: Action }) {
  const current = meds.filter((m) => m.status !== "stopped");
  const stopped = meds.filter((m) => m.status === "stopped");
  return (
    <section className="card stack-md" aria-label="Medicines">
      <h2>Current medicines</h2>
      {current.length === 0 ? (
        <p className="muted">No current medicines. Add one from the API docs page (POST /patients/&#123;id&#125;/medications).</p>
      ) : (
        <ul className="med-list">
          {current.map((m) => (
            <li key={m.id} className="med">
              <div className="med-main">
                <div className="stack-xs">
                  <strong className="med-name">{m.drug_name}</strong>
                  <span className="muted small">
                    {m.reason ? `${m.reason} · ` : ""}
                    {m.prescribed_by ?? "Prescriber not recorded"} · since {fmtDay(m.started_on)}
                  </span>
                </div>
                <div className="stack-xs">
                  <span><strong>{fmtNum(m.dose_amount)} {m.dose_unit}</strong>, {timesPerDayText(m.times_per_day).toLowerCase()}</span>
                  {m.dose_times && m.dose_times.length > 0 && (
                    <span className="muted small">at {m.dose_times.map((t) => t.slice(0, 5)).join(" and ")}</span>
                  )}
                </div>
                <Adherence med={m} />
                <div className="badges">
                  <StatusBadge status={m.status} />
                  <VerifiedBadge verified={m.verified_by_doctor} />
                </div>
              </div>
              <ChangeForm med={m} patientId={patientId} action={changeAction} />
            </li>
          ))}
        </ul>
      )}
      {stopped.length > 0 && (
        <details>
          <summary>Stopped medicines ({stopped.length})</summary>
          <ul className="plain-list">
            {stopped.map((m) => (
              <li key={m.id}>
                <strong>{m.drug_name}</strong>{" "}
                <span className="muted">
                  {fmtNum(m.dose_amount)} {m.dose_unit} · {fmtDay(m.started_on)} to {m.ended_on ? fmtDay(m.ended_on) : "?"}
                </span>
              </li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}

export function EventList({ title, rows, empty }: { title: string; rows: TimelineRow[]; empty: string }) {
  return (
    <section className="card stack-sm" aria-label={title}>
      <h2>{title}</h2>
      {rows.length === 0 ? (
        <p className="muted">{empty}</p>
      ) : (
        <ul className="plain-list">
          {rows.map((r) => (
            <li key={r.row_id} className="event-row">
              <span className="timeline-time">{fmtDateTime(r.happened_at)}</span>
              <span className="grow">{r.summary}</span>
              <VerifiedBadge verified={r.verified_by_doctor} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

import { VerifiedBadge } from "@/components/Badge";
import { fmtDateTime } from "@/lib/format";
import type { EventType, TimelineRow } from "@/lib/types";

type Action = (formData: FormData) => Promise<void>;

const TITLE: Record<EventType, string> = {
  seizure: "Seizure",
  medicine_change: "Medicine change",
  iv_drip: "IV drip",
  hospital_visit: "Hospital visit",
};

export function Timeline({ rows, patientId, verify }: { rows: TimelineRow[]; patientId: string; verify: Action }) {
  return (
    <section className="card stack-sm" aria-label="Timeline">
      <div className="row-between">
        <h2>Everything that happened, newest first</h2>
        <span className="muted small">Seizures, medicine changes, drips and hospital visits</span>
      </div>
      {rows.length === 0 ? (
        <p className="muted">Nothing logged yet.</p>
      ) : (
        <ol className="timeline">
          {rows.map((r) => (
            <li key={`${r.event_type}-${r.row_id}`} className="timeline-row">
              <span className="timeline-time">{fmtDateTime(r.happened_at)}</span>
              <span className={`marker marker-${r.event_type}`} aria-hidden="true" />
              <div className="stack-xs grow">
                <strong>{TITLE[r.event_type] ?? r.event_type}</strong>
                <span className="muted">{r.summary}</span>
              </div>
              <div className="timeline-actions">
                <VerifiedBadge verified={r.verified_by_doctor} />
                {!r.verified_by_doctor && (
                  <form action={verify}>
                    <input type="hidden" name="patient_id" value={patientId} />
                    <input type="hidden" name="kind" value={r.verify_kind} />
                    <input type="hidden" name="row_id" value={r.row_id} />
                    <button type="submit" className="btn btn-small">Verify</button>
                  </form>
                )}
              </div>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

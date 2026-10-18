import { fmtDateTime } from "@/lib/format";
import type { RedFlag } from "@/lib/types";

type Action = (formData: FormData) => Promise<void>;

export function RedFlags({ flags, patientId, markSeen }: { flags: RedFlag[]; patientId: string; markSeen: Action }) {
  if (flags.length === 0) return null;
  return (
    <section aria-label="Red flags" className="stack-sm">
      {flags.map((f) => (
        <div key={f.id} className="alert">
          <div className="stack-xs grow">
            <strong>Red flag: {f.rule_name ?? "Rule"}</strong>
            <span>
              {fmtDateTime(f.triggered_at)}
              {f.trigger_text ? ` · ${f.trigger_text}` : ""}. The parent was shown the emergency message.
            </span>
          </div>
          <form action={markSeen}>
            <input type="hidden" name="patient_id" value={patientId} />
            <input type="hidden" name="event_id" value={f.id} />
            <button type="submit" className="btn btn-alert">Mark as seen</button>
          </form>
        </div>
      ))}
    </section>
  );
}

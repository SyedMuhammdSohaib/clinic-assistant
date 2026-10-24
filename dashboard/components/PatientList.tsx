import Link from "next/link";
import { ageText, fmtNum, shortId } from "@/lib/format";
import type { PatientListItem } from "@/lib/types";

export function PatientList({ patients, now }: { patients: PatientListItem[]; now?: Date }) {
  if (patients.length === 0) {
    return (
      <div className="card stack-sm">
        <h2>No patients yet</h2>
        <p className="muted">
          Use <Link href="/patients/new">+ Add patient</Link> to add the first child.
        </p>
      </div>
    );
  }
  const sorted = [...patients].sort((a, b) => b.unseen_red_flags - a.unseen_red_flags || a.full_name.localeCompare(b.full_name));
  return (
    <ul className="patient-list">
      {sorted.map((p) => (
        <li key={p.id}>
          <Link href={`/patients/${encodeURIComponent(p.id)}`} className="patient-card">
            <div className="stack-xs grow">
              <strong className="patient-name">{p.full_name}</strong>
              <span className="muted small">
                {ageText(p.date_of_birth, now)}
                {p.weight_kg !== null ? ` · ${fmtNum(p.weight_kg)} kg` : ""}
              </span>
              <span className="muted small">ID <span className="patient-id">{shortId(p.id)}</span></span>
            </div>
            <span className="badges">
              {p.unseen_red_flags > 0 ? (
                <span className="badge badge-alert">{p.unseen_red_flags} red flag{p.unseen_red_flags > 1 ? "s" : ""}</span>
              ) : (
                <span className="badge badge-muted">No new red flags</span>
              )}
              {(p.open_questions ?? 0) > 0 && (
                <span className="badge badge-warn">{p.open_questions} question{(p.open_questions ?? 0) > 1 ? "s" : ""}</span>
              )}
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}

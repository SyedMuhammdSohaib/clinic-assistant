import type { Previsit } from "@/lib/types";

export function Stats({ summary }: { summary: Previsit }) {
  const given = summary.adherence.reduce((s, a) => s + a.given, 0);
  const missed = summary.adherence.reduce((s, a) => s + a.missed, 0);
  const vomited = summary.adherence.reduce((s, a) => s + a.vomited, 0);
  const logged = given + missed + vomited;
  const pct = logged ? Math.round((given / logged) * 100) : null;

  return (
    <section className="tiles" aria-label="Summary">
      <div className="tile">
        <span className="tile-label">Seizures, last 4 weeks</span>
        <span className="tile-value">{summary.seizures.total}</span>
        <span className="tile-note">{summary.seizures.previous_period_total} in the 4 weeks before</span>
      </div>
      <div className="tile">
        <span className="tile-label">Doses given, last 4 weeks</span>
        <span className="tile-value">{pct === null ? "–" : `${pct}%`}</span>
        <span className="tile-note">{logged ? `${missed} missed, ${vomited} vomited` : "No doses logged yet"}</span>
      </div>
      <div className="tile">
        <span className="tile-label">Active medicines</span>
        <span className="tile-value">{summary.medicines_now.length}</span>
        <span className="tile-note">{summary.allergies.length ? `Allergies: ${summary.allergies.map((a) => a.substance).join(", ")}` : "No allergies recorded"}</span>
      </div>
      <div className="tile">
        <span className="tile-label">Entries waiting for you</span>
        <span className="tile-value">{summary.unverified_entries}</span>
        <span className="tile-note">Logged by the parent, not yet verified</span>
      </div>
    </section>
  );
}

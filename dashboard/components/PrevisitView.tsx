import { VerifiedBadge } from "@/components/Badge";
import { ageText, changeTypeText, fmtDateTime, fmtDay, fmtDuration, fmtNum, timesPerDayText } from "@/lib/format";
import type { Previsit } from "@/lib/types";

export function PrevisitView({ s, now }: { s: Previsit; now?: Date }) {
  const sz = s.seizures;
  return (
    <article className="card summary stack-lg">
      <header className="summary-head stack-xs">
        <span className="eyebrow">Pre-visit summary</span>
        <h2 className="summary-title">
          {s.patient.full_name}, {ageText(s.patient.date_of_birth, now)}
          {s.patient.weight_kg !== null ? `, ${fmtNum(s.patient.weight_kg)} kg` : ""}
        </h2>
        <span className="muted">
          Covers {fmtDay(s.period.from)} to {fmtDay(s.period.to)}
        </span>
      </header>

      {s.red_flags.length > 0 && (
        <section className="alert stack-xs" aria-label="Red flags">
          <strong>Needs your attention first</strong>
          {s.red_flags.map((f) => (
            <span key={f.id}>
              {fmtDateTime(f.triggered_at)}: {f.rule_name ?? "Red flag"}
              {f.trigger_text ? ` (${f.trigger_text})` : ""}
              {f.doctor_seen_at ? " · seen" : ""}
            </span>
          ))}
        </section>
      )}

      <section className="tiles tiles-compact" aria-label="Numbers">
        <div className="tile">
          <span className="tile-value">{sz.total}</span>
          <span className="tile-note">seizures ({sz.previous_period_total} in the period before)</span>
        </div>
        <div className="tile">
          <span className="tile-value">{fmtDuration(sz.longest_seconds)}</span>
          <span className="tile-note">longest seizure</span>
        </div>
        <div className="tile">
          <span className="tile-value">{sz.with_fever}</span>
          <span className="tile-note">with fever</span>
        </div>
        <div className="tile">
          <span className="tile-value">{sz.went_to_er}</span>
          <span className="tile-note">went to the emergency room</span>
        </div>
      </section>

      <section className="stack-sm" aria-label="Medicines now">
        <h3>Medicines now</h3>
        {s.medicines_now.length === 0 ? (
          <p className="muted">No active medicines.</p>
        ) : (
          <ul className="plain-list">
            {s.medicines_now.map((m) => {
              const a = s.adherence.find((x) => x.medication_id === m.id);
              return (
                <li key={m.id} className="summary-row">
                  <strong className="summary-key">
                    {m.drug_name}, {fmtNum(m.dose_amount)} {m.dose_unit} {timesPerDayText(m.times_per_day).toLowerCase()}
                  </strong>
                  <span className="muted">
                    {a ? `${a.given} doses given, ${a.missed} missed, ${a.vomited} vomited in this period` : "No doses logged in this period"}
                  </span>
                </li>
              );
            })}
          </ul>
        )}
        {s.allergies.length > 0 && (
          <p>
            <strong>Allergies:</strong>{" "}
            {s.allergies.map((a) => `${a.substance}${a.reaction ? ` (${a.reaction})` : ""}`).join(", ")}
          </p>
        )}
      </section>

      <section className="stack-sm" aria-label="Changes">
        <h3>Medicine changes in this period</h3>
        {s.medicine_changes.length === 0 ? (
          <p className="muted">No changes.</p>
        ) : (
          <ul className="plain-list">
            {s.medicine_changes.map((c) => (
              <li key={c.id} className="summary-row">
                <strong className="summary-key">{fmtDay(c.changed_on)}: {c.drug_name}</strong>
                <span>
                  {changeTypeText(c.change_type)}
                  {c.new_dose_amount !== null
                    ? `, ${c.old_dose_amount !== null ? `${fmtNum(c.old_dose_amount)} to ` : ""}${fmtNum(c.new_dose_amount)} ${c.dose_unit}`
                    : ""}
                  {c.new_times_per_day !== null
                    ? `, ${c.old_times_per_day !== null ? `${c.old_times_per_day} to ` : ""}${c.new_times_per_day} times a day`
                    : ""}
                  {c.reason ? `. ${c.reason}` : ""}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      {(s.iv_infusions.length > 0 || s.hospital_visits.length > 0) && (
        <section className="stack-sm" aria-label="Drips and hospital visits">
          <h3>Drips and hospital visits</h3>
          <ul className="plain-list">
            {s.hospital_visits.map((v) => (
              <li key={v.id} className="summary-row">
                <strong className="summary-key">{fmtDay(v.visited_on)}: {changeTypeText(v.visit_type)} visit</strong>
                <span>
                  {[v.facility, v.reason].filter(Boolean).join(", ") || "No details"} <VerifiedBadge verified={v.verified_by_doctor} />
                </span>
              </li>
            ))}
            {s.iv_infusions.map((i) => (
              <li key={i.id} className="summary-row">
                <strong className="summary-key">{fmtDay(i.given_on)}: drip, {i.fluid_or_drug}</strong>
                <span>
                  {[i.given_at, i.duration_minutes ? `${i.duration_minutes} min` : null, i.reaction_noted ? `reaction: ${i.reaction_details ?? "yes"}` : "no reaction noted"]
                    .filter(Boolean)
                    .join(", ")}{" "}
                  <VerifiedBadge verified={i.verified_by_doctor} />
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {s.side_effects.length > 0 && (
        <section className="stack-sm" aria-label="Side effects">
          <h3>Side effects reported</h3>
          <ul className="plain-list">
            {s.side_effects.map((e) => (
              <li key={e.id} className="summary-row">
                <strong className="summary-key">{fmtDay(e.observed_on)}: {e.description}</strong>
                <span>
                  {[e.severity, e.drug_name ? `after ${e.drug_name}` : null].filter(Boolean).join(", ")}{" "}
                  <VerifiedBadge verified={e.verified_by_doctor} />
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      <footer className="muted small summary-foot">
        Built from the parent&apos;s logs and your verified records. {s.unverified_entries} entries are still not verified.
        This summary does not diagnose or advise on doses.
      </footer>
    </article>
  );
}

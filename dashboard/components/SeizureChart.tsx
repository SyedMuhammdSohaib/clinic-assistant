import type { WeekBucket } from "@/lib/chart";
import { fmtShortDay } from "@/lib/format";

export function SeizureChart({ weeks }: { weeks: WeekBucket[] }) {
  const max = Math.max(1, ...weeks.map((w) => w.seizures));
  const total = weeks.reduce((sum, w) => sum + w.seizures, 0);
  const changeWeeks = weeks.filter((w) => w.changes.length > 0).length;
  const label = `Seizures per week for the last ${weeks.length} weeks: ${total} in total. Medicine changed in ${changeWeeks} of those weeks.`;

  return (
    <section className="card stack-md" aria-label="Seizures and medicine changes">
      <div className="row-between">
        <h2>Seizures and medicine changes, last {weeks.length} weeks</h2>
        <div className="legend">
          <span><span className="dot dot-seizure" aria-hidden="true" />Seizures that week</span>
          <span><span className="diamond" aria-hidden="true" />Medicine change</span>
        </div>
      </div>
      <div className="scroll-x">
        <div className="chart" role="img" aria-label={label} style={{ gridTemplateColumns: `repeat(${weeks.length}, minmax(0, 1fr))` }}>
          {weeks.map((w) => {
            const changed = w.changes.length > 0;
            return (
              <div key={w.start.toISOString()} className={changed ? "chart-col chart-col-change" : "chart-col"} title={changed ? w.changes.join("\n") : undefined}>
                {changed && (
                  <div className="chart-flag">
                    <span className="diamond" aria-hidden="true" />
                    <span>{w.changes.length === 1 ? "Change" : `${w.changes.length} changes`}</span>
                  </div>
                )}
                <span className="chart-value">{w.seizures}</span>
                <div className="chart-bar" style={{ height: `${(w.seizures / max) * 160}px` }} />
                <span className="chart-label">{fmtShortDay(w.start)}</span>
              </div>
            );
          })}
        </div>
      </div>
      <p className="muted small">Each bar is one week, starting on the date shown. Hover a marked week to see what changed.</p>
    </section>
  );
}

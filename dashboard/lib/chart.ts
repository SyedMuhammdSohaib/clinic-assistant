// Turns timeline rows into weekly buckets for the seizure chart. Pure function.
import type { TimelineRow } from "./types";

export interface WeekBucket {
  start: Date;
  end: Date;
  seizures: number;
  changes: string[]; // medicine change summaries in this week
}

const DAY = 24 * 60 * 60 * 1000;

/** `weeks` buckets of 7 days each, the last one ending at `now`, oldest first. */
export function weeklyBuckets(rows: TimelineRow[], now: Date, weeks = 12): WeekBucket[] {
  const end = now.getTime();
  const buckets: WeekBucket[] = [];
  for (let i = weeks - 1; i >= 0; i--) {
    const bucketEnd = end - i * 7 * DAY;
    buckets.push({ start: new Date(bucketEnd - 7 * DAY), end: new Date(bucketEnd), seizures: 0, changes: [] });
  }
  const first = buckets[0].start.getTime();
  for (const row of rows) {
    const t = new Date(row.happened_at).getTime();
    if (Number.isNaN(t) || t < first || t > end) continue;
    const index = Math.min(Math.floor((t - first) / (7 * DAY)), weeks - 1);
    const bucket = buckets[index];
    if (row.event_type === "seizure") bucket.seizures += 1;
    if (row.event_type === "medicine_change") bucket.changes.push(row.summary);
  }
  return buckets;
}

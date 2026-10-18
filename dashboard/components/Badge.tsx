export function VerifiedBadge({ verified }: { verified: boolean }) {
  return verified ? (
    <span className="badge badge-ok">Verified</span>
  ) : (
    <span className="badge badge-warn">Not verified</span>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const cls = status === "active" ? "badge-ok" : status === "paused" ? "badge-warn" : "badge-muted";
  return <span className={`badge ${cls}`}>{status.charAt(0).toUpperCase() + status.slice(1)}</span>;
}

import { PatientList } from "@/components/PatientList";
import { apiGet } from "@/lib/api";
import type { PatientListItem } from "@/lib/types";

export default async function HomePage() {
  const patients = await apiGet<PatientListItem[]>("/patients");
  const flagged = patients.reduce((n, p) => n + p.unseen_red_flags, 0);
  return (
    <div className="stack-lg">
      <header className="stack-xs">
        <span className="eyebrow">Patients</span>
        <h1>Your patients</h1>
        <span className="muted">
          {patients.length} active · {flagged ? `${flagged} red flag${flagged > 1 ? "s" : ""} waiting` : "no red flags waiting"}
        </span>
      </header>
      <PatientList patients={patients} />
    </div>
  );
}

import Link from "next/link";
import { ageText, fmtNum } from "@/lib/format";
import type { Patient } from "@/lib/types";

type Tab = "overview" | "medicines" | "previsit" | "slips";

export function PatientHeader({ patient, active, now }: { patient: Patient; active: Tab; now?: Date }) {
  const base = `/patients/${encodeURIComponent(patient.id)}`;
  const tabs: { key: Tab; label: string; href: string }[] = [
    { key: "overview", label: "Timeline", href: base },
    { key: "medicines", label: "Medicines and drips", href: `${base}/medicines` },
    { key: "previsit", label: "Pre-visit summary", href: `${base}/previsit` },
    { key: "slips", label: "Prescription slips", href: `${base}/slips` },
  ];
  const weight = patient.weight_kg !== null ? ` · ${fmtNum(patient.weight_kg)} kg` : "";
  return (
    <header className="patient-header">
      <div className="stack-xs">
        <span className="eyebrow">Patient</span>
        <h1>{patient.full_name}</h1>
        <span className="muted">
          {ageText(patient.date_of_birth, now)}
          {weight}
          {patient.diagnosis ? ` · ${patient.diagnosis}` : ""}
        </span>
      </div>
      <nav className="tabs" aria-label="Patient sections">
        {tabs.map((t) => (
          <Link key={t.key} href={t.href} className={t.key === active ? "tab tab-active" : "tab"} aria-current={t.key === active ? "page" : undefined}>
            {t.label}
          </Link>
        ))}
      </nav>
    </header>
  );
}

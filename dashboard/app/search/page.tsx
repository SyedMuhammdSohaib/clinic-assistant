import { redirect } from "next/navigation";
import { PatientList } from "@/components/PatientList";
import { apiGet, seg } from "@/lib/api";
import type { PatientListItem } from "@/lib/types";

type Search = Promise<{ [key: string]: string | string[] | undefined }>;

export default async function SearchPage({ searchParams }: { searchParams: Search }) {
  const query = await searchParams;
  const text = typeof query.q === "string" ? query.q.trim() : "";
  const patients = text ? await apiGet<PatientListItem[]>(`/patients?q=${seg(text)}`) : [];
  // One match: open that patient's record straight away.
  if (patients.length === 1) redirect(`/patients/${seg(patients[0].id)}`);

  return (
    <div className="stack-lg">
      <header className="stack-xs">
        <span className="eyebrow">Find a patient</span>
        <h1>{text ? `Results for “${text}”` : "Find a patient"}</h1>
        <span className="muted">
          {text
            ? patients.length
              ? `${patients.length} patients match. Pick one.`
              : "No patient matches. Check the ID, or try the child's name or the parent's phone number."
            : "Type a patient ID, a child's name or a parent's phone number in the box on the left."}
        </span>
      </header>
      {patients.length > 1 && <PatientList patients={patients} />}
    </div>
  );
}

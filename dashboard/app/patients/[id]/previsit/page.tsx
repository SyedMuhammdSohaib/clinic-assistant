import { PatientHeader } from "@/components/PatientHeader";
import { PrevisitView } from "@/components/PrevisitView";
import { apiGet, getOrNotFound, seg } from "@/lib/api";
import type { Patient, Previsit } from "@/lib/types";

type Search = Promise<{ [key: string]: string | string[] | undefined }>;

export default async function PrevisitPage({ params, searchParams }: { params: Promise<{ id: string }>; searchParams: Search }) {
  const { id } = await params;
  const query = await searchParams;
  const since = typeof query.since === "string" && /^\d{4}-\d{2}-\d{2}$/.test(query.since) ? query.since : null;

  const patient = await getOrNotFound<Patient>(`/patients/${seg(id)}`);
  const summary = await apiGet<Previsit>(`/patients/${seg(id)}/previsit${since ? `?since=${since}` : ""}`);

  return (
    <div className="stack-lg">
      <PatientHeader patient={patient} active="previsit" />
      <form className="inline-form no-print" method="get">
        <label htmlFor="since">Last visit date</label>
        <input id="since" name="since" type="date" defaultValue={since ?? ""} />
        <button type="submit" className="btn btn-small">Update</button>
        <span className="muted small">Leave empty for the last 4 weeks. Press Ctrl+P to print.</span>
      </form>
      <PrevisitView s={summary} />
    </div>
  );
}

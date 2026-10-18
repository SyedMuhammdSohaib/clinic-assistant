import { changeMedicine } from "@/app/actions";
import { EventList, MedicineTable } from "@/components/Medicines";
import { PatientHeader } from "@/components/PatientHeader";
import { apiGet, getOrNotFound, seg } from "@/lib/api";
import type { Medication, Patient, TimelineRow } from "@/lib/types";

type Search = Promise<{ [key: string]: string | string[] | undefined }>;

export default async function MedicinesPage({ params, searchParams }: { params: Promise<{ id: string }>; searchParams: Search }) {
  const { id } = await params;
  const query = await searchParams;
  const error = typeof query.error === "string" ? query.error : null;
  const saved = query.saved === "1";

  const patient = await getOrNotFound<Patient>(`/patients/${seg(id)}`);
  const [meds, timeline] = await Promise.all([
    apiGet<Medication[]>(`/patients/${seg(id)}/medications?status=all`),
    apiGet<TimelineRow[]>(`/patients/${seg(id)}/timeline?limit=200`),
  ]);

  return (
    <div className="stack-lg">
      <PatientHeader patient={patient} active="medicines" />
      {error && (
        <div className="alert" role="alert">
          <span>Change not saved: {error}</span>
        </div>
      )}
      {saved && !error && (
        <div className="notice" role="status">
          Change saved and added to the history.
        </div>
      )}
      <MedicineTable meds={meds} patientId={patient.id} changeAction={changeMedicine} />
      <EventList
        title="Every start, change and stop"
        rows={timeline.filter((r) => r.event_type === "medicine_change")}
        empty="No medicine history yet."
      />
      <EventList
        title="Drips and IV medicines"
        rows={timeline.filter((r) => r.event_type === "iv_drip")}
        empty="No drips recorded."
      />
    </div>
  );
}

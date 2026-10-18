import { approveSlip, rejectSlip } from "@/app/actions";
import { PatientHeader } from "@/components/PatientHeader";
import { SlipReview } from "@/components/SlipReview";
import { apiGet, getOrNotFound, seg } from "@/lib/api";
import type { Patient, SlipUpload } from "@/lib/types";

type Search = Promise<{ [key: string]: string | string[] | undefined }>;

function clinicToday(): string {
  // en-CA formats as YYYY-MM-DD.
  return new Intl.DateTimeFormat("en-CA", { timeZone: process.env.CLINIC_TZ || "Asia/Karachi" }).format(new Date());
}

export default async function SlipsPage({ params, searchParams }: { params: Promise<{ id: string }>; searchParams: Search }) {
  const { id } = await params;
  const query = await searchParams;
  const error = typeof query.error === "string" ? query.error : null;
  const saved = typeof query.saved === "string" ? Number(query.saved) : null;
  const rejected = query.rejected === "1";

  const patient = await getOrNotFound<Patient>(`/patients/${seg(id)}`);
  const slips = await apiGet<SlipUpload[]>(`/patients/${seg(id)}/prescription-uploads`);

  return (
    <div className="stack-lg">
      <PatientHeader patient={patient} active="slips" />
      {error && (
        <div className="alert" role="alert">
          <span>Not saved: {error}</span>
        </div>
      )}
      {saved !== null && !error && (
        <div className="notice" role="status">
          Approved. {saved} medicine{saved === 1 ? "" : "s"} added to the medicine list.
        </div>
      )}
      {rejected && !error && (
        <div className="notice" role="status">
          Rejected. The parent will see your reason.
        </div>
      )}
      <SlipReview slips={slips} patientId={patient.id} today={clinicToday()} approve={approveSlip} reject={rejectSlip} />
    </div>
  );
}

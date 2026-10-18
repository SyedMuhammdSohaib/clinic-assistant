import { answerQuestion, markRedFlagSeen, verifyEntry } from "@/app/actions";
import { PatientHeader } from "@/components/PatientHeader";
import { Questions } from "@/components/Questions";
import { RedFlags } from "@/components/RedFlags";
import { SeizureChart } from "@/components/SeizureChart";
import { Stats } from "@/components/Stats";
import { Timeline } from "@/components/Timeline";
import { apiGet, getOrNotFound, seg } from "@/lib/api";
import { weeklyBuckets } from "@/lib/chart";
import type { ParentQuestion, Patient, Previsit, RedFlag, TimelineRow } from "@/lib/types";

export default async function PatientPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const patient = await getOrNotFound<Patient>(`/patients/${seg(id)}`);
  const [timeline, flags, summary, questions] = await Promise.all([
    apiGet<TimelineRow[]>(`/patients/${seg(id)}/timeline?limit=200`),
    apiGet<RedFlag[]>(`/patients/${seg(id)}/red-flags`),
    apiGet<Previsit>(`/patients/${seg(id)}/previsit`),
    apiGet<ParentQuestion[]>(`/patients/${seg(id)}/questions`),
  ]);
  const weeks = weeklyBuckets(timeline, new Date(), 12);

  return (
    <div className="stack-lg">
      <PatientHeader patient={patient} active="overview" />
      <RedFlags flags={flags} patientId={patient.id} markSeen={markRedFlagSeen} />
      <Questions questions={questions} patientId={patient.id} answer={answerQuestion} />
      <Stats summary={summary} />
      <SeizureChart weeks={weeks} />
      <Timeline rows={timeline} patientId={patient.id} verify={verifyEntry} />
    </div>
  );
}

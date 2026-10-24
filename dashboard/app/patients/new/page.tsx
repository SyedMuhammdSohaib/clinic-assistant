import Link from "next/link";
import { addPatient } from "@/app/actions";
import { apiGet } from "@/lib/api";
import { clinicToday } from "@/lib/format";
import type { Doctor } from "@/lib/types";

type Search = Promise<{ [key: string]: string | string[] | undefined }>;

export default async function NewPatientPage({ searchParams }: { searchParams: Search }) {
  const query = await searchParams;
  const error = typeof query.error === "string" ? query.error : null;
  const doctors = await apiGet<Doctor[]>("/doctors");
  const today = clinicToday();

  return (
    <div className="stack-lg">
      <header className="stack-xs">
        <span className="eyebrow">Patients</span>
        <h1>Add a patient</h1>
        <span className="muted">The parent can log in to the parent app with the phone number you save here.</span>
      </header>

      {error && (
        <div className="alert" role="alert">
          <span>{error}</span>
        </div>
      )}

      {doctors.length === 0 ? (
        <div className="card stack-sm">
          <h2>No doctor yet</h2>
          <p className="muted">
            Add a doctor first with POST /doctors on the{" "}
            <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">API docs page</a>, then come back.
          </p>
        </div>
      ) : (
        <form action={addPatient} className="card stack-md">
          <section className="form-grid" aria-label="Child">
            <h2>Child</h2>
            {doctors.length > 1 ? (
              <>
                <label htmlFor="doctor_id">Doctor</label>
                <select id="doctor_id" name="doctor_id" required defaultValue={doctors[0].id}>
                  {doctors.map((d) => (
                    <option key={d.id} value={d.id}>{d.full_name}</option>
                  ))}
                </select>
              </>
            ) : (
              <input type="hidden" name="doctor_id" value={doctors[0].id} />
            )}
            <label htmlFor="full_name">Child&apos;s full name</label>
            <input id="full_name" name="full_name" type="text" required maxLength={200} autoComplete="off" />
            <label htmlFor="date_of_birth">Date of birth</label>
            <input id="date_of_birth" name="date_of_birth" type="date" required max={today} />
            <label htmlFor="sex">Sex (optional)</label>
            <select id="sex" name="sex" defaultValue="">
              <option value="">Not given</option>
              <option value="male">Boy</option>
              <option value="female">Girl</option>
              <option value="other">Other</option>
            </select>
            <label htmlFor="weight_kg">Weight in kg (optional)</label>
            <input id="weight_kg" name="weight_kg" type="number" step="0.01" min="0.5" max="199" inputMode="decimal" />
            <label htmlFor="preferred_language">Language the parent reads</label>
            <select id="preferred_language" name="preferred_language" defaultValue="ur">
              <option value="ur">Urdu</option>
              <option value="roman_ur">Roman Urdu</option>
              <option value="en">English</option>
            </select>
          </section>

          <section className="form-grid" aria-label="Parent">
            <h2>Parent</h2>
            <p className="muted small">Optional now; without a number the parent cannot log in yet.</p>
            <label htmlFor="parent_name">Parent&apos;s name</label>
            <input id="parent_name" name="parent_name" type="text" maxLength={200} autoComplete="off" />
            <label htmlFor="parent_phone">Mobile number</label>
            <input id="parent_phone" name="parent_phone" type="tel" placeholder="03001234567" inputMode="tel" autoComplete="off" />
            <label htmlFor="relation">Relation to the child</label>
            <select id="relation" name="relation" defaultValue="mother">
              <option value="mother">Mother</option>
              <option value="father">Father</option>
              <option value="grandmother">Grandmother</option>
              <option value="grandfather">Grandfather</option>
              <option value="other">Other</option>
            </select>
            <div className="form-actions row-gap">
              <button type="submit" className="btn">Add patient</button>
              <Link href="/" className="muted">Cancel</Link>
            </div>
          </section>
        </form>
      )}
    </div>
  );
}

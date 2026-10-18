import { fmtDateTime } from "@/lib/format";
import type { ParentQuestion } from "@/lib/types";

type Action = (formData: FormData) => Promise<void>;

export function Questions({ questions, patientId, answer }: { questions: ParentQuestion[]; patientId: string; answer: Action }) {
  if (questions.length === 0) return null;
  return (
    <section className="card stack-sm" aria-label="Questions from parents">
      <div className="row-between">
        <h2>Questions from parents ({questions.length})</h2>
        <span className="muted small">Not covered by your approved answers. Your reply appears in the parent&apos;s app.</span>
      </div>
      <ul className="plain-list">
        {questions.map((q) => (
          <li key={q.id} className="stack-sm">
            <div className="stack-xs">
              <span className="muted small">
                {fmtDateTime(q.asked_at)}
                {q.guardian_name ? ` · ${q.guardian_name}` : ""}
              </span>
              <strong className="question-text">{q.question}</strong>
            </div>
            <form action={answer} className="answer-form">
              <input type="hidden" name="patient_id" value={patientId} />
              <input type="hidden" name="question_id" value={q.id} />
              <label htmlFor={`ans-${q.id}`} className="sr-only">Your answer</label>
              <textarea id={`ans-${q.id}`} name="answer" rows={2} maxLength={2000} required placeholder="Your answer to the parent" />
              <button type="submit" className="btn btn-small">Send answer</button>
            </form>
          </li>
        ))}
      </ul>
    </section>
  );
}

"use client";

export default function ErrorPage({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div className="card stack-sm">
      <h1>Something went wrong</h1>
      <p>{error.message || "The page could not load."}</p>
      <p className="muted small">
        Check that the backend is running (uvicorn) and that DOCTOR_API_KEY in .env.local matches the backend key.
      </p>
      <div>
        <button type="button" className="btn" onClick={() => reset()}>
          Try again
        </button>
      </div>
    </div>
  );
}

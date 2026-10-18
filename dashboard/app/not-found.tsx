import Link from "next/link";

export default function NotFound() {
  return (
    <div className="card stack-sm">
      <h1>Not found</h1>
      <p className="muted">This patient does not exist, or the link is wrong.</p>
      <Link href="/">Back to patients</Link>
    </div>
  );
}

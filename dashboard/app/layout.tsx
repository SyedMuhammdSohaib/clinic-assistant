import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

// Every page shows live clinic data, so nothing is pre-rendered at build time.
export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Clinic dashboard",
  description: "Child neurology clinic: seizures, medicines and pre-visit summaries",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <nav className="sidebar" aria-label="Main">
            <Link href="/" className="brand">
              <span className="brand-name">Clinic dashboard</span>
              <span className="brand-sub">Child neurology</span>
            </Link>
            <Link href="/" className="side-link">Patients</Link>
            <Link href="/patients/new" className="side-link side-link-button">+ Add patient</Link>
            <a href="http://127.0.0.1:8000/docs" className="side-link" target="_blank" rel="noreferrer">
              API docs (add data)
            </a>
          </nav>
          <main className="content">{children}</main>
        </div>
      </body>
    </html>
  );
}

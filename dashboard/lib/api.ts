// Talks to the FastAPI backend. Only import this from server code (pages and
// server actions): it reads DOCTOR_API_KEY, which must never reach the browser.
import { notFound } from "next/navigation";

const API_URL = (process.env.API_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

function detailText(body: unknown, fallback: string): string {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((d) => (d && typeof d === "object" && "msg" in d ? String((d as { msg: unknown }).msg) : ""))
        .filter(Boolean)
        .join("; ");
    }
  }
  return fallback;
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const key = process.env.DOCTOR_API_KEY;
  if (!key) throw new Error("DOCTOR_API_KEY is not set. Add it to .env.local and restart.");

  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      ...init,
      cache: "no-store",
      headers: { "Content-Type": "application/json", "X-Doctor-Key": key },
    });
  } catch {
    throw new Error(`Cannot reach the API at ${API_URL}. Is the backend (uvicorn) running?`);
  }

  if (!res.ok) {
    let body: unknown = null;
    try {
      body = await res.json();
    } catch {
      // keep the status text
    }
    throw new ApiError(res.status, detailText(body, res.statusText || `HTTP ${res.status}`));
  }
  return (await res.json()) as T;
}

export function apiGet<T>(path: string): Promise<T> {
  return call<T>(path);
}

export function apiPost<T>(path: string, body: unknown = {}): Promise<T> {
  return call<T>(path, { method: "POST", body: JSON.stringify(body) });
}

/** GET that shows the Not Found page for a missing or malformed id. */
export async function getOrNotFound<T>(path: string): Promise<T> {
  try {
    return await apiGet<T>(path);
  } catch (e) {
    if (e instanceof ApiError && (e.status === 404 || e.status === 422)) notFound();
    throw e;
  }
}

export function seg(value: string): string {
  return encodeURIComponent(value);
}

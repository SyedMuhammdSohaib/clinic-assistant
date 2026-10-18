// Streams a prescription photo from the backend, adding the doctor key on the server
// so the key never reaches the browser.
const API_URL = (process.env.API_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");

export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const key = process.env.DOCTOR_API_KEY;
  if (!key) return new Response("DOCTOR_API_KEY is not set", { status: 500 });
  let res: Response;
  try {
    res = await fetch(`${API_URL}/prescription-uploads/${encodeURIComponent(id)}/image`, {
      headers: { "X-Doctor-Key": key },
      cache: "no-store",
    });
  } catch {
    return new Response("Backend not reachable", { status: 502 });
  }
  if (!res.ok || !res.body) return new Response("Photo not found", { status: res.status === 404 ? 404 : 502 });
  return new Response(res.body, {
    headers: {
      "Content-Type": res.headers.get("content-type") ?? "image/jpeg",
      "Cache-Control": "private, no-store",
    },
  });
}

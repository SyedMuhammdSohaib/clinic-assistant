"""Which AI model the app talks to.

  AI_PROVIDER=gemini   Google Gemini (free tier works). Needs GEMINI_API_KEY.
  AI_PROVIDER=offline  No AI: keyword rules and a simple local embedding.
  (unset)              gemini when GEMINI_API_KEY is set, otherwise offline.

Only the Python standard library is used for the HTTP calls, so nothing extra to install.

Note on privacy: on Google's free tier, content you send may be used to improve
Google's products. Use it with made-up demo data only; real patients need a paid
plan with a data agreement, and the clinic's consent.
"""
import base64
import json
import math
import os
import urllib.error
import urllib.request

from app.ai import offline_rules


class AIError(Exception):
    """The AI service could not give an answer. Callers fall back to the manual way."""


def report_fallback(where: str, err: Exception) -> None:
    """Print why the AI was skipped, so it shows in the backend terminal.
    The message never contains the parent's text or the API key."""
    if isinstance(err, AIError) and str(err) == "No AI model is configured":
        return  # offline on purpose; nothing to report
    print(f"[AI] {where}: AI failed, used the fallback. Reason: {err}", flush=True)


class OfflineProvider:
    name = "offline"

    def generate_json(self, prompt: str, schema: dict | None = None, image: tuple[bytes, str] | None = None) -> dict:
        raise AIError("No AI model is configured")

    def embed(self, texts: list[str], kind: str = "document") -> list[list[float]]:
        return [offline_rules.embed(t) for t in texts]


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str, embed_model: str, base_url: str, timeout: float = 30.0):
        self.api_key = api_key
        self.model = model
        self.embed_model = embed_model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # ------------------------------------------------------------ HTTP

    def _post(self, path: str, body: dict) -> dict:
        req = urllib.request.Request(
            f"{self.base_url}/{path}",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:500]
            if e.code == 429:
                raise AIError("The free AI limit was reached. Please try again in a minute.") from e
            raise AIError(f"AI service error {e.code}: {detail}") from e
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise AIError(f"Could not reach the AI service: {e}") from e

    # ------------------------------------------------------------ text and images -> JSON

    def generate_json(self, prompt: str, schema: dict | None = None, image: tuple[bytes, str] | None = None) -> dict:
        parts: list[dict] = [{"text": prompt}]
        if image is not None:
            data, mime = image
            parts.append({"inline_data": {"mime_type": mime, "data": base64.b64encode(data).decode()}})
        config: dict = {"responseMimeType": "application/json", "temperature": 0}
        if schema is not None:
            config["responseSchema"] = schema
        body = {"contents": [{"role": "user", "parts": parts}], "generationConfig": config}
        path = f"models/{self.model}:generateContent"
        try:
            data = self._post(path, body)
        except AIError as e:
            # Some models reject a schema feature; ask again for plain JSON before giving up.
            if schema is None or " 400" not in f" {e}":
                raise
            config.pop("responseSchema")
            data = self._post(path, body)
        return parse_json_reply(data)

    # ------------------------------------------------------------ embeddings

    def embed(self, texts: list[str], kind: str = "document") -> list[list[float]]:
        v2 = self.embed_model.startswith("gemini-embedding-2")
        requests = []
        for text in texts:
            req: dict = {"model": f"models/{self.embed_model}", "output_dimensionality": 768}
            if v2:  # v2 takes the task as part of the text instead of a taskType field
                text = f"task: search result | query: {text}" if kind == "query" else f"title: none | text: {text}"
            else:
                req["taskType"] = "RETRIEVAL_QUERY" if kind == "query" else "RETRIEVAL_DOCUMENT"
            req["content"] = {"parts": [{"text": text}]}
            requests.append(req)
        data = self._post(f"models/{self.embed_model}:batchEmbedContents", {"requests": requests})
        try:
            vectors = [e["values"] for e in data["embeddings"]]
        except (KeyError, TypeError) as e:
            raise AIError("Unexpected embedding reply") from e
        return [normalize(v) for v in vectors]


def parse_json_reply(data: dict) -> dict:
    """Pull the JSON object out of a generateContent reply."""
    try:
        parts = data["candidates"][0]["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts).strip()
    except (KeyError, IndexError, TypeError) as e:
        reason = (data.get("promptFeedback") or {}).get("blockReason") if isinstance(data, dict) else None
        raise AIError(f"The AI gave no answer{f' ({reason})' if reason else ''}") from e
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{"):] if "{" in text else text
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise AIError("The AI answer was not JSON")
    try:
        value = json.loads(text[start:end + 1])
    except json.JSONDecodeError as e:
        raise AIError("The AI answer was not valid JSON") from e
    if not isinstance(value, dict):
        raise AIError("The AI answer was not a JSON object")
    return value


def normalize(v: list[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def get_provider():
    choice = (os.environ.get("AI_PROVIDER") or "").strip().lower()
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if choice == "offline" or (choice == "" and not key):
        return OfflineProvider()
    if not key:
        raise AIError("AI_PROVIDER is gemini but GEMINI_API_KEY is not set")
    return GeminiProvider(
        api_key=key,
        model=os.environ.get("GEMINI_MODEL", "gemini-3.8-flash"),
        embed_model=os.environ.get("GEMINI_EMBED_MODEL", "gemini-embedding-001"),
        base_url=os.environ.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"),
    )

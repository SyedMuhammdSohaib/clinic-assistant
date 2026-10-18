"""AI layer tests. No database and no internet: a tiny fake Gemini server runs locally,
so these check how requests are built and replies are read, not how clever the model is
(that is what evals/ measures)."""
import base64
import json
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from zoneinfo import ZoneInfo

import pytest

from app.ai import faq_match, seizure_text, slip
from app.ai.offline_rules import embed as local_embed
from app.ai.offline_rules import extract_seizure
from app.ai.provider import AIError, GeminiProvider, OfflineProvider, parse_json_reply
from app.ai.redact import redact

NOW = datetime(2026, 10, 14, 16, 0, tzinfo=ZoneInfo("Asia/Karachi"))
FAQS = [
    {"id": "a1", "topic": "first-aid", "question_en": "What should I do during a seizure?", "question_ur": "دورہ پڑے تو کیا کریں؟",
     "answer_en": "Lay your child on their side.", "answer_ur": "بچے کو کروٹ کے بل لٹائیں۔"},
    {"id": "a2", "topic": "video", "question_en": "Should I record the seizure on video?", "question_ur": "کیا ویڈیو بنا لیں؟",
     "answer_en": "Yes, if it is safe.", "answer_ur": "جی ہاں۔"},
]


# ---------------------------------------------------------------- fake Gemini

class FakeGemini(BaseHTTPRequestHandler):
    replies: list = []      # queued (status, body) for generateContent
    requests: list = []

    def log_message(self, *args):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FakeGemini.requests.append({"path": self.path, "key": self.headers.get("x-goog-api-key"), "body": body})
        if self.path.endswith(":batchEmbedContents"):
            out = {"embeddings": [{"values": [v * 3 for v in local_embed(r["content"]["parts"][0]["text"])]}
                                  for r in body["requests"]]}
            return self._send(200, out)
        status, reply = FakeGemini.replies.pop(0) if FakeGemini.replies else (200, {})
        self._send(status, reply)

    def _send(self, status, obj):
        data = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def reply(obj, fenced=False):
    text = json.dumps(obj)
    if fenced:
        text = f"```json\n{text}\n```"
    return 200, {"candidates": [{"content": {"parts": [{"text": text}]}}]}


@pytest.fixture(scope="module")
def gemini():
    server = HTTPServer(("127.0.0.1", 0), FakeGemini)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield GeminiProvider("test-key", "gemini-test-flash", "gemini-embedding-001",
                         f"http://127.0.0.1:{server.server_port}/v1beta", timeout=5)
    server.shutdown()


@pytest.fixture(autouse=True)
def clean_fake():
    FakeGemini.replies.clear()
    FakeGemini.requests.clear()


# ---------------------------------------------------------------- redaction

def test_redact_removes_personal_details_but_keeps_medical_facts():
    text = "Ayaan Khan ko kal 3 minute dora para. Mera number 0300-1234567, CNIC 35202-1234567-1, a@b.com. Dose 7.5 ml on 2026-10-13"
    out = redact(text, ["Ayaan Khan", "Sana"])
    assert "Ayaan" not in out and "Khan" not in out and "0300" not in out and "35202" not in out and "a@b.com" not in out
    assert "3 minute" in out and "7.5 ml" in out and "2026-10-13" in out


# ---------------------------------------------------------------- seizure messages

def test_rules_baseline_reads_roman_urdu_and_urdu():
    r = extract_seizure("kal raat 3 minute dora para, bukhar bhi tha", NOW)
    assert r["duration_seconds"] == 180 and r["fever_present"] is True
    assert r["occurred_at"].isoformat() == "2026-10-13T22:00:00+05:00"
    r = extract_seizure("ابھی ایک منٹ جھٹکے آئے، بخار نہیں", NOW)
    assert r["duration_seconds"] == 60 and r["fever_present"] is False and r["seizure_type"] == "shaking"


def test_extract_with_ai(gemini):
    FakeGemini.replies.append(reply({
        "is_seizure_report": True, "occurred_at": "2026-10-13T22:00:00+05:00", "duration_seconds": 180,
        "seizure_type": "shaking", "fever_present": True, "went_to_er": None, "summary_en": "3 minute seizure last night with fever"}))
    r = seizure_text.extract("Ayaan ko kal raat 3 minute jhatke, bukhar tha. 03001234567", NOW, gemini, ["Ayaan"])
    assert r["source"] == "ai" and r["draft"]["duration_seconds"] == 180 and r["missing"] == []
    sent = FakeGemini.requests[0]
    assert sent["key"] == "test-key" and sent["path"].endswith("/models/gemini-test-flash:generateContent")
    prompt = sent["body"]["contents"][0]["parts"][0]["text"]
    assert "Ayaan" not in prompt and "03001234567" not in prompt and "[NAME]" in prompt
    assert "2026-10-14T16:00" in prompt
    cfg = sent["body"]["generationConfig"]
    assert cfg["responseMimeType"] == "application/json" and cfg["temperature"] == 0 and "responseSchema" in cfg


def test_extract_rejects_impossible_ai_values(gemini):
    FakeGemini.replies.append(reply({
        "is_seizure_report": True, "occurred_at": "2026-10-20T10:00:00+05:00", "duration_seconds": -5,
        "seizure_type": "dancing", "fever_present": "yes", "went_to_er": None, "summary_en": "x"}))
    r = seizure_text.extract("kuch bhi", NOW, gemini)
    assert r["draft"] == {"occurred_at": None, "duration_seconds": None, "seizure_type": None,
                          "fever_present": None, "went_to_er": None}
    assert set(r["missing"]) == {"occurred_at", "duration_seconds"}


def test_extract_falls_back_to_rules_when_ai_fails(gemini):
    FakeGemini.replies.append((429, {"error": "quota"}))
    r = seizure_text.extract("kal raat 3 minute dora para", NOW, gemini)
    assert r["source"] == "rules" and r["draft"]["duration_seconds"] == 180


def test_schema_rejected_then_plain_json(gemini):
    FakeGemini.replies.extend([(400, {"error": "schema"}), reply({"is_seizure_report": False, "occurred_at": None,
                               "duration_seconds": None, "seizure_type": None, "fever_present": None,
                               "went_to_er": None, "summary_en": "question about timing"}, fenced=True)])
    r = seizure_text.extract("dawai ka time kya hai?", NOW, gemini)
    assert r["is_seizure_report"] is False and r["source"] == "ai"
    assert "responseSchema" not in FakeGemini.requests[1]["body"]["generationConfig"]


def test_parse_json_reply_errors():
    with pytest.raises(AIError):
        parse_json_reply({"promptFeedback": {"blockReason": "SAFETY"}})
    with pytest.raises(AIError):
        parse_json_reply({"candidates": [{"content": {"parts": [{"text": "not json"}]}}]})


# ---------------------------------------------------------------- approved answers

def test_match_offline_shows_only_close_matches():
    off = OfflineProvider()
    assert faq_match.match(None, FAQS, "What should I do during a seizure?", off)["topic"] == "first-aid"
    assert faq_match.match(None, FAQS, "Doctor ki fees kitni hai?", off) is None


def test_match_with_ai_check(gemini):
    FakeGemini.replies.append(reply({"choice": 1}))
    found = faq_match.match(None, FAQS, "jab dora pare to kya karein", gemini)
    assert found is not None and found["method"] == "embedding+ai-check"
    embed_calls = [r for r in FakeGemini.requests if r["path"].endswith(":batchEmbedContents")]
    assert embed_calls and embed_calls[0]["body"]["requests"][0]["taskType"] == "RETRIEVAL_DOCUMENT"
    assert embed_calls[-1]["body"]["requests"][0]["taskType"] == "RETRIEVAL_QUERY"
    # The answer shown is the approved text, never something the model wrote.
    assert found["answer_en"] in {f["answer_en"] for f in FAQS}


def test_match_ai_says_none_or_nonsense(gemini):
    FakeGemini.replies.append(reply({"choice": None}))
    assert faq_match.match(None, FAQS, "school ja sakta hai?", gemini) is None
    FakeGemini.replies.append(reply({"choice": 7}))
    assert faq_match.match(None, FAQS, "school ja sakta hai?", gemini) is None


# ---------------------------------------------------------------- prescription photos

def test_read_slip_sends_the_image_and_cleans_the_reply(gemini):
    FakeGemini.replies.append(reply({"is_prescription": True, "items": [
        {"drug_name": "Levetiracetam", "dose_amount": 5, "dose_unit": "ml", "times_per_day": 2, "instructions": None, "legible": True},
        {"drug_name": "Panadol syrup", "dose_amount": None, "dose_unit": None, "times_per_day": 99, "instructions": "SOS for fever", "legible": False},
        {"drug_name": "", "dose_amount": 1, "dose_unit": "x", "times_per_day": 1, "instructions": None, "legible": True},
    ]}))
    image = b"\xff\xd8\xff" + b"0" * 50
    out = slip.read_slip(image, "image/jpeg", gemini)
    assert [i["drug_name"] for i in out["items"]] == ["Levetiracetam", "Panadol syrup"]
    assert out["items"][1]["times_per_day"] is None and out["items"][1]["legible"] is False
    part = FakeGemini.requests[0]["body"]["contents"][0]["parts"][1]["inline_data"]
    assert part["mime_type"] == "image/jpeg" and base64.b64decode(part["data"]) == image


def test_read_slip_needs_ai():
    with pytest.raises(AIError):
        slip.read_slip(b"\xff\xd8\xff", "image/jpeg", OfflineProvider())

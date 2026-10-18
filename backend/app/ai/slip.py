"""Read medicines from a photo of a prescription or discharge slip.

The reading is a suggestion: the parent confirms it, and nothing reaches the medicine
list until the doctor reviews the photo and approves each medicine.
"""
from app.ai.provider import AIError

MAX_ITEMS = 20

SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "is_prescription": {"type": "BOOLEAN"},
        "items": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "drug_name": {"type": "STRING"},
                    "dose_amount": {"type": "NUMBER", "nullable": True},
                    "dose_unit": {"type": "STRING", "nullable": True},
                    "times_per_day": {"type": "INTEGER", "nullable": True},
                    "instructions": {"type": "STRING", "nullable": True},
                    "legible": {"type": "BOOLEAN"},
                },
                "required": ["drug_name", "dose_amount", "dose_unit", "times_per_day", "instructions", "legible"],
            },
        },
    },
    "required": ["is_prescription", "items"],
}

PROMPT = """This photo should be a doctor's prescription or hospital discharge slip from
Pakistan. It may be handwritten, in English, Urdu or both. List every medicine on it.

For each medicine:
- drug_name: as written (brand or generic). Do not correct or substitute it.
- dose_amount and dose_unit: e.g. 5 and "ml", 250 and "mg", 1 and "tablet". null if unclear.
- times_per_day: 1 for OD, 2 for BD, 3 for TDS, 4 for QID; null for SOS / as needed or unclear.
- instructions: any other words as written (e.g. "SOS for fever", "after food"), or null.
- legible: false if you are not sure you read the name or dose correctly.

Do not add medicines that are not written. Do not give medical advice.
If the photo is not a prescription, set is_prescription to false and items to []."""


def _number(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def read_slip(image: bytes, mime: str, provider) -> dict:
    """Returns {"is_prescription": bool, "items": [...]}. Raises AIError when no AI is available."""
    raw = provider.generate_json(PROMPT, SCHEMA, image=(image, mime))
    items = []
    for it in (raw.get("items") or [])[:MAX_ITEMS]:
        if not isinstance(it, dict) or not str(it.get("drug_name") or "").strip():
            continue
        dose = _number(it.get("dose_amount"))
        times = it.get("times_per_day")
        items.append({
            "drug_name": str(it["drug_name"]).strip()[:200],
            "dose_amount": dose if dose is not None and 0 < dose < 1_000_000 else None,
            "dose_unit": (str(it["dose_unit"]).strip()[:20] or None) if it.get("dose_unit") else None,
            "times_per_day": times if isinstance(times, int) and not isinstance(times, bool) and 1 <= times <= 12 else None,
            "instructions": (str(it["instructions"]).strip()[:300] or None) if it.get("instructions") else None,
            "legible": it.get("legible") is not False,
        })
    return {"is_prescription": raw.get("is_prescription") is not False and bool(items), "items": items}


__all__ = ["read_slip", "AIError"]

"""rfp.extract_requirements: implicit requirements from the DOCX narrative, via Mubit."""
from app.ingest import packages
from app.llm import mubit_client

EXTRACT_SCHEMA = {
    "type": "object",
    "properties": {
        "requirements": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "source_section": {"type": "string"},
                    "category": {"type": "string"},
                    "mandatory": {"type": "boolean"},
                },
                "required": ["text", "source_section", "category", "mandatory"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["requirements"],
    "additionalProperties": False,
}

MAX_CHARS = 12000


def extract(slug: str) -> dict:
    doc = packages.narrative(slug)
    reqs = packages.requirements(slug)
    narrative = "\n\n".join(f"## {s['heading']}\n{s['text']}" for s in doc["sections"])[:MAX_CHARS]
    known = "\n".join(f"{r.id}: {r.text}" for r in reqs)
    user = f"WORKBOOK REQUIREMENTS ALREADY CAPTURED\n{known}\n\nRFP NARRATIVE\n{narrative}"
    res = mubit_client.call("rfp.extract_requirements", user, EXTRACT_SCHEMA)
    items = res["output"]["requirements"]
    for i, item in enumerate(items, start=1):
        item["id"] = f"N-{i:03d}"
    return {"requirements": items, "request_id": res["request_id"]}

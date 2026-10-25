"""PII scrubbing before anything is sent to Mubit (README §4.3).

Plain code, conservative: the review only needs to know that an identity
check happened, never the values. Raw text stays in the local database.
"""
import json
import re
from functools import lru_cache

from app.config import CUSTOMERS_PATH

_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("[EMAIL]", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b")),
    ("[CARD]", re.compile(r"\b(?:\d[ -]?){12,18}\d\b")),
    ("[SORT_CODE]", re.compile(r"\b\d{2}[- ]\d{2}[- ]\d{2}\b")),
    ("[PHONE]", re.compile(r"(?:\+44\s?7\d{3}|\b07\d{3})\s?\d{3}\s?\d{3}\b")),
    ("[ACCOUNT]", re.compile(r"\b\d{8}\b")),
    ("[POSTCODE]", re.compile(r"\b[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}\b", re.I)),
    # Dates with a plausible birth year (1920-2012), in common spoken and written forms
    ("[DOB]", re.compile(
        r"\b(?:\d{1,2}(?:st|nd|rd|th)?(?:\s+of)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*,?\s+(?:19[2-9]\d|200\d|201[0-2])"
        r"|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{1,2}(?:st|nd|rd|th)?,?\s+(?:19[2-9]\d|200\d|201[0-2])"
        r"|\d{1,2}[/.-]\d{1,2}[/.-](?:19[2-9]\d|200\d|201[0-2]))\b", re.I)),
    ("[ADDRESS]", re.compile(
        r"\b\d{1,4}[a-z]?\s+(?:[A-Z][a-z]+\s){1,3}(?:Street|St|Road|Rd|Lane|Ln|Avenue|Ave|Drive|Dr|Close|Way|Place|Court|Crescent|Terrace|Gardens|Grove)\b")),
]


def _luhn_ok(digits: str) -> bool:
    total, alt = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if alt:
            d = d * 2 - 9 if d > 4 else d * 2
        total, alt = total + d, not alt
    return total % 10 == 0


@lru_cache(maxsize=1)
def _known_names() -> list[re.Pattern]:
    """Customer names from the (synthetic) customer records, longest first."""
    if not CUSTOMERS_PATH.exists():
        return []
    # Case-sensitive, so a first name like "Will" doesn't hit the word "will".
    return _name_patterns([c.get("name", "") for c in json.loads(CUSTOMERS_PATH.read_text(encoding="utf-8"))])


def _name_patterns(names: list[str]) -> list[re.Pattern]:
    parts = set()
    for full in names:
        full = (full or "").strip()
        if full:
            parts.add(full)
            parts.update(p for p in full.split() if len(p) > 2)
    return [re.compile(rf"\b{re.escape(n)}\b") for n in sorted(parts, key=len, reverse=True)]


def spans(text: str, extra_names: list[str] | None = None) -> list[tuple[int, int, str]]:
    """Character spans to redact in the original text, as (start, end, token), non-overlapping.

    Earlier patterns win over later ones. Used for the text sent to Mubit and to
    find which spoken words to silence in the stored audio.
    """
    found: list[tuple[int, int, str]] = []

    def free(a: int, b: int) -> bool:
        return all(b <= s or a >= e for s, e, _ in found)

    for token, pat in _PATTERNS:
        for m in pat.finditer(text):
            if token == "[CARD]" and not _luhn_ok(re.sub(r"\D", "", m.group(0))):
                continue
            if free(m.start(), m.end()):
                found.append((m.start(), m.end(), token))
    for pat in _name_patterns(extra_names or []) + _known_names():
        for m in pat.finditer(text):
            if free(m.start(), m.end()):
                found.append((m.start(), m.end(), "[NAME]"))
    return sorted(found)


def redact(text: str, extra_names: list[str] | None = None) -> str:
    """extra_names: names known for this call (e.g. the customer typed on the Live call page)."""
    out, last = [], 0
    for s, e, token in spans(text, extra_names):
        out.append(text[last:s])
        out.append(token)
        last = e
    out.append(text[last:])
    return "".join(out)

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
    names = set()
    for c in json.loads(CUSTOMERS_PATH.read_text(encoding="utf-8")):
        full = c.get("name", "").strip()
        if full:
            names.add(full)
            names.update(p for p in full.split() if len(p) > 2)
    # Case-sensitive, so a first name like "Will" doesn't hit the word "will".
    return [re.compile(rf"\b{re.escape(n)}\b") for n in sorted(names, key=len, reverse=True)]


def redact(text: str) -> str:
    out = text
    for token, pat in _PATTERNS:
        if token == "[CARD]":
            out = pat.sub(lambda m: "[CARD]" if _luhn_ok(re.sub(r"\D", "", m.group(0))) else m.group(0), out)
        else:
            out = pat.sub(token, out)
    for pat in _known_names():
        out = pat.sub("[NAME]", out)
    return out

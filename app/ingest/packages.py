"""RFP package registry: each folder under data/rfps holds one DOCX and one XLSX."""
import json
import re
from functools import lru_cache
from pathlib import Path

from app.config import EVAL_DIR, RFPS
from app.ingest.docx_parser import parse_docx
from app.ingest.xlsx_parser import parse_requirements, read_meta
from app.models import Requirement

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


def package_dir(slug: str) -> Path:
    if not SLUG_RE.match(slug):
        raise KeyError(slug)
    for base in (RFPS, RFPS / "uploads"):
        d = base / slug
        if d.is_dir():
            return d
    raise KeyError(slug)


def _files(d: Path) -> tuple[Path | None, Path | None]:
    docx = next(iter(sorted(d.glob("*.docx"))), None)
    xlsx = next(iter(sorted(d.glob("*.xlsx"))), None)
    return docx, xlsx


def list_packages() -> list[dict]:
    out = []
    for base in (RFPS, RFPS / "uploads"):
        if not base.is_dir():
            continue
        for d in sorted(p for p in base.iterdir() if p.is_dir() and p.name != "uploads"):
            try:
                out.append(package_info(d.name))
            except Exception as exc:  # malformed upload: list it with the error
                out.append({"slug": d.name, "error": str(exc)})
    return out


def package_info(slug: str) -> dict:
    d = package_dir(slug)
    docx, xlsx = _files(d)
    meta = read_meta(xlsx) if xlsx else {}
    reqs = parse_requirements(xlsx) if xlsx else []
    return {
        "slug": slug,
        "reference": meta.get("RFP reference"),
        "client": meta.get("Client"),
        "opportunity": meta.get("Opportunity"),
        "deadline": meta.get("Response deadline"),
        "docx": docx.name if docx else None,
        "xlsx": xlsx.name if xlsx else None,
        "sheets": meta.get("sheets", []),
        "requirement_count": len(reqs),
        "has_gold": gold_path(slug).exists(),
        "uploaded": d.parent.name == "uploads",
    }


def requirements(slug: str) -> list[Requirement]:
    _, xlsx = _files(package_dir(slug))
    return parse_requirements(xlsx) if xlsx else []


@lru_cache(maxsize=16)
def _narrative_cached(path: str, mtime: float) -> dict:
    return parse_docx(Path(path))


def narrative(slug: str) -> dict:
    docx, _ = _files(package_dir(slug))
    if not docx:
        return {"reference": None, "title": "", "sections": []}
    return _narrative_cached(str(docx), docx.stat().st_mtime)


def gold_path(slug: str) -> Path:
    return EVAL_DIR / f"gold_{slug}.jsonl"


def gold(slug: str) -> dict[str, dict]:
    p = gold_path(slug)
    if not p.exists():
        return {}
    rows = [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {r["id"]: r for r in rows}


def xlsx_path(slug: str) -> Path | None:
    return _files(package_dir(slug))[1]

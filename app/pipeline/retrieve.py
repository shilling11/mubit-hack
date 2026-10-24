"""Evidence retrieval over data/company_kb (BM25, no LLM)."""
import re
from functools import lru_cache

from rank_bm25 import BM25Okapi

from app.config import KB_DIR, KB_TOP_K
from app.models import Evidence

STOP = set(
    "a an and are as at be by for from has have in is it its of on or that the this to with will must all any "
    "our your their we you they be been not no can may shall should provide support including".split()
)
TOKEN_RE = re.compile(r"[a-z0-9]+(?:\.[0-9]+)?")


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN_RE.findall(text.lower()) if t not in STOP]


def slugify(heading: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")


@lru_cache(maxsize=1)
def passages() -> list[Evidence]:
    out: list[Evidence] = []
    for path in sorted(KB_DIR.glob("*.md")):
        doc_title = ""
        current: tuple[str, list[str]] | None = None
        for line in path.read_text(encoding="utf-8").splitlines() + ["## "]:
            if line.startswith("# "):
                doc_title = line[2:].strip()
            elif line.startswith("## "):
                if current and "".join(current[1]).strip():
                    heading, body = current
                    out.append(Evidence(
                        id=f"{path.stem}#{slugify(heading)}",
                        source=doc_title or path.stem,
                        title=heading,
                        text=" ".join(l.strip() for l in body if l.strip()),
                    ))
                current = (line[3:].strip(), [])
            elif current is not None:
                current[1].append(line)
    return out


@lru_cache(maxsize=1)
def _index() -> BM25Okapi:
    return BM25Okapi([tokenize(f"{p.title} {p.title} {p.text}") for p in passages()])


def by_id() -> dict[str, Evidence]:
    return {p.id: p for p in passages()}


def retrieve(query: str, k: int = KB_TOP_K) -> list[Evidence]:
    scores = _index().get_scores(tokenize(query))
    ranked = sorted(zip(scores, passages()), key=lambda x: -x[0])[:k]
    return [p.model_copy(update={"score": round(float(s), 3)}) for s, p in ranked if s > 0]


def rank_texts(query: str, texts: list[str]) -> list[float]:
    """BM25 scores of `query` against an ad-hoc list of texts (used for playbook examples)."""
    if not texts:
        return []
    return list(BM25Okapi([tokenize(t) or ["_"] for t in texts]).get_scores(tokenize(query)))

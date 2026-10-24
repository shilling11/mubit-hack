"""Deterministic DOCX parsing into ordered sections (paragraphs and tables)."""
import re
from pathlib import Path

import docx
from docx.table import Table
from docx.text.paragraph import Paragraph

REF_RE = re.compile(r"RFP reference:\s*([A-Z0-9][A-Z0-9-]+)")


def _blocks(doc):
    for child in doc.element.body.iterchildren():
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            yield Paragraph(child, doc)
        elif tag == "tbl":
            yield Table(child, doc)


def parse_docx(path: Path) -> dict:
    doc = docx.Document(path)
    sections: list[dict] = [{"heading": "Front matter", "level": 0, "text": ""}]
    reference = None
    for block in _blocks(doc):
        if isinstance(block, Paragraph):
            text = block.text.strip()
            if not text:
                continue
            if reference is None and (m := REF_RE.search(text)):
                reference = m.group(1)
            style = block.style.name if block.style is not None else ""
            if style.startswith("Heading"):
                level = int(style.split()[-1]) if style.split()[-1].isdigit() else 1
                sections.append({"heading": text, "level": level, "text": ""})
                continue
            prefix = "- " if "List" in style else ""
            sections[-1]["text"] += f"{prefix}{text}\n"
        else:
            rows = [" | ".join(c.text.strip() for c in row.cells) for row in block.rows]
            sections[-1]["text"] += "\n".join(rows) + "\n"
    sections = [s for s in sections if s["text"].strip()]
    title_lines = sections[0]["text"].splitlines()[:3] if sections else []
    return {"reference": reference, "title": " ".join(title_lines), "sections": sections}

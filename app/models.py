from typing import Literal

from pydantic import BaseModel, Field

Status = Literal["Comply", "Partially Comply", "Do Not Comply", "Not Applicable"]
STATUSES: list[str] = ["Comply", "Partially Comply", "Do Not Comply", "Not Applicable"]


class Requirement(BaseModel):
    id: str
    sheet: str  # "Requirements" | "Security Questionnaire" | "Narrative"
    category: str = ""
    text: str
    priority: str = ""
    mandatory: str = ""
    row: int | None = None  # 1-based row in the sheet, for write-back


class Evidence(BaseModel):
    id: str  # "<kb file stem>#<heading slug>"
    source: str
    title: str
    text: str
    score: float = 0.0


class DraftOutput(BaseModel):
    status: Status
    response: str
    evidence_ids: list[str] = Field(default_factory=list)
    gaps: str = ""
    confidence: float = 0.0


class CorrectionIn(BaseModel):
    run_id: str
    req_id: str
    status: Status
    response: str
    evidence_ids: list[str] = Field(default_factory=list)
    gaps: str = ""
    rationale: str
    editor: str = "demo-bid-manager"


class RunIn(BaseModel):
    package: str
    playbook_version: int | None = None  # None = latest, 0 = no playbook
    model: str | None = None
    label: str | None = None
    sheets: list[str] | None = None  # restrict to some sheets
    req_ids: list[str] | None = None  # restrict to some requirements

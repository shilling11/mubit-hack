"""Redline API. Run with: uvicorn app.main:app --reload"""
import os
import re
import shutil
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app import db
from app.config import BASELINE_MODEL, MUBIT_API_KEY, MUBIT_BASE_URL, MUBIT_MODEL, RFPS
from app.ingest import packages
from app.ingest.docx_parser import parse_docx
from app.ingest.xlsx_parser import read_meta
from app.learning import corrections, playbook
from app.llm.mubit_client import MubitError
from app.models import CorrectionIn, RunIn
from app.pipeline import runner
from app.pipeline.extract import extract
from app.pipeline.retrieve import by_id, passages
from app.pipeline.summarise import summarise
from app.pipeline.verify import verify_draft


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init()
    db.execute("UPDATE runs SET status = 'interrupted' WHERE status = 'running'")
    yield


app = FastAPI(title="Redline", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("REDLINE_WEB_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


def _404(fn, *args):
    try:
        return fn(*args)
    except KeyError as exc:
        raise HTTPException(404, f"Not found: {exc}") from exc


def _mubit(fn, *args):
    try:
        return fn(*args)
    except MubitError as exc:
        raise HTTPException(502, {"error": str(exc), "request_id": exc.request_id}) from exc


# ── Status ───────────────────────────────────────────────────────────────────
@app.get("/api/status")
def status():
    t = db.one(
        "SELECT COUNT(*) AS calls, SUM(ok = 0) AS errors, SUM(served_by IS NOT NULL AND served_by != model_asked) AS routed "
        "FROM traces"
    )
    served = db.query("SELECT served_by, COUNT(*) AS n FROM traces WHERE ok = 1 GROUP BY served_by ORDER BY n DESC")
    return {
        "mubit": {"base_url": MUBIT_BASE_URL, "key_set": bool(MUBIT_API_KEY), "model": MUBIT_MODEL,
                  "baseline_model": BASELINE_MODEL},
        "playbook_version": playbook.latest_version(),
        "corrections": len(corrections.all_corrections()),
        "pending_corrections": _pending_corrections(),
        "calls": t["calls"] or 0,
        "errors": t["errors"] or 0,
        "routed_to_other_model": t["routed"] or 0,
        "served_by": served,
    }


def _pending_corrections() -> int:
    v = playbook.latest_version()
    included = set(playbook.get_version(v)["correction_ids"]) if v else set()
    return sum(1 for c in corrections.all_corrections() if c["id"] not in included)


# ── Packages ─────────────────────────────────────────────────────────────────
@app.get("/api/packages")
def list_packages():
    return packages.list_packages()


@app.get("/api/packages/{slug}")
def get_package(slug: str):
    info = _404(packages.package_info, slug)
    return {**info, "requirements": [r.model_dump() for r in packages.requirements(slug)]}


@app.get("/api/packages/{slug}/narrative")
def get_narrative(slug: str):
    return _404(packages.narrative, slug)


@app.post("/api/packages/{slug}/extract")
def extract_requirements(slug: str):
    _404(packages.package_dir, slug)
    return _mubit(extract, slug)


@app.post("/api/packages/upload")
async def upload_package(docx: UploadFile = File(...), xlsx: UploadFile = File(...)):
    if not (docx.filename or "").lower().endswith(".docx") or not (xlsx.filename or "").lower().endswith(".xlsx"):
        raise HTTPException(400, "Upload one .docx and one .xlsx")
    with tempfile.TemporaryDirectory() as tmp:
        d_path, x_path = Path(tmp) / "rfp.docx", Path(tmp) / "exhibits.xlsx"
        d_path.write_bytes(await docx.read())
        x_path.write_bytes(await xlsx.read())
        try:
            doc_ref = parse_docx(d_path)["reference"]
            xls_ref = read_meta(x_path).get("RFP reference")
        except Exception as exc:
            raise HTTPException(400, f"Could not parse package: {exc}") from exc
        if doc_ref and xls_ref and doc_ref != xls_ref:
            raise HTTPException(400, f"Reference mismatch: DOCX {doc_ref} vs XLSX {xls_ref}")
        ref = doc_ref or xls_ref or Path(docx.filename).stem
        slug = re.sub(r"[^a-z0-9]+", "-", ref.lower()).strip("-")[:60] or "upload"
        dest = RFPS / "uploads" / slug
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)
        shutil.copy(d_path, dest / Path(docx.filename).name)
        shutil.copy(x_path, dest / Path(xlsx.filename).name)
    return {**packages.package_info(slug), "shared_reference": ref, "references_match": bool(doc_ref and xls_ref)}


# ── Knowledge base ───────────────────────────────────────────────────────────
@app.get("/api/kb")
def kb():
    return [p.model_dump() for p in passages()]


@app.get("/api/kb/{passage_id:path}")
def kb_passage(passage_id: str):
    p = by_id().get(passage_id)
    if not p:
        raise HTTPException(404, passage_id)
    return p.model_dump()


# ── Runs ─────────────────────────────────────────────────────────────────────
@app.post("/api/runs")
def create_run(spec: RunIn):
    try:
        return runner.start(spec)
    except (KeyError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc


@app.get("/api/runs")
def list_runs(package: str | None = None):
    return runner.list_runs(package)


@app.get("/api/runs/{run_id}")
def get_run(run_id: str):
    run = _404(runner.get, run_id)
    return {**run, "drafts": runner.get_drafts(run_id)}


@app.post("/api/runs/{run_id}/verify/{req_id}")
def verify(run_id: str, req_id: str):
    d = db.one("SELECT * FROM drafts WHERE run_id = ? AND req_id = ?", (run_id, req_id))
    if not d or not d.get("status"):
        raise HTTPException(404, "Draft not found or not drafted yet")
    result = _mubit(verify_draft, d, run_id)
    db.update("drafts", {"run_id": run_id, "req_id": req_id}, {"verify_json": result})
    return result


@app.post("/api/runs/{run_id}/summary")
def run_summary(run_id: str):
    run = _404(runner.get, run_id)
    return _mubit(summarise, run, runner.get_drafts(run_id), packages.package_info(run["package"]))


@app.get("/api/runs/{run_id}/export")
def export(run_id: str):
    from app.export.writeback import export_run

    run = _404(runner.get, run_id)
    path = export_run(run, runner.get_drafts(run_id))
    return FileResponse(path, filename=path.name,
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@app.get("/api/compare")
def compare(a: str, b: str):
    ra, rb = _404(runner.get, a), _404(runner.get, b)
    da = {d["req_id"]: d for d in runner.get_drafts(a)}
    db_ = {d["req_id"]: d for d in runner.get_drafts(b)}
    gold = packages.gold(rb["package"])
    rows = []
    for rid in da.keys() | db_.keys():
        rows.append({"req_id": rid, "a": da.get(rid), "b": db_.get(rid), "gold": gold.get(rid)})
    order = list(db_.keys()) + [k for k in da if k not in db_]
    rows.sort(key=lambda r: order.index(r["req_id"]))
    return {"a": ra, "b": rb, "rows": rows}


# ── Learning ─────────────────────────────────────────────────────────────────
@app.post("/api/corrections")
def teach(c: CorrectionIn):
    try:
        return corrections.submit(c)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.get("/api/corrections")
def list_corrections():
    return corrections.all_corrections()


@app.delete("/api/corrections/{cid}")
def delete_correction(cid: int):
    corrections.delete(cid)
    return {"deleted": cid}


@app.post("/api/corrections/seed")
def seed_corrections():
    return {"loaded": corrections.load_seed()}


@app.get("/api/playbook")
def get_playbook():
    return playbook.versions()


@app.post("/api/playbook/build")
def build_playbook():
    try:
        return _mubit(playbook.build)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


# ── Traces ───────────────────────────────────────────────────────────────────
@app.get("/api/traces")
def traces(limit: int = 50, run_id: str | None = None):
    limit = max(1, min(limit, 500))
    if run_id:
        return db.query("SELECT * FROM traces WHERE run_id = ? ORDER BY id DESC LIMIT ?", (run_id, limit))
    return db.query("SELECT * FROM traces ORDER BY id DESC LIMIT ?", (limit,))

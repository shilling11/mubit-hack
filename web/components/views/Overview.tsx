"use client";

import { Download, FileUp, Play, ScrollText, Sparkles } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { api, type Draft, type Run, type Status } from "@/lib/api";
import type { Ctx } from "@/lib/ctx";
import { Button, Card, Empty, Mono, SectionTitle, Select, Shield, Stat, StatusPill } from "../ui";

const SPLIT: { s: Status; cls: string }[] = [
  { s: "Comply", cls: "bg-comply" },
  { s: "Partially Comply", cls: "bg-partial" },
  { s: "Do Not Comply", cls: "bg-dnc" },
  { s: "Not Applicable", cls: "bg-na" },
];

export function useRunDrafts(runId: string | null, runs: Run[]) {
  const [data, setData] = useState<(Run & { drafts: Draft[] }) | null>(null);
  const status = runs.find((r) => r.id === runId)?.status;
  const done = runs.find((r) => r.id === runId)?.done;
  useEffect(() => {
    if (runId) api.run(runId).then(setData).catch(() => setData(null));
  }, [runId, status, done]);
  // Only expose data that belongs to the selected run
  return [data && data.id === runId ? data : null, setData] as const;
}

export function RunPicker({ runs, runId, setRunId }: Pick<Ctx, "runs" | "runId" | "setRunId">) {
  if (!runs.length) return null;
  return (
    <Select
      value={runId ?? ""}
      onChange={setRunId}
      options={runs.map((r) => ({
        value: r.id,
        label: `${r.label} · ${new Date(r.created * 1000).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" })}${
          r.status === "running" ? ` · ${r.done}/${r.total}` : r.status !== "done" ? ` · ${r.status}` : ""
        }`,
      }))}
    />
  );
}

export function StartRun({ ctx, compact }: { ctx: Ctx; compact?: boolean }) {
  const latest = ctx.status?.playbook_version ?? 0;
  const [version, setVersion] = useState<string>("latest");
  const [model, setModel] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const models = ctx.status ? [ctx.status.mubit.model, ctx.status.mubit.baseline_model] : [];

  async function start() {
    setBusy(true);
    try {
      const run = await api.startRun({
        package: ctx.pkg,
        playbook_version: version === "latest" ? null : Number(version),
        model: model || null,
      });
      await ctx.refreshRuns();
      ctx.setRunId(run.id);
      ctx.notify(`Drafting ${run.total} requirements through Mubit…`);
    } catch (e) {
      ctx.notify(`Could not start run: ${(e as Error).message}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Select
        value={version}
        onChange={setVersion}
        options={[
          { value: "latest", label: `Playbook v${latest} (latest)` },
          ...Array.from({ length: latest }, (_, i) => latest - 1 - i).map((v) => ({
            value: String(v),
            label: v === 0 ? "v0 · base, no playbook" : `Playbook v${v}`,
          })),
        ]}
      />
      {!compact && models.length > 0 && (
        <Select
          value={model}
          onChange={setModel}
          options={[{ value: "", label: `${models[0]} (task model)` }, ...models.slice(1).map((m) => ({ value: m, label: `${m} (closed baseline)` }))]}
        />
      )}
      <Button variant="primary" onClick={start} loading={busy}>
        <Play className="h-3.5 w-3.5" /> Draft with Mubit
      </Button>
    </div>
  );
}

export function Overview(ctx: Ctx) {
  const [run] = useRunDrafts(ctx.runId, ctx.runs);
  // Results are tagged with what they were computed for, so switching RFP or run hides stale ones
  const [extractedFor, setExtracted] = useState<{ pkg: string; reqs: Awaited<ReturnType<typeof api.extract>>["requirements"] } | null>(null);
  const [summaryFor, setSummary] = useState<{ runId: string; data: Awaited<ReturnType<typeof api.summary>> } | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const extracted = extractedFor?.pkg === ctx.pkg ? extractedFor.reqs : null;
  const summary = summaryFor?.runId === ctx.runId ? summaryFor.data : null;

  const drafts = run?.drafts ?? [];
  const drafted = drafts.filter((d) => d.status);
  const counts = Object.fromEntries(SPLIT.map(({ s }) => [s, drafted.filter((d) => d.status === s).length]));
  const flagged = drafted.filter((d) => d.flags?.includes("over_promise_risk"));
  const lowConfidence = drafted.filter((d) => d.flags?.includes("low_confidence"));
  const mandatoryPartial = drafted.filter((d) => d.mandatory === "Yes" && d.status !== "Comply");

  async function upload(files: FileList | null) {
    if (!files || files.length < 2) return ctx.notify("Choose one .docx and one .xlsx together");
    const form = new FormData();
    for (const f of Array.from(files)) form.append(f.name.toLowerCase().endsWith(".docx") ? "docx" : "xlsx", f);
    setBusy("upload");
    try {
      const p = await api.upload(form);
      await ctx.refreshPackages();
      ctx.setPkg(p.slug);
      ctx.notify(`Uploaded ${p.shared_reference}: ${p.requirement_count} requirements parsed`);
    } catch (e) {
      ctx.notify(`Upload failed: ${(e as Error).message}`);
    } finally {
      setBusy(null);
    }
  }

  async function act<T>(name: string, fn: () => Promise<T>, done: (v: T) => void) {
    setBusy(name);
    try {
      done(await fn());
    } catch (e) {
      ctx.notify(`${name} failed: ${(e as Error).message}`);
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="text-xs font-medium uppercase tracking-wider text-muted">{ctx.pkgInfo?.reference}</div>
          <h1 className="font-serif text-3xl font-semibold tracking-tight">{ctx.pkgInfo?.opportunity ?? ctx.pkg}</h1>
          <div className="mt-1 text-sm text-ink-2">
            {ctx.pkgInfo?.client} · response due {ctx.pkgInfo?.deadline ?? "—"}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <input ref={fileRef} type="file" multiple accept=".docx,.xlsx" className="hidden" onChange={(e) => upload(e.target.files)} />
          <Button onClick={() => fileRef.current?.click()} loading={busy === "upload"}>
            <FileUp className="h-3.5 w-3.5" /> Upload RFP package
          </Button>
        </div>
      </div>

      <Card className="flex flex-wrap items-center justify-between gap-4 px-5 py-4">
        <div>
          <div className="text-sm font-medium">Draft every requirement</div>
          <div className="text-xs text-muted">
            One <Mono>rfp.draft_response</Mono> call per row, routed through Mubit, grounded in the company knowledge base.
          </div>
        </div>
        <StartRun ctx={ctx} />
      </Card>

      {!run ? (
        <Empty>No runs for this RFP yet. Draft it with Mubit to fill the matrix.</Empty>
      ) : (
        <>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <SectionTitle>Compliance position</SectionTitle>
            <div className="flex items-center gap-2">
              <RunPicker {...ctx} />
              <a href={api.exportUrl(run.id)}>
                <Button disabled={run.status === "running"}>
                  <Download className="h-3.5 w-3.5" /> Export XLSX
                </Button>
              </a>
            </div>
          </div>

          {run.status === "running" && (
            <div className="h-1.5 overflow-hidden rounded-full bg-line">
              <div className="h-full bg-red transition-all" style={{ width: `${(run.done / Math.max(1, run.total)) * 100}%` }} />
            </div>
          )}

          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Stat label="Requirements" value={`${drafted.length}/${run.total}`} sub={run.label} />
            <Stat
              label="Flagged over-promise"
              value={flagged.length}
              tone={flagged.length ? "red" : "green"}
              sub="Comply without supporting evidence"
            />
            <Stat
              label="Mandatory not Comply"
              value={mandatoryPartial.length}
              sub="Each needs a defensible gap"
            />
            <Stat label="Low confidence" value={lowConfidence.length} sub="Model unsure (< 0.6): review first" />
          </div>

          <Card className="px-5 py-4">
            <div className="flex h-3 overflow-hidden rounded-full bg-line">
              {SPLIT.map(({ s, cls }) =>
                counts[s] ? <div key={s} className={cls} style={{ width: `${(counts[s] / Math.max(1, drafted.length)) * 100}%` }} /> : null,
              )}
            </div>
            <div className="mt-3 flex flex-wrap gap-4 text-sm">
              {SPLIT.map(({ s }) => (
                <span key={s} className="flex items-center gap-2">
                  <StatusPill status={s} short /> <span className="font-medium">{counts[s]}</span>
                </span>
              ))}
            </div>
          </Card>

          {flagged.length > 0 && (
            <div>
              <SectionTitle>Over-promise flags</SectionTitle>
              <div className="space-y-2">
                {flagged.map((d) => (
                  <Card key={d.req_id} className="flex items-start gap-3 px-4 py-3">
                    <Shield ok={false} />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <Mono>{d.req_id}</Mono> <StatusPill status={d.status} short />
                      </div>
                      <div className="mt-1 text-sm">{d.requirement}</div>
                      <div className="mt-1 text-xs text-red">{d.flags?.filter((f) => f !== "over_promise_risk").join(" · ")}</div>
                    </div>
                    <Button variant="ghost" onClick={() => ctx.goto("matrix")}>
                      Review
                    </Button>
                  </Card>
                ))}
              </div>
            </div>
          )}

          <div className="grid gap-4 md:grid-cols-2">
            <Card className="px-5 py-4">
              <div className="flex items-center justify-between">
                <div className="text-sm font-medium">Implicit requirements in the narrative</div>
                <Button
                  onClick={() => act("Extraction", () => api.extract(ctx.pkg), (r) => setExtracted({ pkg: ctx.pkg, reqs: r.requirements }))}
                  loading={busy === "Extraction"}
                >
                  <ScrollText className="h-3.5 w-3.5" /> Extract
                </Button>
              </div>
              <div className="mt-1 text-xs text-muted">
                <Mono>rfp.extract_requirements</Mono> reads the DOCX for requirements the workbook doesn&apos;t list.
              </div>
              {extracted && (
                <ul className="mt-3 space-y-2 text-sm">
                  {extracted.length === 0 && <li className="text-muted">None found.</li>}
                  {extracted.map((r) => (
                    <li key={r.id} className="border-l-2 border-red pl-3">
                      {r.text}
                      <div className="text-xs text-muted">
                        {r.source_section} · {r.category}
                        {r.mandatory ? " · mandatory" : ""}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
            <Card className="px-5 py-4">
              <div className="flex items-center justify-between">
                <div className="text-sm font-medium">Executive summary & win risks</div>
                <Button
                  onClick={() => act("Summary", () => api.summary(run.id), (data) => setSummary({ runId: run.id, data }))}
                  loading={busy === "Summary"}
                  disabled={run.status === "running"}
                >
                  <Sparkles className="h-3.5 w-3.5" /> Write
                </Button>
              </div>
              <div className="mt-1 text-xs text-muted">
                <Mono>rfp.exec_summary</Mono> over this run&apos;s compliance position.
              </div>
              {summary && (
                <div className="mt-3 space-y-3 text-sm">
                  <p className="leading-relaxed">{summary.summary}</p>
                  <ul className="space-y-1.5">
                    {summary.win_risks.map((w) => (
                      <li key={w.requirement_id + w.risk} className="text-xs">
                        <Mono className="text-red">{w.requirement_id}</Mono> {w.risk} <span className="text-muted">→ {w.action}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </Card>
          </div>
        </>
      )}
    </div>
  );
}

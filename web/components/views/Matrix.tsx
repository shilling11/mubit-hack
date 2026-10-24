"use client";

import clsx from "clsx";
import { ArrowUpDown } from "lucide-react";
import { useMemo, useState } from "react";
import type { Draft } from "@/lib/api";
import type { Ctx } from "@/lib/ctx";
import { Empty, Mono, SectionTitle, Shield, StatusPill } from "../ui";
import { RunPicker, StartRun, useRunDrafts } from "./Overview";
import { RowDrawer } from "./RowDrawer";

type SortKey = "order" | "status" | "confidence";

export function Matrix(ctx: Ctx) {
  const [run, setRun] = useRunDrafts(ctx.runId, ctx.runs);
  const [selected, setSelected] = useState<string | null>(null);
  const [sheet, setSheet] = useState<string>("all");
  const [sort, setSort] = useState<SortKey>("order");
  const [taught, setTaught] = useState<Set<string>>(new Set());

  const rows = useMemo(() => {
    let r = (run?.drafts ?? []).filter((d) => sheet === "all" || d.sheet === sheet);
    if (sort === "status") r = [...r].sort((a, b) => (a.status ?? "").localeCompare(b.status ?? ""));
    if (sort === "confidence") r = [...r].sort((a, b) => (a.confidence ?? 0) - (b.confidence ?? 0));
    return r;
  }, [run, sheet, sort]);

  const sel = run?.drafts.find((d) => d.req_id === selected) ?? null;

  if (!run) {
    return (
      <div className="mx-auto max-w-5xl space-y-4">
        <SectionTitle aside={<StartRun ctx={ctx} />}>Requirements matrix</SectionTitle>
        <Empty>No drafts yet for this RFP.</Empty>
      </div>
    );
  }

  const sheets = Array.from(new Set(run.drafts.map((d) => d.sheet)));
  const header = (key: SortKey, label: string) => (
    <button className="inline-flex items-center gap-1 hover:text-ink" onClick={() => setSort(sort === key ? "order" : key)}>
      {label} <ArrowUpDown className={clsx("h-3 w-3", sort === key ? "text-red" : "opacity-40")} />
    </button>
  );

  return (
    <div className="mx-auto max-w-6xl space-y-4">
      <SectionTitle
        aside={
          <div className="flex items-center gap-2">
            <RunPicker {...ctx} />
            <StartRun ctx={ctx} compact />
          </div>
        }
      >
        Requirements matrix
      </SectionTitle>

      <div className="flex gap-1 text-sm">
        {["all", ...sheets].map((s) => (
          <button
            key={s}
            onClick={() => setSheet(s)}
            className={clsx("rounded-md px-3 py-1", sheet === s ? "bg-ink text-sheet" : "text-ink-2 hover:bg-line/60")}
          >
            {s === "all" ? "All" : s}
          </button>
        ))}
        {run.status === "running" && (
          <span className="ml-auto text-xs text-muted">
            Drafting {run.done}/{run.total} through Mubit…
          </span>
        )}
      </div>

      <div className="overflow-hidden rounded-lg border border-line bg-sheet">
        <table className="w-full text-sm">
          <thead className="border-b border-line bg-paper text-left text-[11px] uppercase tracking-wider text-muted">
            <tr>
              <th className="w-20 px-3 py-2">{header("order", "ID")}</th>
              <th className="px-3 py-2">Requirement</th>
              <th className="w-36 px-3 py-2">{header("status", "Status")}</th>
              <th className="w-16 px-3 py-2">{header("confidence", "Conf")}</th>
              <th className="w-14 px-3 py-2">Evid.</th>
              <th className="w-14 px-3 py-2" title="Over-promise detector: Comply without evidence, unsupported figures or citations">Risk</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((d) => (
              <Row
                key={d.req_id}
                d={d}
                active={d.req_id === selected}
                taught={taught.has(d.req_id)}
                onClick={() => setSelected(d.req_id)}
              />
            ))}
          </tbody>
        </table>
      </div>

      {sel && (
        <RowDrawer
          key={`${sel.run_id}-${sel.req_id}-${sel.status}`}
          draft={sel}
          runId={run.id}
          ctx={ctx}
          onClose={() => setSelected(null)}
          onVerified={(v) =>
            setRun((r) => r && { ...r, drafts: r.drafts.map((x) => (x.req_id === sel.req_id ? { ...x, verify_json: v } : x)) })
          }
          onTaught={() => setTaught((s) => new Set(s).add(sel.req_id))}
        />
      )}
    </div>
  );
}

function Row({
  d,
  active,
  taught,
  onClick,
}: {
  d: Draft;
  active: boolean;
  taught: boolean;
  onClick: () => void;
}) {
  // Deterministic detector only: gold labels are evaluation data and stay on the Compare tab.
  const risky = d.flags?.includes("over_promise_risk");
  const unsure = d.flags?.includes("low_confidence");
  return (
    <tr
      onClick={onClick}
      className={clsx(
        "cursor-pointer border-b border-line/70 align-top last:border-0",
        active ? "bg-red-soft/60" : "hover:bg-paper",
      )}
    >
      <td className="px-3 py-2.5">
        <Mono className={clsx(taught && "text-red")}>{d.req_id}</Mono>
        {d.mandatory === "Yes" && <div className="text-[10px] uppercase tracking-wider text-muted">mand.</div>}
      </td>
      <td className="px-3 py-2.5">
        <div className="text-[11px] text-muted">{d.category}</div>
        <div className="leading-snug">{d.requirement}</div>
        {d.error && <div className="mt-1 text-xs text-red">{d.error.slice(0, 140)}</div>}
      </td>
      <td className="px-3 py-2.5">
        {d.status ? <StatusPill status={d.status} short /> : <span className="text-xs text-muted">{d.error ? "failed" : "drafting…"}</span>}
        {taught && <div className="mt-1 text-[11px] font-medium text-red">corrected</div>}
      </td>
      <td className="px-3 py-2.5 text-xs text-ink-2">{d.confidence != null ? d.confidence.toFixed(2) : ""}</td>
      <td className="px-3 py-2.5 text-xs text-ink-2">{d.evidence_ids?.length ?? ""}</td>
      <td className="px-3 py-2.5">
        {d.status &&
          (risky ? (
            <Shield ok={false} title={d.flags?.filter((f) => f !== "over_promise_risk").join(", ") || "Over-promise risk"} />
          ) : unsure ? (
            <span className="text-[11px] font-medium text-partial" title="Model confidence below 0.6">
              unsure
            </span>
          ) : null)}
      </td>
    </tr>
  );
}

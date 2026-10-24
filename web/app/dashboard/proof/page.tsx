"use client";

import clsx from "clsx";
import { useState } from "react";
import { SectionHead, Spinner } from "@/components/bits";
import { Glass } from "@/components/fx";
import { api, pct, secs, type CompareGroup, type Range, type Run } from "@/lib/api";
import { usePoll } from "@/lib/usePoll";

const ROWS: { key: keyof CompareGroup["metrics"]; label: string; kind: "pct" | "num" | "ms"; good: "up" | "down" }[] = [
  { key: "system_critical_recall", label: "Breaches caught (critical recall)", kind: "pct", good: "up" },
  { key: "false_negatives", label: "Missed breaches (false negatives)", kind: "num", good: "down" },
  { key: "critical_precision", label: "Flag precision", kind: "pct", good: "up" },
  { key: "human_queue_rate", label: "Sent to a human", kind: "pct", good: "down" },
  { key: "item_accuracy", label: "Items matching the gold label", kind: "pct", good: "up" },
  { key: "complaint_recall", label: "Complaints recognised", kind: "pct", good: "up" },
  { key: "vulnerability_recall", label: "Vulnerability recognised", kind: "pct", good: "up" },
  { key: "latency_p50_ms", label: "Review time (median)", kind: "ms", good: "down" },
];

function fmt(r: Range | null | undefined, kind: "pct" | "num" | "ms") {
  if (!r) return "—";
  const f = (v: number) => (kind === "pct" ? pct(v) : kind === "ms" ? secs(v) : Number.isInteger(v) ? String(v) : v.toFixed(1));
  return r.min === r.max ? f(r.mean) : `${f(r.mean)}`;
}
function range(r: Range | null | undefined, kind: "pct" | "num" | "ms") {
  if (!r || r.min === r.max) return "";
  const f = (v: number) => (kind === "pct" ? pct(v) : kind === "ms" ? secs(v) : String(v));
  return `${f(r.min)}–${f(r.max)}`;
}

export default function Proof() {
  const [groups] = usePoll<CompareGroup[]>(api.compare, 5000);
  const [runs] = usePoll<Run[]>(api.runs, 3000);
  const [busy, setBusy] = useState(false);
  const running = (runs ?? []).filter((r) => r.status === "running");
  const latest = groups && [...groups].sort((a, b) => b.playbook_version - a.playbook_version)[0];

  return (
    <div className="grid gap-6">
      <SectionHead
        lab="Proof · held-out calls"
        title={<>Never seen in training. <em>Scored against gold labels.</em></>}
        sub="25 held-out calls with gold labels written before any run. Held-out reviews are sent with x-middleware-record: metadata, so Mubit never trains on them. Numbers are means over repeated runs; ranges show min–max."
        right={
          <button className="btn primary" disabled={busy || running.length > 0}
            onClick={async () => { setBusy(true); try { await api.startEval(3); } finally { setBusy(false); } }}>
            {(busy || running.length > 0) && <Spinner />} Run 3× base vs latest
          </button>
        }
      />

      {running.length > 0 && (
        <Glass className="p-4 text-[13px] text-mute">
          Running: {running.map((r) => `${r.label} ${r.done}/${r.total}`).join(" · ")}
        </Glass>
      )}

      <Glass className="overflow-x-auto p-6">
        <table className="w-full min-w-[640px] text-[13.5px]">
          <thead>
            <tr className="text-left">
              <th className="lab pb-3 font-normal">Metric</th>
              {(groups ?? []).map((g) => (
                <th key={g.label + g.model} className={clsx("pb-3 text-right font-normal", g === latest ? "text-lime" : "text-mute")}>
                  <span className="mono text-[10.5px] uppercase tracking-[.12em]">{g.label} ×{g.runs}</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ROWS.map((row) => (
              <tr key={row.key} className="border-t border-line">
                <td className="py-3">{row.label}</td>
                {(groups ?? []).map((g) => (
                  <td key={g.label + g.model} className={clsx("py-3 text-right", g === latest && "text-[17px]")}>
                    {fmt(g.metrics[row.key], row.kind)}
                    <span className="block text-[10.5px] text-mute-2">{range(g.metrics[row.key], row.kind)}</span>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {!groups?.length && <p className="mt-4 text-sm text-mute">No finished evaluation runs yet.</p>}
      </Glass>

      <Glass className="p-6">
        <div className="lab">[ Per call · latest run of each version ]</div>
        <div className="mt-4 grid gap-3">
          {(groups ?? []).map((g) => (
            <div key={g.label + g.model} className="grid grid-cols-[140px_1fr] items-center gap-4">
              <div className={clsx("mono rounded-lg border px-2 py-2 text-center text-[9.5px] uppercase tracking-[.12em]",
                g === latest ? "border-lime/45 bg-lime/10 text-lime" : "border-line bg-white/5 text-[#c6cec6]")}>{g.label}</div>
              <div className={clsx("ticks", g === latest && "latest")}>
                {g.per_call.map((c) => (
                  <span key={c.call_id} title={`${c.call_id}: ${c.items_correct}/${g.n_items} items${c.false_negatives.length ? ` · missed ${c.false_negatives.join(", ")}` : ""}`}
                    className={c.false_negatives.length ? "fn" : c.items_correct >= g.n_items - 1 ? "ok" : ""} />
                ))}
              </div>
            </div>
          ))}
        </div>
        <p className="lab mt-4">lit = at least 8 of 9 items match gold · red = a missed breach · hover for detail</p>
      </Glass>
    </div>
  );
}

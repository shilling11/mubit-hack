"use client";

import clsx from "clsx";
import { useEffect, useState } from "react";
import { api, ago, type AppStatus, type Trace } from "@/lib/api";
import { Mono } from "./ui";

const TASK_LABEL: Record<string, string> = {
  "rfp.draft_response": "draft_response",
  "rfp.verify_claims": "verify_claims",
  "rfp.induce_rule": "induce_rule",
  "rfp.extract_requirements": "extract_requirements",
  "rfp.exec_summary": "exec_summary",
};

export function MubitPanel({ status }: { status: AppStatus | null }) {
  const [traces, setTraces] = useState<Trace[]>([]);

  useEffect(() => {
    let alive = true;
    const tick = () => api.traces(40).then((t) => alive && setTraces(t)).catch(() => {});
    tick();
    const id = setInterval(tick, 2500);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  return (
    <aside className="flex h-full flex-col border-l border-line bg-sheet">
      <div className="border-b border-line px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-muted">Mubit gateway</div>
          <span
            className={clsx(
              "inline-flex items-center gap-1 text-xs",
              status?.mubit.key_set ? "text-comply" : "text-red",
            )}
          >
            <span className={clsx("h-1.5 w-1.5 rounded-full", status?.mubit.key_set ? "bg-comply" : "bg-red")} />
            {status?.mubit.key_set ? "connected" : "no key"}
          </span>
        </div>
        <div className="mt-2 grid grid-cols-3 gap-2 text-center">
          <Metric label="calls" value={status?.calls ?? 0} />
          <Metric label="errors" value={status?.errors ?? 0} tone={status?.errors ? "red" : undefined} />
          <Metric label="routed" value={status?.routed_to_other_model ?? 0} />
        </div>
        <div className="mt-2 text-xs text-muted">
          Model asked <Mono className="text-ink-2">{status?.mubit.model ?? "…"}</Mono>
        </div>
        {status?.served_by?.length ? (
          <div className="mt-1 text-xs text-muted">
            Served by{" "}
            {status.served_by.map((s) => (
              <Mono key={s.served_by} className="mr-1 text-ink-2">
                {s.served_by}×{s.n}
              </Mono>
            ))}
          </div>
        ) : null}
      </div>

      <div className="px-4 pt-3 text-[11px] font-semibold uppercase tracking-wider text-muted">Live traces</div>
      <div className="min-h-0 flex-1 overflow-y-auto px-2 py-2">
        {traces.length === 0 && <div className="px-2 py-6 text-center text-xs text-muted">No calls yet.</div>}
        {traces.map((t) => (
          <div key={t.id} className="flash-in rounded-md px-2 py-1.5 hover:bg-paper">
            <div className="flex items-center justify-between gap-2">
              <Mono className={clsx("truncate", t.ok ? "text-ink" : "text-red")}>{TASK_LABEL[t.task] ?? t.task}</Mono>
              <span className="shrink-0 text-[11px] text-muted">{t.latency_ms != null ? `${t.latency_ms}ms` : ""}</span>
            </div>
            <div className="flex items-center justify-between gap-2 text-[11px] text-muted">
              <Mono className="truncate text-[11px]" >{t.request_id ? t.request_id.slice(0, 18) + "…" : "no request id"}</Mono>
              <span className="shrink-0">{ago(t.ts)}</span>
            </div>
            <div className="flex flex-wrap items-center gap-1 text-[11px]">
              {t.served_by && (
                <span
                  className={clsx(
                    "rounded px-1",
                    t.served_by !== t.model_asked ? "bg-comply-soft text-comply" : "bg-paper text-ink-2",
                  )}
                  title="Model that served the call (response.model)"
                >
                  {t.served_by}
                </span>
              )}
              {t.record_mode !== "full" && (
                <span className="rounded bg-na-soft px-1 text-na" title="x-middleware-record: metadata — never a training example">
                  not trained
                </span>
              )}
              {!t.ok && <span className="truncate text-red" title={t.error ?? ""}>{t.error?.slice(0, 40)}</span>}
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}

function Metric({ label, value, tone }: { label: string; value: number; tone?: "red" }) {
  return (
    <div className="rounded-md bg-paper py-1.5">
      <div className={clsx("font-serif text-lg font-semibold leading-none", tone === "red" && "text-red")}>{value}</div>
      <div className="mt-0.5 text-[10px] uppercase tracking-wider text-muted">{label}</div>
    </div>
  );
}

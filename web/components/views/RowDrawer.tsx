"use client";

import clsx from "clsx";
import { GraduationCap, SearchCheck, X } from "lucide-react";
import { useState } from "react";
import { api, STATUSES, type Draft, type Status, type Verify } from "@/lib/api";
import type { Ctx } from "@/lib/ctx";
import { Button, Mono, StatusPill } from "../ui";

export function RowDrawer({
  draft,
  runId,
  ctx,
  onClose,
  onVerified,
  onTaught,
}: {
  draft: Draft;
  runId: string;
  ctx: Ctx;
  onClose: () => void;
  onVerified: (v: Verify) => void;
  onTaught: () => void;
}) {
  const [status, setStatus] = useState<Status>(draft.status ?? "Comply");
  const [response, setResponse] = useState(draft.response ?? "");
  const [gaps, setGaps] = useState(draft.gaps ?? "");
  const [evidence, setEvidence] = useState<string[]>(draft.evidence_ids ?? []);
  const [rationale, setRationale] = useState("");
  const [open, setOpen] = useState<string | null>(null);
  const [busy, setBusy] = useState<"verify" | "teach" | null>(null);
  const [taughtId, setTaughtId] = useState<number | null>(null);

  const changed =
    status !== draft.status ||
    response.trim() !== (draft.response ?? "").trim() ||
    gaps.trim() !== (draft.gaps ?? "").trim() ||
    evidence.join() !== (draft.evidence_ids ?? []).join();

  async function verify() {
    setBusy("verify");
    try {
      onVerified(await api.verify(runId, draft.req_id));
    } catch (e) {
      ctx.notify(`Verify failed: ${(e as Error).message}`);
    } finally {
      setBusy(null);
    }
  }

  async function teach() {
    setBusy("teach");
    try {
      const c = await api.teach({ run_id: runId, req_id: draft.req_id, status, response, evidence_ids: evidence, gaps, rationale });
      setTaughtId(c.id);
      onTaught();
      ctx.notify(`Correction #${c.id} saved — build a playbook update to teach Mubit`);
      ctx.refreshStatus();
    } catch (e) {
      ctx.notify(`Teach failed: ${(e as Error).message}`);
    } finally {
      setBusy(null);
    }
  }

  const v = draft.verify_json;
  return (
    <div className="fixed inset-y-0 right-0 z-40 flex w-[min(640px,100vw)] flex-col border-l border-line bg-sheet shadow-2xl">
      <div className="flex items-center justify-between border-b border-line px-5 py-3">
        <div className="flex items-center gap-2">
          <Mono className="text-base font-medium">{draft.req_id}</Mono>
          <span className="text-xs text-muted">
            {draft.sheet} · {draft.category} {draft.mandatory === "Yes" && "· mandatory"}
          </span>
        </div>
        <button onClick={onClose} className="rounded p-1 hover:bg-paper" aria-label="Close">
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="min-h-0 flex-1 space-y-6 overflow-y-auto px-5 py-5">
        <section>
          <Label>Requirement</Label>
          <p className="font-serif text-lg leading-snug">{draft.requirement}</p>
        </section>

        <section className="rounded-lg border border-line bg-paper/60 p-4">
          <div className="flex items-center justify-between">
            <Label>AI draft</Label>
            <div className="flex items-center gap-2 text-[11px] text-muted">
              {draft.served_by && <span>served by {draft.served_by}</span>}
              {draft.latency_ms != null && <span>· {draft.latency_ms}ms</span>}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <StatusPill status={draft.status} />
            {draft.confidence != null && <span className="text-xs text-muted">confidence {draft.confidence.toFixed(2)}</span>}
          </div>
          <p className="mt-2 text-sm leading-relaxed">{draft.response}</p>
          {draft.gaps && <p className="mt-2 text-sm text-ink-2"><span className="font-medium">Gap: </span>{draft.gaps}</p>}
          {!!draft.flags?.length && (
            <div className="mt-2 flex flex-wrap gap-1">
              {draft.flags.map((f) => (
                <span key={f} className={clsx("rounded px-1.5 py-0.5 text-[11px]", f === "low_confidence" ? "bg-partial-soft text-partial" : "bg-red-soft text-red")}>
                  {f}
                </span>
              ))}
            </div>
          )}
          {draft.request_id && <div className="mt-2 text-[11px] text-muted">Mubit request <Mono className="text-[11px]">{draft.request_id}</Mono></div>}
        </section>

        <section>
          <div className="flex items-center justify-between">
            <Label>Evidence retrieved</Label>
            <Button variant="ghost" onClick={verify} loading={busy === "verify"}>
              <SearchCheck className="h-3.5 w-3.5" /> Verify claims
            </Button>
          </div>
          <div className="space-y-1.5">
            {(draft.retrieved ?? []).map((e) => {
              const cited = (draft.evidence_ids ?? []).includes(e.id);
              return (
                <div key={e.id} className={clsx("rounded-md border px-3 py-2 text-sm", cited ? "border-ink/30" : "border-line")}>
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={evidence.includes(e.id)}
                      onChange={(ev) => setEvidence((xs) => (ev.target.checked ? [...xs, e.id] : xs.filter((x) => x !== e.id)))}
                      title="Cite in corrected answer"
                    />
                    <button className="min-w-0 flex-1 truncate text-left" onClick={() => setOpen(open === e.id ? null : e.id)}>
                      <span className="font-medium">{e.title}</span> <span className="text-xs text-muted">· {e.source}</span>
                    </button>
                    {cited && <span className="text-[10px] uppercase tracking-wider text-muted">cited</span>}
                  </div>
                  {open === e.id && <p className="mt-2 text-[13px] leading-relaxed text-ink-2">{e.text}</p>}
                </div>
              );
            })}
          </div>
          {v && (
            <div className={clsx("mt-3 rounded-md border p-3 text-sm", v.over_promise ? "border-red/40 bg-red-soft/50" : "border-line")}>
              <div className="flex items-center gap-2">
                <span className={clsx("font-medium", v.over_promise ? "text-red" : "text-comply")}>
                  {v.over_promise ? "Over-promise detected" : "Claims supported"}
                </span>
                <span className="text-xs text-muted">suggests</span> <StatusPill status={v.suggested_status} short />
              </div>
              <p className="mt-1 text-ink-2">{v.reason}</p>
              <ul className="mt-2 space-y-1 text-xs">
                {v.claims.map((c, i) => (
                  <li key={i} className={c.supported ? "text-ink-2" : "text-red"}>
                    {c.supported ? "✓" : "✗"} {c.claim}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>

        <section className="rounded-lg border-2 border-red/30 p-4">
          <Label className="text-red">Bid manager correction</Label>
          <div className="mb-3 flex flex-wrap gap-1">
            {STATUSES.map((s) => (
              <button
                key={s}
                onClick={() => setStatus(s)}
                className={clsx(
                  "rounded-full border px-3 py-1 text-xs",
                  status === s ? "border-ink bg-ink text-sheet" : "border-line-2 hover:bg-paper",
                )}
              >
                {s}
              </button>
            ))}
          </div>
          {status !== draft.status && draft.status && (
            <div className="mb-2 flex items-center gap-2 text-xs">
              <StatusPill status={draft.status} strike /> → <StatusPill status={status} />
            </div>
          )}
          <textarea
            value={response}
            onChange={(e) => setResponse(e.target.value)}
            rows={5}
            className="w-full rounded-md border border-line-2 bg-sheet p-2 text-sm leading-relaxed"
          />
          <input
            value={gaps}
            onChange={(e) => setGaps(e.target.value)}
            placeholder="Gap, condition, option or roadmap item"
            className="mt-2 w-full rounded-md border border-line-2 bg-sheet p-2 text-sm"
          />
          <textarea
            value={rationale}
            onChange={(e) => setRationale(e.target.value)}
            rows={2}
            placeholder="Why? The rule the bid team follows (this is what Redline learns)"
            className="mt-2 w-full rounded-md border border-line-2 bg-sheet p-2 text-sm"
          />
          <div className="mt-3 flex items-center justify-between">
            <span className="text-xs text-muted">
              {taughtId ? `Saved as correction #${taughtId}.` : "Corrections feed the next playbook version."}
            </span>
            <Button variant="red" onClick={teach} loading={busy === "teach"} disabled={!rationale.trim() || (!changed && !rationale.trim())}>
              <GraduationCap className="h-4 w-4" /> Teach Redline
            </Button>
          </div>
        </section>
      </div>
    </div>
  );
}

function Label({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={clsx("mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted", className)}>{children}</div>;
}

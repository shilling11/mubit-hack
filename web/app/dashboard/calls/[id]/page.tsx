"use client";

import clsx from "clsx";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { AnswerTag, QueueTag, Spinner, TierTag } from "@/components/bits";
import { Glass } from "@/components/fx";
import { api, secs, ts, type Answer, type Call, type Correction, type Review, type ReviewItem, type Rule } from "@/lib/api";

const ANSWERS: Answer[] = ["yes", "no", "na", "unsure"];
const LABEL: Record<Answer, string> = { yes: "pass", no: "fail", na: "n/a", unsure: "unsure" };
const REASONS: Record<string, string[]> = {
  S3: ["Score each mistake under the one item it belongs to. A promised refund is a C3 fail, not inaccurate information: S3 is only for factually wrong statements about fees, rules or timescales."],
  C3: ["A wrong timescale is an S1/S3 issue, not a promised outcome. C3 is only for promising or implying the result before it is decided."],
  C2: ["Sympathy is not support: C2 fails unless the colleague offers specific help such as the Financial Support team."],
  C1: ["Dissatisfaction with money lost is a complaint even without the word; a note on the account is not logging it."],
};

export default function CallReview() {
  const { id } = useParams<{ id: string }>();
  const [call, setCall] = useState<Call | null>(null);
  const [choice, setChoice] = useState<Record<string, { answer: Answer; reason: string }>>({});
  const [showRedacted, setShowRedacted] = useState(false);
  const [compare, setCompare] = useState<Review | null>(null);
  const [compareVersion, setCompareVersion] = useState<number | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [result, setResult] = useState<{ corrections: Correction[]; rules: Rule[]; playbook_version: number } | null>(null);
  const [tested, setTested] = useState<Awaited<ReturnType<typeof api.testRule>> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const audio = useRef<HTMLAudioElement>(null);

  // Poll until the call has a review
  useEffect(() => {
    let alive = true;
    const load = () => api.call(id).then((c) => alive && setCall(c)).catch((e: Error) => alive && setError(e.message));
    load();
    const t = setInterval(() => {
      if (!call?.review) load();
    }, 1500);
    return () => { alive = false; clearInterval(t); };
  }, [id, call?.review]);

  const review = call?.review;
  const items = (review?.items ?? []).slice().sort((a, b) => (a.kind === b.kind ? a.id.localeCompare(b.id) : a.kind === "critical" ? -1 : 1));
  const cited = new Set<number>();
  for (const it of items) if (it.answer !== "yes") for (const e of it.evidence) cited.add(e.start_s);
  const changed = Object.entries(choice).filter(([k, v]) => review?.items_json[k] && v.answer !== review.items_json[k].answer);
  const missingReason = changed.some(([, v]) => !v.reason.trim());

  function seek(t: number) {
    if (audio.current) { audio.current.currentTime = t; audio.current.play().catch(() => {}); }
    document.getElementById(`u-${t}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  async function submit() {
    if (!review) return;
    setBusy("submit"); setError(null);
    try {
      const r = await api.evaluate(id, { review_id: review.id, items: changed.map(([k, v]) => ({ id: k, answer: v.answer, reason: v.reason })) });
      setResult(r);
      setChoice({});
    } catch (e) { setError((e as Error).message); } finally { setBusy(null); }
  }

  async function runCompare(v: number) {
    setBusy("compare"); setCompareVersion(v);
    try { setCompare(await api.rereview(id, v)); } catch (e) { setError((e as Error).message); } finally { setBusy(null); }
  }

  async function rescore() {
    setBusy("rescore");
    try { await api.rereview(id); setCall(await api.call(id)); setCompare(null); setResult(null); } catch (e) { setError((e as Error).message); } finally { setBusy(null); }
  }

  if (!call) return <p className="text-mute">{error ?? "Loading…"}</p>;

  return (
    <div className="grid gap-6">
      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-5">
        <div>
          <div className="lab g">[ Evaluation form · {call.split} call ]</div>
          <h1 className="mt-3 text-[clamp(32px,3.4vw,50px)] leading-[1.04]">
            {call.id} <em>· {call.agent_name || "colleague"}</em>
          </h1>
          <p className="mt-2 text-[13px] text-mute">
            {call.duration_s ? `${ts(call.duration_s)} long · ` : ""}{call.source}
            {call.stt_confidence != null ? ` · transcription confidence ${call.stt_confidence.toFixed(2)}` : ""}
          </p>
        </div>
        {review ? (
          <div className="flex items-end gap-6">
            <div className="text-right">
              <div className="text-[56px] font-light leading-none tracking-tight">{review.score}</div>
              <div className="lab">score / 100</div>
            </div>
            <div className="grid gap-2">
              <span className={clsx("tag", review.pass ? "" : "red")}>{review.pass ? "PASS" : "FAIL"}</span>
              <TierTag t={review.risk_tier} />
              <QueueTag k={call.queue?.kind} />
            </div>
          </div>
        ) : (
          <span className="flex items-center gap-2 text-mute"><Spinner /> {call.status === "failed" ? call.error : "Scoring through Mubit…"}</span>
        )}
      </div>

      {review && (
        <Glass className="flex flex-wrap items-center gap-x-6 gap-y-2 p-4 text-[12.5px]">
          <span className="lab g">[ Why it was routed ]</span>
          {(call.queue?.reasons_json ?? []).map((r, i) => <span key={i} className="text-[#d3dad3]">{r}</span>)}
          {!call.queue?.reasons_json?.length && <span className="text-mute">Nothing uncertain: auto-scored.</span>}
          <span className="mono ml-auto text-[10.5px] text-mute-2">
            review.call · {review.model} · {secs(review.latency_ms)} · v{review.playbook_version} · {review.record_mode} · {review.request_id?.slice(0, 18)}…
          </span>
        </Glass>
      )}

      <div className="grid gap-4 lg:grid-cols-[1fr_1.15fr]">
        {/* Transcript */}
        <Glass className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="lab">[ Transcript ]</div>
              <h3 className="mt-2 text-[22px]">{showRedacted ? "What Mubit saw (redacted)" : "Every word, as it was said"}</h3>
            </div>
            <div className="seg">
              <button className={clsx(!showRedacted && "on")} onClick={() => setShowRedacted(false)}>Original</button>
              <button className={clsx(showRedacted && "on")} onClick={() => setShowRedacted(true)}>What Mubit saw</button>
            </div>
          </div>
          {call.audio_path && <audio ref={audio} controls src={api.audioUrl(call.id)} className="mt-4 w-full opacity-80" />}
          <div className="scroll mt-4 flex max-h-[640px] flex-col gap-3 pr-1">
            {call.utterances.map((u, i) => (
              <div key={i} id={`u-${u.start_s}`} className={clsx("msg", u.speaker, cited.has(u.start_s) && "flagged")}>
                <small>
                  <span>{u.speaker === "agent" ? "COLLEAGUE" : "CUSTOMER"}</span>
                  <button className="hover:text-lime" onClick={() => seek(u.start_s)}>▶ {ts(u.start_s)}</button>
                </small>
                {showRedacted ? u.text : u.raw}
              </div>
            ))}
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <button className="btn ghost sm" onClick={async () => { await api.swap(call.id); setCall({ ...call, review: null }); }}>Swap speakers</button>
            <button className="btn ghost sm" onClick={rescore} disabled={!!busy}>{busy === "rescore" && <Spinner />} Re-score at latest playbook</button>
          </div>
          {review?.output_json && (
            <p className="mt-4 border-t border-line pt-4 text-[13px] leading-relaxed text-[#c6cec6]"><span className="lab mr-2">Summary</span>{review.output_json.summary}</p>
          )}
        </Glass>

        {/* Scorecard */}
        <Glass className="p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="lab">[ AI scorecard · check, then correct ]</div>
              <h3 className="mt-2 text-[22px]">Agree, or change it and say why</h3>
            </div>
            <div className="flex items-center gap-2">
              <span className="lab">Compare with</span>
              {[0, Math.max(0, (review?.playbook_version ?? 1) - 1)].filter((v, i, a) => a.indexOf(v) === i && v !== review?.playbook_version).map((v) => (
                <button key={v} className={clsx("btn ghost sm", compareVersion === v && "border-lime")} onClick={() => runCompare(v)} disabled={!!busy || !review}>
                  {busy === "compare" && compareVersion === v && <Spinner />} v{v}{v === 0 ? " (base)" : ""}
                </button>
              ))}
            </div>
          </div>

          <div className="mt-4 grid gap-3">
            {items.map((it) => (
              <ItemRow key={it.id} it={it} chosen={choice[it.id]} compare={compare?.items_json?.[it.id]?.answer} compareVersion={compareVersion}
                onPick={(a) => setChoice((c) => ({ ...c, [it.id]: { answer: a, reason: c[it.id]?.reason ?? "" } }))}
                onReason={(r) => setChoice((c) => ({ ...c, [it.id]: { answer: c[it.id]?.answer ?? it.answer, reason: r } }))}
                onSeek={seek} />
            ))}
          </div>

          {review && (
            <div className="mt-5 flex flex-wrap items-center gap-3 border-t border-line pt-4">
              <button className="btn primary" onClick={submit} disabled={!!busy || missingReason}>
                {busy === "submit" && <Spinner />}
                {changed.length ? `Submit ${changed.length} correction${changed.length > 1 ? "s" : ""} & teach` : "Agree with every item"}
              </button>
              {missingReason && <span className="text-[12px] text-amber">Add a one-line reason for each change.</span>}
              {error && <span className="text-[12px] text-red">{error}</span>}
            </div>
          )}

          {result && (
            <div className="enter mt-5 rounded-2xl border border-lime/40 bg-lime/[.06] p-4">
              {result.corrections.length ? (
                <>
                  <div className="text-[14px]"><b className="font-medium">Rule added → playbook v{result.playbook_version}.</b> The next calls are scored with it straight away, and those reviews become Mubit training examples.</div>
                  {result.corrections.map((c) => {
                    const rule = result.rules.find((r) => r.correction_id === c.id);
                    return (
                      <div key={c.id} className="mt-3 border-t border-dashed border-line pt-3 text-[13px]">
                        <span className="mono mr-2 text-[11px] text-mute">{c.item_id}</span>
                        <span className="was">{LABEL[c.before as Answer] ?? c.before}</span>
                        <span className="now">{LABEL[c.after as Answer] ?? c.after}</span>
                        {rule && <p className="mt-2 text-[13px] leading-relaxed text-[#d3dad3]">{rule.rule}</p>}
                        <button className="btn ghost sm mt-3" disabled={!!busy}
                          onClick={async () => { setBusy("test"); try { setTested(await api.testRule(c.id, 4)); } finally { setBusy(null); } }}>
                          {busy === "test" && <Spinner />} Test this rule on archived calls
                        </button>
                      </div>
                    );
                  })}
                  {tested && (
                    <div className="mt-3 text-[12.5px] text-[#c6cec6]">
                      Re-scored {tested.tested.length} similar calls: {tested.changed.length ? "" : "no answers changed."}
                      {tested.changed.map((ch, i) => (
                        <div key={i} className="mt-1">
                          <Link href={`/dashboard/calls/${ch.call_id}`} className="underline decoration-dotted">{ch.call_id}</Link>
                          <span className="mono mx-2 text-[11px] text-mute">{ch.item_id}</span>
                          <span className="was">{LABEL[ch.before]}</span><span className="now">{LABEL[ch.after]}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              ) : (
                <div className="text-[14px]">Agreed with every item. Agreement is tracked per item; nothing to learn from this call.</div>
              )}
            </div>
          )}
        </Glass>
      </div>
    </div>
  );
}

function ItemRow({ it, chosen, compare, compareVersion, onPick, onReason, onSeek }: {
  it: ReviewItem;
  chosen?: { answer: Answer; reason: string };
  compare?: Answer;
  compareVersion: number | null;
  onPick: (a: Answer) => void;
  onReason: (r: string) => void;
  onSeek: (t: number) => void;
}) {
  const current = chosen?.answer ?? it.answer;
  const isChanged = current !== it.answer;
  const presets = REASONS[it.id] ?? [];
  return (
    <div className={clsx("rounded-2xl border p-4 transition-colors",
      it.answer === "no" && it.kind === "critical" ? "border-red/40 bg-red/[.05]" : it.answer === "unsure" ? "border-amber/40 bg-amber/[.04]" : "border-line bg-black/20")}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="mono text-[11px] text-mute">{it.id}</span>
          <span className="text-[14.5px]">{it.label}</span>
          {it.kind === "critical" ? <span className="tag red !text-[9px]">critical</span> : <span className="tag grey !text-[9px]">{it.weight} pts</span>}
        </div>
        <div className="flex items-center gap-2">
          {compare && compareVersion !== null && (
            <span className="flex items-center gap-1 text-[11px] text-mute">v{compareVersion}: <AnswerTag a={compare} /></span>
          )}
          <span className="lab">AI {Math.round(it.confidence * 100)}%</span>
          <div className="seg">
            {ANSWERS.map((a) => (
              <button key={a} className={clsx(current === a && "on", current === a && a !== it.answer && "!text-lime")} onClick={() => onPick(a)}>
                {LABEL[a]}
              </button>
            ))}
          </div>
        </div>
      </div>
      <p className="mt-2 text-[12.5px] leading-relaxed text-[#b9c2ba]">{it.reasoning}</p>
      {it.evidence.map((e, i) => (
        <button key={i} onClick={() => onSeek(e.start_s)} className="mt-2 block text-left text-[12.5px] text-[#d9e0d9] hover:text-white">
          <span className="mono mr-2 text-[10.5px] text-lime">▶ {ts(e.start_s)}</span>
          <span className={clsx("hl", it.answer === "no" && "v")}>&ldquo;{e.quote}&rdquo;</span>
        </button>
      ))}
      {isChanged && (
        <div className="enter mt-3">
          <div className="mb-2 text-[12px]"><span className="was">{LABEL[it.answer]}</span><span className="now">{LABEL[current]}</span></div>
          <input className="input" placeholder="Why? One line (this is what Redress learns)" value={chosen?.reason ?? ""} onChange={(e) => onReason(e.target.value)} />
          {presets.map((p) => (
            <button key={p} className="mt-2 block text-left text-[11.5px] text-mute hover:text-lime" onClick={() => onReason(p)}>↳ {p}</button>
          ))}
        </div>
      )}
    </div>
  );
}

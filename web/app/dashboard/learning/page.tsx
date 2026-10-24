"use client";

import clsx from "clsx";
import Link from "next/link";
import { useState } from "react";
import { SectionHead, Spinner } from "@/components/bits";
import { Glass } from "@/components/fx";
import { ago, api, type Answer, type Learning } from "@/lib/api";
import { usePoll } from "@/lib/usePoll";

const LABEL: Record<string, string> = { yes: "pass", no: "fail", na: "n/a", unsure: "unsure" };

export default function LearningPage() {
  const [data, , refresh] = usePoll<Learning>(api.learning, 5000);
  const [busy, setBusy] = useState<number | "seed" | null>(null);
  const [tests, setTests] = useState<Record<number, Awaited<ReturnType<typeof api.testRule>>>>({});
  const latest = data?.versions[data.versions.length - 1];

  return (
    <div className="grid gap-6">
      <SectionHead
        lab="Learning · playbook"
        title={<>Every correction becomes a rule. <em>Then a model.</em></>}
        sub="Rules go into every later review straight away. Reviews made with them on practice and live calls are sent to Mubit in full, so its task adapter learns how this bank scores calls."
        right={<button className="btn ghost" disabled={busy !== null} onClick={async () => { setBusy("seed"); try { await api.seed(); await refresh(); } finally { setBusy(null); } }}>{busy === "seed" && <Spinner />} Load guardrail seeds</button>}
      />

      <Glass className="p-6">
        <div className="lab">[ Playbook versions ]</div>
        <div className="mt-4 flex flex-wrap gap-2">
          {data?.versions.map((v) => (
            <span key={v.version} className={clsx("ver", v.version === data.playbook_version ? "pass" : "on")}>
              v{v.version} · {v.version === 0 ? "base" : `${v.rules_json.length} rules`}
            </span>
          ))}
        </div>
      </Glass>

      <div>
        <div className="lab mb-3">[ Rules in playbook v{latest?.version ?? 0} ]</div>
        <div className="grid gap-4 md:grid-cols-3">
          {(latest?.rules_json ?? []).slice().reverse().map((r, i) => (
            <Glass key={r.correction_id} className={clsx("p-5", i === 0 && r.source === "analyst" && "lit")}>
              <div className="flex items-center justify-between">
                <span className="lab">[ {r.item_id} · {r.source === "seed" ? "guardrail" : "analyst"} ]</span>
                <span className="lab">#{r.correction_id}</span>
              </div>
              <p className="mt-3 text-[14px] leading-relaxed">{r.rule}</p>
              <p className="mt-2 text-[12px] text-mute">when: {r.applies_when}</p>
              <button className="btn ghost sm mt-4" disabled={busy !== null}
                onClick={async () => { setBusy(r.correction_id); try { const t = await api.testRule(r.correction_id, 4); setTests((x) => ({ ...x, [r.correction_id]: t })); } finally { setBusy(null); } }}>
                {busy === r.correction_id && <Spinner />} Test on archive
              </button>
              {tests[r.correction_id] && (
                <div className="mt-3 text-[12px] text-[#c6cec6]">
                  {tests[r.correction_id].tested.length} calls re-scored · {tests[r.correction_id].changed.length} answers changed
                  {tests[r.correction_id].changed.map((c, j) => (
                    <div key={j}>
                      <Link className="underline decoration-dotted" href={`/dashboard/calls/${c.call_id}`}>{c.call_id}</Link> {c.item_id}{" "}
                      <span className="was">{LABEL[c.before]}</span><span className="now">{LABEL[c.after]}</span>
                    </div>
                  ))}
                </div>
              )}
            </Glass>
          ))}
          {!latest?.rules_json.length && <p className="text-sm text-mute">No rules yet. Load the guardrail seeds or correct a call.</p>}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-[1.4fr_1fr]">
        <Glass className="p-6">
          <div className="lab">[ Corrections ]</div>
          <h3 className="mb-4 mt-2 text-[22px]">What analysts changed, and why</h3>
          <div className="grid gap-3">
            {(data?.corrections ?? []).map((c) => (
              <div key={c.id} className="border-b border-line pb-3 text-[13px]">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="mono text-[11px] text-mute">#{c.id} {c.item_id}</span>
                  {c.before && <span className="was">{LABEL[c.before as Answer] ?? c.before}</span>}
                  <span className="now">{LABEL[c.after as Answer] ?? c.after}</span>
                  <span className={clsx("tag !text-[9px]", c.source === "seed" ? "grey" : "")}>{c.source}</span>
                  {c.call_id && <Link href={`/dashboard/calls/${c.call_id}`} className="text-[12px] text-lime">{c.call_id}</Link>}
                  <span className="ml-auto text-[11px] text-mute-2">{ago(c.created_at)}</span>
                </div>
                <p className="mt-1.5 italic text-[#b9c2ba]">&ldquo;{c.reason}&rdquo;</p>
              </div>
            ))}
          </div>
        </Glass>
        <Glass className="p-6">
          <div className="lab">[ Agreement ]</div>
          <h3 className="mb-4 mt-2 text-[22px]">AI vs analyst, per item</h3>
          <div className="grid gap-3">
            {(data?.agreement ?? []).map((a) => (
              <div key={a.item_id}>
                <div className="mb-1 flex justify-between text-[12.5px]"><span className="mono">{a.item_id}</span><span>{a.pct == null ? "—" : `${Math.round(a.pct * 100)}%`} <span className="text-mute">of {a.n}</span></span></div>
                <div className="h-1.5 overflow-hidden rounded-full bg-white/5">
                  <div className="h-full rounded-full bg-gradient-to-r from-lime-2 to-lime" style={{ width: `${(a.pct ?? 0) * 100}%`, boxShadow: "0 0 10px rgba(124,255,79,.5)" }} />
                </div>
              </div>
            ))}
            {!data?.agreement.length && <p className="text-sm text-mute">Filled in as analysts submit evaluations.</p>}
          </div>
        </Glass>
      </div>
    </div>
  );
}

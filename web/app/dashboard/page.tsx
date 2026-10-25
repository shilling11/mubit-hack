"use client";

import clsx from "clsx";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { QueueTag, SectionHead, Spinner, TierTag } from "@/components/bits";
import { CountUp, Glass, Glyph } from "@/components/fx";
import { api, type QueueKind, type QueueRow, type Wall } from "@/lib/api";
import { usePoll } from "@/lib/usePoll";

export default function Overview() {
  const router = useRouter();
  const [wall] = usePoll<Wall>(api.wall, 5000);
  const [queue] = usePoll<QueueRow[]>(api.queue, 5000);
  const [filter, setFilter] = useState<QueueKind | "all">("all");
  const [loading, setLoading] = useState<string | null>(null);
  const [shown, setShown] = useState(10);

  async function loadScript(id: string) {
    setLoading(id);
    try {
      await api.loadScript(id);
      router.push(`/dashboard/calls/${id}`);
    } finally {
      setLoading(null);
    }
  }

  const rows = (queue ?? []).filter((q) => filter === "all" || q.kind === filter);

  return (
    <div className="grid gap-6">
      <div className="grid items-end gap-6 md:grid-cols-[1.25fr_1fr]">
        <SectionHead
          lab="Thistle Bank · Call QA"
          title={<>Every call gets scored, <em>so you only check the ones that matter</em></>}
          sub="Redress scores each call against the scorecard and sends you the possible breaches, anything it isn't sure about and a random 5% sample. When you correct its scorecard, it learns from the change."
        />
        <Glass className="overflow-hidden p-5">
          <div className="flex items-center gap-3">
            <span className="live">READY FOR A CALL</span>
            <span className="ml-auto"><Glyph className="eq" /></span>
          </div>
          <h3 className="mt-2 text-[22px]">Take a live call</h3>
          <p className="text-[13px] text-mute">Record the call, hang up, and the scorecard is ready about 15 seconds later.</p>
          <div className="beam run my-4" />
          <div className="flex flex-wrap gap-2">
            <Link href="/dashboard/live" className="btn primary sm">Record a call</Link>
            <button className="btn ghost sm" onClick={() => loadScript("demo_call1")} disabled={!!loading}>
              {loading === "demo_call1" && <Spinner />} Demo call 1 (text)
            </button>
            <button className="btn ghost sm" onClick={() => loadScript("demo_call2")} disabled={!!loading}>
              {loading === "demo_call2" && <Spinner />} Demo call 2 (text)
            </button>
          </div>
        </Glass>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {[
          ["01", "Calls scored", wall?.scored],
          ["02", "Audit sample", wall?.sampled],
          ["03", "Breaches flagged", wall?.breaches],
          ["04", "Sent to an analyst", wall?.to_analyst],
        ].map(([k, label, v]) => (
          <Glass key={k as string} className="p-5">
            <div className="lab">[ {k} ] {label}</div>
            <div className="mt-4 text-[clamp(38px,3.4vw,52px)] font-light leading-none tracking-tight">
              <CountUp value={v as number | undefined} />
            </div>
          </Glass>
        ))}
      </div>

      <Glass className="p-6">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="lab">[ Wall ]</div>
            <h3 className="mt-2 text-[22px]">Every call as a tile, coloured by risk</h3>
          </div>
          <div className="flex flex-wrap gap-4 text-[11px] text-mute">
            <span className="flex items-center gap-2"><i className="tile critical inline-block h-3 w-3" />breach</span>
            <span className="flex items-center gap-2"><i className="tile high inline-block h-3 w-3" />needs a human</span>
            <span className="flex items-center gap-2"><i className="tile medium inline-block h-3 w-3" />below pass</span>
            <span className="flex items-center gap-2"><i className="tile low inline-block h-3 w-3" />compliant</span>
            <span className="flex items-center gap-2"><i className="tile low sampled inline-block h-3 w-3" />audit sample</span>
          </div>
        </div>
        <div className="mt-5 grid gap-[6px]" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(22px, 1fr))" }}>
          {(wall?.tiles ?? []).map((t) => (
            <Link key={t.call_id} href={`/dashboard/calls/${t.call_id}`} title={`${t.call_id} · ${t.risk_tier ?? t.status}`}
              className={clsx("tile", t.risk_tier ?? "dark", t.sampled && "sampled")} />
          ))}
          {!wall && <span className="text-sm text-mute">Loading…</span>}
        </div>
      </Glass>

      <div>
        <div className="mb-3 flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="lab">[ Queue ]</div>
            <h3 className="mt-2 text-[24px]">Calls waiting for a person, most urgent first</h3>
          </div>
          <div className="seg">
            {(["all", "breach", "analyst", "audit"] as const).map((f) => (
              <button key={f} className={clsx(filter === f && "on")} onClick={() => { setFilter(f); setShown(10); }}>
                {f === "all" ? `All · ${queue?.length ?? 0}` : f}
              </button>
            ))}
          </div>
        </div>
        <div className="grid gap-2">
          {rows.slice(0, shown).map((q) => (
            <Link key={q.call_id} href={`/dashboard/calls/${q.call_id}`}
              className="rowc grid-cols-[minmax(0,1fr)_150px_110px_minmax(0,2.2fr)_70px]">
              <div>
                <b className="block text-[15px] font-medium">{q.call_id}</b>
                <span className="text-[12px] text-mute">{q.agent_name || "-"} · {q.split}</span>
              </div>
              <QueueTag k={q.kind} />
              <TierTag t={q.risk_tier} />
              <div className="truncate text-[12.5px] text-[#c6cec6]">{(q.reasons_json ?? [])[0] ?? ""}</div>
              <span className="text-[13px] text-lime">Review →</span>
            </Link>
          ))}
          {queue && rows.length === 0 && <p className="text-sm text-mute">Nothing is waiting for review.</p>}
        </div>
        {rows.length > shown && (
          <div className="mt-3 flex items-center justify-center gap-3">
            <button className="btn ghost sm" onClick={() => setShown((n) => n + 10)}>Show 10 more</button>
            <button className="btn ghost sm" onClick={() => setShown(rows.length)}>Show all {rows.length}</button>
          </div>
        )}
        {shown > 10 && rows.length <= shown && rows.length > 10 && (
          <div className="mt-3 flex justify-center">
            <button className="btn ghost sm" onClick={() => setShown(10)}>Show fewer</button>
          </div>
        )}
      </div>
    </div>
  );
}

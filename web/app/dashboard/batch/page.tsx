"use client";

import clsx from "clsx";
import Link from "next/link";
import { useRef, useState } from "react";
import { QueueTag, SectionHead, Spinner, TierTag } from "@/components/bits";
import { CountUp, Glass } from "@/components/fx";
import { api, type Batch, type BatchImport, type BatchSummary } from "@/lib/api";
import { usePoll } from "@/lib/usePoll";

const ACCEPT = ".xlsx,.csv,.json,.txt";

export default function BatchPage() {
  const [batches, , refreshBatches] = usePoll<BatchSummary[]>(api.batches, 10000);
  const [picked, setPicked] = useState<string | null>(null);
  const current = picked ?? batches?.[0]?.id ?? null;
  const [batch, , refresh] = usePoll<Batch | null>(() => (current ? api.batch(current) : Promise.resolve(null)), 1500, [current]);
  const [imported, setImported] = useState<BatchImport | null>(null);
  const [busy, setBusy] = useState<"import" | "finish" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [drag, setDrag] = useState(false);
  const [paste, setPaste] = useState<string | null>(null); // null = paste box closed
  const fileInput = useRef<HTMLInputElement>(null);

  async function importFiles(files: File[], text = "") {
    if (!files.length && !text.trim()) return;
    setBusy("import"); setError(null); setImported(null);
    try {
      const r = await api.importBatch(files, text);
      setImported(r);
      setPicked(r.batch_id);
      setPaste(null);
      refreshBatches();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(null);
    }
  }

  async function finish() {
    if (!current) return;
    setBusy("finish"); setError(null);
    try {
      await api.finishBatch(current);
      refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(null);
    }
  }

  const s = batch?.stats;
  const scoring = !!s && s.scored + s.failed < s.total;
  const rest = s ? s.total - s.checked : 0;
  const firstError = batch?.calls.find((c) => c.status === "failed")?.error;

  return (
    <div className="grid gap-6">
      <SectionHead
        lab="Batch · this month's calls"
        title={<>The client&apos;s calls for the month, <em>scored before you open them</em></>}
        sub="Import the client's monthly export and check a few calls together. Redress learns from each correction, then scores the rest and flags the ones a person should look at."
        right={
          batches && batches.length > 1 ? (
            <select className="input !w-auto" value={current ?? ""} onChange={(e) => setPicked(e.target.value)}>
              {batches.map((b) => <option key={b.id} value={b.id}>{b.name} · {b.total} calls</option>)}
            </select>
          ) : undefined
        }
      />

      <div className="grid gap-4 lg:grid-cols-3">
        {/* 1 · Import */}
        <Glass className="flex flex-col p-6">
          <div className="lab">[ 1 · Import ]</div>
          <h3 className="mb-4 mt-2 text-[22px]">Drop in the client&apos;s export</h3>
          <button
            className={clsx("flex min-h-[132px] flex-col items-center justify-center gap-2 rounded-xl border border-dashed p-5 text-center transition-colors",
              drag ? "border-lime bg-lime/5" : "border-line hover:border-lime/50")}
            onClick={() => fileInput.current?.click()}
            onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
            onDragLeave={() => setDrag(false)}
            onDrop={(e) => { e.preventDefault(); setDrag(false); importFiles([...e.dataTransfer.files]); }}
            disabled={busy === "import"}
          >
            {busy === "import" ? <Spinner /> : <span className="text-[15px]">Drop files here, or click to choose</span>}
            <span className="text-[12px] text-mute">Excel or CSV · Amazon Connect JSON · text</span>
          </button>
          <input ref={fileInput} type="file" multiple accept={ACCEPT} className="hidden"
            onChange={(e) => { importFiles([...(e.target.files ?? [])]); e.target.value = ""; }} />
          <ul className="mt-4 grid gap-1.5 text-[12.5px] text-[#c6cec6]">
            <li><b className="font-medium text-text">Excel or CSV</b> · one row per line: Call ID, Agent, Speaker, Start, Text</li>
            <li><b className="font-medium text-text">Amazon Connect</b> · the post-call transcript file (.json), one per call</li>
            <li><b className="font-medium text-text">Text</b> · &quot;Agent: …&quot; / &quot;Customer: …&quot;, one turn per line</li>
          </ul>
          {paste === null ? (
            <button className="btn ghost sm mt-4 self-start" onClick={() => setPaste("")}>Paste a transcript</button>
          ) : (
            <div className="mt-4 grid gap-2">
              <textarea className="input min-h-[120px] font-mono text-[12px]" value={paste} onChange={(e) => setPaste(e.target.value)}
                placeholder={"Agent: Thistle Bank, Sam speaking, how can I help?\nCustomer: Hi, I've been charged overdraft fees…"} />
              <div className="flex gap-2">
                <button className="btn primary sm" onClick={() => importFiles([], paste)} disabled={!paste.trim() || busy === "import"}>Import</button>
                <button className="btn ghost sm" onClick={() => setPaste(null)}>Cancel</button>
              </div>
            </div>
          )}
          {imported && (
            <p className="mt-4 text-[13px] text-lime">
              Imported {imported.count} calls · {Object.entries(imported.formats).map(([f, n]) => `${f}${f === "call list" ? "" : ` ${n}`}`).join(" · ")}
            </p>
          )}
          {imported?.skipped.map((k) => <p key={k.file} className="mt-1 text-[12px] text-amber">Skipped {k.file}: {k.reason}</p>)}
          {error && <p className="mt-3 text-[13px] text-red">{error}</p>}
        </Glass>

        {/* 2 · Check a few together */}
        <Glass className="flex flex-col p-6">
          <div className="lab">[ 2 · Check a few together ]</div>
          <h3 className="mb-4 mt-2 text-[22px]">Correct the AI on a handful</h3>
          {!batch ? (
            <p className="text-[13px] text-mute">Import a batch first.</p>
          ) : (
            <>
              <div className="flex items-baseline justify-between text-[13px]">
                <span className="text-mute">{scoring ? "Scoring" : "Scored"}</span>
                <span><b className="text-[20px] font-light"><CountUp value={s?.scored} /></b> <span className="text-mute">/ {s?.total}</span></span>
              </div>
              <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/5">
                <div className="h-full rounded-full bg-lime transition-all" style={{ width: `${s?.total ? (100 * (s.scored + s.failed)) / s.total : 0}%` }} />
              </div>
              {!!s?.failed && <p className="mt-2 text-[12px] text-red">{s.failed} not scored: {firstError}</p>}
              <div className="mt-4 grid gap-2">
                {batch.suggested.map((c) => (
                  <Link key={c.id} href={`/dashboard/calls/${c.id}`} className="rowc grid-cols-[minmax(0,1fr)_auto] !gap-3">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-baseline gap-x-2">
                        <b className="text-[14px] font-medium">{c.id}</b>
                        <span className="truncate text-[12px] text-mute">{c.agent_name || "-"}</span>
                        {(c.source === "live" || c.source === "demo") && <span className="tag">just taken</span>}
                      </div>
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        <TierTag t={c.risk_tier} />
                        <QueueTag k={c.queue_kind} />
                      </div>
                    </div>
                    <span className="text-[13px] text-lime">Check →</span>
                  </Link>
                ))}
                {!batch.suggested.length && !scoring && <p className="text-[13px] text-mute">Nothing left to check together.</p>}
              </div>
              <p className="mt-auto pt-4 text-[12.5px] text-[#c6cec6]">
                <b className="text-text">{s?.checked ?? 0}</b> checked · playbook <b className="text-lime">v{batch.playbook_version}</b> ·{" "}
                {batch.rules} rules learned from corrections
              </p>
            </>
          )}
        </Glass>

        {/* 3 · Let Redress finish */}
        <Glass className="flex flex-col p-6">
          <div className="lab">[ 3 · Let Redress finish ]</div>
          <h3 className="mb-4 mt-2 text-[22px]">Score the rest with what it learned</h3>
          {!batch ? (
            <p className="text-[13px] text-mute">Import a batch first.</p>
          ) : (
            <>
              <button className="btn primary self-start" onClick={finish} disabled={busy === "finish" || scoring || !rest}>
                {busy === "finish" && <Spinner />} Score the other {rest} with playbook v{batch.playbook_version}
              </button>
              <div className="mt-3 flex items-baseline justify-between text-[13px]">
                <span className="text-mute">On playbook v{batch.playbook_version}</span>
                <span>{s?.current ?? 0} / {s?.total ?? 0}</span>
              </div>
              <div className="mt-4 grid grid-cols-2 gap-3">
                {([
                  ["Escalate now", s?.flagged.breach, "breach"],
                  ["To an analyst", s?.flagged.analyst, "analyst"],
                  ["Audit sample", s?.flagged.audit, "audit"],
                  ["Auto-accepted", s?.auto, "auto"],
                ] as const).map(([label, n, k]) => (
                  <div key={k} className={clsx("flcard min-h-[88px]", k !== "auto" && !!n && "lit")}>
                    <div className="lab">[ {label} ]</div>
                    <div className="mt-2 text-[28px] font-light leading-none"><CountUp value={n} /></div>
                  </div>
                ))}
              </div>
              <Link href="/dashboard" className="btn ghost sm mt-auto self-start">Open the queue →</Link>
            </>
          )}
        </Glass>
      </div>

      {batch && (
        <Glass className="p-6">
          <div className="lab">[ {batch.name} ]</div>
          <h3 className="mt-2 text-[22px]">Every call in the batch</h3>
          <div className="mt-5 grid gap-[6px]" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(22px, 1fr))" }}>
            {batch.calls.map((c) => (
              <Link key={c.id} href={`/dashboard/calls/${c.id}`}
                title={`${c.id} · ${c.agent_name || "-"} · ${c.checked ? "checked" : c.risk_tier ?? c.status}`}
                className={clsx("tile", c.risk_tier ?? "dark", c.audit && "sampled", c.checked && "outline outline-1 outline-lime")} />
            ))}
          </div>
        </Glass>
      )}
    </div>
  );
}

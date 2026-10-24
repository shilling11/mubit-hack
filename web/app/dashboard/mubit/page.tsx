"use client";

import clsx from "clsx";
import { useState } from "react";
import { SectionHead } from "@/components/bits";
import { Glass } from "@/components/fx";
import { Morph } from "@/components/Morph";
import { ago, api, secs, type Status, type Trace } from "@/lib/api";
import { usePoll } from "@/lib/usePoll";

export default function MubitPage() {
  const [status] = usePoll<Status>(api.status, 4000);
  const [traces] = usePoll<Trace[]>(() => api.traces(60), 2500);
  const [stage, setStage] = useState<0 | 1 | 2 | null>(null);
  const examples = status?.training_examples_sent ?? 0;
  const shape = stage ?? (examples >= 25 ? 1 : 0);

  return (
    <div className="grid gap-6">
      <SectionHead
        lab="Mubit · gateway"
        title={<>Every model call, <em>through Mubit</em></>}
        sub="Mubit records each call, groups calls into tasks and trains a small adapter per task once it has 25 kept examples. Base and held-out reviews are sent as metadata only, so they never train it."
      />

      <div className="grid gap-4 md:grid-cols-[1fr_1.2fr]">
        <Glass className="overflow-hidden p-6">
          <div className="lab g">[ review.call · {status?.mubit.model ?? "…"} ]</div>
          <div className="cursor-pointer" onClick={() => setStage(((shape + 1) % 3) as 0 | 1 | 2)} title="Click to step through the stages">
            <Morph shape={shape} height={230} />
          </div>
          <div className="flex flex-wrap gap-2">
            <span className={clsx("ver", "on")}>Collecting · {Math.min(examples, 25)}/25</span>
            <span className={clsx("ver", shape >= 1 && "on")}>Training</span>
            <span className={clsx("ver", shape === 2 && "pass")}>Adapter passed ✓</span>
          </div>
          <p className="mt-3 text-[12.5px] text-mute">
            {examples} corrected-behaviour reviews sent in full. The adapter&apos;s status lives in the Mubit console (Tasks → Adapters), and a passing version is compared in Try models.
          </p>
          <a href="https://app.mubit.ai/console/" target="_blank" rel="noreferrer" className="btn ghost sm mt-4">Open the Mubit console ↗</a>
        </Glass>
        <Glass className="p-6">
          <div className="lab">[ Gateway ]</div>
          <div className="mt-3 grid gap-0">
            {[
              ["Base URL", status?.mubit.base_url],
              ["Key", status?.mubit.key_set ? "set" : "missing"],
              ["Model", status?.mubit.model],
              ["Reasoning effort", status?.mubit.reasoning_effort ?? "default"],
              ["Calls logged", status?.mubit_calls],
              ["Errors", status?.mubit_errors],
              ["Training examples", examples],
              ["Playbook", `v${status?.playbook_version ?? 0}`],
              ["Deepgram", status?.deepgram_key_set ? "key set" : "missing"],
            ].map(([k, v]) => (
              <div key={k as string} className="field"><span>{k}</span><span className="mono text-[12.5px]">{v ?? "—"}</span></div>
            ))}
          </div>
        </Glass>
      </div>

      <Glass className="overflow-x-auto p-6">
        <div className="lab">[ Live traces ]</div>
        <table className="mt-3 w-full min-w-[760px] text-[12.5px]">
          <thead>
            <tr className="text-left text-mute-2">
              {["When", "Task", "Record", "Request ID", "Served by", "Latency", "Tokens", "Call"].map((h) => (
                <th key={h} className="lab pb-2 font-normal">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {(traces ?? []).map((t) => (
              <tr key={t.id} className={clsx("border-t border-line", !t.ok && "text-red")}>
                <td className="py-2 text-mute">{ago(t.ts)}</td>
                <td className="mono py-2">{t.task}</td>
                <td className="py-2"><span className={clsx("tag !text-[9px]", t.record_mode === "full" ? "" : "grey")}>{t.record_mode === "full" ? "trains" : t.record_mode}</span></td>
                <td className="mono py-2 text-mute">{t.request_id ? `${t.request_id.slice(0, 20)}…` : t.error?.slice(0, 40)}</td>
                <td className="py-2">{t.served_by ?? "—"}</td>
                <td className="py-2">{secs(t.latency_ms)}</td>
                <td className="py-2 text-mute">{(t.tokens_in ?? 0) + (t.tokens_out ?? 0) || "—"}</td>
                <td className="py-2 text-mute">{t.call_id ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Glass>
    </div>
  );
}

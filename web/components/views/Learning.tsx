"use client";

import clsx from "clsx";
import { ArrowRight, Hammer, Sprout, Trash2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { api, type Correction, type PlaybookVersion } from "@/lib/api";
import type { Ctx } from "@/lib/ctx";
import { Button, Card, Empty, Mono, SectionTitle, StatusPill } from "../ui";

const fetchLearning = () => Promise.all([api.corrections(), api.playbook()]);

export function Learning(ctx: Ctx) {
  const [corrections, setCorrections] = useState<Correction[]>([]);
  const [versions, setVersions] = useState<PlaybookVersion[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const apply = useCallback(([c, v]: [Correction[], PlaybookVersion[]]) => {
    setCorrections(c.reverse());
    setVersions(v);
    setSelected((s) => s ?? v[v.length - 1]?.version ?? 0);
  }, []);
  const load = useCallback(() => fetchLearning().then(apply).catch(() => {}), [apply]);

  useEffect(() => {
    fetchLearning().then(apply).catch(() => {});
  }, [apply]);

  const latest = versions[versions.length - 1];
  const included = new Set(latest?.correction_ids ?? []);
  const pending = corrections.filter((c) => !included.has(c.id));
  const shown = versions.find((v) => v.version === selected);

  async function build() {
    setBusy("build");
    try {
      const v = await api.buildPlaybook();
      ctx.notify(`Playbook v${v.version} ready — ${v.rules.length} rules induced via Mubit`);
      setSelected(v.version);
      await load();
      ctx.refreshStatus();
    } catch (e) {
      ctx.notify(`Build failed: ${(e as Error).message}`);
    } finally {
      setBusy(null);
    }
  }

  async function seed() {
    setBusy("seed");
    try {
      const r = await api.seed();
      ctx.notify(r.loaded ? `Loaded ${r.loaded} seed corrections` : "Seed corrections already loaded");
      await load();
      ctx.refreshStatus();
    } finally {
      setBusy(null);
    }
  }

  async function remove(id: number) {
    await api.deleteCorrection(id);
    await load();
    ctx.refreshStatus();
  }

  return (
    <div className="mx-auto grid max-w-6xl gap-8 lg:grid-cols-[minmax(0,1fr)_380px]">
      <div>
        <SectionTitle
          aside={
            <div className="flex items-center gap-2">
              <Button variant="ghost" onClick={seed} loading={busy === "seed"}>
                <Sprout className="h-3.5 w-3.5" /> Load seed corrections
              </Button>
              <Button variant="red" onClick={build} loading={busy === "build"} disabled={!pending.length}>
                <Hammer className="h-3.5 w-3.5" /> Build playbook v{(latest?.version ?? 0) + 1}
                {pending.length ? ` (${pending.length})` : ""}
              </Button>
            </div>
          }
        >
          Corrections
        </SectionTitle>
        {busy === "build" && (
          <div className="mb-3 rounded-md bg-red-soft px-3 py-2 text-sm text-red">
            Inducing a reusable rule from each new correction through Mubit (<Mono>rfp.induce_rule</Mono>)…
          </div>
        )}
        {corrections.length === 0 ? (
          <Empty>
            No corrections yet. Open a row in the Matrix, fix the status or wording, give your reason and press <b>Teach Redline</b>.
          </Empty>
        ) : (
          <div className="space-y-3">
            {corrections.map((c) => (
              <Card key={c.id} className={clsx("px-4 py-3", !included.has(c.id) && "border-red/40")}>
                <div className="flex items-start justify-between gap-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <Mono className="text-red">#{c.id}</Mono>
                    <Mono>{c.req_id}</Mono>
                    <span className="text-xs text-muted">{c.package}</span>
                    {!included.has(c.id) && <span className="rounded bg-red-soft px-1.5 text-[11px] text-red">pending</span>}
                  </div>
                  <button onClick={() => remove(c.id)} className="text-muted hover:text-red" aria-label="Delete correction">
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
                <div className="mt-1 text-sm">{c.requirement}</div>
                <div className="mt-2 flex items-center gap-2 text-xs">
                  {c.model_output ? <StatusPill status={c.model_output.status} strike /> : <span className="text-muted">seeded</span>}
                  <ArrowRight className="h-3 w-3 text-muted" />
                  <StatusPill status={c.corrected_output.status} />
                  <span className="ml-1 flex flex-wrap gap-1">
                    {c.correction_type.map((t) => (
                      <span key={t} className="rounded bg-paper px-1.5 text-[11px] text-ink-2">
                        {t.replaceAll("_", " ")}
                      </span>
                    ))}
                  </span>
                </div>
                <p className="mt-2 border-l-2 border-red pl-3 text-sm italic text-ink-2">{c.rationale}</p>
                {c.rule && (
                  <p className="mt-2 text-sm">
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-muted">Induced rule · </span>
                    {c.rule.rule}
                  </p>
                )}
              </Card>
            ))}
          </div>
        )}
      </div>

      <div>
        <SectionTitle>Playbook versions</SectionTitle>
        <div className="mb-4 flex flex-wrap items-center gap-1">
          {versions.map((v, i) => (
            <span key={v.version} className="flex items-center gap-1">
              {i > 0 && <ArrowRight className="h-3 w-3 text-muted" />}
              <button
                onClick={() => setSelected(v.version)}
                className={clsx(
                  "rounded-full border px-2.5 py-0.5 text-xs font-medium",
                  selected === v.version ? "border-ink bg-ink text-sheet" : "border-line-2 hover:bg-sheet",
                )}
              >
                v{v.version}
              </button>
            </span>
          ))}
        </div>
        {shown && (
          <Card className="px-4 py-3">
            <div className="text-sm font-medium">v{shown.version}</div>
            <div className="text-xs text-muted">
              {shown.note}
              {shown.created ? ` · ${new Date(shown.created * 1000).toLocaleString("en-GB")}` : ""}
            </div>
            {shown.rules.length === 0 ? (
              <p className="mt-3 text-sm text-muted">The base agent: no learned rules, only the knowledge base.</p>
            ) : (
              <ol className="mt-3 space-y-3">
                {shown.rules.map((r, i) => (
                  <li key={r.correction_id} className="text-sm">
                    <div className="flex items-baseline gap-2">
                      <span className="font-serif font-semibold text-red">{i + 1}.</span>
                      <span>{r.rule}</span>
                    </div>
                    <div className="ml-5 mt-0.5 text-xs text-muted">
                      when {r.applies_when} · from <Mono className="text-[11px]">{r.req_id}</Mono>
                    </div>
                  </li>
                ))}
              </ol>
            )}
          </Card>
        )}
        <p className="mt-4 text-xs leading-relaxed text-muted">
          Each draft call carries the playbook in its user message, so Mubit keeps one <Mono className="text-[11px]">rfp.draft_response</Mono> task.
          Corrected calls become Mubit kept examples; at 25 the task trains an adapter, and the trace panel shows when Mubit serves it.
        </p>
      </div>
    </div>
  );
}

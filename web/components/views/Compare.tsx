"use client";

import clsx from "clsx";
import { Play } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api, pct, type Run } from "@/lib/api";
import type { Ctx } from "@/lib/ctx";
import { Button, Card, Empty, Mono, SectionTitle, Select, Shield, StatusPill } from "../ui";

type CompareData = Awaited<ReturnType<typeof api.compare>>;

export function Compare(ctx: Ctx) {
  const heldOut = ctx.packages.find((p) => p.slug === "meridian") ? "meridian" : ctx.pkg;
  const [pkg, setPkg] = useState(heldOut);
  const [runs, setRuns] = useState<Run[]>([]);
  const [a, setA] = useState("");
  const [b, setB] = useState("");
  const [raw, setRaw] = useState<CompareData | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const latest = ctx.status?.playbook_version ?? 0;

  useEffect(() => {
    let alive = true;
    const load = () =>
      api.runs(pkg).then((r) => {
        if (!alive) return;
        setRuns(r);
        const done = r.filter((x) => x.status === "done");
        setA((cur) => cur && r.some((x) => x.id === cur) ? cur : done.find((x) => x.playbook_version === 0)?.id ?? "");
        setB((cur) =>
          cur && r.some((x) => x.id === cur) ? cur : [...done].sort((x, y) => y.playbook_version - x.playbook_version)[0]?.id ?? "",
        );
      });
    load();
    const id = setInterval(load, 2500);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [pkg]);

  const ra = runs.find((r) => r.id === a);
  const rb = runs.find((r) => r.id === b);
  const ready = !!(a && b && ra?.status === "done" && rb?.status === "done");
  useEffect(() => {
    if (ready) api.compare(a, b).then(setRaw).catch(() => setRaw(null));
  }, [a, b, ready]);
  const data = ready && raw && raw.a.id === a && raw.b.id === b ? raw : null;

  async function start(version: number, model?: string) {
    setBusy(`${version}-${model ?? ""}`);
    try {
      const r = await api.startRun({ package: pkg, playbook_version: version, model: model ?? null });
      if (version === 0 && !model) setA(r.id);
      else setB(r.id);
      ctx.notify(`${r.label}: drafting ${r.total} requirements`);
    } catch (e) {
      ctx.notify(`Could not start: ${(e as Error).message}`);
    } finally {
      setBusy(null);
    }
  }

  const changed = useMemo(() => data?.rows.filter((r) => r.a?.status !== r.b?.status).length ?? 0, [data]);
  const sa = data?.a.score_json;
  const sb = data?.b.score_json;
  const running = runs.filter((r) => r.status === "running");
  const runOpts = runs.map((r) => ({ value: r.id, label: `${r.label}${r.status !== "done" ? ` · ${r.status} ${r.done}/${r.total}` : ""}` }));

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <SectionTitle
        aside={
          <Select
            value={pkg}
            onChange={(v) => {
              setPkg(v);
              setA("");
              setB("");
            }}
            options={ctx.packages.map((p) => ({ value: p.slug, label: `${p.reference} ${p.slug === "meridian" ? "(held out)" : ""}` }))}
          />
        }
      >
        Base vs learned, on an unseen RFP
      </SectionTitle>

      <Card className="flex flex-wrap items-center gap-3 px-5 py-4">
        <span className="text-sm text-ink-2">Run on {pkg}:</span>
        <Button onClick={() => start(0)} loading={busy === "0-"}>
          <Play className="h-3.5 w-3.5" /> Base · v0
        </Button>
        <Button variant="red" onClick={() => start(latest)} loading={busy === `${latest}-`} disabled={latest === 0}>
          <Play className="h-3.5 w-3.5" /> Playbook v{latest}
        </Button>
        {ctx.status && (
          <Button onClick={() => start(0, ctx.status!.mubit.baseline_model)} loading={busy === `0-${ctx.status.mubit.baseline_model}`}>
            <Play className="h-3.5 w-3.5" /> Closed baseline · {ctx.status.mubit.baseline_model}
          </Button>
        )}
        {running.length > 0 && (
          <span className="text-xs text-muted">
            {running.map((r) => `${r.label} ${r.done}/${r.total}`).join(" · ")}
          </span>
        )}
      </Card>

      <div className="grid gap-3 md:grid-cols-2">
        <div className="flex items-center gap-2">
          <span className="w-6 font-serif text-lg font-semibold text-muted">A</span>
          <Select value={a} onChange={setA} options={[{ value: "", label: "Choose run…" }, ...runOpts]} className="flex-1" />
        </div>
        <div className="flex items-center gap-2">
          <span className="w-6 font-serif text-lg font-semibold text-red">B</span>
          <Select value={b} onChange={setB} options={[{ value: "", label: "Choose run…" }, ...runOpts]} className="flex-1" />
        </div>
      </div>

      {!data ? (
        <Empty>Pick two finished runs on the same RFP — typically Base v0 (A) and the latest playbook (B).</Empty>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Delta label="Status accuracy" a={sa?.status_accuracy} b={sb?.status_accuracy} fmt={(v) => pct(v)} higherBetter />
            <Delta label="Over-promises" a={sa?.over_promises} b={sb?.over_promises} fmt={String} />
            <Delta label="Under-claims (hedged)" a={sa?.under_claims} b={sb?.under_claims} fmt={String} />
            <Delta
              label="Trap rows correct"
              a={sa?.trap_correct}
              b={sb?.trap_correct}
              fmt={(v) => `${v}/${sb?.trap_total ?? 0}`}
              higherBetter
            />
            <Delta label="Citation coverage" a={sa?.citation_coverage} b={sb?.citation_coverage} fmt={(v) => pct(v)} higherBetter />
            <Delta label="Key facts stated" a={sa?.key_fact_coverage ?? undefined} b={sb?.key_fact_coverage ?? undefined} fmt={(v) => pct(v)} higherBetter />
            <Delta label="Latency p50" a={sa?.latency_p50_ms ?? undefined} b={sb?.latency_p50_ms ?? undefined} fmt={(v) => `${(v / 1000).toFixed(1)}s`} />
            <Delta
              label="Tokens per RFP"
              a={sa ? (sa.tokens_in ?? 0) + (sa.tokens_out ?? 0) : undefined}
              b={sb ? (sb.tokens_in ?? 0) + (sb.tokens_out ?? 0) : undefined}
              fmt={(v) => `${(v / 1000).toFixed(1)}k`}
            />
          </div>
          <div className="text-xs text-muted">
            A: <Mono className="text-[11px]">{data.a.label}</Mono> on {data.a.model} · B: <Mono className="text-[11px]">{data.b.label}</Mono> on{" "}
            {data.b.model} · scored against hand-written gold labels, no LLM judge · {changed} rows changed status
          </div>

          <div className="overflow-hidden rounded-lg border border-line bg-sheet">
            <table className="w-full text-sm">
              <thead className="border-b border-line bg-paper text-left text-[11px] uppercase tracking-wider text-muted">
                <tr>
                  <th className="w-20 px-3 py-2">ID</th>
                  <th className="px-3 py-2">Requirement</th>
                  <th className="w-32 px-3 py-2">Gold</th>
                  <th className="w-36 px-3 py-2">A</th>
                  <th className="w-36 px-3 py-2">B</th>
                </tr>
              </thead>
              <tbody>
                {data.rows.map((r) => {
                  const okA = sa?.rows[r.req_id]?.status_ok;
                  const okB = sb?.rows[r.req_id]?.status_ok;
                  const diff = r.a?.status !== r.b?.status;
                  return (
                    <tr key={r.req_id} className={clsx("border-b border-line/70 align-top last:border-0", diff && "bg-red-soft/40")}>
                      <td className="px-3 py-2.5">
                        <Mono>{r.req_id}</Mono>
                        {r.gold?.trap && <div className="text-[10px] font-semibold uppercase tracking-wider text-red">trap</div>}
                      </td>
                      <td className="px-3 py-2.5 leading-snug">
                        {r.b?.requirement ?? r.a?.requirement}
                        {diff && r.b?.response && <div className="mt-1 text-xs text-ink-2">B: {r.b.response.slice(0, 220)}…</div>}
                      </td>
                      <td className="px-3 py-2.5">{r.gold ? <StatusPill status={r.gold.status} short /> : <span className="text-xs text-muted">—</span>}</td>
                      <td className="px-3 py-2.5">
                        <span className="flex items-center gap-1.5">
                          <StatusPill status={r.a?.status ?? null} short strike={diff && okA === false} />
                          {okA !== undefined && <Shield ok={okA} />}
                        </span>
                      </td>
                      <td className="px-3 py-2.5">
                        <span className="flex items-center gap-1.5">
                          <StatusPill status={r.b?.status ?? null} short />
                          {okB !== undefined && <Shield ok={okB} />}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

function Delta({
  label,
  a,
  b,
  fmt,
  higherBetter,
}: {
  label: string;
  a: number | undefined;
  b: number | undefined;
  fmt: (v: number) => string;
  higherBetter?: boolean;
}) {
  const better = a != null && b != null && a !== b ? (higherBetter ? b > a : b < a) : null;
  return (
    <Card className="px-4 py-3">
      <div className="text-[11px] font-medium uppercase tracking-wider text-muted">{label}</div>
      <div className="mt-1 flex items-baseline gap-2">
        <span className="font-serif text-lg text-muted">{a != null ? fmt(a) : "—"}</span>
        <span className="text-muted">→</span>
        <span className={clsx("font-serif text-2xl font-semibold", better === true && "text-comply", better === false && "text-red")}>
          {b != null ? fmt(b) : "—"}
        </span>
      </div>
    </Card>
  );
}

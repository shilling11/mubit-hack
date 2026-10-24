"use client";

import clsx from "clsx";
import { BookOpenCheck, Columns2, LayoutDashboard, Table2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { MubitPanel } from "@/components/MubitPanel";
import { Select } from "@/components/ui";
import { Compare } from "@/components/views/Compare";
import { Learning } from "@/components/views/Learning";
import { Matrix } from "@/components/views/Matrix";
import { Overview } from "@/components/views/Overview";
import { api, type AppStatus, type Package, type Run } from "@/lib/api";
import type { View } from "@/lib/ctx";

const NAV: { id: View; label: string; icon: typeof Table2 }[] = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "matrix", label: "Matrix", icon: Table2 },
  { id: "learning", label: "Learning", icon: BookOpenCheck },
  { id: "compare", label: "Compare", icon: Columns2 },
];

function readPref(key: string) {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}
function writePref(key: string, value: string) {
  try {
    localStorage.setItem(key, value);
  } catch {}
}

export default function Home() {
  const [view, setView] = useState<View>("overview");
  const [packages, setPackages] = useState<Package[]>([]);
  const [pkg, setPkg] = useState<string>("northstar");
  const [runs, setRuns] = useState<Run[]>([]);
  const [runId, setRunId] = useState<string | null>(null);
  const [status, setStatus] = useState<AppStatus | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [apiDown, setApiDown] = useState(false);

  const notify = useCallback((msg: string) => {
    setToast(msg);
    setTimeout(() => setToast((t) => (t === msg ? null : t)), 3500);
  }, []);

  const refreshStatus = useCallback(
    () =>
      api
        .status()
        .then((s) => {
          setStatus(s);
          setApiDown(false);
        })
        .catch(() => setApiDown(true)),
    [],
  );

  const refreshRuns = useCallback(async (slug: string) => {
    const r = await api.runs(slug).catch(() => [] as Run[]);
    setRuns(r);
    return r;
  }, []);

  useEffect(() => {
    // Read before the pkg effect below writes the default back.
    const saved = readPref("redline.pkg");
    api
      .packages()
      .then((p) => {
        setPackages(p);
        if (saved && p.some((x) => x.slug === saved)) setPkg(saved);
      })
      .catch(() => setApiDown(true));
    refreshStatus();
    const id = setInterval(refreshStatus, 4000);
    return () => clearInterval(id);
  }, [refreshStatus]);

  useEffect(() => {
    writePref("redline.pkg", pkg);
    api
      .runs(pkg)
      .catch(() => [] as Run[])
      .then((r) => {
        setRuns(r);
        setRunId(r.find((x) => x.status !== "failed")?.id ?? r[0]?.id ?? null);
      });
  }, [pkg]);

  // Keep the run list fresh while a run is in progress
  useEffect(() => {
    if (!runs.some((r) => r.status === "running")) return;
    const id = setInterval(() => refreshRuns(pkg), 1500);
    return () => clearInterval(id);
  }, [runs, pkg, refreshRuns]);

  const current = packages.find((p) => p.slug === pkg);
  const ctx = {
    pkg,
    pkgInfo: current,
    packages,
    runs,
    runId,
    setRunId,
    status,
    notify,
    refreshRuns: () => refreshRuns(pkg),
    refreshStatus,
    refreshPackages: () => api.packages().then(setPackages),
    setPkg,
    goto: setView,
  };

  return (
    <div className="grid h-screen grid-cols-[200px_minmax(0,1fr)_300px] grid-rows-[56px_minmax(0,1fr)]">
      {/* Header */}
      <header className="col-span-3 flex items-center gap-6 border-b border-line bg-sheet px-5">
        <div className="flex items-baseline gap-2">
          <span className="font-serif text-2xl font-bold tracking-tight">
            Red<span className="text-red">line</span>
          </span>
          <span className="hidden text-xs text-muted lg:inline">RFP answers that learn from every correction</span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span className="text-muted">RFP</span>
          <Select
            value={pkg}
            onChange={setPkg}
            options={packages.map((p) => ({
              value: p.slug,
              label: `${p.reference ?? p.slug} · ${p.client?.replace(" (fictional)", "") ?? ""}`,
            }))}
          />
        </div>
        <div className="ml-auto flex items-center gap-3 text-sm">
          {apiDown && <span className="rounded bg-red-soft px-2 py-1 text-xs text-red">API offline — start uvicorn</span>}
          <span className="text-muted">Mubit</span>
          <span
            className={clsx(
              "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium",
              status?.pending_corrections ? "pulse-red border-red/40 text-red" : "border-line-2 text-ink",
            )}
          >
            <span className="h-1.5 w-1.5 rounded-full bg-comply" />
            playbook v{status?.playbook_version ?? 0}
            {status?.pending_corrections ? ` · ${status.pending_corrections} pending` : ""}
          </span>
        </div>
      </header>

      {/* Nav */}
      <nav className="flex flex-col gap-1 border-r border-line bg-sheet px-3 py-4">
        {NAV.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setView(id)}
            className={clsx(
              "flex items-center gap-2 rounded-md px-3 py-2 text-left text-sm",
              view === id ? "bg-ink text-sheet" : "text-ink-2 hover:bg-paper",
            )}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
        <div className="mt-auto space-y-1 px-1 text-[11px] leading-relaxed text-muted">
          <div className="font-semibold uppercase tracking-wider">Package</div>
          <div className="truncate" title={current?.docx ?? ""}>{current?.docx ?? "—"}</div>
          <div className="truncate" title={current?.xlsx ?? ""}>{current?.xlsx ?? "—"}</div>
          <div>{current?.requirement_count ?? 0} requirements{current?.has_gold ? " · gold labels" : ""}</div>
        </div>
      </nav>

      {/* Main */}
      <main className="min-h-0 overflow-y-auto px-8 py-6">
        {view === "overview" && <Overview {...ctx} />}
        {view === "matrix" && <Matrix {...ctx} />}
        {view === "learning" && <Learning {...ctx} />}
        {view === "compare" && <Compare {...ctx} />}
      </main>

      <div className="min-h-0">
        <MubitPanel status={status} />
      </div>

      {toast && (
        <div className="fixed bottom-6 left-1/2 z-50 -translate-x-1/2 rounded-md bg-ink px-4 py-2 text-sm text-sheet shadow-lg">
          {toast}
        </div>
      )}
    </div>
  );
}

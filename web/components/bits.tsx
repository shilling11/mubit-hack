"use client";

import clsx from "clsx";
import type { Answer, QueueKind, Tier } from "@/lib/api";

export function AnswerTag({ a, className }: { a: Answer | null | undefined; className?: string }) {
  if (!a) return <span className="tag grey">-</span>;
  const cls = { yes: "", no: "red", na: "grey", unsure: "amber" }[a];
  const label = { yes: "pass", no: "fail", na: "n/a", unsure: "unsure" }[a];
  return <span className={clsx("tag", cls, className)}>{label}</span>;
}

export function TierTag({ t }: { t: Tier | null | undefined }) {
  if (!t) return <span className="tag grey">not scored</span>;
  const cls = { low: "", medium: "grey", high: "amber", critical: "red" }[t];
  return <span className={clsx("tag", cls)}>{t}</span>;
}

export function QueueTag({ k }: { k: QueueKind | null | undefined }) {
  if (!k) return <span className="tag grey">-</span>;
  const cls = { breach: "red", analyst: "amber", audit: "", auto: "grey" }[k];
  const label = { breach: "breach · escalate", analyst: "to an analyst", audit: "audit sample", auto: "auto-scored" }[k];
  return <span className={clsx("tag", cls)}>{label}</span>;
}

export function Spinner() {
  return <span className="spin inline-block h-3.5 w-3.5 rounded-full border-2 border-lime/30 border-t-lime" />;
}

export function SectionHead({ lab, title, sub, right }: { lab: string; title: React.ReactNode; sub?: React.ReactNode; right?: React.ReactNode }) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-4">
      <div>
        <div className="lab g">[ {lab} ]</div>
        <h1 className="mt-3 text-[clamp(34px,3.8vw,56px)] leading-[1.04]">{title}</h1>
        {sub && <p className="mt-3 max-w-[64ch] text-[14px] text-[#b9c2ba]">{sub}</p>}
      </div>
      {right}
    </div>
  );
}

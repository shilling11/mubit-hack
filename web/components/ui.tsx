"use client";

import clsx from "clsx";
import { Loader2, ShieldAlert, ShieldCheck } from "lucide-react";
import type { ButtonHTMLAttributes, ReactNode } from "react";
import type { Status } from "@/lib/api";

const STATUS_STYLE: Record<Status, string> = {
  Comply: "bg-comply-soft text-comply",
  "Partially Comply": "bg-partial-soft text-partial",
  "Do Not Comply": "bg-dnc-soft text-dnc",
  "Not Applicable": "bg-na-soft text-na",
};
const STATUS_SHORT: Record<Status, string> = {
  Comply: "Comply",
  "Partially Comply": "Partial",
  "Do Not Comply": "Do not comply",
  "Not Applicable": "N/A",
};

export function StatusPill({ status, strike, short }: { status: Status | null; strike?: boolean; short?: boolean }) {
  if (!status) return <span className="text-xs text-muted">—</span>;
  return (
    <span
      className={clsx(
        "inline-flex items-center whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium",
        STATUS_STYLE[status],
        strike && "redline-strike !bg-transparent",
      )}
    >
      {short ? STATUS_SHORT[status] : status}
    </span>
  );
}

export function Button({
  variant = "secondary",
  loading,
  className,
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "red" | "ghost"; loading?: boolean }) {
  return (
    <button
      {...props}
      disabled={props.disabled || loading}
      className={clsx(
        "inline-flex items-center justify-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50",
        variant === "primary" && "bg-ink text-sheet hover:bg-ink-2",
        variant === "red" && "bg-red text-white hover:bg-[#a81f17]",
        variant === "secondary" && "border border-line-2 bg-sheet text-ink hover:bg-paper",
        variant === "ghost" && "text-ink-2 hover:bg-line/60",
        className,
      )}
    >
      {loading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
      {children}
    </button>
  );
}

export function Card({ className, children }: { className?: string; children: ReactNode }) {
  return <div className={clsx("rounded-lg border border-line bg-sheet", className)}>{children}</div>;
}

export function SectionTitle({ children, aside }: { children: ReactNode; aside?: ReactNode }) {
  return (
    <div className="mb-3 flex items-end justify-between gap-4">
      <h2 className="font-serif text-xl font-semibold tracking-tight">{children}</h2>
      {aside}
    </div>
  );
}

export function Stat({
  label,
  value,
  sub,
  tone,
}: {
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  tone?: "red" | "green" | "neutral";
}) {
  return (
    <Card className="px-4 py-3">
      <div className="text-[11px] font-medium uppercase tracking-wider text-muted">{label}</div>
      <div
        className={clsx(
          "mt-1 font-serif text-2xl font-semibold",
          tone === "red" && "text-red",
          tone === "green" && "text-comply",
        )}
      >
        {value}
      </div>
      {sub && <div className="mt-0.5 text-xs text-muted">{sub}</div>}
    </Card>
  );
}

export function Shield({ ok, title }: { ok: boolean; title?: string }) {
  return ok ? (
    <ShieldCheck className="h-4 w-4 text-comply" aria-label={title ?? "Matches gold"} />
  ) : (
    <ShieldAlert className="h-4 w-4 text-red" aria-label={title ?? "Risk"} />
  );
}

export function Mono({ children, className }: { children: ReactNode; className?: string }) {
  return <span className={clsx("font-mono text-[12px]", className)}>{children}</span>;
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="rounded-lg border border-dashed border-line-2 px-6 py-10 text-center text-sm text-muted">{children}</div>;
}

export function Select({
  value,
  onChange,
  options,
  className,
}: {
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
  className?: string;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className={clsx("rounded-md border border-line-2 bg-sheet px-2 py-1.5 text-sm", className)}
    >
      {options.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  );
}

"use client";

import clsx from "clsx";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BgCanvas } from "@/components/BgCanvas";
import { Logo } from "@/components/fx";
import { api, type Status } from "@/lib/api";
import { usePoll } from "@/lib/usePoll";

const NAV = [
  { href: "/dashboard", label: "Overview" },
  { href: "/dashboard/live", label: "Live call", plus: true },
  { href: "/dashboard/batch", label: "Batch" },
  { href: "/dashboard/learning", label: "Learning" },
  { href: "/dashboard/proof", label: "Proof" },
  { href: "/dashboard/mubit", label: "Mubit" },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const [status, error] = usePoll<Status>(api.status, 4000);

  return (
    <div className="relative min-h-screen">
      <BgCanvas opacity={0.55} />
      <div className="fixed left-7 top-6 z-50"><Logo /></div>
      <div className="fixed right-6 top-5 z-50 flex items-center gap-2">
        {error ? (
          <span className="tag red">API offline · start uvicorn</span>
        ) : (
          <>
            <span className={clsx("tag", status?.mubit.key_set ? "" : "red")}>
              <span className={clsx("live", !status && "off")} style={{ fontSize: 10 }}>MUBIT</span>
              {status ? `${status.mubit_calls} calls` : "…"}
            </span>
            <span className={clsx("tag", status?.pending_corrections ? "amber" : "grey")}>
              playbook v{status?.playbook_version ?? 0}
              {status?.pending_corrections ? ` · ${status.pending_corrections} pending` : ""}
            </span>
          </>
        )}
      </div>

      <main className="relative z-10 mx-auto w-[min(1240px,calc(100%-48px))] pb-36 pt-[104px]">{children}</main>

      <nav className="island">
        {NAV.map((n) => {
          const on = n.href === "/dashboard" ? path === "/dashboard" : path.startsWith(n.href);
          return (
            <Link key={n.href} href={n.href} className={clsx(on && "active")}>
              {n.label}
              {n.plus && <span className="plus">+</span>}
            </Link>
          );
        })}
        <Link href="/">Home</Link>
      </nav>
    </div>
  );
}

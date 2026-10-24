"use client";

import clsx from "clsx";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/", label: "Wall" },
  { href: "/call", label: "Live call" },
];

export function Logo() {
  return (
    <Link href="/" className="flex items-center gap-2 text-[15px] font-semibold tracking-[0.02em]">
      <svg width="26" height="14" viewBox="0 0 26 14" fill="none" aria-hidden>
        <circle cx="7.5" cy="7" r="5.6" stroke="#fff" strokeWidth="2" />
        <circle cx="18.5" cy="7" r="5.6" stroke="#7CFF4F" strokeWidth="2" />
      </svg>
      <span>
        RE<b className="font-semibold text-lime">DRESS</b>
      </span>
    </Link>
  );
}

export function Shell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  return (
    <>
      <header className="fixed left-0 right-0 top-0 z-50 flex items-center justify-between px-7 py-5">
        <Logo />
        <span className="lab">Thistle Bank · Call QA</span>
      </header>

      <main className="mx-auto max-w-6xl px-6 pb-32 pt-24">{children}</main>

      <nav className="fixed bottom-6 left-1/2 z-50 flex -translate-x-1/2 gap-0.5 rounded-xl border border-line bg-[rgba(8,14,9,.75)] p-1.5 backdrop-blur-md">
        {NAV.map((n) => {
          const active = n.href === "/" ? path === "/" : path.startsWith(n.href);
          return (
            <Link
              key={n.href}
              href={n.href}
              className={clsx(
                "flex items-center gap-2 whitespace-nowrap rounded-lg px-3.5 py-2 text-[13px] transition-colors",
                active ? "bg-white/[.075] text-white" : "text-[#c6cec6] hover:text-white",
              )}
            >
              {active && <span className="h-[5px] w-[5px] rounded-full bg-lime shadow-[0_0_8px_#7CFF4F]" />}
              {n.label}
            </Link>
          );
        })}
      </nav>
    </>
  );
}

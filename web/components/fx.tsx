"use client";

import clsx from "clsx";
import Link from "next/link";
import { useEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";

/** The RE·DRESS mark (two rings), as in the prototypes. */
export function Logo({ href = "/" }: { href?: string }) {
  return (
    <Link href={href} className="logo">
      <svg width="26" height="14" viewBox="0 0 26 14" fill="none" aria-hidden>
        <circle cx="7.5" cy="7" r="5.6" stroke="#fff" strokeWidth="2" />
        <circle cx="18.5" cy="7" r="5.6" stroke="#7CFF4F" strokeWidth="2" />
      </svg>
      <span>
        RE<b>DRESS</b>
      </span>
    </Link>
  );
}

export function Arrow() {
  return (
    <svg width="13" height="13" viewBox="0 0 12 12" fill="none" stroke="#071407" strokeWidth="1.8" strokeLinecap="round" aria-hidden>
      <path d="M3 9l6-6M4 3h5v5" />
    </svg>
  );
}

/** Pixel voice-wave glyph (7×5). With `level` (0..1) it follows a real signal; without, it animates on its own. */
export function Glyph({ cols = 7, rows = 5, level, className }: { cols?: number; rows?: number; level?: number; className?: string }) {
  const [t, setT] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setT(performance.now() * 0.006), 110);
    return () => clearInterval(id);
  }, []);
  const mid = Math.floor(rows / 2);
  return (
    <span className={className ?? "glyph"} aria-hidden>
      {Array.from({ length: cols }, (_, ci) => {
        const wave = Math.abs(Math.sin(t + ci * 0.9) * Math.cos(t * 0.37 + ci * 0.5));
        const amp = level === undefined ? wave * 2.2 : Math.min(1, level * (0.55 + 0.9 * wave)) * (mid + 0.4);
        const lvl = Math.round(amp);
        return (
          <span key={ci}>
            {Array.from({ length: rows }, (_, ri) => (
              <i key={ri} className={Math.abs(ri - mid) <= lvl && (level === undefined || level > 0.02) ? "on" : ""} />
            ))}
          </span>
        );
      })}
    </span>
  );
}

/** Adds the "in" class once the element scrolls into view (drives .w and .rise). */
export function InView({ as: Tag = "div", className, children, style }: {
  as?: "div" | "section" | "h1" | "h2" | "h3" | "p" | "span";
  className?: string;
  children: ReactNode;
  style?: CSSProperties;
}) {
  const ref = useRef<HTMLElement>(null);
  const [inView, setInView] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver((es) => es.forEach((e) => e.isIntersecting && setInView(true)), { threshold: 0.3 });
    io.observe(el);
    return () => io.disconnect();
  }, []);
  const Comp = Tag as "div";
  return (
    <Comp ref={ref as React.Ref<HTMLDivElement>} className={clsx(className, inView && "in")} style={style}>
      {children}
    </Comp>
  );
}

/** Word-by-word blur reveal: wrap inside an <InView>. `start` offsets the stagger. */
export function Words({ text, start = 0 }: { text: string; start?: number }) {
  const parts = text.split(/(\s+)/);
  let n = start;
  return (
    <>
      {parts.map((p, i) =>
        /^\s+$/.test(p) || !p ? (
          p
        ) : (
          <span key={i} className="w" style={{ transitionDelay: `${Math.min(n++ * 30, 900)}ms` }}>
            {p}
          </span>
        ),
      )}
    </>
  );
}

/** A glass card whose border lights up where the cursor is. */
export function Glass({ className, children, style, onClick }: {
  className?: string;
  children: ReactNode;
  style?: CSSProperties;
  onClick?: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  return (
    <div
      ref={ref}
      onClick={onClick}
      onMouseMove={(e) => {
        const r = ref.current?.getBoundingClientRect();
        if (!r || !ref.current) return;
        ref.current.style.setProperty("--mx", `${e.clientX - r.left}px`);
        ref.current.style.setProperty("--my", `${e.clientY - r.top}px`);
      }}
      className={clsx("glass", className)}
      style={style}
    >
      {children}
    </div>
  );
}

/** Animated number that counts up to `value`. */
export function CountUp({ value, decimals = 0, suffix = "" }: { value: number | null | undefined; decimals?: number; suffix?: string }) {
  const [shown, setShown] = useState(0);
  useEffect(() => {
    if (value == null) return;
    let raf = 0;
    const start = performance.now(), from = 0, dur = 1100;
    const step = (now: number) => {
      const k = Math.min(1, (now - start) / dur);
      setShown(from + (value - from) * (1 - Math.pow(1 - k, 3)));
      if (k < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [value]);
  if (value == null) return <span className="text-mute-2">—</span>;
  return (
    <span>
      {shown.toFixed(decimals)}
      {suffix}
    </span>
  );
}

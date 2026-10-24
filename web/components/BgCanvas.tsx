"use client";

import { useEffect, useRef } from "react";

/** Corridor rails, light streaks and dust: the background of design/prototype.html, ported as-is. */
export function BgCanvas({ opacity = 1 }: { opacity?: number }) {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const bg = ref.current;
    if (!bg) return;
    const bx = bg.getContext("2d");
    if (!bx) return;
    let BW = 0, BH = 0, raf = 0;
    const RAILS = [-0.46, -0.37, -0.29, -0.22, -0.15, -0.09, 0.09, 0.15, 0.22, 0.29, 0.37, 0.46];
    const head = (() => {
      const c = document.createElement("canvas");
      c.width = c.height = 64;
      const g = c.getContext("2d")!;
      const r = g.createRadialGradient(32, 32, 0, 32, 32, 32);
      r.addColorStop(0, "rgba(255,255,255,1)"); r.addColorStop(0.2, "rgba(190,255,150,.9)");
      r.addColorStop(0.55, "rgba(124,255,79,.18)"); r.addColorStop(1, "rgba(124,255,79,0)");
      g.fillStyle = r; g.fillRect(0, 0, 64, 64);
      return c;
    })();
    const size = () => {
      const dpr = Math.min(2, window.devicePixelRatio || 1);
      BW = window.innerWidth; BH = window.innerHeight;
      bg.width = BW * dpr; bg.height = BH * dpr;
      bx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    const railPts = (side: number, k: number) => {
      const cx = BW / 2, cy = BH * 0.5;
      return { x0: cx + side * BW * 0.1, y0: cy + k * BH * 0.5, x1: side < 0 ? -BW * 0.02 : BW * 1.02, y1: cy + k * BH * 1.08 };
    };
    const ease = (t: number) => t * t * (1.25 - 0.25 * t);
    type Streak = { side: number; k: number; t: number; v: number; len: number; w: number };
    const newStreak = (delay = true): Streak => ({
      side: Math.random() < 0.5 ? -1 : 1, k: RAILS[Math.floor(Math.random() * RAILS.length)],
      t: delay ? -Math.random() * 1.4 : Math.random(), v: 0.0012 + Math.random() * 0.0016,
      len: 0.12 + Math.random() * 0.12, w: 0.5 + Math.random() * 0.7,
    });
    const streaks = Array.from({ length: 14 }, () => newStreak(false));
    const dust = Array.from({ length: 70 }, () => ({
      x: Math.random(), y: Math.random(), r: 0.4 + Math.random() * 1.1, p: Math.random() * 6.28,
      s: 0.4 + Math.random() * 1.4, vy: -(0.00002 + Math.random() * 0.00006),
    }));
    const draw = (time: number) => {
      bx.clearRect(0, 0, BW, BH);
      bx.lineWidth = 1;
      for (const side of [-1, 1]) for (const k of RAILS) {
        const p = railPts(side, k);
        const g = bx.createLinearGradient(p.x0, p.y0, p.x1, p.y1);
        g.addColorStop(0, "rgba(140,255,110,0)"); g.addColorStop(0.45, "rgba(140,255,110,.05)"); g.addColorStop(1, "rgba(140,255,110,.09)");
        bx.strokeStyle = g; bx.beginPath(); bx.moveTo(p.x0, p.y0); bx.lineTo(p.x1, p.y1); bx.stroke();
      }
      bx.globalCompositeOperation = "lighter";
      for (const s of streaks) {
        s.t += s.v * (0.55 + Math.max(0, s.t) * 1.6);
        if (s.t - s.len > 1) { Object.assign(s, newStreak(true)); continue; }
        if (s.t <= 0) continue;
        const p = railPts(s.side, s.k), h = Math.min(1, ease(Math.min(s.t, 1))), tl = ease(Math.max(0, s.t - s.len));
        const hx = p.x0 + (p.x1 - p.x0) * h, hy = p.y0 + (p.y1 - p.y0) * h, tx = p.x0 + (p.x1 - p.x0) * tl, ty = p.y0 + (p.y1 - p.y0) * tl;
        const fade = Math.min(1, s.t / 0.18) * (s.t > 0.9 ? Math.max(0, 1 - (s.t - 0.9) / (s.len + 0.1)) : 1), w = s.w * (0.5 + 1.8 * h);
        const g = bx.createLinearGradient(tx, ty, hx, hy);
        g.addColorStop(0, "rgba(124,255,79,0)"); g.addColorStop(0.75, `rgba(124,255,79,${0.5 * fade})`); g.addColorStop(1, `rgba(205,255,180,${0.9 * fade})`);
        bx.strokeStyle = g; bx.lineCap = "round";
        bx.globalAlpha = 0.14; bx.lineWidth = w * 7; bx.beginPath(); bx.moveTo(tx, ty); bx.lineTo(hx, hy); bx.stroke();
        bx.globalAlpha = 1; bx.lineWidth = w; bx.beginPath(); bx.moveTo(tx, ty); bx.lineTo(hx, hy); bx.stroke();
        const hs = 6 + w * 6; bx.globalAlpha = 0.35 * fade; bx.drawImage(head, hx - hs / 2, hy - hs / 2, hs, hs);
      }
      for (const d of dust) {
        d.y += d.vy; if (d.y < 0) d.y = 1;
        bx.globalAlpha = 0.12 + 0.38 * (0.5 + 0.5 * Math.sin(time * 0.001 * d.s + d.p));
        bx.fillStyle = "#d8ffc8"; bx.beginPath(); bx.arc(d.x * BW, d.y * BH, d.r, 0, 6.283); bx.fill();
      }
      bx.globalAlpha = 1; bx.globalCompositeOperation = "source-over";
      raf = requestAnimationFrame(draw);
    };
    size();
    window.addEventListener("resize", size);
    raf = requestAnimationFrame(draw);
    return () => { cancelAnimationFrame(raf); window.removeEventListener("resize", size); };
  }, []);

  return (
    <canvas
      ref={ref}
      aria-hidden
      className="pointer-events-none fixed inset-0 z-0 h-full w-full"
      style={{ opacity, transition: "opacity .9s ease" }}
    />
  );
}

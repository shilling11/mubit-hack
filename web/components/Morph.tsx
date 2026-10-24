"use client";

import { useEffect, useRef } from "react";

/** Particle morph from design/prototype.html: 0 scattered (calls), 1 loose sphere (training), 2 ∞ (adapter passed). */
export function Morph({ shape, height = 260 }: { shape: 0 | 1 | 2; height?: number }) {
  const ref = useRef<HTMLCanvasElement>(null);
  const shapeRef = useRef(shape);
  useEffect(() => {
    shapeRef.current = shape;
  }, [shape]);

  useEffect(() => {
    const mc = ref.current;
    if (!mc) return;
    const mx = mc.getContext("2d");
    if (!mx) return;
    const sprite = (stops: [number, string][]) => {
      const c = document.createElement("canvas"); c.width = c.height = 64;
      const g = c.getContext("2d")!; const r = g.createRadialGradient(32, 32, 0, 32, 32, 32);
      stops.forEach(([o, col]) => r.addColorStop(o, col)); g.fillStyle = r; g.fillRect(0, 0, 64, 64); return c;
    };
    const LIME = sprite([[0, "rgba(235,255,220,1)"], [0.16, "rgba(160,255,110,.95)"], [0.42, "rgba(90,210,45,.28)"], [1, "rgba(60,160,30,0)"]]);
    const DEEP = sprite([[0, "rgba(190,255,160,.95)"], [0.2, "rgba(90,200,50,.8)"], [0.5, "rgba(40,120,20,.2)"], [1, "rgba(30,90,15,0)"]]);
    const N = 1800, P = new Float32Array(N * 3), T = [new Float32Array(N * 3), new Float32Array(N * 3), new Float32Array(N * 3)];
    const K = new Float32Array(N), SZ = new Float32Array(N), PH = new Float32Array(N), SP = new Uint8Array(N);
    for (let i = 0; i < N; i++) {
      const j = i * 3;
      T[0][j] = (Math.random() * 2 - 1) * 2.5; T[0][j + 1] = (Math.random() * 2 - 1) * 1.5; T[0][j + 2] = (Math.random() * 2 - 1) * 1.3;
      const u = Math.random() * 2 - 1, a = Math.random() * 6.283, r = 0.92 * (0.72 + Math.random() * 0.5), q = Math.sqrt(1 - u * u);
      T[1][j] = r * q * Math.cos(a); T[1][j + 1] = r * u; T[1][j + 2] = r * q * Math.sin(a);
      const side = i % 2 ? 1 : -1, R = 0.47, rr = 0.2 + (Math.random() - 0.5) * 0.035, uu = Math.random() * 6.283, vv = Math.random() * 6.283;
      let x = (R + rr * Math.cos(vv)) * Math.cos(uu), z = rr * Math.sin(vv);
      const y = (R + rr * Math.cos(vv)) * Math.sin(uu);
      const ty = side * 0.32, cy = Math.cos(ty), sy = Math.sin(ty);
      [x, z] = [x * cy + z * sy, -x * sy + z * cy];
      T[2][j] = x + side * 0.6; T[2][j + 1] = y; T[2][j + 2] = z;
      P[j] = T[0][j]; P[j + 1] = T[0][j + 1]; P[j + 2] = T[0][j + 2];
      K[i] = 0.018 + Math.random() * 0.04; SZ[i] = 0.7 + Math.random() * 0.7; PH[i] = Math.random() * 6.283; SP[i] = Math.random() < 0.72 ? 0 : 1;
    }
    let W = 0, H = 0, rot = 0, ptrX = 0, ptrY = 0, raf = 0;
    const size = () => {
      const dpr = Math.min(2, window.devicePixelRatio || 1);
      const r = mc.getBoundingClientRect(); W = r.width; H = r.height;
      mc.width = W * dpr; mc.height = H * dpr; mx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    const onPtr = (e: PointerEvent) => { ptrX = e.clientX / window.innerWidth - 0.5; ptrY = e.clientY / window.innerHeight - 0.5; };
    const draw = (time: number) => {
      const shapeNow = shapeRef.current;
      mx.clearRect(0, 0, W, H); mx.globalCompositeOperation = "lighter";
      const tgt = T[shapeNow], t = time * 0.001; rot += shapeNow === 2 ? 0 : 0.0025;
      const ay = (shapeNow === 2 ? Math.sin(t * 0.35) * 0.55 : rot) + ptrX * 0.35, ax = 0.12 + ptrY * 0.22;
      const cyA = Math.cos(ay), syA = Math.sin(ay), cxA = Math.cos(ax), sxA = Math.sin(ax);
      const cx = W / 2, cy = H / 2, sc = Math.min(W, H) * 0.3, D = 3.2;
      for (let i = 0; i < N; i++) {
        const j = i * 3, k = K[i];
        P[j] += (tgt[j] - P[j]) * k; P[j + 1] += (tgt[j + 1] - P[j + 1]) * k; P[j + 2] += (tgt[j + 2] - P[j + 2]) * k;
        const wob = shapeNow === 0 ? 0.05 : 0.008;
        const x = P[j] + Math.sin(t * 0.7 + PH[i]) * wob, y = P[j + 1] + Math.cos(t * 0.6 + PH[i] * 1.3) * wob, z = P[j + 2];
        const x2 = x * cyA + z * syA; let z2 = -x * syA + z * cyA; const y2 = y * cxA - z2 * sxA; z2 = y * sxA + z2 * cxA;
        const pr = D / (D - z2); if (pr <= 0) continue;
        const sx = cx + x2 * sc * pr, sy = cy + y2 * sc * pr, s = (2.1 + 3.8 * (pr - 0.72)) * SZ[i];
        mx.globalAlpha = Math.max(0.12, Math.min(1, 0.2 + (pr - 0.75) * 1.7)) * (0.75 + 0.25 * Math.sin(t * 2 + PH[i]));
        mx.drawImage(SP[i] ? DEEP : LIME, sx - s, sy - s, s * 2, s * 2);
      }
      mx.globalAlpha = 1; mx.globalCompositeOperation = "source-over";
      raf = requestAnimationFrame(draw);
    };
    size();
    window.addEventListener("resize", size);
    window.addEventListener("pointermove", onPtr);
    raf = requestAnimationFrame(draw);
    return () => { cancelAnimationFrame(raf); window.removeEventListener("resize", size); window.removeEventListener("pointermove", onPtr); };
  }, []);

  return <canvas ref={ref} aria-hidden className="block w-full" style={{ height }} />;
}

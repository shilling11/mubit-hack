"use client";

import clsx from "clsx";
import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { BgCanvas } from "@/components/BgCanvas";
import { Arrow, CountUp, Glass, Glyph, InView, Logo, Words } from "@/components/fx";
import { Morph } from "@/components/Morph";
import { api, pct, type CompareGroup, type Status, type Wall } from "@/lib/api";
import { usePoll } from "@/lib/usePoll";

const SECTIONS = ["Home", "Problem", "How it works", "Proof", "Mubit"] as const;

const CRITICAL = [
  { id: "C1", title: "Complaint recognised", text: "Unhappy and out of pocket is a complaint, even if nobody says the word." },
  { id: "C2", title: "Vulnerability supported", text: "“I was in hospital” needs support offered, not just sympathy." },
  { id: "C3", title: "No promised outcome", text: "“I’m sure we’ll refund that” is a commitment the bank hasn’t made." },
  { id: "C4", title: "Identity first", text: "Nothing about the account is discussed until two pieces of ID have been checked." },
];

const PIPELINE = [
  { k: "01", t: "Record", d: "The colleague takes the call as normal" },
  { k: "02", t: "Transcribe", d: "Deepgram writes out both speakers with timestamps" },
  { k: "03", t: "Scrub", d: "Card numbers, dates of birth, addresses and names are removed" },
  { k: "04", t: "Score", d: "Mubit marks every item and quotes the evidence" },
  { k: "05", t: "Route", d: "Breaches are escalated and anything uncertain goes to a person" },
  { k: "06", t: "Correct", d: "An analyst fixes an item and says why in a sentence" },
  { k: "07", t: "Learn", d: "It becomes a rule now and part of a Mubit model later" },
];

export default function Landing() {
  const main = useRef<HTMLDivElement>(null);
  const [active, setActive] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [morphStage, setMorphStage] = useState<0 | 1 | 2 | null>(null);
  const [status] = usePoll<Status>(api.status, 5000);
  const [wall] = usePoll<Wall>(api.wall, 0);
  const [compare] = usePoll<CompareGroup[]>(api.compare, 0);

  // Which section is on screen drives the nav and the background brightness
  useEffect(() => {
    const root = main.current;
    if (!root) return;
    const secs = [...root.querySelectorAll("section")];
    const io = new IntersectionObserver(
      (es) => es.forEach((e) => e.isIntersecting && e.intersectionRatio > 0.55 && setActive(secs.indexOf(e.target as HTMLElement))),
      { root, threshold: [0.55] },
    );
    secs.forEach((s) => io.observe(s));
    return () => io.disconnect();
  }, []);

  const go = (i: number) => {
    const sec = main.current?.querySelectorAll("section")[i] as HTMLElement | undefined;
    if (sec) setTimeout(() => main.current?.scrollTo({ top: sec.offsetTop, behavior: "smooth" }), 30);
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowDown" || e.key === "PageDown") { e.preventDefault(); go(Math.min(SECTIONS.length - 1, active + 1)); }
      if (e.key === "ArrowUp" || e.key === "PageUp") { e.preventDefault(); go(Math.max(0, active - 1)); }
      if (/^[1-5]$/.test(e.key)) go(Number(e.key) - 1);
      if (e.key.toLowerCase() === "l" && active === 1) setFlipped(true);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [active]);

  // The wall: 100 tiles. 5 lit = what QA samples today; flip = what Redress scores
  const tiles = useMemo(() => {
    const real = wall?.tiles ?? [];
    return Array.from({ length: 100 }, (_, i) => ({ tier: real[i % Math.max(1, real.length)]?.risk_tier ?? "low", sampled: [7, 23, 41, 66, 88].includes(i) }));
  }, [wall]);

  const base = compare?.find((g) => g.playbook_version === 0);
  const latest = compare && [...compare].sort((a, b) => b.playbook_version - a.playbook_version)[0];
  const examples = status?.training_examples_sent ?? 0;
  const autoStage: 0 | 1 = examples >= 25 ? 1 : 0;
  const stage = morphStage ?? autoStage;

  return (
    <div className="relative h-screen overflow-hidden">
      <BgCanvas opacity={[1, 0.85, 0.6, 0.35, 0.15][active] ?? 1} />

      <div className="fixed left-7 top-6 z-50"><Logo /></div>
      <Link href="/dashboard" className="cta fixed right-6 top-5 z-50">
        Open the dashboard <i><Arrow /></i>
      </Link>

      <div ref={main} className="snap">
        {/* 1 · HERO */}
        <section className="flex flex-col items-center px-6 pt-[15vh] text-center">
          <InView as="h1" className="max-w-[17ch] text-[clamp(38px,5.2vw,74px)] leading-[1.03]">
            <Words text="We hear" />
            <span className="w" style={{ transitionDelay: "60ms" }}><Glyph /></span>
            <Words text="every call your bank takes" start={3} />
          </InView>
          <InView as="p" className="mt-6 max-w-[660px] text-[15px] leading-relaxed text-[#b9c2ba]">
            <Words text="Redress scores 100% of regulated calls against your compliance scorecard, and learns from every correction your QA analysts make." />
          </InView>
          <div className="absolute bottom-[14vh] left-1/2 grid w-[min(1080px,88vw)] -translate-x-1/2 grid-cols-1 gap-8 md:grid-cols-3">
            {[
              ["01", "We listen", "Each call is recorded and transcribed, and personal details are stripped out first."],
              ["02", "We score", "Every item on the scorecard is marked, with the quote and timestamp behind it."],
              ["03", "We learn", "When an analyst fixes something, it becomes a rule right away and, over time, a model you own."],
            ].map(([k, t, d]) => (
              <InView key={k}>
                <div className="lab">[ {k} ]</div>
                <h3 className="mb-3 mt-2 text-[clamp(18px,1.7vw,23px)]"><Words text={t} /></h3>
                <p className="mx-auto max-w-[300px] text-[13px] leading-relaxed text-[#aab3ab]"><Words text={d} start={2} /></p>
              </InView>
            ))}
          </div>
        </section>

        {/* 2 · PROBLEM */}
        <section className="flex items-center px-[clamp(28px,8vw,120px)]">
          <div className="grid w-full items-center gap-14 md:grid-cols-[1fr_1fr]">
            <InView>
              <div className="lab g">[ The problem ]</div>
              <h2 className="mb-5 mt-3 text-[clamp(38px,4.4vw,64px)] leading-none">
                <Words text="Banks listen to about one call in twenty" /> <em><Words text="and never check the rest" start={7} /></em>
              </h2>
              <p className="max-w-[46ch] text-[15px] leading-relaxed text-[#b9c2ba]">
                QA analysts listen to a small random sample and fill in a compliance scorecard by hand. It takes a long time, two
                analysts can score the same call differently, and whatever goes wrong on the other calls never comes to light.
              </p>
              <div className="mt-8 grid max-w-[520px] grid-cols-3 gap-6">
                <div><div className="text-4xl font-light tracking-tight">1–2%</div><p className="mt-1 text-[11.5px] text-mute">of calls sampled in UK contact centres*</p></div>
                <div><div className="text-4xl font-light tracking-tight">~5%</div><p className="mt-1 text-[11.5px] text-mute">our example: one call in twenty</p></div>
                <div><div className="text-4xl font-light tracking-tight text-lime">100%</div><p className="mt-1 text-[11.5px] text-mute">scored by Redress</p></div>
              </div>
              <p className="lab mt-6">* from our research (ContactBabel, Recordsure), worth checking before quoting</p>
            </InView>
            <Glass className="p-6">
              <div className="flex items-center justify-between">
                <div className="lab">{flipped ? "[ Redress · every call scored ]" : "[ Today · the random sample ]"}</div>
                <button className="btn ghost sm" onClick={() => setFlipped((f) => !f)}>{flipped ? "Show today" : "Score them all"}</button>
              </div>
              <div className="mt-5 grid grid-cols-10 gap-[6px]">
                {tiles.map((t, i) => (
                  <div
                    key={i}
                    className={clsx("tile", flipped ? t.tier : t.sampled ? "low sampled" : "dark")}
                    style={{ transitionDelay: flipped ? `${i * 9}ms` : "0ms" }}
                  />
                ))}
              </div>
              <div className="mt-4 flex flex-wrap gap-4 text-[11px] text-mute">
                {flipped ? (
                  <>
                    <span className="flex items-center gap-2"><i className="tile critical inline-block h-3 w-3" />breach</span>
                    <span className="flex items-center gap-2"><i className="tile high inline-block h-3 w-3" />needs a human</span>
                    <span className="flex items-center gap-2"><i className="tile medium inline-block h-3 w-3" />below pass</span>
                    <span className="flex items-center gap-2"><i className="tile low inline-block h-3 w-3" />compliant</span>
                  </>
                ) : (
                  <span>An analyst hears 5 of these 100 calls, and nobody checks the other 95.</span>
                )}
              </div>
            </Glass>
          </div>
        </section>

        {/* 3 · HOW IT WORKS */}
        <section className="flex flex-col justify-center px-[clamp(28px,7vw,110px)]">
          <InView className="text-center">
            <div className="lab g">[ How it works ]</div>
            <h2 className="mx-auto mt-3 max-w-[22ch] text-[clamp(34px,3.8vw,56px)] leading-[1.04]">
              <Words text="Scored the way your best analyst would" /> <em><Words text="with a person checking whenever it matters" start={6} /></em>
            </h2>
          </InView>
          <div className="mx-auto mt-10 w-full max-w-[1180px]">
            <div className="beam run mb-6" />
            <div className="grid grid-cols-2 gap-3 md:grid-cols-7">
              {PIPELINE.map((p, i) => (
                <InView key={p.k} className="rise" style={{ transitionDelay: `${i * 90}ms` }}>
                  <div className={clsx("flcard h-full", (p.k === "04" || p.k === "07") && "lit")}>
                    <div className="lab">[ {p.k} ]</div>
                    <h4 className="mb-2 mt-2 text-[18px]">{p.t}</h4>
                    <p className="text-[11.5px] leading-snug text-mute">{p.d}</p>
                  </div>
                </InView>
              ))}
            </div>
            <div className="mt-10 grid gap-3 md:grid-cols-4">
              {CRITICAL.map((c) => (
                <Glass key={c.id} className="p-5">
                  <div className="lab g">[ {c.id} · critical ]</div>
                  <h4 className="mb-2 mt-2 text-[18px]">{c.title}</h4>
                  <p className="text-[12.5px] leading-relaxed text-mute">{c.text}</p>
                </Glass>
              ))}
            </div>
            <p className="mt-6 text-center text-[13px] text-mute">
              Missing a breach is far worse than an extra review, so a critical item only passes when a quote proves it, and anything uncertain goes to a person.
            </p>
          </div>
        </section>

        {/* 4 · PROOF */}
        <section className="flex flex-col items-center px-6 pt-[86px]">
          <InView className="text-center">
            <div className="lab g">[ Held-out calls · never seen in training ]</div>
            <h2 className="mt-3 text-[clamp(32px,3.8vw,54px)] leading-[1.05]">
              <Words text="Every breach was caught" /> <em><Words text="on calls it had never seen" start={4} /></em>
            </h2>
            <p className="mt-3 text-[12.5px] leading-relaxed text-mute">
              {latest?.per_call.length ?? 25} held-out calls, labelled by hand before any run and never used for training. These figures come straight from the evaluation runs.
            </p>
          </InView>
          <div className="mt-8 grid w-[min(1000px,88vw)] grid-cols-2 gap-8 md:grid-cols-4">
            <Stat label="Breaches caught" sub={`critical recall · ${latest?.label ?? "latest"}`} value={latest?.metrics.system_critical_recall?.mean} pctv />
            <Stat label="Missed breaches" sub="false negatives on held-out" value={latest?.metrics.false_negatives?.mean} />
            <Stat label="Flag precision" sub={`base ${pct(base?.metrics.critical_precision?.mean)}`} value={latest?.metrics.critical_precision?.mean} pctv />
            <Stat label="Calls scored" sub={`${wall?.breaches ?? 0} breaches flagged now`} value={wall?.scored} />
          </div>
          <div className="mt-4 grid w-[min(1000px,88vw)] gap-3">
            {(compare ?? []).map((g) => {
              const isLatest = g === latest;
              return (
                <div key={`${g.playbook_version}-${g.model}`} className="grid grid-cols-[150px_1fr] items-center gap-4">
                  <div className={clsx("mono rounded-lg border px-2 py-2 text-center text-[9.5px] uppercase tracking-[.12em]",
                    isLatest ? "border-lime/45 bg-lime/10 text-lime" : "border-line bg-white/5 text-[#c6cec6]")}>
                    {g.label} ×{g.runs}
                  </div>
                  <div className={clsx("ticks", isLatest && "latest")}>
                    {g.per_call.map((c) => (
                      <span key={c.call_id} title={`${c.call_id}: ${c.items_correct}/${g.n_items} items`}
                        className={c.false_negatives.length ? "fn" : c.items_correct >= g.n_items - 1 ? "ok" : ""} />
                    ))}
                  </div>
                </div>
              );
            })}
            {!compare?.length && <p className="text-center text-sm text-mute">Run the held-out evaluation to fill this in.</p>}
          </div>
          <p className="lab mt-5 text-center">Each bar is one held-out call. It lights up when at least 8 of the 9 items match the gold label, and turns red if a breach was missed.</p>
        </section>

        {/* 5 · MUBIT + CLOSE */}
        <section className="flex flex-col items-center justify-center px-6">
          <div className="aurora"><i className="a3" /><i className="a1" /><i className="a2" /></div>
          <div className="relative z-10 w-[min(900px,92vw)] text-center">
            <div className="cursor-pointer" onClick={() => setMorphStage(((stage + 1) % 3) as 0 | 1 | 2)} title="Click to step">
              <Morph shape={stage} height={250} />
            </div>
            <InView>
              <div className="lab g">[ Mubit · review.call ]</div>
              <h2 className="mt-3 text-[clamp(34px,4.2vw,58px)] leading-none">
                <Words text="Corrections become" /> <em><Words text="a model you own" start={2} /></em>
              </h2>
            </InView>
            <p className="mt-4 text-[13px] text-mute">
              {stage === 0 && <>So far <b className="text-text">{examples}</b> reviews that use the analysts&apos; rules have gone to Mubit as training examples (playbook v{status?.playbook_version ?? 0}).</>}
              {stage === 1 && <>Mubit has enough examples and is training a small adapter on how this bank scores its calls.</>}
              {stage === 2 && <>The adapter passed Mubit&apos;s tests, so the calls nobody listens to can be scored by a model the bank owns.</>}
            </p>
            <div className="mt-4 flex flex-wrap justify-center gap-2">
              <span className={clsx("ver", stage >= 0 && "on")}>Collecting · {Math.min(examples, 25)}/25</span>
              <span className={clsx("ver", stage >= 1 && "on")}>Training</span>
              <span className={clsx("ver", stage === 2 && "pass")}>Adapter passed ✓</span>
            </div>
            <InView className="mt-10">
              <h3 className="text-[clamp(22px,2.2vw,32px)] leading-snug">
                <Words text="Without Mubit, AI scores calls." /> <span className="text-[#7b857c]"><Words text="With Mubit, it learns how your QA team scores them." start={5} /></span>
              </h3>
            </InView>
            <div className="mt-8 flex justify-center">
              <Link href="/dashboard" className="btn primary px-6 py-3 text-[14px]">Open the dashboard <Arrow /></Link>
            </div>
            <p className="lab mt-8">Built with Mubit, Deepgram, FastAPI and Next.js. All the data is synthetic, and a person signs off every decision.</p>
          </div>
        </section>
      </div>

      <nav className="island">
        {SECTIONS.map((s, i) => (
          <a key={s} className={clsx(active === i && "active")} onClick={() => go(i)}>{s}</a>
        ))}
        <Link href="/dashboard">Dashboard <span className="plus">+</span></Link>
      </nav>
    </div>
  );
}

function Stat({ label, sub, value, pctv }: { label: string; sub: string; value: number | null | undefined; pctv?: boolean }) {
  return (
    <div>
      <div className="flex items-center gap-2 text-[clamp(32px,3.2vw,44px)] tracking-tight">
        <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#7CFF4F" strokeWidth="1.8" style={{ filter: "drop-shadow(0 0 6px rgba(124,255,79,.6))" }}>
          <path d="M12 20V4M5 11l7-7 7 7" />
        </svg>
        {pctv ? <CountUp value={value == null ? null : value * 100} suffix="%" /> : <CountUp value={value} />}
      </div>
      <div className="mt-1 text-[13px]">{label}</div>
      <p className="mt-1 text-[11.5px] leading-snug text-mute">{sub}</p>
    </div>
  );
}

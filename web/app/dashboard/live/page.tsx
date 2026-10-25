"use client";

import clsx from "clsx";
import Link from "next/link";
import { DisconnectReason, Room, RoomEvent, Track } from "livekit-client";
import { useEffect, useRef, useState } from "react";
import { AnswerTag, QueueTag, SectionHead, Spinner } from "@/components/bits";
import { Glass, Glyph } from "@/components/fx";
import { api, lineApi, secs, ts, type Call } from "@/lib/api";
import { StereoRecorder } from "@/lib/line";
import { WavRecorder } from "@/lib/wav";

type Phase = "idle" | "recording" | "calling" | "uploading" | "processing" | "scored" | "failed";

export default function LiveCall() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [elapsed, setElapsed] = useState(0);
  const [level, setLevel] = useState(0);
  const [agent, setAgent] = useState("Sam");
  const [customer, setCustomer] = useState("Ellen Hart");
  const [callId, setCallId] = useState<string | null>(null);
  const [call, setCall] = useState<Call | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [scoredIn, setScoredIn] = useState<number | null>(null);
  const [transcribedIn, setTranscribedIn] = useState<number | null>(null);
  // Phone line: who's on the call ("customer", "agent"); the timer runs once both are
  const [parties, setParties] = useState<string[]>([]);
  const line = useRef<{ room: Room; rec: StereoRecorder } | null>(null);
  const rec = useRef<WavRecorder | null>(null);
  const meter = useRef<AnalyserNode | null>(null); // what the equaliser follows right now
  const stream = useRef<MediaStream | null>(null);
  const started = useRef(0);
  const stoppedAt = useRef(0);
  const fileInput = useRef<HTMLInputElement>(null);
  // A re-review (swap speakers, re-loading a script) must wait for a new review, not show the old one
  const prevReview = useRef<number | null>(null);

  // Recording timer and mic level (drives the pixel equaliser)
  const onCall = phase === "calling" && parties.length === 2;
  useEffect(() => {
    if (phase !== "recording" && !onCall) return;
    const id = setInterval(() => setElapsed((Date.now() - started.current) / 1000), 250);
    return () => clearInterval(id);
  }, [phase, onCall]);

  // Poll the call until it's scored
  useEffect(() => {
    if (!callId || (phase !== "processing" && phase !== "uploading")) return;
    const id = setInterval(async () => {
      try {
        const c = await api.call(callId);
        setCall(c);
        if (c.audio_path && c.utterances.length) setTranscribedIn((v) => v ?? (Date.now() - stoppedAt.current) / 1000);
        if (c.review && c.review.id !== prevReview.current) {
          setPhase("scored");
          setScoredIn((Date.now() - stoppedAt.current) / 1000);
        } else if (c.status === "failed") {
          setPhase("failed");
          setError(c.error ?? "processing failed");
        }
      } catch {}
    }, 500);
    return () => clearInterval(id);
  }, [callId, phase]);

  useEffect(() => () => { stopTracks(); line.current?.room.disconnect(); }, []);

  function stopTracks() {
    stream.current?.getTracks().forEach((t) => t.stop());
    stream.current = null;
  }

  // Drives the pixel equaliser from any audio node (the mic, or both sides of a phone call)
  function watchLevel(an: AnalyserNode) {
    meter.current = an;
    const buf = new Uint8Array(an.fftSize);
    const tick = () => {
      if (meter.current !== an) return;
      an.getByteTimeDomainData(buf);
      let sum = 0;
      for (const v of buf) sum += ((v - 128) / 128) ** 2;
      setLevel(Math.min(1, Math.sqrt(sum / buf.length) * 4));
      requestAnimationFrame(tick);
    };
    tick();
  }

  // Phone line: the laptop joins the call hidden and records Ellen (left) and Sam (right) in one stereo file
  async function openLine() {
    setError(null); setCall(null); setCallId(null); setScoredIn(null); setTranscribedIn(null); setParties([]); setElapsed(0);
    prevReview.current = null;
    const recorder = new StereoRecorder();
    const room = new Room();
    const joined = new Set<string>();
    room.on(RoomEvent.TrackSubscribed, (track, _pub, p) => {
      if (track.kind !== Track.Kind.Audio || (p.identity !== "customer" && p.identity !== "agent")) return;
      recorder.add(track.mediaStreamTrack, p.identity === "agent" ? 1 : 0);
      recorder.start();
      joined.add(p.identity);
      if (joined.size === 2) started.current = Date.now();
      setParties([...joined]);
    });
    room.on(RoomEvent.ParticipantDisconnected, (p) => { if (joined.has(p.identity)) hangUpLine(); });
    room.on(RoomEvent.Disconnected, (reason) => {
      if (line.current?.room !== room) return; // we hung up ourselves
      setError(reason === DisconnectReason.DUPLICATE_IDENTITY
        ? "The line was opened in another tab or on another laptop, which took over the recording."
        : "The laptop lost its connection to the call.");
      hangUpLine();
    });
    try {
      const l = await lineApi.join("recorder");
      await room.connect(l.url!, l.token!);
      line.current = { room, rec: recorder };
      watchLevel(recorder.analyser);
      setPhase("calling");
    } catch (e) {
      recorder.close();
      setError((e as Error).message);
    }
  }

  async function hangUpLine() {
    const l = line.current;
    if (!l) return;
    line.current = null;
    stoppedAt.current = Date.now();
    meter.current = null;
    setLevel(0);
    const blob = await l.rec.stop();
    l.room.disconnect();
    // No recording means nobody called: the line was just closed
    if (blob?.size) upload(blob, "call.webm", true);
    else setPhase("idle");
  }

  async function start() {
    setError(null); setCall(null); setCallId(null); setScoredIn(null); setTranscribedIn(null);
    prevReview.current = null;
    try {
      const s = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: false, noiseSuppression: true, autoGainControl: true } });
      stream.current = s;
      const r = new WavRecorder(s);
      rec.current = r;
      watchLevel(r.analyser);
      started.current = Date.now();
      stoppedAt.current = 0;
      setElapsed(0);
      setPhase("recording");
    } catch (e) {
      setError(`Microphone unavailable: ${(e as Error).message}`);
    }
  }

  async function stop() {
    const r = rec.current;
    if (!r) return;
    stoppedAt.current = Date.now();
    rec.current = null;
    meter.current = null;
    setLevel(0);
    setPhase("uploading");
    const wav = await r.stop();
    stopTracks();
    upload(wav, "call.wav");
  }

  async function upload(blob: Blob, name: string, twoChannel = false) {
    setPhase("uploading");
    if (!stoppedAt.current) stoppedAt.current = Date.now();
    try {
      const { call_id } = await api.upload(blob, name, agent, customer, twoChannel);
      setCallId(call_id);
      setPhase("processing");
    } catch (e) {
      setError((e as Error).message);
      setPhase("failed");
    }
  }

  async function loadScript(id: string) {
    setError(null); setCall(null); setScoredIn(null); setTranscribedIn(null);
    prevReview.current = (await api.call(id).catch(() => null))?.review?.id ?? null;
    stoppedAt.current = Date.now();
    const { call_id } = await api.loadScript(id);
    setCallId(call_id);
    setPhase("processing");
  }

  const review = call?.review;
  const fails = review?.critical_fails ?? [];
  const out = review?.output_json;
  const cards = [
    { k: "Complaint", on: !!out?.complaint.expressed, h: out?.complaint.expressed ? out.complaint.category || "Complaint" : "—", p: out?.complaint.quote },
    { k: "Vulnerable", on: !!out?.vulnerability.length, h: out?.vulnerability.map((v) => v.driver.replace("_", " ")).join(", ") || "—", p: out?.vulnerability[0]?.quote },
    { k: "Critical fails", on: fails.length > 0, h: fails.length ? fails.join(" · ") : review ? "None" : "—", p: review ? `Score ${review.score} · ${review.pass ? "pass" : "fail"}` : undefined, amber: true },
    { k: "Routed", on: !!call?.queue, h: call?.queue ? { breach: "Escalate now", analyst: "To an analyst", audit: "Audit sample", auto: "Auto-scored" }[call.queue.kind] : "—", p: call?.queue?.reasons_json?.[0] },
  ];

  return (
    <div className="grid gap-6">
      <SectionHead
        lab="Live call · recording"
        title={<>Redress is <em>listening</em></>}
        sub="Open the line and call from the two phones, or put a phone on speaker next to the laptop and record. Hang up, and the scorecard appears with every quote and timestamp."
        right={
          <div className="text-right">
            <span className={clsx("live", phase !== "recording" && !onCall && "off")}>
              {phase === "recording" ? "RECORDING" : phase === "calling" ? (onCall ? "ON CALL" : parties.length ? "RINGING" : "LINE OPEN") : phase.toUpperCase()}
            </span>
            <span className="mono block text-[48px] tracking-[.02em]" style={{ textShadow: "0 0 24px rgba(124,255,79,.25)" }}>{ts(elapsed)}</span>
            <div className="flex justify-end gap-2">
              {phase === "recording" ? (
                <button className="btn danger" onClick={stop}>Stop &amp; score</button>
              ) : phase === "calling" ? (
                <button className="btn danger" onClick={hangUpLine}>{parties.length ? "Hang up & score" : "Close the line"}</button>
              ) : (
                <>
                  <button className="btn primary" onClick={openLine} disabled={phase === "uploading" || phase === "processing"}>Open the line</button>
                  <button className="btn ghost" onClick={start} disabled={phase === "uploading" || phase === "processing"}>Record call</button>
                </>
              )}
              <button className="btn ghost" onClick={() => fileInput.current?.click()} disabled={phase === "recording" || phase === "calling"}>Upload file</button>
              <input ref={fileInput} type="file" accept="audio/*" className="hidden"
                onChange={(e) => { const f = e.target.files?.[0]; if (f) { setCall(null); prevReview.current = null; stoppedAt.current = Date.now(); upload(f, f.name); } e.target.value = ""; }} />
            </div>
          </div>
        }
      />

      <Glass className="relative overflow-hidden p-8">
        <div className="grid items-center gap-8 md:grid-cols-[1fr_1.2fr_2fr]">
          <div>
            <Glyph className="eq" cols={9} rows={7} level={phase === "recording" || phase === "calling" ? level : phase === "processing" ? undefined : 0} />
            <span className="mono mt-4 block text-[10.5px] tracking-[.16em] text-lime">
              {phase === "recording" ? "BOTH SPEAKERS · ROOM MIC"
                : phase === "calling" ? (onCall ? "TWO PHONES · ONE CHANNEL EACH" : parties.length ? "RINGING THE COLLEAGUE" : "WAITING FOR THE CUSTOMER TO CALL")
                : phase === "processing" || phase === "uploading" ? "TRANSCRIBING · SCORING" : "WAITING FOR THE CALL"}
            </span>
            <dl className="mt-4 grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-[13px]">
              <dt className="lab pt-0.5">Colleague</dt>
              <dd><input className="input !py-1" value={agent} onChange={(e) => setAgent(e.target.value)} /></dd>
              <dt className="lab pt-0.5" title="Spoken names to redact from the transcript and the stored audio">Customer</dt>
              <dd><input className="input !py-1" value={customer} placeholder="name to redact" onChange={(e) => setCustomer(e.target.value)} /></dd>
              <dt className="lab pt-0.5">Phones</dt><dd className="mono text-[11.5px] text-[#cfd7cf]">/call/customer · /call/agent</dd>
              <dt className="lab pt-0.5">Call</dt><dd className="text-[#cfd7cf]">{callId ?? "—"}</dd>
              <dt className="lab pt-0.5">Transcript in</dt><dd className="text-[#cfd7cf]">{transcribedIn ? `${transcribedIn.toFixed(1)}s after hang-up` : "—"}</dd>
              <dt className="lab pt-0.5">Scored in</dt><dd className="text-[#cfd7cf]">{scoredIn ? `${scoredIn.toFixed(1)}s after hang-up` : "—"}</dd>
            </dl>
          </div>
          <div className={clsx("beam", (phase === "processing" || phase === "uploading" || phase === "recording" || phase === "calling") && "run")} />
          <div className="grid grid-cols-2 gap-3">
            {cards.map((c) => (
              <div key={c.k} className={clsx("flcard min-h-[112px]", c.on && (c.amber ? "lit" : "lit"))}>
                <div className="lab">[ {c.k} ]</div>
                <h4 className="mb-1 mt-2 text-[18px] capitalize">{c.h}</h4>
                {c.p && <p className="line-clamp-3 text-[11.5px] leading-snug text-mute">{c.p}</p>}
              </div>
            ))}
          </div>
        </div>
        {(phase === "uploading" || phase === "processing") && (
          <p className="mt-6 flex items-center gap-2 text-sm text-mute"><Spinner /> Deepgram is transcribing, then Mubit scores the call…</p>
        )}
        {error && <p className="mt-6 text-sm text-red">{error}</p>}
      </Glass>

      <div className="grid gap-4 md:grid-cols-[1.3fr_1fr]">
        <Glass className="p-6">
          <div className="lab">[ Transcript ]</div>
          <h3 className="mb-4 mt-2 text-[22px]">Every word, both speakers</h3>
          {call?.audio_path && (
            <div className="mb-4">
              <div className="lab mb-2">Recording · phone calls: customer left, colleague right</div>
              <audio controls src={api.audioUrl(call.id)} className="w-full" />
            </div>
          )}
          <div className="scroll flex max-h-[420px] flex-col gap-3 pr-1">
            {(call?.utterances ?? []).map((u, i) => (
              <div key={i} className={clsx("msg enter", u.speaker)}>
                <small><span>{u.speaker === "agent" ? "COLLEAGUE" : "CUSTOMER"}</span><span>{ts(u.start_s)}</span></small>
                {u.raw}
              </div>
            ))}
            {!call?.utterances?.length && <p className="text-sm text-mute">The transcript appears after the call.</p>}
          </div>
          {call?.utterances?.length ? (
            <button className="btn ghost sm mt-4" onClick={async () => { prevReview.current = call.review?.id ?? null; stoppedAt.current = Date.now(); await api.swap(call.id); setPhase("processing"); }}>Swap speakers</button>
          ) : null}
        </Glass>
        <Glass className="p-6">
          <div className="lab">[ Scorecard ]</div>
          <h3 className="mb-4 mt-2 text-[22px]">{review ? `Score ${review.score} · ${review.pass ? "pass" : "fail"}` : "Waiting for the review"}</h3>
          <div className="grid gap-2">
            {(review?.items ?? []).map((it) => (
              <div key={it.id} className="flex items-center justify-between gap-3 border-b border-line pb-2 text-[13px]">
                <span><b className="mono mr-2 text-[11px] text-mute">{it.id}</b>{it.label}</span>
                <AnswerTag a={it.answer} />
              </div>
            ))}
          </div>
          {review && (
            <div className="mt-4 flex flex-wrap items-center gap-2">
              <QueueTag k={call?.queue?.kind} />
              <span className="lab">{review.model} · {secs(review.latency_ms)} · v{review.playbook_version}</span>
            </div>
          )}
          {call && review && (
            <Link href={`/dashboard/calls/${call.id}`} className="btn primary mt-5">Open the evaluation form →</Link>
          )}
          {call?.batch_id && (
            <Link href="/dashboard/batch" className="btn ghost mt-5 ml-2">See it in this month&apos;s batch →</Link>
          )}
          <div className="mt-6 border-t border-line pt-4">
            <div className="lab mb-2">Rehearse without audio</div>
            <div className="flex gap-2">
              <button className="btn ghost sm" onClick={() => loadScript("demo_call1")}>Demo call 1 (text)</button>
              <button className="btn ghost sm" onClick={() => loadScript("demo_call2")}>Demo call 2 (text)</button>
            </div>
          </div>
        </Glass>
      </div>
    </div>
  );
}

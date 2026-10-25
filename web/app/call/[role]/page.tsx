"use client";

/*
  The two phones of the demo call (state and tokens: lib/line-server.ts). Open on the Vercel deploy
  (or any HTTPS tunnel), because phones only allow the mic over HTTPS:
    /call/customer  Ellen's phone: rings Thistle Bank once the laptop has opened the line
    /call/agent     Sam's phone: shows the incoming call and answers it
  The laptop's Live call page records both sides; this page only talks.
*/
import { DisconnectReason, Room, RoomEvent } from "livekit-client";
import { useParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Glyph } from "@/components/fx";
import { lineApi, ts, type Line } from "@/lib/api";
import { joinCall } from "@/lib/line";

type Phase = "idle" | "joining" | "live" | "ended";

export default function PhoneCall() {
  const { role } = useParams<{ role: string }>();
  const isAgent = role === "agent";
  const otherSide = isAgent ? "customer" : "agent";
  const [line, setLine] = useState<Line>({ state: "closed" });
  const [phase, setPhase] = useState<Phase>("idle");
  const [connected, setConnected] = useState(false); // the other phone is on the call
  const [elapsed, setElapsed] = useState(0);
  const [needsTap, setNeedsTap] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const room = useRef<Room | null>(null);
  const since = useRef(0);
  const leaving = useRef(false); // we hung up ourselves, so a closed connection isn't an error
  const dropped = useRef<string | null>(null); // why LiveKit closed the call, if it did

  // Watch the line until this phone joins it
  useEffect(() => {
    if (phase === "joining" || phase === "live") return;
    const tick = () => lineApi.line().then(setLine).catch(() => setLine({ state: "closed" }));
    tick();
    const id = setInterval(tick, 1500);
    return () => clearInterval(id);
  }, [phase]);

  const incoming = isAgent && phase !== "live" && line.state === "calling";
  useEffect(() => {
    if (incoming) navigator.vibrate?.([500, 300, 500]);
  }, [incoming, line]);

  useEffect(() => {
    if (phase !== "live" || !connected) return;
    const id = setInterval(() => setElapsed((Date.now() - since.current) / 1000), 250);
    return () => clearInterval(id);
  }, [phase, connected]);

  useEffect(() => () => { room.current?.disconnect(); }, []);

  function otherJoined() {
    since.current = Date.now();
    setElapsed(0);
    setConnected(true);
  }

  async function call() {
    setError(null); setConnected(false); setPhase("joining");
    leaving.current = false;
    dropped.current = null;
    // No auto gain: it turns up the other person's voice from across the room, which ends up on this channel as echo
    const r = new Room({ audioCaptureDefaults: { echoCancellation: true, noiseSuppression: true, autoGainControl: false } });
    room.current = r;
    r.startAudio().catch(() => {}); // unlock playback while we still have the tap (iOS)
    r.on(RoomEvent.AudioPlaybackStatusChanged, () => setNeedsTap(!r.canPlaybackAudio));
    r.on(RoomEvent.ParticipantConnected, (p) => { if (p.identity === otherSide) otherJoined(); });
    r.on(RoomEvent.ParticipantDisconnected, (p) => { if (p.identity === otherSide) hangUp(); });
    // LiveKit closed the call: say why in words (its own message is "Cancelled publication by calling unpublish")
    r.on(RoomEvent.Disconnected, (reason) => {
      if (leaving.current) return;
      dropped.current = reason === DisconnectReason.DUPLICATE_IDENTITY
        ? `This ${isAgent ? "colleague" : "customer"} link was opened on another phone or tab, which took the call over. Open /call/customer on one phone and /call/agent on the other.`
        : "The call dropped: the connection was lost. Check the signal and try again.";
      setError(dropped.current);
      setConnected(false);
      setPhase("ended");
    });
    try {
      const l = await lineApi.join(isAgent ? "agent" : "customer");
      await joinCall(r, l.url!, l.token!);
      if (r.remoteParticipants.has(otherSide)) otherJoined();
      setPhase("live");
      navigator.wakeLock?.request("screen").catch(() => {});
    } catch (e) {
      if (leaving.current) return;
      leaving.current = true;
      setError(dropped.current ?? `Couldn't join the call: ${(e as Error).message}`);
      setPhase(dropped.current ? "ended" : "idle");
      r.disconnect();
    }
  }

  function hangUp() {
    leaving.current = true;
    room.current?.disconnect();
    room.current = null;
    setConnected(false);
    setPhase("ended");
  }

  const canCall = isAgent ? line.state === "calling" : line.state === "waiting";
  const status =
    phase === "joining" ? "CONNECTING"
    : phase === "live" ? (connected ? "ON CALL" : isAgent ? "CONNECTING" : "CALLING THISTLE BANK")
    : incoming ? "INCOMING CALL"
    : phase === "ended" ? "CALL ENDED"
    : isAgent ? "WAITING FOR CALLS"
    : line.state === "waiting" ? "LINE OPEN" : "LINE CLOSED";

  return (
    <main className="mx-auto flex min-h-[100dvh] max-w-[430px] flex-col items-center px-6 pb-[calc(env(safe-area-inset-bottom)+28px)] pt-[calc(env(safe-area-inset-top)+28px)] text-center">
      <div className="lab g">[ {isAgent ? "Colleague phone" : "Complaints line"} ]</div>
      <h1 className="mt-3 text-[30px]">Thistle Bank</h1>
      <p className="mt-1 text-[13px] text-mute">{isAgent ? (incoming ? "Customer calling" : "Complaints team") : "0800 · complaints"}</p>

      <div className="flex flex-1 flex-col items-center justify-center gap-6">
        <Glyph className="eq" cols={9} rows={7} level={(phase === "live" && connected) || incoming ? undefined : 0} />
        <span className="mono text-[11px] tracking-[.16em] text-lime">{status}</span>
        {phase === "live" && connected && <span className="mono text-[44px] tracking-[.02em]">{ts(elapsed)}</span>}
      </div>

      {(error || line.error) && <p className="mb-4 text-sm text-red">{error || line.error}</p>}
      {needsTap && (
        <button className="btn ghost mb-3" onClick={() => room.current?.startAudio()}>Tap to hear the call</button>
      )}
      {phase === "joining" ? (
        // Not "End call" yet: a second tap on the same spot while connecting would hang up mid-join
        <button className="btn ghost w-full justify-center !py-4 !text-[16px]" disabled>Connecting…</button>
      ) : phase === "live" ? (
        <button className="btn danger w-full justify-center !py-4 !text-[16px]" onClick={hangUp}>End call</button>
      ) : (
        <button className="btn primary w-full justify-center !py-4 !text-[16px]" onClick={call} disabled={!canCall}>
          {isAgent ? "Answer" : "Call Thistle Bank"}
        </button>
      )}
    </main>
  );
}

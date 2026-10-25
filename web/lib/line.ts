/** LiveKit for the phone line (app/capture/room.py): the two phones talk, the laptop records both sides. */
import { Room, RoomEvent, Track } from "livekit-client";

/** A phone joins the call: publish the mic, play the other side. */
export async function joinCall(room: Room, url: string, token: string) {
  room.on(RoomEvent.TrackSubscribed, (track) => {
    if (track.kind === Track.Kind.Audio) document.body.appendChild(track.attach());
  });
  room.on(RoomEvent.TrackUnsubscribed, (track) => track.detach().forEach((el) => el.remove()));
  await room.connect(url, token);
  await room.localParticipant.setMicrophoneEnabled(true);
}

/**
 * The laptop's silent recorder: one stereo file with the customer on the left channel (0) and the
 * colleague on the right (1), so the backend labels speakers from the channel. Create it inside a click:
 * Chrome only runs an AudioContext after the user has interacted with the page.
 */
export class StereoRecorder {
  readonly ctx = new AudioContext();
  readonly analyser = this.ctx.createAnalyser();
  private merger = this.ctx.createChannelMerger(2);
  private dest = this.ctx.createMediaStreamDestination();
  private rec: MediaRecorder | null = null;
  private chunks: Blob[] = [];
  private players: HTMLAudioElement[] = [];

  constructor() {
    this.analyser.fftSize = 512;
    this.merger.connect(this.dest);
    this.merger.connect(this.analyser);
  }

  add(track: MediaStreamTrack, channel: 0 | 1) {
    const stream = new MediaStream([track]);
    // Chrome only feeds remote WebRTC audio into Web Audio while a media element plays it, so keep a muted one
    const el = new Audio();
    el.muted = true;
    el.srcObject = stream;
    el.play().catch(() => {});
    this.players.push(el);
    this.ctx.createMediaStreamSource(stream).connect(this.merger, 0, channel);
  }

  /** Starts recording (on the first voice); later tracks join the same timeline. */
  start() {
    if (this.rec) return;
    const mime = MediaRecorder.isTypeSupported("audio/webm;codecs=opus") ? "audio/webm;codecs=opus" : "";
    this.rec = new MediaRecorder(this.dest.stream, mime ? { mimeType: mime, audioBitsPerSecond: 128000 } : undefined);
    this.rec.ondataavailable = (e) => e.data.size && this.chunks.push(e.data);
    this.rec.start(1000);
  }

  /** Stops and returns the stereo recording, or null if nobody ever spoke on the line. */
  stop(): Promise<Blob | null> {
    const rec = this.rec;
    if (!rec) {
      this.close();
      return Promise.resolve(null);
    }
    return new Promise((resolve) => {
      rec.onstop = () => {
        this.close();
        resolve(new Blob(this.chunks, { type: "audio/webm" }));
      };
      rec.stop();
    });
  }

  close() {
    this.players.forEach((el) => (el.srcObject = null));
    this.ctx.close().catch(() => {});
  }
}

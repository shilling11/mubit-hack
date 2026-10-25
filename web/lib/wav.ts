/** Record the mic as raw PCM and encode a 16 kHz mono WAV.
 *
 * WAV (not WebM) because: the file states its exact length, so the audio player's
 * scrub bar moves linearly; and the server can silence redacted words in it
 * with Python's built-in wave module.
 */
const TARGET_RATE = 16000;

export class WavRecorder {
  private ctx: AudioContext;
  private node: ScriptProcessorNode;
  private source: MediaStreamAudioSourceNode;
  private chunks: Float32Array[] = [];
  readonly analyser: AnalyserNode;

  constructor(stream: MediaStream) {
    this.ctx = new AudioContext();
    this.source = this.ctx.createMediaStreamSource(stream);
    this.analyser = this.ctx.createAnalyser();
    this.analyser.fftSize = 512;
    // ScriptProcessor is deprecated but universally supported and needs no worklet file
    this.node = this.ctx.createScriptProcessor(4096, 1, 1);
    this.node.onaudioprocess = (e) => this.chunks.push(new Float32Array(e.inputBuffer.getChannelData(0)));
    this.source.connect(this.analyser);
    this.source.connect(this.node);
    this.node.connect(this.ctx.destination); // required for onaudioprocess to fire; it outputs silence
  }

  /** Stop and return the recording as a WAV blob. */
  async stop(): Promise<Blob> {
    this.node.disconnect();
    this.source.disconnect();
    const rate = this.ctx.sampleRate;
    await this.ctx.close();
    const total = this.chunks.reduce((n, c) => n + c.length, 0);
    const all = new Float32Array(total);
    let o = 0;
    for (const c of this.chunks) { all.set(c, o); o += c.length; }
    return encodeWav(downsample(all, rate, TARGET_RATE), TARGET_RATE);
  }
}

function downsample(input: Float32Array, from: number, to: number): Float32Array {
  if (from === to) return input;
  const ratio = from / to;
  const out = new Float32Array(Math.floor(input.length / ratio));
  for (let i = 0; i < out.length; i++) {
    // average the source samples in this window (simple low-pass)
    const a = Math.floor(i * ratio), b = Math.min(input.length, Math.floor((i + 1) * ratio));
    let sum = 0;
    for (let j = a; j < b; j++) sum += input[j];
    out[i] = sum / Math.max(1, b - a);
  }
  return out;
}

function encodeWav(samples: Float32Array, rate: number): Blob {
  const buf = new ArrayBuffer(44 + samples.length * 2);
  const v = new DataView(buf);
  const str = (off: number, s: string) => { for (let i = 0; i < s.length; i++) v.setUint8(off + i, s.charCodeAt(i)); };
  str(0, "RIFF"); v.setUint32(4, 36 + samples.length * 2, true); str(8, "WAVE");
  str(12, "fmt "); v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true);
  v.setUint32(24, rate, true); v.setUint32(28, rate * 2, true); v.setUint16(32, 2, true); v.setUint16(34, 16, true);
  str(36, "data"); v.setUint32(40, samples.length * 2, true);
  for (let i = 0; i < samples.length; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    v.setInt16(44 + i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }
  return new Blob([buf], { type: "audio/wav" });
}

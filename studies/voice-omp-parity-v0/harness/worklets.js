// AudioWorklet processors for the Chromium (z0live) arm.
// pcm-source: sample-accurate scripted microphone (clips mixed over a -85 dBFS noise floor).
// level-meter: 50 ms (2400-sample @48 kHz) RMS windows of the REMOTE assistant audio, plus a
//              16 kHz int16 copy for the private raw recording.
class PcmSource extends AudioWorkletProcessor {
  constructor() {
    super();
    this.active = [];
    this.seed = 20261020;
    this.port.onmessage = ({ data }) => {
      if (data.type === "play") this.active.push({ pcm: data.pcm, pos: 0, mark: data.mark, started: false });
    };
  }
  process(_inputs, outputs) {
    const out = outputs[0][0];
    for (let i = 0; i < out.length; i++) {
      this.seed = (this.seed * 1664525 + 1013904223) >>> 0;
      out[i] = ((this.seed / 4294967296) * 2 - 1) * 1e-4;
    }
    for (const a of [...this.active]) {
      if (!a.started) {
        a.started = true;
        this.port.postMessage({ type: "mark", mark: a.mark, phase: "start", ctx: currentTime });
      }
      const n = Math.min(out.length, a.pcm.length - a.pos);
      for (let i = 0; i < n; i++) out[i] += a.pcm[a.pos + i];
      a.pos += n;
      if (a.pos >= a.pcm.length) {
        this.active.splice(this.active.indexOf(a), 1);
        this.port.postMessage({ type: "mark", mark: a.mark, phase: "end", ctx: currentTime + n / sampleRate });
      }
    }
    return true;
  }
}
registerProcessor("pcm-source", PcmSource);

class LevelMeter extends AudioWorkletProcessor {
  constructor() {
    super();
    this.window = Math.round(sampleRate * 0.05);
    this.sum = 0;
    this.n = 0;
    this.raw = new Int16Array(800);
    this.rawN = 0;
    this.phase = 0;
    this.acc = 0;
    this.decim = Math.round(sampleRate / 16000);
  }
  process(inputs) {
    const ch = inputs[0] && inputs[0][0];
    const len = ch ? ch.length : 128;
    for (let i = 0; i < len; i++) {
      const s = ch ? ch[i] : 0;
      this.sum += s * s;
      this.n++;
      this.acc += s;
      if (++this.phase === this.decim) {
        const v = Math.max(-1, Math.min(1, this.acc / this.decim));
        this.raw[this.rawN++] = Math.round(v * 32767);
        this.phase = 0;
        this.acc = 0;
        if (this.rawN === this.raw.length) {
          this.port.postMessage({ type: "raw", pcm: this.raw });
          this.raw = new Int16Array(800);
          this.rawN = 0;
        }
      }
      if (this.n === this.window) {
        this.port.postMessage({ type: "level", rms: Math.sqrt(this.sum / this.n), ctx: currentTime + (i + 1) / sampleRate });
        this.sum = 0;
        this.n = 0;
      }
    }
    return true;
  }
}
registerProcessor("level-meter", LevelMeter);

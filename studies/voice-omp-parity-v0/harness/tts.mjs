// Offline TTS for scenario utterances: Kokoro-82M (Apache-2.0) via kokoro-js 1.2.1.
// Uses the locally cached runtime that OMP installs for its own TTS; no network access.
// Usage: node tts.mjs <scenarios.json> <out-dir> [voice]
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const RUNTIME = process.env.KOKORO_RUNTIME || path.join(process.env.HOME, ".cache/omp/cache/tts-runtime/kokoro-1.2.1");
const MODEL = "onnx-community/Kokoro-82M-v1.0-ONNX";
const [scenarioPath, outDir, voice = "am_michael"] = process.argv.slice(2);
if (!scenarioPath || !outDir) throw new Error("usage: node tts.mjs <scenarios.json> <out-dir> [voice]");

const require = createRequire(path.join(RUNTIME, "node_modules/kokoro-js/package.json"));
const transformers = require("@huggingface/transformers");
transformers.env.allowRemoteModels = false;
transformers.env.localModelPath = path.join(RUNTIME, "node_modules/@huggingface/transformers/.cache");
transformers.env.cacheDir = transformers.env.localModelPath;
const { KokoroTTS } = await import(path.join(RUNTIME, "node_modules/kokoro-js/dist/kokoro.js"));

function wav16(samples, rate) {
  const data = Buffer.alloc(samples.length * 2);
  for (let i = 0; i < samples.length; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    data.writeInt16LE(Math.round(s * 32767), i * 2);
  }
  const h = Buffer.alloc(44);
  h.write("RIFF", 0); h.writeUInt32LE(36 + data.length, 4); h.write("WAVE", 8);
  h.write("fmt ", 12); h.writeUInt32LE(16, 16); h.writeUInt16LE(1, 20); h.writeUInt16LE(1, 22);
  h.writeUInt32LE(rate, 24); h.writeUInt32LE(rate * 2, 28); h.writeUInt16LE(2, 32); h.writeUInt16LE(16, 34);
  h.write("data", 36); h.writeUInt32LE(data.length, 40);
  return Buffer.concat([h, data]);
}

const spec = JSON.parse(fs.readFileSync(scenarioPath, "utf8"));
fs.mkdirSync(outDir, { recursive: true });
const tts = await KokoroTTS.from_pretrained(MODEL, { dtype: "q8", device: "cpu" });
const manifest = { engine: "kokoro-js@1.2.1", model: MODEL, dtype: "q8", voice, sample_rate: 24000, utterances: {} };
for (const [id, text] of Object.entries(spec.utterances)) {
  const audio = await tts.generate(text, { voice });
  const file = path.join(outDir, `${id}.24k.wav`);
  fs.writeFileSync(file, wav16(audio.audio, audio.sampling_rate));
  manifest.utterances[id] = { text, file: path.basename(file), samples: audio.audio.length, rate: audio.sampling_rate };
  console.log(`tts ${id} ${(audio.audio.length / audio.sampling_rate).toFixed(2)}s`);
}
fs.writeFileSync(path.join(outDir, "tts-manifest.json"), JSON.stringify(manifest, null, 2));

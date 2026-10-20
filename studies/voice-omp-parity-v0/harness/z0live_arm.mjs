// z0live arm driver (Node + playwright-core + system Chromium). Uses an ISOLATED broker
// (loopback port, private Z0LIVE_DATA) — never the owner's phone broker/inbox.
// node harness/z0live_arm.mjs --scenario <id> --run-dir <dir> --assets <dir> --z0live <worktree> --data <dir> --base http://127.0.0.1:18791
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { parseArgs } from "node:util";
import { createRequire } from "node:module";

const { values: args } = parseArgs({
  options: {
    scenario: { type: "string" },
    "run-dir": { type: "string" },
    assets: { type: "string" },
    z0live: { type: "string" },
    data: { type: "string" },
    base: { type: "string", default: "http://127.0.0.1:18791" },
    scenarios: { type: "string", default: path.join(import.meta.dirname, "../scenarios.json") },
    chromium: { type: "string", default: process.env.CHROMIUM_PATH || "/usr/bin/chromium" },
    arm: { type: "string", default: "z0live-realtime" },
    "playwright-from": { type: "string", default: "/mnt/zer0models/workspace/zer0/products/z0live/desktop/tests/package.json" },
  },
});
const require = createRequire(args["playwright-from"]);
const { chromium } = require("playwright-core");
const here = import.meta.dirname;
const runDir = args["run-dir"];
fs.mkdirSync(runDir, { recursive: true });
const spec = JSON.parse(fs.readFileSync(args.scenarios, "utf8"));
const scenario = spec.scenarios.find(s => s.id === args.scenario);
if (!scenario) throw new Error("unknown scenario " + args.scenario);
const clipIds = [...new Set(scenario.steps.flatMap(s => (s.utt ? [s.utt] : s.clip ? [s.clip] : [])))];
const env = { ...process.env, Z0LIVE_DATA: args.data };
const pairing = execFileSync(path.join(args.z0live, "bin/z0live"), ["pair", "voice-eval-" + Date.now()], { encoding: "utf8", env });
const token = pairing.match(/Device token: ([^\n]+)/)[1];
const revoke = () => execFileSync("python3", ["-c", `import sys;sys.path.insert(0,${JSON.stringify(path.join(args.z0live, "desktop"))});from z0live_desktop.core import Store;Store().revoke_token(sys.stdin.read())`], { input: token, env });

const browser = await chromium.launch({
  executablePath: args.chromium,
  args: ["--no-sandbox", "--autoplay-policy=no-user-gesture-required", "--disable-audio-output", "--mute-audio", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
});
const meta = { arm: args.arm, scenario: scenario.id, loadavg_start: fs.readFileSync("/proc/loadavg", "utf8").trim(), chromium: browser.version(), level_window_ms: 50, level_point: "Chromium WebAudio on remote track (after NetEq jitter buffer/decoder), before output device" };
let out;
try {
  const page = await browser.newPage();
  const files = { "/voice-eval/index.html": ["text/html", "<!doctype html><title>voice eval</title><script type=module>import {runZ0live} from '/voice-eval/z0live_page.mjs'; window.runZ0live=runZ0live; window.ready=true;</script>"], "/voice-eval/z0live_page.mjs": ["text/javascript", fs.readFileSync(path.join(here, "z0live_page.mjs"))], "/voice-eval/runner.mjs": ["text/javascript", fs.readFileSync(path.join(here, "runner.mjs"))], "/voice-eval/worklets.js": ["text/javascript", fs.readFileSync(path.join(here, "worklets.js"))] };
  await page.route(args.base + "/voice-eval/**", route => {
    const p = new URL(route.request().url()).pathname;
    if (files[p]) return route.fulfill({ contentType: files[p][0], body: files[p][1] });
    const m = p.match(/^\/voice-eval\/assets\/([\w-]+)\.48k\.f32$/);
    if (m) return route.fulfill({ contentType: "application/octet-stream", body: fs.readFileSync(path.join(args.assets, `${m[1]}.48k.f32`)) });
    return route.fulfill({ status: 404, body: "" });
  });
  page.on("console", msg => msg.type() === "error" && fs.appendFileSync(path.join(runDir, "console.log"), msg.text() + "\n"));
  await page.goto(args.base + "/voice-eval/index.html");
  await page.waitForFunction(() => window.ready === true);
  out = await page.evaluate(params => window.runZ0live(params), {
    base: args.base,
    token,
    scenario,
    clipIds,
    mintBody: { client: "web", context: { app: "voice-eval", screen: "headless", test: true }, tools: [] },
    transport: args.arm === "z0live-bidi" ? "bidi" : "realtime",
  });
} catch (e) {
  meta.error = String(e?.message ?? e);
} finally {
  await browser.close();
  revoke();
}
if (out && out.session?.transport === "bidi") {
  // The bidi client sees no assistant turn.done on its data channel; import the broker's own
  // sideband transcript record (read-only) on the same local clock.
  const rows = JSON.parse(execFileSync("python3", ["-c", `import json,sqlite3,sys,pathlib; db=sqlite3.connect((pathlib.Path(sys.argv[1])/'broker.db').as_uri()+'?mode=ro',uri=True); print(json.dumps([[r[0], json.loads(r[1])] for r in db.execute("SELECT ts, body FROM events WHERE session_id=? ORDER BY id", (sys.argv[2],))]))`, args.data, out.session.id], { encoding: "utf8" }));
  for (const [ts, body] of rows) {
    const role = body.type === "user_transcript" ? "user" : body.type === "assistant_transcript" ? "assistant" : null;
    if (role && body.text) out.events.push({ t: +(ts * 1000 - out.epoch0).toFixed(1), kind: "wire", channel: "datachannel", type: "turn.done", source: "broker_db", turn: { role, transcript: body.text } });
  }
  out.events.sort((a, b) => a.t - b.t);
}
if (out) {
  fs.writeFileSync(path.join(runDir, "events.jsonl"), out.events.map(e => JSON.stringify(e)).join("\n") + "\n");
  fs.writeFileSync(path.join(runDir, "levels.jsonl"), out.levels.map(([t, r]) => `${t} ${r}`).join("\n") + "\n");
  const pcm = Buffer.from(out.raw_b64, "base64");
  const h = Buffer.alloc(44);
  h.write("RIFF", 0); h.writeUInt32LE(36 + pcm.length, 4); h.write("WAVE", 8); h.write("fmt ", 12); h.writeUInt32LE(16, 16); h.writeUInt16LE(1, 20); h.writeUInt16LE(1, 22); h.writeUInt32LE(16000, 24); h.writeUInt32LE(32000, 28); h.writeUInt16LE(2, 32); h.writeUInt16LE(16, 34); h.write("data", 36); h.writeUInt32LE(pcm.length, 40);
  fs.writeFileSync(path.join(runDir, "output.16k.wav"), Buffer.concat([h, pcm]));
  Object.assign(meta, { error: meta.error ?? out.error, connect_ms: out.connect_ms, model: out.session.model, voice: out.session.voice, live_transport: out.session.transport, instructions_version: out.session.instructions_version, voice_plan_digest: out.session.plan_digest, transport: out.session.transport === "bidi" ? "Codex Frameless Bidi WebRTC (Chromium, Opus), SDP relayed by isolated z0live broker which owns the sideband + delegation" : "OpenAI Realtime WebRTC (Chromium, Opus), ephemeral client secret minted by isolated z0live broker", wire_types: out.wire_types, webrtc_stats: out.stats, result: out.result, output_windows: out.levels.length });
}
meta.loadavg_end = fs.readFileSync("/proc/loadavg", "utf8").trim();
fs.writeFileSync(path.join(runDir, "meta.json"), JSON.stringify(meta, null, 2));
console.log(JSON.stringify({ arm: meta.arm, scenario: scenario.id, connect_ms: meta.connect_ms ?? null, error: meta.error ?? null, windows: meta.output_windows ?? 0 }));

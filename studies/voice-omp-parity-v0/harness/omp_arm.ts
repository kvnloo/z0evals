// OMP /live arm driver (Bun). Runs the INSTALLED OMP LiveSessionController + CodexLiveTransport
// unchanged; only the microphone (AudioCapture) is replaced by a scripted PCM source, and the
// native peer / sideband are wrapped (not modified) to timestamp output-audio RMS windows and events.
//
// bun harness/omp_arm.ts --scenario <id> --run-dir <dir> --assets <dir> --cwd <repo> [--voice sol]
// Speaker output: run with ALSA_CONFIG_PATH pointing at a null-PCM config so nothing is audible.
import fs from "node:fs";
import path from "node:path";
import { parseArgs } from "node:util";
import { createRunner, WINDOW_MS } from "./runner.mjs";

const { values: args } = parseArgs({
	options: {
		scenario: { type: "string" },
		"run-dir": { type: "string" },
		assets: { type: "string" },
		cwd: { type: "string" },
		voice: { type: "string" },
		scenarios: { type: "string", default: path.join(import.meta.dir, "../scenarios.json") },
		pkg: { type: "string", default: path.join(process.env.HOME ?? "", ".bun/install/global/node_modules/@oh-my-pi/pi-coding-agent") },
	},
});
const runDir = args["run-dir"]!;
fs.mkdirSync(runDir, { recursive: true });
const spec = JSON.parse(fs.readFileSync(args.scenarios!, "utf8"));
const scenario = spec.scenarios.find((s: { id: string }) => s.id === args.scenario);
if (!scenario) throw new Error(`unknown scenario ${args.scenario}`);
const assets = JSON.parse(fs.readFileSync(path.join(args.assets!, "assets.json"), "utf8"));

const T0 = performance.now();
const now = () => performance.now() - T0;
const eventsOut = fs.openSync(path.join(runDir, "events.jsonl"), "w");
const levelsOut = fs.openSync(path.join(runDir, "levels.jsonl"), "w");
const log = (rec: Record<string, unknown>) => fs.writeSync(eventsOut, `${JSON.stringify({ t: +now().toFixed(1), ...rec })}\n`);

// ---------- native/module interception (no OMP source changes) ----------
const pkgDir = args.pkg!;
const nativesPath = Bun.resolveSync("@oh-my-pi/pi-natives", pkgDir);
const real = await import(nativesPath);
let micSink: ((error: Error | null, samples: Float32Array) => void) | undefined;
class ScriptedAudioCapture {
	constructor(rate: number, onAudio: (error: Error | null, samples: Float32Array) => void) {
		if (rate !== 16000) throw new Error(`unexpected capture rate ${rate}`);
		micSink = onAudio;
		log({ kind: "harness", msg: "scripted_capture_open", rate });
	}
	stop() {
		micSink = undefined;
	}
}
let runner: ReturnType<typeof createRunner>;
let outputWindows = 0;
function WrappedPeer(onEvent: (e: Error | null, p: string) => void, onLevel: (e: Error | null, l: number) => void, onFailure: (e: Error | null, m: string) => void) {
	return new real.LiveWebRtcPeer(
		(error: Error | null, payload: string) => {
			logWire("datachannel", payload);
			onEvent(error, payload);
		},
		(error: Error | null, level: number) => {
			if (!error) {
				const t = now();
				outputWindows++;
				fs.writeSync(levelsOut, `${t.toFixed(1)} ${level.toFixed(5)}\n`);
				runner?.level(level, t);
			}
			onLevel(error, level);
		},
		onFailure,
	);
}
Bun.plugin({
	name: "voice-eval-scripted-mic",
	setup(build) {
		build.module("@oh-my-pi/pi-natives", () => ({
			exports: { ...real, AudioCapture: ScriptedAudioCapture, LiveWebRtcPeer: WrappedPeer },
			loader: "object",
		}));
	},
});

const audioDeltaOut = fs.openSync(path.join(runDir, "sideband-audio.b64.jsonl"), "w");
const wireTypes: Record<string, number> = {};
function logWire(channel: string, payload: unknown) {
	if (typeof payload !== "string") return;
	let ev: Record<string, any>;
	try {
		ev = JSON.parse(payload);
	} catch {
		return;
	}
	const type = String(ev.type);
	wireTypes[type] = (wireTypes[type] ?? 0) + 1;
	if (type === "session.output_audio.delta" || type === "output_audio.delta") {
		if (channel === "sideband") fs.writeSync(audioDeltaOut, `${JSON.stringify({ t: +now().toFixed(1), start_ms: ev.start_ms, end_ms: ev.end_ms, delta: ev.delta ?? ev.audio })}\n`);
		return;
	}
	if (type === "session.input_audio.append") return;
	const keep: Record<string, unknown> = { kind: "wire", channel, type };
	if (ev.item?.text) keep.text = ev.item.text;
	if (ev.turn) keep.turn = { role: ev.turn.role, transcript: ev.turn.transcript };
	if (type === "delegation.created") keep.delegation = { id: ev.item?.id, text: (ev.item?.content ?? []).map((c: any) => c.text).join("\n") };
	if (type === "error") keep.error = ev.error ?? ev.message;
	if (!["output_transcript.added", "input_transcript.added", "turn.done", "delegation.created", "error"].includes(type)) keep.keys = Object.keys(ev).slice(0, 12);
	log(keep);
}
const NativeWS = globalThis.WebSocket;
class LoggedWebSocket extends NativeWS {
	constructor(url: string | URL, options?: any) {
		super(url, options);
		this.addEventListener("message", (event: MessageEvent) => logWire("sideband", event.data));
		log({ kind: "harness", msg: "sideband_open_attempt", host: new URL(String(url)).host });
	}
}
(globalThis as any).WebSocket = LoggedWebSocket;

// ---------- OMP session + live controller (installed package) ----------
const { createAgentSession } = await import(path.join(pkgDir, "src/sdk.ts"));
const { SessionManager } = await import(path.join(pkgDir, "src/session/session-manager.ts"));
const { LiveSessionController } = await import(path.join(pkgDir, "src/live/controller.ts"));
const { LIVE_MODEL } = await import(path.join(pkgDir, "src/live/protocol.ts"));
const { DEFAULT_LIVE_VOICE } = await import(path.join(pkgDir, "src/live/voices.ts"));
const { extractVisibleAssistantText } = await import(path.join(pkgDir, "src/modes/rpc/rpc-live.ts"));

const cwd = args.cwd ?? process.cwd();
const created = await createAgentSession({ cwd, sessionManager: SessionManager.inMemory(cwd), disableExtensionDiscovery: true, hasUI: false });
const session = created.session;
const voice = args.voice || DEFAULT_LIVE_VOICE;
let terminalAgentEnds = 0;
session.subscribe((event: any) => {
	if (event.type === "agent_start") log({ kind: "agent", type: "agent_start" });
	else if (event.type === "agent_end") {
		if (event.isTerminal !== false) terminalAgentEnds++;
		log({ kind: "agent", type: "agent_end", terminal: event.isTerminal !== false });
	} else if (event.type === "tool_execution_start") log({ kind: "agent", type: "tool_start", name: event.toolName });
	else if (event.type === "message_end" && event.message?.role === "assistant")
		log({ kind: "agent", type: "assistant_message", stop: event.message.stopReason, text: extractVisibleAssistantText(event.message).slice(0, 4000) });
});

let terminalError: string | undefined;
const controller = new LiveSessionController({
	session,
	voice,
	extractAssistantText: extractVisibleAssistantText,
	callbacks: {
		onPhase: (phase: string) => {
			log({ kind: "phase", phase });
		},
		onLevels: () => {},
		onTranscript: (tr: any) => tr?.final && log({ kind: "transcript", role: tr.role, turn: tr.turn, text: tr.text }),
		onTerminal: (error?: Error) => {
			terminalError = error?.message;
			log({ kind: "terminal", error: error?.message ?? null });
		},
	},
});

// ---------- scripted microphone pump (20 ms frames @16 kHz) ----------
const RATE = 16000;
const FRAME = 320;
const clips: Record<string, Float32Array> = {};
const clipFor = (id: string) => {
	if (!clips[id]) {
		const file = path.join(args.assets!, assets.clips[id].files[String(RATE)]);
		const buf = fs.readFileSync(file);
		clips[id] = new Float32Array(buf.buffer, buf.byteOffset, buf.byteLength / 4);
	}
	return clips[id];
};
type Active = { pcm: Float32Array; pos: number; mark: string; resolve: (v: { start: number; end: number }) => void; start?: number };
const active: Active[] = [];
let seed = 20261020;
const noiseFloor = () => {
	seed = (seed * 1664525 + 1013904223) >>> 0;
	return ((seed / 4294967296) * 2 - 1) * 1e-4;
};
let pumping = true;
const pump = (async () => {
	let next = performance.now();
	while (pumping) {
		const frame = new Float32Array(FRAME);
		for (let i = 0; i < FRAME; i++) frame[i] = noiseFloor();
		for (const a of [...active]) {
			if (a.start === undefined) {
				a.start = now();
				log({ kind: "mark", mark: a.mark, phase: "start" });
			}
			const n = Math.min(FRAME, a.pcm.length - a.pos);
			for (let i = 0; i < n; i++) frame[i] += a.pcm[a.pos + i];
			a.pos += n;
			if (a.pos >= a.pcm.length) {
				active.splice(active.indexOf(a), 1);
				const end = now() + (n / RATE) * 1000;
				log({ kind: "mark", mark: a.mark, phase: "end", t_end: +end.toFixed(1) });
				a.resolve({ start: a.start, end });
			}
		}
		micSink?.(null, frame);
		next += (FRAME / RATE) * 1000;
		const wait = next - performance.now();
		if (wait > 0) await Bun.sleep(wait);
	}
})();

const play = (id: string, mark: string) => new Promise<{ start: number; end: number }>(resolve => active.push({ pcm: clipFor(id), pos: 0, mark, resolve }));
runner = createRunner({
	now,
	play,
	playAsync: (id: string, mark: string) => void play(id, mark),
	workPending: () => delegationsCreated() > terminalAgentEnds,
	log,
});
const delegationsCreated = () => (wireTypes["delegation.created"] ?? 0);

const meta: Record<string, unknown> = {
	arm: "omp-live",
	scenario: scenario.id,
	model: LIVE_MODEL,
	voice,
	transport: "Codex quicksilver WebRTC (native webrtc-rs peer, Opus 16 kHz in / 48 kHz out) + api.openai.com sideband WebSocket",
	delegation_model: `${session.model?.provider}/${session.model?.id}`,
	omp_version: JSON.parse(fs.readFileSync(path.join(pkgDir, "package.json"), "utf8")).version,
	level_window_ms: WINDOW_MS,
	level_point: "decoded remote Opus before speaker playback (webrtc-rs, no jitter buffer)",
	loadavg_start: fs.readFileSync("/proc/loadavg", "utf8").trim(),
};
let result: unknown;
try {
	const tStart = now();
	await controller.start();
	meta.connect_ms = +(now() - tStart).toFixed(1);
	log({ kind: "harness", msg: "connected" });
	result = await runner.run(scenario);
} catch (error) {
	meta.error = String((error as Error)?.message ?? error);
} finally {
	pumping = false;
	await pump;
	try {
		await controller.stop();
	} catch {}
	try {
		await session.abort?.();
	} catch {}
	meta.terminal_error = terminalError ?? null;
	meta.wire_types = wireTypes;
	meta.output_windows = outputWindows;
	meta.delegations = delegationsCreated();
	meta.loadavg_end = fs.readFileSync("/proc/loadavg", "utf8").trim();
	meta.result = result ?? null;
	fs.writeFileSync(path.join(runDir, "meta.json"), JSON.stringify(meta, null, 2));
	fs.closeSync(eventsOut);
	fs.closeSync(levelsOut);
	fs.closeSync(audioDeltaOut);
	console.log(JSON.stringify({ arm: "omp-live", scenario: scenario.id, connect_ms: meta.connect_ms, error: meta.error ?? null, terminal_error: meta.terminal_error, windows: outputWindows }));
	process.exit(0);
}

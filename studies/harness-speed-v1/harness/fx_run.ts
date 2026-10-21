#!/usr/bin/env bun
/**
 * fx arm: the libfx engine (the Zig engine behind the fx CLI) on the Codex provider, with four
 * host tools that mirror pi's built-ins (read, bash, edit, write). libfx's native backend does not
 * turn on fx's own shell/file tools, so these are the bench's, rooted at --cwd.
 *
 * Cold:  bun fx_run.ts --cwd DIR --model gpt-6.1-sol --effort low --prompt "..."   (one turn, exit)
 * Warm:  bun fx_run.ts --serve --model ...  then JSONL on stdin: {"id","prompt","cwd"} per request;
 *        each request gets a fresh engine (fresh conversation) in the same warm process.
 * stdout: JSONL {type, t} with t = ms since process start (performance.now()).
 * Credentials: ~/.codex/auth.json access token only; the refresh token is never given to libfx.
 */
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, isAbsolute, join, relative, resolve } from "node:path";
import { createInterface } from "node:readline";
import { createFxEngine } from "libfx";

const argv = process.argv.slice(2);
const flag = (n: string, d?: string) => { const i = argv.indexOf(`--${n}`); return i >= 0 ? argv[i + 1] : d; };
const model = flag("model", "gpt-6.1-sol") as string;
const effort = flag("effort", "low") as "low";
const emit = (o: Record<string, unknown>) => process.stdout.write(`${JSON.stringify({ t: performance.now(), ...o })}\n`);

const INSTRUCTIONS = [
  "You are a coding agent working in the current directory.",
  "Use the tools to read files, edit files, and run shell commands (for example the tests).",
  "Make the smallest correct change, verify it, then reply briefly.",
].join(" ");

function codexCredentials() {
  const auth = JSON.parse(readFileSync(join(homedir(), ".codex", "auth.json"), "utf8")) as { tokens?: { access_token?: string; account_id?: string } };
  const token = auth.tokens?.access_token;
  if (!token || !auth.tokens?.account_id) throw new Error("codex sign-in not found");
  const claims = JSON.parse(Buffer.from(token.split(".")[1] ?? "", "base64url").toString()) as { exp?: number };
  return { accessToken: token, accountId: auth.tokens.account_id, expiresAt: (claims.exp ?? 0) * 1000 };
}

function tools(cwd: string) {
  const inside = (p: string) => {
    const full = isAbsolute(p) ? p : resolve(cwd, p);
    if (relative(cwd, full).startsWith("..")) throw new Error(`path outside workspace: ${p}`);
    return full;
  };
  return [
    { name: "read", description: "Read a text file. Optional 1-based offset and limit in lines.", idempotent: true,
      inputSchema: { type: "object", properties: { path: { type: "string" }, offset: { type: "number" }, limit: { type: "number" } }, required: ["path"] },
      async execute({ path, offset, limit }: { path: string; offset?: number; limit?: number }) {
        const lines = readFileSync(inside(path), "utf8").split("\n");
        const start = Math.max(0, (offset ?? 1) - 1);
        return lines.slice(start, limit ? start + limit : undefined).join("\n");
      } },
    { name: "write", description: "Create or overwrite a file with the given content.", idempotent: false,
      inputSchema: { type: "object", properties: { path: { type: "string" }, content: { type: "string" } }, required: ["path", "content"] },
      async execute({ path, content }: { path: string; content: string }) {
        const full = inside(path); mkdirSync(dirname(full), { recursive: true }); writeFileSync(full, content);
        return `wrote ${content.length} bytes to ${path}`;
      } },
    { name: "edit", description: "Replace exactly one occurrence of oldText with newText in a file.", idempotent: false,
      inputSchema: { type: "object", properties: { path: { type: "string" }, oldText: { type: "string" }, newText: { type: "string" } }, required: ["path", "oldText", "newText"] },
      async execute({ path, oldText, newText }: { path: string; oldText: string; newText: string }) {
        const full = inside(path); const text = readFileSync(full, "utf8");
        const n = text.split(oldText).length - 1;
        if (n !== 1) throw new Error(`oldText must match exactly once (matched ${n})`);
        writeFileSync(full, text.replace(oldText, newText)); return `edited ${path}`;
      } },
    { name: "bash", description: "Run a bash command in the workspace and return exit code, stdout and stderr.", idempotent: false,
      inputSchema: { type: "object", properties: { command: { type: "string" }, timeout: { type: "number", description: "seconds" } }, required: ["command"] },
      async execute({ command, timeout }: { command: string; timeout?: number }) {
        const r = spawnSync("bash", ["-c", command], { cwd, encoding: "utf8", timeout: (timeout ?? 120) * 1000, maxBuffer: 4 << 20 });
        return `exit ${r.status}\n${(r.stdout ?? "").slice(-20000)}${r.stderr ? `\n[stderr]\n${r.stderr.slice(-8000)}` : ""}`;
      } },
  ];
}

async function runOne(prompt: string, cwd: string, id?: string) {
  if (!existsSync(cwd)) throw new Error(`cwd missing: ${cwd}`);
  const t0 = performance.now();
  emit({ type: "request_start", id });
  const engine = await createFxEngine({
    provider: "codex", model: { id: model, effort }, credentials: () => codexCredentials(),
    instructions: INSTRUCTIONS, tools: tools(cwd) as never,
  } as never);
  let first = true, toolCalls = 0, text = "";
  try {
    const turn = (engine as { prompt(p: string): AsyncIterable<{ type: string; delta?: string; name?: string; isError?: boolean }> & { result: Promise<{ stopReason: string; usage: Record<string, number> }> } }).prompt(prompt);
    for await (const ev of turn) {
      if (ev.type === "text_delta") { if (first) { emit({ type: "first_text", id }); first = false; } text += ev.delta ?? ""; }
      else if (ev.type === "tool_start") { toolCalls++; emit({ type: "tool_start", id, name: ev.name }); }
      else if (ev.type === "tool_end") emit({ type: "tool_end", id, name: ev.name, isError: ev.isError });
    }
    const result = await turn.result;
    emit({ type: "result", id, stopReason: result.stopReason, usage: result.usage, toolCalls, text, ms: performance.now() - t0 });
  } catch (e) {
    emit({ type: "error", id, message: String((e as Error)?.message ?? e).slice(0, 500) });
  } finally {
    await (engine as { close(): Promise<void> }).close();
  }
}

if (argv.includes("--serve")) {
  emit({ type: "ready" });
  const rl = createInterface({ input: process.stdin });
  for await (const line of rl) {
    if (!line.trim()) continue;
    const req = JSON.parse(line) as { id: string; prompt: string; cwd: string };
    await runOne(req.prompt, req.cwd, req.id);
  }
} else {
  const promptFile = flag("prompt-file");
  const prompt = promptFile ? readFileSync(promptFile, "utf8") : (flag("prompt") as string);
  await runOne(prompt, resolve(flag("cwd", process.cwd()) as string));
  process.exit(0);
}

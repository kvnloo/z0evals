// Live generation sweep: every case x model through `hermes chat`, judged by the oracle.
// Usage (inside a scratch install with @openuidev 1.0.2, zod and tsx): node --import tsx generate.ts <outDir> <model> [caseId...]
import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import { cases } from "./cases.mjs";
import { judge } from "./oracle";

const [outDir, model, ...only] = process.argv.slice(2);
const catalog = readFileSync(join(outDir!, "..", "catalog-prompt.txt"), "utf8");
const hash = (s: string) => createHash("sha256").update(s).digest("hex").slice(0, 16);
mkdirSync(outDir!, { recursive: true });

function run(prompt: string) {
  const args = ["chat", ...(model === "default" ? [] : ["--model", model!]), "--ignore-rules", "--format", "stream-json", "--query-file", "-"];
  return new Promise<{ text: string; ms: number; firstTextMs: number | null; result: any; code: number | null }>((resolve) => {
    const started = performance.now();
    const child = spawn("hermes", args, { stdio: ["pipe", "pipe", "pipe"] });
    let buffer = "", text = "", result: any = null, firstTextMs: number | null = null;
    const timer = setTimeout(() => child.kill("SIGTERM"), 240_000);
    child.stdout.on("data", (chunk) => {
      buffer += chunk.toString();
      let end;
      while ((end = buffer.indexOf("\n")) !== -1) {
        const line = buffer.slice(0, end);
        buffer = buffer.slice(end + 1);
        if (!line.startsWith("{")) continue;
        try {
          const e = JSON.parse(line);
          if (e.type === "text") { firstTextMs ??= performance.now() - started; text += e.text ?? ""; }
          if (e.type === "result") result = e;
        } catch {}
      }
    });
    child.stderr.on("data", () => {});
    child.on("close", (code) => { clearTimeout(timer); resolve({ text: result?.text ?? text, ms: performance.now() - started, firstTextMs, result, code }); });
    child.stdin.end(prompt);
  });
}

const rows = [];
for (const c of cases.filter((c: any) => only.length === 0 || only.includes(c.id))) {
  const prompt = `${catalog}\n\n${c.message}`;
  const r = await run(prompt);
  const verdict = judge(r.text, c.expect);
  const row = {
    id: c.id, model, ready: verdict.ready, faithful: verdict.faithful, problems: verdict.problems, panels: verdict.panels,
    totalMs: Math.round(r.ms), firstTextMs: r.firstTextMs && Math.round(r.firstTextMs), exit: r.code,
    sessionId: r.result?.session_id, tokens: r.result?.tokens, promptHash: hash(prompt), outputChars: r.text.length,
  };
  rows.push(row);
  writeFileSync(join(outDir!, `${c.id}.${model}.json`), JSON.stringify({ ...row, prompt, text: r.text, result: r.result }, null, 1));
  console.log(`${verdict.faithful ? "PASS" : verdict.ready ? "DATA" : "FAIL"} ${c.id} ${model} ${(r.ms / 1000).toFixed(1)}s ${verdict.panels.join("+")} ${verdict.problems.join(" | ")}`);
}
writeFileSync(join(outDir!, `summary.${model}.json`), JSON.stringify(rows, null, 1));

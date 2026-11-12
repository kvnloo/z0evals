// Format A/B: same case data, same model, same harness; only the answer format changes.
//   openui: catalog prompt + request, answer is one ```openui-v2 block + 2-sentence summary
//   html:   request, answer is one self-contained ```html page + 2-sentence summary
// Order alternates per rep so warm-up and cache effects hit both formats.
// Usage (inside a scratch install with @openuidev 1.0.2, zod and tsx): node --import tsx ab.ts <outDir> <model> <reps> [caseId...]
import { spawn } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import { cases } from "./cases.mjs";
import { judge } from "./oracle";

const [outDir, model, repsArg, ...only] = process.argv.slice(2);
const reps = Number(repsArg);
const catalog = readFileSync(join(outDir!, "..", "catalog-prompt.txt"), "utf8");
mkdirSync(outDir!, { recursive: true });

const suffix = {
  openui: "Reply with one openui-v2 fenced block, then a two-sentence Markdown summary. Do not call tools.",
  html: "Reply with one self-contained HTML page (inline CSS and JS, no external assets) in an html fenced block that renders this interactively, then a two-sentence Markdown summary. Do not call tools.",
} as const;
type Format = keyof typeof suffix;
const prompt = (format: Format, message: string) => (format === "openui" ? `${catalog}\n\n${message}\n\n${suffix.openui}` : `${message}\n\n${suffix.html}`);

function run(text: string) {
  const args = ["chat", ...(model === "default" ? [] : ["--model", model!]), "--ignore-rules", "--format", "stream-json", "--query-file", "-"];
  return new Promise<{ text: string; ms: number; firstTextMs: number | null; result: any; code: number | null }>((resolve) => {
    const started = performance.now();
    const child = spawn("hermes", args, { stdio: ["pipe", "pipe", "pipe"] });
    let buffer = "", out = "", result: any = null, firstTextMs: number | null = null;
    const timer = setTimeout(() => child.kill("SIGTERM"), 300_000);
    child.stdout.on("data", (chunk) => {
      buffer += chunk.toString();
      let end;
      while ((end = buffer.indexOf("\n")) !== -1) {
        const line = buffer.slice(0, end);
        buffer = buffer.slice(end + 1);
        if (!line.startsWith("{")) continue;
        try {
          const e = JSON.parse(line);
          if (e.type === "text") { firstTextMs ??= performance.now() - started; out += e.text ?? ""; }
          if (e.type === "result") result = e;
        } catch {}
      }
    });
    child.stderr.on("data", () => {});
    child.on("close", (code) => { clearTimeout(timer); resolve({ text: result?.text ?? out, ms: performance.now() - started, firstTextMs, result, code }); });
    child.stdin.end(text);
  });
}

// HTML has no schema, so its check is weak: a fence exists and every expected number appears in it.
function numbers(value: unknown): number[] {
  if (typeof value === "number") return [value];
  if (Array.isArray(value)) return value.flatMap(numbers);
  if (value && typeof value === "object") return Object.values(value).flatMap(numbers);
  return [];
}
function judgeHtml(text: string, expect: Record<string, unknown>) {
  const page = /```html[ \t]*\r?\n([\s\S]*?)\r?\n```/i.exec(text)?.[1] ?? null;
  if (!page) return { ready: false, faithful: false, chars: 0, missing: ["no html fence"] };
  const missing = [...new Set(numbers(expect))].filter((n) => !new RegExp(`(^|[^0-9.])${String(n).replace(".", "\\.")}([^0-9]|$)`).test(page));
  return { ready: true, faithful: missing.length === 0, chars: page.length, missing: missing.map(String) };
}

const rows = [];
const chosen = cases.filter((c: any) => only.length === 0 || only.includes(c.id));
for (let rep = 1; rep <= reps; rep += 1) {
  for (const [index, c] of chosen.entries()) {
    const order: Format[] = (rep + index) % 2 === 0 ? ["openui", "html"] : ["html", "openui"];
    for (const format of order) {
      const r = await run(prompt(format, c.message));
      const v = format === "openui" ? judge(r.text, c.expect) : judgeHtml(r.text, c.expect);
      const row = {
        id: c.id, format, rep, model, ready: v.ready, faithful: v.faithful,
        problems: "problems" in v ? v.problems : v.missing,
        artifactChars: format === "openui" ? ((v as any).code?.length ?? 0) : (v as any).chars,
        totalMs: Math.round(r.ms), firstTextMs: r.firstTextMs && Math.round(r.firstTextMs), exit: r.code,
        tokens: r.result?.tokens, sessionId: r.result?.session_id,
      };
      rows.push(row);
      writeFileSync(join(outDir!, `${c.id}.${format}.r${rep}.json`), JSON.stringify({ ...row, text: r.text }, null, 1));
      writeFileSync(join(outDir!, "rows.json"), JSON.stringify(rows, null, 1));
      console.log(`${v.faithful ? "PASS" : v.ready ? "DATA" : "FAIL"} ${c.id} ${format} r${rep} ${(r.ms / 1000).toFixed(1)}s out=${r.result?.tokens?.output ?? "?"} chars=${row.artifactChars}`);
    }
  }
}

// Score the live in-T3 thread with the same oracle as generate.ts.
// Usage (inside a scratch install with @openuidev 1.0.2, zod and tsx): node --import tsx judge-t3.ts <t3-live-thread.jsonl> <out.json>
import { readFileSync, writeFileSync } from "node:fs";

import { cases } from "./cases.mjs";
import { judge } from "./oracle";

// Run order in the live thread (one T3 thread, Hermes over ACP, gpt-6.1-sol).
const order = ["repo-treemap", "token-week", "activity-heatmap", "disk-usage", "ci-durations", "review-load-dense", "deep-paths-dashboard", "unsupported-pie", "sparse-zeros"];
const runs = readFileSync(process.argv[2]!, "utf8").trim().split("\n").map((line) => JSON.parse(line) as { run: number; text: string });
const rows = order.map((id, index) => {
  const c = cases.find((entry) => entry.id === id)!;
  const verdict = judge(runs[index]!.text, c.expect);
  const { code: _code, ...rest } = verdict;
  return { run: index + 1, id, status: !verdict.ready ? "INVALID" : verdict.faithful ? "PASS" : "DATA", ...rest };
});
for (const row of rows) console.log(`${row.status.padEnd(5)} run ${row.run} ${row.id} ${row.problems?.join("; ") ?? ""}`);
writeFileSync(process.argv[3]!, JSON.stringify(rows, null, 1));

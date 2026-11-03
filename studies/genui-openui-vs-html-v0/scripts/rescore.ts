// Re-score saved generations with the current oracle. Usage: node --import tsx rescore.ts <genDir>
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { cases } from "./cases.mjs";
import { judge } from "./oracle";

const dir = process.argv[2]!;
const tally: Record<string, { pass: number; total: number }> = {};
for (const file of readdirSync(dir).filter((name) => name.endsWith(".json") && !name.startsWith("summary."))) {
  const row = JSON.parse(readFileSync(join(dir, file), "utf8"));
  const c = cases.find((entry) => entry.id === row.id)!;
  const v = judge(row.text, c.expect);
  const t = (tally[row.model] ??= { pass: 0, total: 0 });
  t.total += 1;
  if (v.ready && v.faithful) t.pass += 1;
  else console.log(row.model, row.id, v.problems.join("; "));
}
console.log(JSON.stringify(tally));

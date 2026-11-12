// Oracle: validity via the shipped web module, data fidelity via a positional-name parser.
// Run inside the smoke scratch install (needs @openuidev 1.0.2, zod, tsx).
import { createParser } from "@openuidev/lang-core";
import { createLibrary, defineComponent } from "@openuidev/react-lang";
import { z } from "zod/v4";

import { inspectOpenUiChart } from "./OpenUiCharts";

const any = z.any();
const component = (name: string, keys: string[]) => defineComponent({ name, description: name, props: z.object(Object.fromEntries(keys.map((key) => [key, any]))), component: () => null });
const oracleLibrary = createLibrary({
  components: [
    component("Board", ["title", "summary", "panels"]),
    component("Treemap", ["title", "sizeLabel", "colorLabel", "rows"]),
    component("BarChart", ["title", "unit", "bars"]),
    component("StackedArea", ["title", "unit", "categories", "series"]),
    component("Heatmap", ["title", "unit", "rows", "columns", "counts"]),
  ],
  root: "Board",
});
const parser = createParser(oracleLibrary.toJSONSchema(), "Board");

export function extractFence(text: string) {
  const match = /```openui-v2[ \t]*\r?\n([\s\S]*?)\r?\n```/.exec(text);
  return match ? match[1]! : null;
}

type Panel = { typeName: string; props: Record<string, any> };
const near = (a: number, b: number) => Math.abs(a - b) < 1e-9;

function checkPanel(panel: Panel, spec: Record<string, any>): string[] {
  const p = panel.props;
  const problems: string[] = [];
  if (panel.typeName === "Treemap") {
    const want = new Map(spec.rows.map((r: any) => [r.path, r]));
    const got = new Map((p.rows ?? []).map((r: any) => [r.path, r]));
    if (got.size !== want.size) problems.push(`treemap rows ${got.size} != ${want.size}`);
    for (const [path, r] of want as Map<string, any>) {
      const g: any = got.get(path);
      if (!g) problems.push(`missing ${path}`);
      else {
        if (!near(g.size, r.size)) problems.push(`${path} size ${g.size} != ${r.size}`);
        if (r.color !== undefined && !near(g.color, r.color)) problems.push(`${path} color ${g.color} != ${r.color}`);
      }
    }
  } else if (panel.typeName === "BarChart") {
    const bars: any[] = p.bars ?? [];
    if (bars.length !== spec.bars.length) problems.push(`bars ${bars.length} != ${spec.bars.length}`);
    const matches = (label: string, want: string) => (spec.labelMatch === "suffix" ? label === want || label.endsWith("/" + want) || label.endsWith(want) : label === want);
    spec.bars.forEach(([label, value]: [string, number], index: number) => {
      const found = spec.ordered ? bars[index] : bars.find((bar) => matches(String(bar.label), label));
      if (!found || !matches(String(found.label), label)) problems.push(`bar ${label} ${spec.ordered ? `not at ${index}` : "missing"}`);
      else if (!near(found.value, value)) problems.push(`bar ${label} ${found.value} != ${value}`);
    });
  } else if (panel.typeName === "StackedArea") {
    const label = (c: string) => (spec.categoryPrefix ? String(c).slice(0, spec.categoryPrefix) : String(c));
    if (JSON.stringify((p.categories ?? []).map(label)) !== JSON.stringify(spec.categories.map(label))) problems.push(`categories ${JSON.stringify(p.categories)}`);
    const series = new Map((p.series ?? []).map((s: any) => [s.name, s.values]));
    if (series.size !== Object.keys(spec.series).length) problems.push(`series ${series.size}`);
    for (const [name, values] of Object.entries(spec.series)) {
      if (JSON.stringify(series.get(name)) !== JSON.stringify(values)) problems.push(`series ${name} ${JSON.stringify(series.get(name))}`);
    }
  } else if (panel.typeName === "Heatmap") {
    if (JSON.stringify(p.rows) !== JSON.stringify(spec.rows)) problems.push(`rows ${JSON.stringify(p.rows)}`);
    if ((p.columns ?? []).length !== spec.columns) problems.push(`columns ${(p.columns ?? []).length}`);
    if (JSON.stringify(p.counts) !== JSON.stringify(spec.counts)) problems.push("counts differ");
  }
  return problems;
}

/** Valid per the shipped renderer, and every expected panel present with exact data. */
export function judge(text: string, expect: Record<string, Record<string, any>[]>) {
  const code = extractFence(text);
  if (!code) return { ready: false, faithful: false, problems: ["no openui-v2 fence"], panels: [] as string[] };
  const status = inspectOpenUiChart(code);
  const parsed = parser.parse(code);
  const panels: Panel[] = (parsed.root?.props as any)?.panels ?? [];
  const problems: string[] = status.kind === "ready" ? [] : [`${status.kind}: ${status.reason}`];
  for (const [typeName, specs] of Object.entries(expect)) {
    const candidates = panels.filter((panel) => panel.typeName === typeName);
    for (const spec of specs) {
      const results = candidates.map((panel) => checkPanel(panel, spec));
      if (!results.some((r) => r.length === 0)) problems.push(`${typeName}: ${(results[0] ?? ["missing panel"]).join("; ")}`);
    }
  }
  return { ready: status.kind === "ready", faithful: problems.length === 0, problems, panels: panels.map((panel) => panel.typeName), code };
}

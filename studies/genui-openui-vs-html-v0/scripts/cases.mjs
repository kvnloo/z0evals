// Ephemeral-UI generation cases for the OpenUI chart catalog (openui-v2).
// Each case: a realistic one-turn request with literal synthetic data, plus an exact oracle.
// Modeled on the tracked cohort (OMP #143 Code/Churn explorer, Hermes #432 RepoExplorer,
// Theo's Oct 6 T3 Code visualizations) and on everyday agent reports.

const rowsText = (rows) => JSON.stringify(rows);

const repo = [["src/auth/login.ts", 80, 12], ["src/auth/tokens.ts", 40, 6], ["src/ui/chat.ts", 120, 4], ["tests/auth.test.ts", 60, 7]];
const disk = [
  ["home/user/models/qwen3-32b.gguf", 19800], ["home/user/models/llama-8b.gguf", 4900], ["home/user/.cache/pnpm/store", 6100],
  ["home/user/.cache/huggingface/hub", 11200], ["home/user/projects/t3code/node_modules", 2400], ["home/user/projects/t3code/.git", 900],
  ["home/user/projects/quackles/tiles", 7300], ["var/lib/docker/overlay2", 15600], ["var/log/journal", 1200], ["opt/cuda", 5400],
];
const ci = [["web unit", 412], ["mobile typecheck", 288], ["server integration", 655], ["android assemble", 1310], ["lint", 74], ["desktop package", 540]];
const days7 = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const providers = { Claude: [120, 98, 143, 160, 151, 40, 22], Codex: [80, 102, 95, 77, 130, 12, 30], Cursor: [10, 14, 0, 22, 18, 0, 0] };
const hours = Array.from({ length: 24 }, (_, h) => `${String(h).padStart(2, "0")}`);
const reviews = days7.map((_, d) => hours.map((h) => (d >= 5 ? (Number(h) % 7 === 0 ? 1 : 0) : Math.max(0, 6 - Math.abs(Number(h) - 14) - (d % 3)))));
const deep = [["packages/client-runtime/src/openUiCharts.ts", 410, 9], ["packages/client-runtime/src/zip/boundedZip.ts", 220, 2], ["apps/mobile/src/native/OpenUiCharts.tsx", 330, 7],
  ["apps/mobile/src/native/OpenUiReport.tsx", 80, 3], ["apps/web/src/components/chat/OpenUiCharts.tsx", 300, 6], ["apps/web/src/components/ChatMarkdown.tsx", 1700, 14],
  ["docs/user/openui-reports.md", 43, 4]];

export const cases = [
  {
    id: "repo-treemap",
    message: `Render inline a repo treemap: area=LOC, color=commits, with the top-3 churn files as bars. Use only this synthetic fixture. Rows [path,LOC,commits]: ${rowsText(repo)}.`,
    expect: { Treemap: [{ rows: repo.map(([path, size, color]) => ({ path, size, color })) }], BarChart: [{ bars: [["login.ts", 12], ["auth.test.ts", 7], ["tokens.ts", 6]], labelMatch: "suffix" }] },
  },
  {
    id: "model-stacked-area",
    message: `Render inline a stacked-area chart of turns by model, with legend. Use only this synthetic fixture. Rows [day,Codex,Claude]: [["Mon",8,4],["Tue",4,10],["Wed",10,6]].`,
    expect: { StackedArea: [{ categories: ["Mon", "Tue", "Wed"], series: { Codex: [8, 4, 10], Claude: [4, 10, 6] } }] },
  },
  {
    id: "activity-heatmap",
    message: `Render inline an activity heatmap with labeled axes and a count legend. Use only this synthetic fixture. Days [Mon,Tue,Wed], UTC hours [0,6,12,18], counts [[0,2,7,1],[1,4,9,2],[0,3,5,1]].`,
    expect: { Heatmap: [{ rows: ["Mon", "Tue", "Wed"], columns: 4, counts: [[0, 2, 7, 1], [1, 4, 9, 2], [0, 3, 5, 1]] }] },
  },
  {
    id: "disk-usage",
    message: `My disk is filling up. Show where the space goes as a treemap sized by MB (no second metric, so color by MB too), plus the five largest entries as bars. Paths and sizes in MB: ${rowsText(disk)}.`,
    expect: { Treemap: [{ rows: disk.map(([path, size]) => ({ path, size })) }], BarChart: [{ bars: [["qwen3-32b.gguf", 19800], ["overlay2", 15600], ["hub", 11200], ["tiles", 7300], ["store", 6100]], labelMatch: "suffix" }] },
  },
  {
    id: "ci-durations",
    message: `Which CI jobs are slowest? Show job durations in seconds as bars, slowest first. Jobs [name,seconds]: ${rowsText(ci)}.`,
    expect: { BarChart: [{ bars: [...ci].sort((a, b) => b[1] - a[1]), ordered: true }] },
  },
  {
    id: "token-week",
    message: `Chart this week's turns per provider as a stacked area, one series per provider, Monday to Sunday. Data: ${JSON.stringify(providers)}.`,
    expect: { StackedArea: [{ categories: days7, categoryPrefix: 3, series: providers }] },
    note: "Day labels are not in the data; 'Mon' and 'Monday' are both faithful to 'Monday to Sunday'.",
  },
  {
    id: "review-load-dense",
    message: `Show PR review requests by weekday and hour (UTC) as a heatmap. Rows are ${JSON.stringify(days7)}, columns are hours 00-23, counts row by row: ${JSON.stringify(reviews)}.`,
    expect: { Heatmap: [{ rows: days7, columns: 24, counts: reviews }] },
  },
  {
    id: "deep-paths-dashboard",
    message: `Give me one board for the OpenUI change: a treemap of files (area=LOC, color=commits) and a bar chart of the three most-committed files. Rows [path,LOC,commits]: ${rowsText(deep)}.`,
    expect: { Treemap: [{ rows: deep.map(([path, size, color]) => ({ path, size, color })) }], BarChart: [{ bars: [["ChatMarkdown.tsx", 14], ["openUiCharts.ts", 9], ["OpenUiCharts.tsx", 7]], labelMatch: "suffix" }] },
  },
  {
    id: "unsupported-pie",
    message: `Make a pie chart of the share of this week's turns per provider: Claude 734, Codex 526, Cursor 64.`,
    expect: { BarChart: [{ bars: [["Claude", 734], ["Codex", 526], ["Cursor", 64]] }] },
    note: "No pie in the catalog; the honest answer is a bar chart of the raw values.",
  },
  {
    id: "sparse-zeros",
    message: `Show failed CI runs per day and workflow as a heatmap. Workflows (rows) [web, mobile, server], days (columns) [Mon..Fri], counts [[0,0,0,0,0],[0,3,0,0,1],[0,0,0,0,0]]. Most cells are zero; keep them.`,
    expect: { Heatmap: [{ rows: ["web", "mobile", "server"], columns: 5, counts: [[0, 0, 0, 0, 0], [0, 3, 0, 0, 1], [0, 0, 0, 0, 0]] }] },
  },
];

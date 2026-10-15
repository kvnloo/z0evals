import type { Metadata } from "next";
import StoryShell, { type StoryMeta, type StoryBanner } from "@/components/StoryShell";
import type { TocItem } from "@/components/Toc";
import MetricRow from "@/components/MetricRow";
import Callout from "@/components/Callout";
// Read the frozen artifacts, not a second transcription of the measurements.
import optchat from "@/data/optchat-long-horizon-v0.json";

const summary = optchat.summary;
const turns = optchat.turns;

export const metadata: Metadata = {
  title: "does optchat stay small after fifty tool calls? — z0evals",
  description: "an unscored, source-reported context-size trajectory. not a recall-quality result or a live-harness token-saving claim.",
};

const publication = "cb5acc5c9729cb5a6de389eea4ebd71a93f45566";
const evidence = `https://github.com/kvnloo/z0evals/blob/${publication}/studies/optchat-long-horizon-v0`;
const format = (value: number) => new Intl.NumberFormat("en-US").format(value);
const last = turns[turns.length - 1];
if (!last || turns.length !== summary.turns || last.raw_bytes !== summary.final_raw_bytes ||
    last.view_bytes !== summary.final_view_bytes) {
  throw new Error("OptChat publication: summary and frozen trajectory disagree");
}
const ratio = last.view_bytes / last.raw_bytes;
const meta: StoryMeta = {
  title: "does optchat stay small after fifty tool calls?",
  subtitle: "the log kept growing. the view was smaller. that is the result — not a memory victory lap.",
  author: "zer0 research",
  date: "october 5, 2026",
  status: "unscored",
  lede: "the new optmem / optchat work belongs here too. this follow-up measures the size of a derived view against an accumulated transcript, while keeping answer quality and actual model requests as separate questions.",
};
const banner: StoryBanner = {
  tag: "unscored · source-reported",
  text: "context bytes only. no held-out answer check. the measured implementation was uncommitted relative to its source pin, so this is not an exact-code reproduction or a production promotion.",
};
const toc: TocItem[] = [
  { id: "question", label: "what we actually measured", depth: 0 },
  { id: "trajectory", label: "the full trajectory", depth: 0 },
  { id: "limits", label: "small is not the same as correct", depth: 0 },
  { id: "next-proof", label: "what still needs a test", depth: 0 },
  { id: "explore", label: "source and provenance", depth: 0 },
];

function Trajectory() {
  const width = 640, height = 300, left = 72, right = 18, top = 18, bottom = 44;
  const max = Math.max(...turns.map((row) => row.raw_bytes), ...turns.map((row) => row.view_bytes));
  const x = (turn: number) => left + (turn - 1) / Math.max(1, summary.turns - 1) * (width - left - right);
  const y = (bytes: number) => height - bottom - bytes / max * (height - top - bottom);
  const points = (key: "raw_bytes" | "view_bytes") => turns.map((row) => `${x(row.turn)},${y(row[key])}`).join(" ");
  return (
    <figure aria-labelledby="trajectory-caption">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-labelledby="trajectory-title trajectory-description"
        style={{ width: "100%", height: "auto", display: "block" }}>
        <title id="trajectory-title">accumulated transcript and optchat view, in bytes</title>
        <desc id="trajectory-description">{summary.turns} recorded turns. the solid line is the raw transcript;
          the dashed line is the view. all measurements are available in the table below.</desc>
        <path d={`M${left},${top}V${height - bottom}H${width - right}`} fill="none" stroke="currentColor" opacity="0.35" />
        {[0, max / 2, max].map((value) => (
          <g key={value}>
            <line x1={left} x2={width - right} y1={y(value)} y2={y(value)} stroke="currentColor" opacity="0.12" />
            <text x={left - 8} y={y(value) + 4} textAnchor="end" fill="currentColor" fontSize="12">{format(Math.round(value / 1000))} kb</text>
          </g>
        ))}
        <polyline points={points("raw_bytes")} fill="none" stroke="currentColor" strokeWidth="2" />
        <polyline points={points("view_bytes")} fill="none" stroke="currentColor" strokeWidth="2" strokeDasharray="6 4" />
        {[1, summary.turns].map((turn) => <text key={turn} x={x(turn)} y={height - 20}
          textAnchor={turn === 1 ? "start" : "end"} fill="currentColor" fontSize="12">turn {turn}</text>)}
      </svg>
      <figcaption id="trajectory-caption">solid: accumulated transcript. dashed: optchat view.
        bytes, not tokens; one recorded trajectory, not a distribution or a quality score.</figcaption>
    </figure>
  );
}

const story = (
  <>
    <h2 id="question">what we actually measured</h2>
    <p>the source report extends a file-review protocol to {summary.turns} public python files.
      each step adds a user line, a file echo capped at {format(summary.echo_cap_chars)} characters,
      and a short reply. the comparison is the accumulated text versus a derived optchat view.</p>
    <p>the local compactor was <code>{summary.model}</code>, with a {format(summary.router_n_ctx)}-token
      context window. it saw a {format(summary.compactor_input_cap_chars)}-character excerpt,
      not the full tool echo. that difference matters when asking what information survived.</p>
    <Callout kind="warning" title="the comparison is not the host request">
      <p>the hook described by this study added the view beside the host transcript. it did not
        replace that transcript. view size is therefore not a measurement of the tokens the
        live omp session actually sent.</p>
    </Callout>
    <h2 id="trajectory">the full trajectory</h2>
    <MetricRow items={[
      { k: "raw transcript", v: `${format(last.raw_bytes)} b`, s: `at turn ${last.turn}` },
      { k: "optchat view", v: `${format(last.view_bytes)} b`, s: "same recorded turn" },
      { k: "view / raw", v: `${(ratio * 100).toFixed(2)}%`, s: "byte ratio, not token savings" },
      { k: "placeholders", v: format(summary.placeholders_at_end), s: "at the end of this run" },
    ]} />
    <Trajectory />
    <p>the view is smaller, but it also grows. this run does not demonstrate constant context.
      the source report says higher tree levels were not needed within its configured budget;
      the observed reduction came from per-message summaries.</p>
    <details>
      <summary>show all {summary.turns} recorded turns</summary>
      <div className="x-table-wrap">
        <table className="x-table">
          <caption>context-size trajectory; source-reported bytes</caption>
          <thead><tr><th scope="col">turn</th><th scope="col">raw bytes</th><th scope="col">view bytes</th><th scope="col">view / raw</th></tr></thead>
          <tbody>{turns.map((row) => <tr key={row.turn}>
            <th scope="row">{row.turn}</th><td>{format(row.raw_bytes)}</td><td>{format(row.view_bytes)}</td>
            <td>{(100 * row.view_bytes / row.raw_bytes).toFixed(2)}%</td>
          </tr>)}</tbody>
        </table>
      </div>
    </details>
    <h2 id="limits">small is not the same as correct</h2>
    <p>there was no held-out answer-quality verifier. a small view could omit exactly the detail
      a later question needs. zero remaining placeholders says the nodes were built, not that
      their summaries were faithful or sufficient.</p>
    <p>the source report records one failed compaction request and a fallback line. the manifest
      also says the optchat implementation was uncommitted relative to its recorded source pin.
      publishing that limitation is not the same as repairing the missing provenance.</p>
    <p>the older observationpack / sol-pi comparison is background, not another arm in this
      trajectory. the earlier <a href="../unified-memory-v0/">cross-harness memory study</a>
      remains separate and unscored. neither is promoted by making this article visible.</p>
    <h2 id="next-proof">what still needs a test</h2>
    <p>freeze the exact implementation, measure the actual model-input boundary, and ask delayed
      questions against held-out evidence. keep correctness, stale-context errors, latency,
      bytes, and tokens separate. newer fresh-turn and hermes adapters need their own exact-head
      evidence; this old run cannot certify them retroactively.</p>
  </>
);
const explore = (
  <>
    <h2>source and provenance</h2>
    <p>the publication artifacts are pinned to <code>{publication}</code>. that freezes what the
      report says; it does not supply the missing tested implementation revision.</p>
    <p><a href={`${evidence}/manifest.yaml`}>study manifest and limitations</a>{" · "}
      <a href={`${evidence}/summary.json`}>summary</a>{" · "}
      <a href={`${evidence}/turns.json`}>all recorded turns</a>{" · "}
      <a href={`https://github.com/kvnloo/z0evals/blob/${publication}/posts/optchat-long-horizon-v0.md`}>original write-up</a></p>
    <p>credit: Victor Taelin for the original <a href="https://gist.github.com/VictorTaelin/91837951a5ce5b38f341ec1ba1df6449">OptMem / OptChat reference</a>;
      zer0 research for this study and its recorded limitations. the publication repair reuses
      the existing shared story design rather than introducing another blog template.</p>
  </>
);
export default function Page() {
  return <StoryShell meta={meta} toc={toc} banner={banner} story={story} explore={explore} />;
}

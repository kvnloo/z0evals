import type { Metadata } from "next";
import StoryShell, { type StoryMeta, type StoryBanner } from "@/components/StoryShell";
import type { TocItem } from "@/components/Toc";
import MetricRow from "@/components/MetricRow";
import Callout from "@/components/Callout";
import { Citation, Evidence, ExpHead, SetupFigure, Teaser, Tldr } from "@/components/essay/Essay";
import TrajectoryChart, { KbBars } from "./TrajectoryChart";
import "./optchat.css";
// Read the frozen artifacts, not a second transcription of the measurements.
import optchat from "@/data/optchat-long-horizon-v0.json";

const summary = optchat.summary;
const turns = optchat.turns;
const manifest = optchat.manifest;

export const metadata: Metadata = {
  title: "does optchat stay small after fifty tool calls? — z0evals",
  description: "an unscored, source-reported context-size trajectory. not a recall-quality result or a live-harness token-saving claim.",
};

const publication = "cb5acc5c9729cb5a6de389eea4ebd71a93f45566";
const evidence = `https://github.com/kvnloo/z0evals/blob/${publication}/studies/optchat-long-horizon-v0`;
const format = (value: number) => new Intl.NumberFormat("en-US").format(value);
const first = turns[0];
const last = turns[turns.length - 1];
if (!first || !last || turns.length !== summary.turns || last.raw_bytes !== summary.final_raw_bytes ||
    last.view_bytes !== summary.final_view_bytes) {
  throw new Error("OptChat publication: summary and frozen trajectory disagree");
}
if (manifest.scoring !== "unscored" || manifest.claims.length !== 0) {
  throw new Error("OptChat publication: the manifest no longer says unscored with no claims");
}
const ratio = last.view_bytes / last.raw_bytes;
const firstRatio = first.view_bytes / first.raw_bytes;
const maxPlaceholders = Math.max(...turns.map((row) => row.placeholders));
const source = manifest.sources[0];
const meta: StoryMeta = {
  title: "does optchat stay small after fifty tool calls?",
  subtitle: "the log kept growing. the view was smaller. that is the result, not a memory victory lap.",
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
  { id: "cite", label: "cite this", depth: 0 },
  { id: "explore", label: "source and provenance", depth: 0 },
];

/** Teaser sparkline: both series on one shared byte scale, straight from turns. */
function Spark() {
  const w = 240, h = 150, pad = 10;
  const max = Math.max(...turns.map((row) => row.raw_bytes));
  const x = (k: number) => pad + (k / (turns.length - 1)) * (w - 2 * pad);
  const y = (v: number) => h - pad - (v / max) * (h - 2 * pad);
  const pts = (key: "raw_bytes" | "view_bytes") => turns.map((row, k) => `${x(k)},${y(row[key])}`).join(" ");
  return (
    <svg className="oc-spark" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" aria-hidden="true">
      <polyline points={pts("raw_bytes")} fill="none" stroke="currentColor" strokeWidth="2" vectorEffect="non-scaling-stroke" />
      <polyline points={pts("view_bytes")} fill="none" stroke="var(--color-sb-highlight)" strokeWidth="2.5"
        strokeDasharray="5 3" vectorEffect="non-scaling-stroke" />
    </svg>
  );
}

const teaser = (
  <Teaser
    label="the optchat run in three panels"
    panels={[
      {
        step: "1 · the run",
        task: <>{summary.turns} file reviews. each turn echoes a file, capped at {format(summary.echo_cap_chars)} characters.</>,
        visual: (
          <KbBars from={first.raw_bytes} to={last.raw_bytes} labels={[`turn ${first.turn}`, `turn ${last.turn}`]} />
        ),
        by: "accumulated transcript, bytes",
        big: `${format(Math.round(last.raw_bytes / 1000))} kb`,
        note: <>raw transcript at turn {last.turn}</>,
      },
      {
        step: "2 · the view",
        task: <>a local {summary.model} compactor builds the optchat view beside the log.</>,
        visual: <Spark />,
        by: "solid: raw. dashed: view. same scale.",
        big: `${(ratio * 100).toFixed(2)}%`,
        note: <>view / raw bytes at turn {last.turn}. the view still grows.</>,
      },
      {
        step: "3 · not scored",
        task: <>what the view kept was never checked against a question.</>,
        visual: (
          <ul className="oc-unmeasured">
            <li>answer quality on delayed questions</li>
            <li>tokens the live omp session sent</li>
            <li>the exact optchat code revision</li>
          </ul>
        ),
        by: `manifest scoring: ${manifest.scoring}`,
        big: "0",
        note: <>held-out answer checks. recall quality is unscored.</>,
      },
    ]}
  />
);

const setup = (
  <>
    <p><b>protocol.</b> <code>{summary.protocol}</code> on <code>{summary.parent_task}</code>, run
      for {summary.turns} turns. each turn adds a user line, a file echo capped at{" "}
      {format(summary.echo_cap_chars)} characters, and a short reply.</p>
    <p><b>compactor.</b> <code>{summary.model}</code> with n_ctx {format(summary.router_n_ctx)}. it saw a{" "}
      {format(summary.compactor_input_cap_chars)}-character excerpt of each echo.</p>
    <p><b>source pin.</b> <code>{source.repo}@{source.commit.slice(0, 7)}</code>: {source.role}.</p>
    <p><b>limitations, from the manifest.</b></p>
    <ul className="oc-setup-list">
      {manifest.limitations.map((line) => <li key={line}>{line}</li>)}
    </ul>
  </>
);

const story = (
  <>
    <Tldr>
      <p>after {summary.turns} tool-heavy turns the raw transcript was {format(last.raw_bytes)} bytes
        and the optchat view was {format(last.view_bytes)} bytes, {(ratio * 100).toFixed(2)}% of it.
        the view also grew, so this run does not show constant context.</p>
      <p>nothing here was scored. there was no held-out answer check, the bytes are not the tokens the
        live session sent, and the measured code was uncommitted relative to its source pin.</p>
    </Tldr>
    {teaser}
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
    <ExpHead n={1} id="exp-bytes">is the view smaller than the transcript?</ExpHead>
    <p><Evidence kind="source-reported">bytes from the source report, not rerun here</Evidence></p>
    <MetricRow items={[
      { k: "raw transcript", v: `${format(last.raw_bytes)} b`, s: `at turn ${last.turn}` },
      { k: "optchat view", v: `${format(last.view_bytes)} b`, s: "same recorded turn" },
      { k: "view / raw", v: `${(ratio * 100).toFixed(2)}%`, s: "byte ratio, not token savings" },
      { k: "placeholders", v: format(summary.placeholders_at_end), s: "at the end of this run" },
    ]} />
    <SetupFigure setup={setup} caption={<>solid: accumulated transcript. dashed: optchat view.
      bytes, not tokens; one recorded trajectory, not a distribution or a quality score.
      the view / raw scale shows the ratio at every turn: {(firstRatio * 100).toFixed(2)}% at
      turn {first.turn}, {(ratio * 100).toFixed(2)}% at turn {last.turn}.</>}>
      <TrajectoryChart turns={turns} />
    </SetupFigure>
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
    <ExpHead n={2} id="exp-nodes">did the local model build the nodes?</ExpHead>
    <p><Evidence kind="source-reported">node construction, not summary quality</Evidence></p>
    <p>the most placeholders recorded on any of the {summary.turns} turns was {maxPlaceholders}, and{" "}
      {summary.placeholders_at_end} remained at the end. no node was left as a placeholder on any recorded turn, so the free local
      model did run the compaction step. that is completion. it does not say what it wrote was faithful,
      which is the next section.</p>
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
    <h2 id="cite">cite this</h2>
    <Citation id="zer0-optchat-long-horizon-v0" title={meta.title} year={2026}
      url="https://kvnloo.github.io/z0evals/optchat-long-horizon-v0/"
      note={`unscored; source-reported context bytes; study ${manifest.id}`} />
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

import type { Metadata } from "next";
import data from "@/data/agentweb-study.json";
import StoryShell, { type StoryMeta, type StoryBanner } from "@/components/StoryShell";
import type { TocItem } from "@/components/Toc";
import MetricRow from "@/components/MetricRow";
import Callout from "@/components/Callout";

export const metadata: Metadata = {
  title: "agentweb + emma + z0 — z0evals",
  description:
    "downstream-first integration evidence for AgentWeb, Emma, z0intelligence and z0evals: "
    + "what is green, what is blocked, and what still cannot be promoted.",
};

const meta: StoryMeta = {
  title: "agentweb + emma + z0",
  subtitle: "first-class integration, still shadow-first.",
  author: "zer0 research",
  date: data.date,
  status: "experimental",
  lede:
    "the plumbing is real now. that does not mean the decisions are allowed to own behavior yet. "
    + "this page separates deterministic integration evidence from the model-backed evidence we still do not have.",
};

const banner: StoryBanner = {
  tag: "downstream only",
  text:
    "active routing and upstream promotion are both disabled. the model-backed report/stop campaign "
    + "is blocked because the required repo credentials are absent; zero calls were made.",
};

const toc: TocItem[] = [
  { id: "first-class", label: "what first-class means here", depth: 0 },
  { id: "green", label: "what is actually green", depth: 0 },
  { id: "context", label: "context packets", depth: 1 },
  { id: "reliability", label: "reliability receipts", depth: 1 },
  { id: "blocked", label: "what is blocked", depth: 0 },
  { id: "ladder", label: "promotion is per capability", depth: 0 },
  { id: "limits", label: "what this does not prove", depth: 0 },
  { id: "explore", label: "receipts and exact refs", depth: 1 },
];

const pct = (v: number) => (v * 100).toFixed(1) + "%";
const short = (sha: string) => sha.slice(0, 8);

const story = (
  <>
    <h2 id="first-class">what first-class means here</h2>
    <p>
      agentweb is no longer just a random caller bolted onto z0. it has a typed AODL executor id,
      a pseudonymous harness identity, deterministic trace semantics, exact-ref architecture
      manifests, a z0-owned receipt boundary, and a frozen z0evals cohort.
    </p>
    <p>
      the important part is the ownership split. agentweb still owns user/session authorization,
      confirmation, publishing, evaluation-workspace, funding, and scheduling rules. z0 owns
      routing identity, replay/conflict semantics, bounded decision receipts, and the experiment
      authority beneath Emma.
    </p>
    <Callout kind="warning" title="configured is not promoted">
      <p>
        every new route defaults off or shadow. a successful HTTP request, tool call, or authored
        fixture never becomes quality evidence by itself.
      </p>
    </Callout>

    <h2 id="green">what is actually green</h2>
    <MetricRow items={[
      { k: "scenario matrix", v: String(data.scenarioCount), s: "privacy · replay · guards · context · quality" },
      { k: "context E2E", v: data.context.rows + "/18", s: "required evidence preserved" },
      { k: "reliability E2E", v: data.reliability.durableRows + "/7", s: "one durable row per observation" },
      { k: "active routing", v: data.global.active_routing_enabled ? "on" : "off", s: "still blocked" },
    ]} />

    <h3 id="context">context packets</h3>
    <p>
      the real AgentWeb mapper and real local z0 service ran the 18-case context corpus end to end.
      there were <strong>{data.context.requiredTermFailures} required-term failures</strong>,{" "}
      <strong>{data.context.budgetViolations} byte-budget violations</strong>,{" "}
      <strong>{data.context.privacyLeaks} source-label leaks</strong>, and{" "}
      <strong>{data.context.modelCallViolations} model calls</strong>.
    </p>
    <p>
      on the three inputs large enough for total-byte compression to be meaningful, final packet /
      input ratios were{" "}
      {Object.values(data.context.largeContextRatios).map((value, index) => (
        <span key={value}>
          <strong>{pct(value)}</strong>{index < 2 ? ", " : "."}
        </span>
      ))}
      {" "}that is promising, but assist injection is still disabled because authored fixtures are
      not the required live shadow sample.
    </p>

    <h3 id="reliability">reliability receipts</h3>
    <p>
      seven bounded AgentWeb outcome classes crossed the real projection/export/ingest path twice.
      the first pass stored seven rows; the duplicate pass replayed them instead of writing seven
      more. privacy leaks: <strong>{data.reliability.privacyLeaks}</strong>. quality-gold
      violations: <strong>{data.reliability.qualityViolations}</strong>.
    </p>
    <p>
      that gives us execution/reliability evidence. it very deliberately does not tell us that the
      agent made a good decision.
    </p>

    <h2 id="blocked">the model-backed part is blocked, not green</h2>
    <p>
      the paired report and stop campaigns are wired, but the smoke found no usable model
      credentials in the AgentWeb repo. missing:{" "}
      <code>{data.modelCampaign.missing.join(", ")}</code>.
    </p>
    <Callout kind="info" title="zero spend means zero evidence">
      <p>
        the smoke exited before any incumbent or TypeSafe request. that is the correct behavior.
        green workflow status here means the blocker was represented honestly, not that model
        quality was tested.
      </p>
    </Callout>

    <h2 id="ladder">promotion is per capability</h2>
    <div className="x-table-wrap">
      <table className="x-table">
        <thead>
          <tr><th>capability</th><th>current stage</th><th>next evidence gate</th></tr>
        </thead>
        <tbody>
          <tr>
            <td>context_packet_v1</td>
            <td>{data.context.stage}</td>
            <td>500 live shadow packets + 100 large inputs before assist review</td>
          </tr>
          <tr>
            <td>reliability_observation_v1</td>
            <td>{data.reliability.stage}</td>
            <td>stay observational; never becomes quality authority</td>
          </tr>
          <tr>
            <td>report_type_v1</td>
            <td>{data.modelCampaign.reportStage}</td>
            <td>{data.modelCampaign.requiredReportLivePairs.toLocaleString()} live paired decisions</td>
          </tr>
          <tr>
            <td>stop_request_v1</td>
            <td>{data.modelCampaign.stopStage}</td>
            <td>
              {data.modelCampaign.requiredStopLivePairs.toLocaleString()} live pairs, including{" "}
              {data.modelCampaign.requiredExplicitStops} explicit stops
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <p>
      there is intentionally no global "integration passed" switch. a green context compiler does
      not authorize a stop classifier, and a good report classifier would not authorize general
      routing.
    </p>

    <h2 id="limits">what this still does not prove</h2>
    <ul>
      <li>no model-backed report or stop quality result has been measured in this cohort yet;</li>
      <li>18 authored context fixtures are not 500 real KB packets;</li>
      <li>reliability transport success is not task success;</li>
      <li>the frozen downstream refs are not upstream recommendations;</li>
      <li>active routing remains disabled.</li>
    </ul>
  </>
);

const explore = (
  <>
    <h2>exact frozen cohort</h2>
    <div className="x-table-wrap">
      <table className="x-table">
        <thead><tr><th>repo</th><th>exact ref</th></tr></thead>
        <tbody>
          {Object.entries(data.frozenHeads).map(([repo, sha]) => (
            <tr key={repo}><td>{repo}</td><td><code>{short(sha)}</code></td></tr>
          ))}
        </tbody>
      </table>
    </div>

    <h2>scenario families</h2>
    <div className="x-table-wrap">
      <table className="x-table">
        <thead><tr><th>family</th><th>scenarios</th></tr></thead>
        <tbody>
          {Object.entries(data.families).map(([family, count]) => (
            <tr key={family}><td>{family}</td><td>{count}</td></tr>
          ))}
        </tbody>
      </table>
    </div>

    <h2>frozen evidence</h2>
    <p>
      context workflow <code>{data.context.workflowRunId}</code> · artifact{" "}
      <code>{data.context.artifactSha256.slice(0, 16)}</code>
    </p>
    <p>
      reliability workflow <code>{data.reliability.workflowRunId}</code> · artifact{" "}
      <code>{data.reliability.artifactSha256.slice(0, 16)}</code>
    </p>
    <p>
      model-smoke blocker workflow <code>{data.modelCampaign.workflowRunId}</code> · artifact{" "}
      <code>{data.modelCampaign.artifactSha256.slice(0, 16)}</code>
    </p>

    <h2>evidence classes</h2>
    <pre>{JSON.stringify(data.evidenceClasses, null, 2)}</pre>
    <p>
      only model-backed paired evidence is allowed to inform quality. contract and deterministic
      E2E evidence can prove the plumbing without pretending to prove the model.
    </p>
  </>
);

export default function Page() {
  return (
    <StoryShell
      meta={meta}
      toc={toc}
      banner={banner}
      story={story}
      explore={explore}
      exploreLabel="show me the exact receipts"
    />
  );
}

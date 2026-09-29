import type { Metadata } from "next";
import StoryShell, { type StoryMeta, type StoryBanner } from "@/components/StoryShell";
import type { TocItem } from "@/components/Toc";
import MetricRow from "@/components/MetricRow";
import Callout from "@/components/Callout";

export const metadata: Metadata = {
  title: "one memory plane, four agent harnesses — z0evals",
  description: "Unified-memory v0: frozen cohort, model-visible evidence, provenance, and measured OMP context cost.",
};

const meta: StoryMeta = {
  title: "One Memory Plane, Four Agent Harnesses",
  subtitle: "Source-backed recall without replaying the whole transcript.",
  author: "Zer0 Research",
  date: "September 29, 2026",
  status: "evidence-pending",
  lede: "The cohort is frozen. OMP is measured. The four-harness result is not finished.",
};

const banner: StoryBanner = {
  tag: "PARTIAL RESULT — OMP MEASURED",
  text: "DSH has the transport overlay but still needs the same frozen model-visible proof. Hermes and OMO do not yet have final comparable cohort receipts imported into z0evals.",
};

const toc: TocItem[] = [
  { id: "contract", label: "What counts as memory", depth: 0 },
  { id: "cohort", label: "Six frozen questions", depth: 0 },
  { id: "omp", label: "OMP measured lane", depth: 0 },
  { id: "status", label: "Harness status", depth: 0 },
  { id: "limits", label: "Limits", depth: 0 },
];

const story = (
  <>
    <h2 id="contract">Memory only counts when the model got the evidence</h2>
    <p><strong>retrieval → model-visible injection → answer support → verification</strong></p>
    <Callout kind="warning" title="The contract">
      <p><code>configured ≠ retrieved ≠ injected ≠ supported ≠ verified</code></p>
    </Callout>

    <h2 id="cohort">Six questions are frozen</h2>
    <p>
      <code>exact-identifier</code>, <code>supersession</code>, <code>cross-harness</code>,{" "}
      <code>contradiction</code>, <code>missing-evidence</code>, and <code>minimal-context</code>.
      The contradiction case must show both claims with provenance; the missing-evidence case must abstain.
    </p>

    <h2 id="omp">OMP is the first measured lane</h2>
    <p>
      OMP PR #107 passes <strong>16/16</strong> focused tests against the common receipt schema.
      At turn 4:
    </p>
    <MetricRow items={[
      { k: "native", v: "320,075 B", s: "+80,008 B growth" },
      { k: "donor spill stub", v: "2,847 B", s: "+701 B growth" },
      { k: "state packet", v: "960 B", s: "+0 B growth" },
      { k: "reduction", v: "99.70%", s: "333.4× smaller than native" },
    ]} />
    <p>
      This is a context-shaping result, not a four-harness correctness claim. AgentsView search
      failed closed on that host; no retrieval hit was fabricated.
    </p>

    <h2 id="status">Keep pending lanes pending</h2>
    <div className="x-table-wrap">
      <table className="x-table">
        <thead><tr><th>harness</th><th>status</th><th>evidence</th></tr></thead>
        <tbody>
          <tr><td>OMP</td><td><strong>MEASURED</strong></td><td>common receipts, 16/16 tests, turn-4 context measurement</td></tr>
          <tr><td>DSH</td><td>BOUNDED</td><td>default-off AgentsView stdio overlay; frozen model-visible proof pending</td></tr>
          <tr><td>Hermes</td><td>PENDING</td><td>final comparable cohort receipts not imported</td></tr>
          <tr><td>OMO</td><td>PENDING</td><td>final comparable cohort receipts not imported</td></tr>
        </tbody>
      </table>
    </div>

    <h2 id="limits">What this does not prove</h2>
    <ul>
      <li>one OMP lane does not establish four-harness equivalence;</li>
      <li>context reduction does not establish answer quality by itself;</li>
      <li>retrieved text is evidence, not automatically verified truth;</li>
      <li>no cross-harness aggregate ships until comparable frozen receipts exist.</li>
    </ul>
  </>
);

const explore = (
  <>
    <h2>Sources</h2>
    <ul>
      <li>z0evals #56 / PR #57 / PR #59 — cohort and receipt contract</li>
      <li>kvnloo/oh-my-pi#107 — measured OMP lane</li>
      <li>kvnloo/deepseek-harness#2 — DSH transport overlay</li>
    </ul>
  </>
);

export default function Page() {
  return <StoryShell meta={meta} toc={toc} banner={banner} story={story} explore={explore} />;
}

import type { Metadata } from "next";
import StoryShell, { type StoryMeta, type StoryBanner } from "@/components/StoryShell";
import type { TocItem } from "@/components/Toc";
import MetricRow from "@/components/MetricRow";
import Callout from "@/components/Callout";

export const metadata: Metadata = {
  title: "can four agents remember the same thing? — z0evals",
  description: "unified-memory v0: same questions, same evidence contract, four different agent harnesses.",
};

const meta: StoryMeta = {
  title: "can four agents remember the same thing?",
  subtitle: "i got tired of every harness having its own half-broken version of memory.",
  author: "zer0 research",
  date: "september 29, 2026",
  status: "evidence-pending",
  lede: "the cohort is frozen. omp is measured. the four-harness result is still not done, and i am not pretending it is.",
};

const banner: StoryBanner = {
  tag: "partial result · omp measured",
  text: "dsh has the transport path but still needs the same frozen model-visible proof. hermes and omo do not have final comparable cohort receipts imported yet. so: one measured lane, not four.",
};

const toc: TocItem[] = [
  { id: "contract", label: "memory is not one thing", depth: 0 },
  { id: "cohort", label: "freeze the questions first", depth: 0 },
  { id: "omp", label: "omp finally gave us a number", depth: 0 },
  { id: "status", label: "do not average pending work", depth: 0 },
  { id: "limits", label: "what this still does not prove", depth: 0 },
];

const story = (
  <>
    <h2 id="contract">memory is not one thing</h2>
    <p>
      this kept biting us because we would say “memory worked” when we actually meant one of like
      four different things.
    </p>
    <p><strong>retrieval → model-visible injection → answer support → verification</strong></p>
    <p>
      those are not interchangeable. finding a row in an index is not the same as putting it in
      front of the model. putting it in front of the model is not the same as the answer using it.
      and even a supported answer is not automatically verified.
    </p>
    <Callout kind="warning" title="the annoying rule">
      <p><code>configured ≠ retrieved ≠ injected ≠ supported ≠ verified</code></p>
    </Callout>

    <h2 id="cohort">freeze the questions before touching the harnesses</h2>
    <p>
      i did not want dsh, hermes, omo, and omp each “passing” their own custom little memory demo.
      so the cohort is frozen first:
      <code>exact-identifier</code>, <code>supersession</code>, <code>cross-harness</code>,{" "}
      <code>contradiction</code>, <code>missing-evidence</code>, and <code>minimal-context</code>.
    </p>
    <p>
      the contradiction case has to show both claims and pick no winner. the missing-evidence case
      has to say “i do not have it.” honestly those two are more interesting than the easy recall
      cases anyway.
    </p>

    <h2 id="omp">omp finally gave us a number i actually care about</h2>
    <p>
      omp pr #107 runs the same six question ids through the common receipt schema and passes{" "}
      <strong>16/16</strong> focused tests. the fun part is the context size at turn 4:
    </p>
    <MetricRow items={[
      { k: "native", v: "320,075 b", s: "+80,008 b growth" },
      { k: "donor spill stub", v: "2,847 b", s: "+701 b growth" },
      { k: "state packet", v: "960 b", s: "+0 b growth" },
      { k: "reduction", v: "99.70%", s: "333.4× smaller than native" },
    ]} />
    <p>
      960 bytes versus 320,075 bytes is the kind of difference that changes architecture. but it
      only says we shaped context way better. it does <em>not</em> magically prove all four
      harnesses remember correctly.
    </p>
    <p>
      agentsview also failed closed on that host. good. no hit was invented just to make the demo
      look green.
    </p>

    <h2 id="status">do not average pending work into a headline</h2>
    <p>
      this table is intentionally boring. boring is good here.
    </p>
    <div className="x-table-wrap">
      <table className="x-table">
        <thead><tr><th>harness</th><th>status</th><th>what we actually have</th></tr></thead>
        <tbody>
          <tr><td>omp</td><td><strong>measured</strong></td><td>common receipts, 16/16 tests, turn-4 context measurement</td></tr>
          <tr><td>dsh</td><td>bounded</td><td>default-off agentsview stdio overlay; frozen model-visible proof still pending</td></tr>
          <tr><td>hermes</td><td>pending</td><td>final comparable cohort receipts not imported yet</td></tr>
          <tr><td>omo</td><td>pending</td><td>final comparable cohort receipts not imported yet</td></tr>
        </tbody>
      </table>
    </div>
    <p>
      i am not turning one good omp row into “unified memory solved.” once all four lanes produce
      the same receipt shape against the same frozen cohort, then we can talk.
    </p>

    <h2 id="limits">what this still does not prove</h2>
    <ul>
      <li>one omp lane does not prove four-harness equivalence;</li>
      <li>smaller context does not prove better answers by itself;</li>
      <li>we do not need one giant universal memory database for this to work;</li>
      <li>retrieved text is evidence, not automatically truth;</li>
      <li>there is no cross-harness aggregate until the comparable receipts exist.</li>
    </ul>
    <p>
      the thing i actually want is simpler: same question, same evidence contract, different
      harness, same answer support. once that is boring, memory stops being a product-specific
      magic trick and starts becoming infrastructure.
    </p>
  </>
);

const explore = (
  <>
    <h2>show me the receipts</h2>
    <ul>
      <li>z0evals #56 / pr #57 / pr #59 — cohort + receipt contract</li>
      <li>kvnloo/oh-my-pi#107 — measured omp lane</li>
      <li>kvnloo/deepseek-harness#2 — dsh transport overlay</li>
    </ul>
  </>
);

export default function Page() {
  return <StoryShell meta={meta} toc={toc} banner={banner} story={story} explore={explore} />;
}

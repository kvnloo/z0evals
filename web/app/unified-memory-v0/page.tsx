import type { Metadata } from "next";
import StoryShell, { type StoryMeta, type StoryBanner } from "@/components/StoryShell";
import type { TocItem } from "@/components/Toc";
import MetricRow from "@/components/MetricRow";
import Callout from "@/components/Callout";

export const metadata: Metadata = {
  title: "can four agents remember the same thing? — z0evals",
  description: "unified-memory v0, updated october 5: integrated OptMem foundations, separate OptChat experiments, and the unchanged four-harness evidence boundary.",
};

const meta: StoryMeta = {
  title: "can four agents remember the same thing?",
  subtitle: "i got tired of every harness having its own half-broken version of memory.",
  author: "zer0 research",
  date: "updated october 5, 2026",
  status: "evidence-pending",
  lede: "optmem's structural foundation is integrated. optchat is a separate harness experiment. the original cohort is still partial, so implementation progress and measured recall stay separate.",
};

const banner: StoryBanner = {
  tag: "implementation update · original cohort still partial",
  text: "the october 5 update below reports pinned public implementation evidence, not a new recall benchmark. the september 29 cohort measurements remain unchanged; no four-harness aggregate is claimed.",
};

const toc: TocItem[] = [
  { id: "optmem-update", label: "what landed in optmem", depth: 0 },
  { id: "optchat-update", label: "optchat is a different layer", depth: 0 },
  { id: "contract", label: "memory is not one thing", depth: 0 },
  { id: "cohort", label: "freeze the questions first", depth: 0 },
  { id: "omp", label: "omp finally gave us a number", depth: 0 },
  { id: "status", label: "do not average pending work", depth: 0 },
  { id: "limits", label: "what this still does not prove", depth: 0 },
];

const story = (
  <>
    <h2 id="optmem-update">what actually landed in optmem</h2>
    <p>
      the old page stopped at the september 29 cohort. work continued, but the publication did
      not. this is the missing implementation update, frozen to the public revisions linked below.
    </p>
    <p>
      first, credit where it belongs: <a href="https://github.com/VictorTaelin/OptMem">Victor Taelin's OptMem</a>
      {" "}is the upstream reference for the temporal-memory approach. Kevin directed the z0 integration
      and identified the missing publication. our adaptation and its evidence are separate from the original project.
    </p>
    <p>
      z0intelligence integrated the event ledger, optmem-style temporal projection, and scoped memory
      contract through reconciliation pr #109 at <code>b345aa2</code>. the exact source is inspectable in the{" "}
      <a href="https://github.com/kvnloo/z0intelligence/blob/b345aa2bef199779cac8672b08d535cb28526fd7/docs/pr-reconciliation-2026-10-02.md">pinned reconciliation record</a>
      {" "}and <a href="https://github.com/kvnloo/z0intelligence/blob/b345aa2bef199779cac8672b08d535cb28526fd7/src/z0int/memory/optmem_tree.py">pinned temporal projection</a>.
    </p>
    <p>
      <code>events.jsonl</code> stays canonical. the tree is a rebuildable view over older history;
      recent events remain raw, sticky historical events can be expanded, and <code>zoom()</code>
      {" "}returns the original event payloads. rebuilding that view does not turn it into another authority.
    </p>
    <Callout kind="warning" title="structural memory is not semantic recall">
      <p>
        this implementation explicitly proves structure, not semantic summarization. its coarse
        nodes contain counts and digests, not learned conversation summaries. integration tests
        are not a new model-quality result, and the old 960-byte omp measurement below is not an optmem benchmark.
      </p>
    </Callout>

    <h2 id="optchat-update">optchat is a different layer</h2>
    <p>
      shared memory and a harness's compacted chat history are related, but they are not the same
      store. the new optchat work keeps those responsibilities separate:
    </p>
    <div className="x-table-wrap">
      <table className="x-table">
        <thead><tr><th>slice</th><th>status on october 5</th><th>boundary</th></tr></thead>
        <tbody>
          <tr>
            <td>optmem foundation</td><td>integrated structural baseline</td>
            <td>canonical event log plus derived temporal view; no semantic-quality qualification</td>
          </tr>
          <tr>
            <td>omp optchat</td><td>open pr #126</td>
            <td>append-only harness chat log and compactor; not a new shared memory store</td>
          </tr>
          <tr>
            <td>hermes optchat</td><td>draft pr #127, stacked on #126</td>
            <td>optional off / shadow / on adapter; default off, separate Hermes log root</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p>
      the omp snapshot is <a href="https://github.com/kvnloo/z0intelligence/commit/0828b7738d35e712b57814aa09a8bddf82a48fcc"><code>0828b77</code></a>
      {" "}in <a href="https://github.com/kvnloo/z0intelligence/pull/126">pr #126</a>.
      the hermes adapter is <a href="https://github.com/kvnloo/z0intelligence/commit/fc31fb5ca3e1322af3951080dfb0cd95b76fc93d"><code>fc31fb5</code></a>
      {" "}in <a href="https://github.com/kvnloo/z0intelligence/pull/127">pr #127</a>.
      these are pinned implementation snapshots, not a claim that either open branch has reached the runtime default.
    </p>
    <p>
      #126 reports focused optchat/retrieval-replay tests. #127 reports green core-unit and no new
      optchat, hermes-adapter, or memory failures relative to its base, while the full offline suite
      still has base failures. that is narrower than saying the whole stack is green.
      publishing this update does not merge those runtime prs or enable either adapter.
    </p>
    <p>
      the next missing evidence is comparable answer support, provenance, contradictions, abstention,
      context size, and cold/warm latency against the same frozen questions. private chat logs and
      personal memory stores are not imported into this public report.
    </p>
    <Callout kind="info" title="the original cohort, unchanged">
      <p>the sections below preserve the september 29 report. the implementation update above does not rescore it.</p>
    </Callout>

    <Callout kind="info" title="new · october 5">
      <p>the <a href="../optchat-long-horizon-v0/">optmem / optchat follow-up</a> now has its own
        fifty-turn context-size report. it remains unscored: smaller views do not certify recall quality.</p>
    </Callout>

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
      <li><a href="https://github.com/VictorTaelin/OptMem">Victor Taelin — original OptMem project</a></li>
      <li><a href="https://github.com/kvnloo/z0intelligence/pull/109">z0intelligence #109 — integrated event ledger, OptMem projection, and scoped memory contract</a></li>
      <li><a href="https://github.com/kvnloo/z0intelligence/pull/126">z0intelligence #126 — separate OMP OptChat experiment</a></li>
      <li><a href="https://github.com/kvnloo/z0intelligence/pull/127">z0intelligence #127 — optional Hermes OptChat adapter</a></li>
      <li>z0evals #56 / pr #57 / pr #59 — cohort + receipt contract</li>
      <li>kvnloo/oh-my-pi#107 — measured omp lane</li>
      <li>kvnloo/deepseek-harness#2 — dsh transport overlay</li>
    </ul>
  </>
);

export default function Page() {
  return <StoryShell meta={meta} toc={toc} banner={banner} story={story} explore={explore} />;
}

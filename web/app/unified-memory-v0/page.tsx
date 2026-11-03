import type { Metadata } from "next";
import StoryShell, { type StoryMeta, type StoryBanner } from "@/components/StoryShell";
import type { TocItem } from "@/components/Toc";
import MetricRow from "@/components/MetricRow";
import Callout from "@/components/Callout";
import { Citation, Evidence, ExpHead, SetupFigure, Teaser, Tldr, TracePages, type TraceItem } from "@/components/essay/Essay";
import "./memory.css";
// The frozen cohort, question contract and receipt schema, adapted by
// scripts/build_site_data.py. No harness receipts are frozen yet, so the page
// shows the questions and what each one requires, never an invented answer.
import study from "@/data/unified-memory-v0.json";

export const metadata: Metadata = {
  title: "can four agents remember the same thing? — z0evals",
  description: "unified-memory v0, updated october 5: integrated OptMem foundations, separate OptChat experiments, and the unchanged four-harness evidence boundary.",
};

const { manifest, cohort, contract } = study;
const receipts: unknown[] = study.receipts;
const harnesses = study.receipt_harnesses;
if (manifest.scoring !== "unscored" || manifest.claims.length !== 0) {
  throw new Error("unified-memory publication: the manifest no longer says unscored with no claims");
}
if (receipts.length !== 0) {
  throw new Error("unified-memory publication: harness receipts were imported; rewrite the page before scoring it");
}
const expectedById = new Map(contract.questions.map((q) => [q.id, q.expected]));
const evidenceById = new Map(cohort.evidence.map((e) => [e.source_id, e]));
if (cohort.questions.some((q) => !expectedById.has(q.id))) {
  throw new Error("unified-memory publication: cohort and question contract disagree");
}

// Lane status as reported in the september 29 write-up below (the status table).
// It is the page's existing claim, not a frozen receipt.
const lanes: { harness: string; state: "measured" | "bounded" | "pending" }[] = [
  { harness: "omp", state: "measured" },
  { harness: "dsh", state: "bounded" },
  { harness: "hermes", state: "pending" },
  { harness: "omo", state: "pending" },
];
if (lanes.length !== harnesses.length || lanes.some((l) => !harnesses.includes(l.harness))) {
  throw new Error("unified-memory publication: lane list and receipt schema harnesses disagree");
}
const gates = ["retrieval", "injection", "answer support", "verification"];

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
  { id: "cite", label: "cite this", depth: 0 },
];

const actionText: Record<string, string> = {
  answer: "answer, citing the evidence",
  observe: "report both claims with provenance, pick no winner",
  abstain: "abstain: say the evidence is not there",
};

const traces: TraceItem[] = cohort.questions.map((q) => {
  const present = q.evidence_ids.filter((id) => evidenceById.has(id));
  const absent = q.evidence_ids.filter((id) => !evidenceById.has(id));
  return {
    label: q.id,
    group: q.expected_action,
    ask: <>{q.prompt}</>,
    given: (
      <>
        <span className="um-tag">kind: {q.kind}</span>
        <ul className="um-evidence">
          {present.map((id) => {
            const e = evidenceById.get(id)!;
            return (
              <li key={id}>
                <code>{e.source_id}</code> ({e.trust_class}, observed {e.observed_at.slice(0, 10)}): <code>{e.claim}</code>
              </li>
            );
          })}
          {absent.map((id) => (
            <li key={id}><code>{id}</code>: not in the fixture, on purpose</li>
          ))}
        </ul>
      </>
    ),
    answer: (
      <>
        <p>no harness answer is frozen. the contract expects: <b>{actionText[q.expected_action] ?? q.expected_action}</b>{" "}
          (<code>{expectedById.get(q.id)}</code>).</p>
        {q.expected_support.length ? (
          <div className="um-tags">
            {q.expected_support.map((s) => <span key={s} className="um-tag">{s}</span>)}
          </div>
        ) : null}
        {q.forbidden.length ? (
          <div className="um-tags">
            {q.forbidden.map((s) => <span key={s} className="um-tag" data-kind="forbidden">{s}</span>)}
          </div>
        ) : null}
      </>
    ),
    verdict: { text: "unscored · no receipt", tone: "hold" },
    steps: [
      <>retrieval: should find {q.evidence_ids.map((id) => <code key={id}>{id} </code>)}. no frozen receipt.</>,
      <>injection: that evidence has to reach the model, not just the index. no frozen receipt.</>,
      <>answer support: {q.expected_support.length
        ? <>the answer has to contain {q.expected_support.length} expected support string{q.expected_support.length === 1 ? "" : "s"}.</>
        : <>there is nothing to support, so the right move is to abstain.</>}{q.forbidden.length ? <> it must not say <code>{q.forbidden.join(", ")}</code>.</> : null} not run.</>,
      <>verification: contract outcome <code>{expectedById.get(q.id)}</code>. not run.</>,
    ],
    foot: <>question {q.id} · studies/unified-memory-v0/cohort.json · {cohort.source}</>,
  };
});

const teaser = (
  <Teaser
    label="the memory study in three panels"
    panels={[
      {
        step: "1 · the questions",
        task: <>one cohort, frozen before any harness touched it.</>,
        visual: (
          <ul className="um-kinds">
            {cohort.questions.map((q) => <li key={q.id}>{q.id}</li>)}
          </ul>
        ),
        by: "studies/unified-memory-v0/cohort.json",
        big: cohort.questions.length,
        note: <>questions, each with its own evidence and expected action</>,
      },
      {
        step: "2 · the harnesses",
        task: <>the same receipt shape, required from {harnesses.join(", ")}.</>,
        visual: (
          <div className="um-lanes">
            {lanes.map((l) => (
              <div className="um-lane" data-state={l.state} key={l.harness}>
                <span>{l.harness}</span>
                <span className="um-lane-bar" title={l.state} />
              </div>
            ))}
          </div>
        ),
        by: "lane status from the september 29 report",
        big: <>{lanes.filter((l) => l.state === "measured").length} / {lanes.length}</>,
        note: <>lanes with a measured row. that row is omp, source-reported.</>,
      },
      {
        step: "3 · not scored",
        task: <>a pass needs every gate on a frozen receipt.</>,
        visual: (
          <ul className="um-gates">
            {gates.map((g) => <li key={g}><span>{g}</span><span>no receipt</span></li>)}
          </ul>
        ),
        by: `manifest scoring: ${manifest.scoring}`,
        big: receipts.length,
        note: <>frozen harness receipts. not a pass and not a fail.</>,
      },
    ]}
  />
);

const cohortSetup = (
  <>
    <p><b>what the study asks.</b></p>
    <ul className="um-setup-list">{manifest.questions.map((q) => <li key={q}>{q}</li>)}</ul>
    <p><b>receipt.</b> every harness row must carry {study.receipt_required.length} fields, including{" "}
      <code>retrieval_ok</code>, <code>injected</code>, <code>answer_supported</code> and <code>verified</code> as
      separate booleans.</p>
    <p><b>starting revisions.</b></p>
    <ul className="um-setup-list">
      {manifest.sources.map((s) => (
        <li key={s.repo}><code>{s.repo}@{s.commit.slice(0, 7)}</code>: {s.role}</li>
      ))}
    </ul>
    <p><b>limitations, from the manifest.</b></p>
    <ul className="um-setup-list">{manifest.limitations.map((l) => <li key={l}>{l}</li>)}</ul>
  </>
);

const story = (
  <>
    <Tldr>
      <p>the october 5 update is implementation evidence, not a recall benchmark. optmem&apos;s structural
        foundation is integrated and optchat is a separate harness experiment.</p>
      <p>the {cohort.questions.length}-question cohort is frozen. no harness receipts are frozen yet, so the
        study is {manifest.scoring}: not a pass and not a fail. omp&apos;s 960-byte state
        packet against 320,075 bytes native is a source-reported context-size number, not proof that four
        harnesses remember correctly.</p>
    </Tldr>
    {teaser}

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
      this kept biting us because we would say "memory worked" when we actually meant one of like
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
    <ExpHead n={1} id="exp-cohort">what does each question require?</ExpHead>
    <p>
      i did not want dsh, hermes, omo, and omp each "passing" their own custom little memory demo.
      so the cohort is frozen first:
      <code>exact-identifier</code>, <code>supersession</code>, <code>cross-harness</code>,{" "}
      <code>contradiction</code>, <code>missing-evidence</code>, and <code>minimal-context</code>.
    </p>
    <p>
      the contradiction case has to show both claims and pick no winner. the missing-evidence case
      has to say "i do not have it." honestly those two are more interesting than the easy recall
      cases anyway.
    </p>
    <SetupFigure setup={cohortSetup} caption={<>the {cohort.questions.length} frozen questions, with the
      evidence each one may use and the outcome the contract expects. every gate reads &ldquo;no receipt&rdquo;
      because no harness run has been frozen. use the left and right arrow keys to move between questions.</>}>
      <TracePages items={traces} label="frozen cohort questions" columns={["question", "required outcome", "gates"]} />
    </SetupFigure>

    <h2 id="omp">omp finally gave us a number i actually care about</h2>
    <ExpHead n={2} id="exp-omp">how much context does omp hand the model at turn 4?</ExpHead>
    <p><Evidence kind="source-reported">omp pr #107, not a receipt frozen in this study</Evidence></p>
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
      i am not turning one good omp row into "unified memory solved." once all four lanes produce
      the same receipt shape against the same frozen cohort, then we can talk. this study has{" "}
      {receipts.length} of those receipts frozen today.
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

    <h2 id="cite">cite this</h2>
    <Citation id="zer0-unified-memory-v0" title={meta.title} year={2026}
      url="https://kvnloo.github.io/z0evals/unified-memory-v0/"
      note={`${manifest.scoring}; no harness receipts frozen; study ${manifest.id}`} />
  </>
);

const explore = (
  <>
    <h2>show me the receipts</h2>
    <ul>
      <li><a href="https://github.com/VictorTaelin/OptMem">Victor Taelin: original OptMem project</a></li>
      <li><a href="https://github.com/kvnloo/z0intelligence/pull/109">z0intelligence #109: integrated event ledger, OptMem projection, and scoped memory contract</a></li>
      <li><a href="https://github.com/kvnloo/z0intelligence/pull/126">z0intelligence #126: separate OMP OptChat experiment</a></li>
      <li><a href="https://github.com/kvnloo/z0intelligence/pull/127">z0intelligence #127: optional Hermes OptChat adapter</a></li>
      <li>z0evals #56 / pr #57 / pr #59: cohort + receipt contract</li>
      <li>kvnloo/oh-my-pi#107: measured omp lane</li>
      <li>kvnloo/deepseek-harness#2: dsh transport overlay</li>
      <li><a href="https://github.com/kvnloo/z0evals/tree/main/studies/unified-memory-v0">studies/unified-memory-v0</a>: manifest, cohort, question contract and receipt schema</li>
    </ul>
  </>
);

export default function Page() {
  return <StoryShell meta={meta} toc={toc} banner={banner} story={story} explore={explore} />;
}

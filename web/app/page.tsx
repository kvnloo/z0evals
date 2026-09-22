import study from "@/data/study.json";
import type { Arm, Matrix } from "@/data/types";
import RouteProgress from "@/components/RouteProgress";
import Toc, { type TocItem } from "@/components/Toc";
import Callout from "@/components/Callout";
import MetricRow from "@/components/MetricRow";
import HeadlineFigure from "@/components/HeadlineFigure";
import LadderFlow from "@/components/LadderFlow";
import ResultsExplorer from "@/components/ResultsExplorer";
import ArmScatter from "@/components/charts/ArmScatter";
import ResidencyBars from "@/components/charts/ResidencyBars";
import CompositionSplit from "@/components/charts/CompositionSplit";
import OrchestrationBars from "@/components/charts/OrchestrationBars";
import DensityBars from "@/components/charts/DensityBars";
import Calibration from "@/components/charts/Calibration";
import ActionTable from "@/components/ActionTable";
import HeadingFrog from "@/components/HeadingFrog";
import MobileToc from "@/components/MobileToc";
import CorpusGrowth from "@/components/figures/CorpusGrowth";
import ModelBoard, { type Coverage, type ModelBoardData } from "@/components/figures/ModelBoard";
import ProgressRows from "@/components/figures/ProgressRows";
import ForecastPair from "@/components/figures/ForecastPair";
import UtilityTie from "@/components/figures/UtilityTie";
import FamilyBoard from "@/components/figures/FamilyBoard";
import ReferenceMap from "@/components/ReferenceMap";
import { MarginNote, Footnotes } from "@/components/Notes";

const S = study.study;
const D = study.density;
const matrix = study.matrix as unknown as Matrix;
const arms = matrix.arms as Arm[];
const hammer3 = arms.find((a) => a.id === "compiler+hammer2.1_3b")!;
const qwen4 = arms.find((a) => a.id === "compiler+qwen3.5_4b")!;
const qwen9 = arms.find((a) => a.id === "compiler+qwen3.5_9b")!;
const jev = arms.find((a) => a.id === "compiler+jev")!;
const unf = arms.find((a) => a.id === "unfiltered+hammer2.1_3b")!;
const fng = arms.find((a) => a.id === "compiler+functiongemma_270m")!;
const calibration = (matrix as unknown as { calibration: never[] }).calibration;
const actionCensus = (matrix as unknown as { actions: never[] }).actions;

const C = (study as unknown as { components: Record<string, never> }).components;
const board = C.modelBoard as unknown as ModelBoardData;
const progress = C.progress as never;
const forecast = C.forecast as never;
const utility = C.utility as never;
const coverage = C.coverage as unknown as Coverage;
const familyBoard = C.familyBoard as never;
// Recovered J1 routing-shadow pilot. Separate evidence artifact from Phase 1B.
const pilot = study.pilot as unknown as {
  highRiskCount: number;
  agreementRate: number;
  decisions: number;
  highConfidenceAgreement: string;
};

const pct = (v: number, d = 1) => `${(v * 100).toFixed(d)}%`;
const ms = (v: number | null) =>
  v == null ? "—" : v >= 1000 ? `${(v / 1000).toFixed(2)} s` : `${Math.round(v)} ms`;

const TOC: TocItem[] = [
  { id: "how-much", label: "how much of the llm do we need?", depth: 0 },
  { id: "first-shortcut", label: "the first shortcut", depth: 0 },
  { id: "boring-3b", label: "the boring 3b ruined the ladder", depth: 0 },
  { id: "phase1", label: "phase 1 was kind of trash", depth: 0 },
  { id: "held-up", label: "hammer3b actually held up", depth: 0 },
  { id: "wrong-job", label: "we gave big models the wrong job", depth: 0 },
  { id: "residency", label: "residency wrecked the framing", depth: 0 },
  { id: "composition", label: "composition made it worse", depth: 0 },
  { id: "jev", label: "jev failed. jev isn't useless.", depth: 0 },
  { id: "compiler", label: "the compiler was the intelligence", depth: 0 },
  { id: "gate", label: "the gate failed its own eval", depth: 0 },
  { id: "errors", label: "the errors were not noise", depth: 0 },
  { id: "architecture", label: "what architecture survived", depth: 0 },
  { id: "weirder", label: "make the bottom weirder", depth: 0 },
  { id: "result", label: "the actual result", depth: 0 },
  { id: "author", label: "author's note", depth: 0 },
  { id: "appendix", label: "appendix", depth: 0 },
  { id: "explore", label: "explore the matrix", depth: 1 },
  { id: "gate-caveats", label: "gate defects recorded", depth: 1 },
  { id: "provenance", label: "check or reuse the evidence", depth: 1 },
  { id: "references", label: "references", depth: 1 },
];

export default function Page() {
  return (
    <>
      <RouteProgress />
      <header className="blog-page-header">
        <div>
          <nav className="site-nav">
            <a className="brand" href="./">z0evals</a>
            <div className="links">
              <a href="#held-up">results</a>
              <a href="#appendix">method</a>
              <a href="https://github.com/kvnloo/z0evals">github</a>
            </div>
          </nav>
        </div>
      </header>

      <div className="shell">
        <div className="rail"><Toc items={TOC} /></div>
        <MobileToc items={TOC} />
        <main className="article article-shell">
          <div className="article-header">
            <div>
              <h1 className="article-title">how much of the llm do we actually need?</h1>
              <div className="title-accent-line" aria-hidden="true" />
              <div className="article-meta">
                {S.author}<span className="sep">·</span>{S.date}
                <span className="sep">·</span>
                <span style={{ fontFamily: "var(--font-mono)" }}>{S.runId}</span>
              </div>
            </div>
          </div>

          <div className="article-body prose">
            <HeadingFrog id="how-much" level={2}>
              how much of the llm do we actually need?
            </HeadingFrog>

            <p>
              i started this with a pretty simple question: <strong>why are we paying an
              autoregressive language model to make decisions that barely require
              language?</strong>
            </p>

            <p>
              a lot of agent work looks intelligent from the outside because the whole loop is
              intelligent. but when you zoom in, a huge fraction of the individual decisions are
              boring:
            </p>

            <ul>
              <li>can i call this tool?</li>
              <li>which of these four actions is legal?</li>
              <li>should i retry or escalate?</li>
              <li>is this context relevant?</li>
              <li>do i need a bigger model yet?</li>
              <li>has enough changed that i should keep reasoning?</li>
            </ul>

            <p>
              those are not all &ldquo;write me a thoughtful paragraph&rdquo; problems. some of
              them are barely even language problems.
            </p>

            <p>
              and this mattered because i was trying to run more and more of zer0 locally. the
              free remote models were useful, but they were also slow enough that you could feel
              every unnecessary call. meanwhile, wiring the jev skill into hermes was one of
              those stupidly simple changes where the whole thing just felt faster immediately.
            </p>

            <p>so naturally i got greedy.</p>

            <p>
              what if the expensive model stopped being the default brain? what if we could
              progressively replace its responsibilities with cheaper and cheaper machinery until
              the llm only saw the part of the problem that actually needed it?
            </p>

            <p>that became the rough hierarchy i had in my head:</p>

            <pre>{`deterministic compiler / cached rule
              ↓
mushroom-body / fly specialist
              ↓
jev / nanojev
              ↓
tiny tool-calling model
              ↓
small orchestrator
              ↓
general local model
              ↓
remote frontier model`}</pre>

            <p>
              the basic hypothesis was that intelligence should get{" "}
              <strong>more expensive only as the uncertainty survives</strong>.
            </p>

            <p>nice idea. the models had other plans.</p>

            <hr />

            <HeadingFrog id="first-shortcut" level={2}>
              the first shortcut looked better than it was
            </HeadingFrog>

            <p>
              jev was the obvious place to start because it does not need to generate an answer
              token by token. give it a typed question and a bounded set of possibilities, and it
              gives you a distribution. that sounded perfect for routing.
            </p>

            <p>
              then we got nanojev running locally: roughly a 0.6b model, around 300 mib resident,
              no autoregressive decode loop, and a clean <code>decisionbackend</code> interface.
            </p>

            <p>
              on the first paired shadow run, we had 27 decisions. nanojev looked fast enough to
              care about. but it agreed with the jev teacher only <strong>48.1%</strong> of the
              time, including <strong>{pilot.highRiskCount} high-risk disagreements</strong>.
            </p>

            <MarginNote n={1} label="it was the menu, not the model">
              those two routers were choosing from <em>different</em> candidate sets. when the
              menu is held equal the agreement is <strong>100%</strong>, not 48.1% &mdash; the
              later J1_1 rerun reports <code>candidate_set_equal: true</code> on all 40 rows, and
              the pre-fix corpus reports <code>0</code> matched of 40. so 48.1% measures a
              mismatched menu, not nanojev&rsquo;s quality. note also that jev was confident
              (&ge;0.7) on 21 of the 27 and nanojev agreed on only{" "}
              <strong>{pilot.highConfidenceAgreement}</strong> of them. artifact:{" "}
              <code>nanojev-j1-shadow-pilot.json</code>,{" "}
              <code>evidence_class = exploratory_beta</code>.
            </MarginNote>

            <p>
              and there was an implementation trap hiding inside the latency number too: the cli
              path was reloading the model on every invocation. what looked like a ~236 ms
              decision engine was sitting behind a ~15.5 second cold load when invoked the dumb
              way.
            </p>

            <p>that was the first useful correction to the architecture:</p>

            <Callout kind="warning" title="a small model is not a cheap decision">
              <p>
                residency, process lifetime, serving path, and escalation policy are part of the
                model. a checkpoint&rsquo;s forward-pass time is not its cost.
              </p>
            </Callout>

            <p>we moved nanojev off the critical path and kept collecting evidence.</p>

            <hr />

            <HeadingFrog id="boring-3b" level={2}>
              then the boring 3b model ruined the beautiful ladder
            </HeadingFrog>

            <p>
              the original plan was much more sophisticated than what ended up winning. we had
              jev, nanojev, nemotron as an orchestrator, qwen as a stronger fallback,
              specialists, cascades. the whole thing looked like it should become a nice
              multi-stage cognition stack.
            </p>

            <p>
              then we actually put the models on the same bounded decisions. the first phase was
              small and noisy, but the result was hard to ignore.
            </p>

            <p>
              <code>hammer2.1-3b</code> kept winning.
            </p>

            <p>
              not because it was the smartest model in some abstract sense. qwen3.5-9b could
              still solve a few things hammer missed. but for the actual job in front of us
              — <strong>choose among actions after the compiler has already removed the illegal
              ones</strong> — Hammer was absurdly competitive for how cheap it was.
            </p>

            <p>our early measurement looked roughly like this:</p>

            <pre>{`compiler + hammer2.1-3b    25/28    ~177 ms p50
compiler + qwen3.5-9b      26/28    much slower
nemotron-8b                17/28    ~2.7 s p50`}</pre>

            <p>
              and an even more important result had started showing up beside it: when we removed
              the compiler and let the model see dangerous actions, it sometimes chose them. when
              the compiler removed those actions first, the dangerous selections disappeared.
            </p>

            <p>that started changing the question. we had been asking:</p>

            <blockquote>which model should be the router?</blockquote>

            <p>
              the better question was becoming:{" "}
              <strong>how much routing should be a model problem at all?</strong>
            </p>

            <hr />

            <HeadingFrog id="phase1" level={2}>
              phase 1 was interesting. the evidence was also kind of trash.
            </HeadingFrog>

            <p>there was one problem with getting excited about any of this.</p>

            <p>
              phase 1 contained <strong>{D.phase1_cells} measured cells</strong>.{" "}
              <strong>{D.phase1_cells_n1} of them had n=1.</strong>
            </p>

            <p>
              that is enough to find weird things. it is not enough to build the architecture
              around them.
            </p>

            <p>
              so phase 1b was deliberately boring. we froze the run structure, stopped changing
              the hypotheses every five minutes, ran everything through the same local{" "}
              <code>z0int cognition serve</code> supervisor, and repeated the state/arm
              combinations until the comparison stopped being mostly anecdotes.
            </p>

            <MetricRow
              items={[
                { k: "run", v: S.runId, s: "immutable" },
                { k: "raw receipts", v: D.raw_receipts.toLocaleString(), s: "one per model call" },
                { k: "measured cells", v: String(D.phase1b_measured_cells), s: `${D.phase1_cells} in phase 1` },
                { k: "cells at n ≥ 3", v: String(D.phase1b_cells_n_ge_3), s: `n=1: ${D.phase1b_cells_n1}` },
                { k: "external spend", v: `$${S.externalSpendUsd.toFixed(2)}`, s: "all local" },
              ]}
            />

            <p>
              all of the inference in this experiment ran locally. and once the evidence got
              denser, the architecture got simpler again.
            </p>

            <HeadlineFigure
              value={D.raw_receipts.toLocaleString()}
              unit="raw receipts · one per model call"
              caption={
                <>
                  {D.phase1b_measured_cells} measured cells, {D.phase1b_cells_n_ge_3} of them at
                  n≥3. Best bounded-choice success {pct(qwen9.successRate)} ({qwen9.label},{" "}
                  {ms(qwen9.warmP50Ms)}). The unfiltered control selected a dangerous action{" "}
                  {unf.dangerous} times; every compiler-first arm, zero.
                </>
              }
            >
              <DensityBars d={D} />
            </HeadlineFigure>

            <div className="diagram-wrapper">
              <CorpusGrowth d={C.corpus as never} />
            </div>

            <div className="diagram-wrapper">
              <ForecastPair d={forecast} />
            </div>

            <hr />

            <HeadingFrog id="held-up" level={2}>
              hammer3b actually held up
            </HeadingFrog>

            <p>
              here is the part i expected to move around once we repeated it. it mostly
              didn&rsquo;t.
            </p>

            <div className="diagram-wrapper">
              <ModelBoard d={board} coverage={coverage} />
            </div>

            <p>
              the funny thing is that qwen3.5-9b technically wins the aggregate accuracy number.{" "}
              <strong>
                {qwen9.success}/{qwen9.n} versus {hammer3.success}/{hammer3.n}.
              </strong>
            </p>

            <p>
              but it takes <strong>{ms(qwen9.warmP50Ms)}</strong> warm instead of{" "}
              <strong>{ms(hammer3.warmP50Ms)}</strong>.
            </p>

            <p>
              qwen3.5-4b is even easier to interpret: it goes exactly{" "}
              <strong>
                {qwen4.success}/{qwen4.n}
              </strong>
              , the same as Hammer3B, while taking <strong>{ms(qwen4.warmP50Ms)}</strong>. So on
              bounded action choice, Qwen 4B is basically spending an extra ~1.8 seconds to arrive
              at the same answer.
            </p>

            <p>that is not escalation. that is just waiting.</p>

            <p>
              hammer3b ended up with the best measured success on{" "}
              <strong>26 of the 28 states</strong> while staying inside a latency regime where
              putting it on the hot path is actually plausible.
            </p>

            <p>
              qwen9b still matters. it is the unique best arm on one state:{" "}
              <code>tool_fails</code>.
            </p>

            <p>
              <strong>that one state is going to become important again later.</strong>
            </p>

            <div className="diagram-wrapper">
              <ProgressRows d={progress} />
            </div>

            <div className="diagram-wrapper">
              <ArmScatter arms={arms} />
            </div>

            <hr />

            <HeadingFrog id="wrong-job" level={2}>
              bigger models were not useless. we were giving them the wrong job.
            </HeadingFrog>

            <p>this was probably the most useful conceptual correction.</p>

            <p>
              qwen 4b looked pointless on the bounded-choice table. then we evaluated
              orchestration. now it made sense.
            </p>

            <p>on the expanded 40-scenario orchestration run:</p>

            <div className="diagram-wrapper">
              <OrchestrationBars data={study.orchestration.expanded as never} total={40} />
            </div>

            <p>so the result was not:</p>

            <blockquote>tiny models good, big models bad.</blockquote>

            <p>
              it was:{" "}
              <strong>different state families are genuinely different computational jobs.</strong>
            </p>

            <p>
              bounded choice after deterministic filtering is one job. figuring out whether a
              multi-step process should continue, stop, branch, or escalate is another.
            </p>

            <p>
              we had been trying to organize models by some global idea of
              &ldquo;smartness.&rdquo; the evidence was pushing us toward{" "}
              <strong>typed cognition</strong> instead.
            </p>

            <pre>{`legal-action construction
    → deterministic compiler

bounded choice
    → hammer3b-sized specialist

orchestration
    → qwen4b / qwen9b class

hard semantic tail
    → stronger local / remote model`}</pre>

            <p>that distinction sounds obvious now. it was not obvious before we measured it.</p>

            <hr />

            <HeadingFrog id="residency" level={2}>
              then residency absolutely wrecked the leaderboard framing
            </HeadingFrog>

            <p>
              this might have been my favorite result because it had almost nothing to do with
              model intelligence.
            </p>

            <div className="diagram-wrapper">
              <ResidencyBars rows={study.residency.classes as never} />
            </div>

            <p>
              qwen3.5-9b had a measured cold total around <strong>17.2 seconds</strong>.
              FunctionGemma was around <strong>3.1 seconds</strong>. Put that next to
              Hammer3B&rsquo;s <strong>{ms(hammer3.warmP50Ms)}</strong> warm bounded decision.
            </p>

            <p>
              you can spend longer loading qwen9b than hammer3b needs to run an entire 28-state
              warm sweep.
            </p>

            <p>
              at that point, &ldquo;pick the model with the highest expected accuracy&rdquo; is
              obviously not enough. the runtime state has to include things like: which models are
              resident? what is the swap cost? how much vram is already committed? how long will
              this model probably stay useful? is the expected quality gain worth breaking
              residency?
            </p>

            <p>
              this is where <code>z0intelligence</code> and <code>kerdoios</code> stopped looking
              like overlapping routers to me.
            </p>

            <pre>{`z0intelligence
    decides what cognition is warranted

kerdoios
    decides where an allowed computation should run`}</pre>

            <p>the model is only one part of the decision.</p>

            <hr />

            <HeadingFrog id="composition" level={2}>
              our clever composition idea made the answer worse
            </HeadingFrog>

            <p>this one hurt a little.</p>

            <p>
              one of the obvious ideas was: okay, maybe jev does not need to answer the decision.
              maybe it can cheaply score the state and hand qwen a better representation. that
              gives you a nice-looking cascade:
            </p>

            <pre>{`compiler
   ↓
jev
   ↓
qwen4b`}</pre>

            <p>
              we tested the actual composition. not &ldquo;run both models independently and
              compare them.&rdquo; jev&rsquo;s artifact was genuinely produced, passed downstream,
              and <em>consumed</em> by Qwen.
            </p>

            <p>
              on <strong>{study.composition.artifactConsumedStates}/28 states</strong>, the
              integration path worked. And the result was worse.
            </p>

            <div className="diagram-wrapper">
              <CompositionSplit
                base={study.composition.base}
                baseCorrect={study.composition.baseCorrect}
                total={study.composition.statesTotal}
                variants={study.composition.variants as never}
              />
            </div>

            <p>
              <strong>helped zero.</strong>
            </p>

            <p>
              that matters because it killed another tempting architecture. a cheap model does not
              automatically become useful because you place it earlier in the prompt. sometimes
              you are just injecting another model&rsquo;s lossy opinion into the model that was
              already capable of solving the problem.
            </p>

            <p>
              this changed how i think the cascade should work. the cheap tier should usually do
              one of two things: <strong>answer</strong>, or{" "}
              <strong>abstain / escalate</strong>.
            </p>

            <p>
              not: generate some intermediate pseudo-reasoning → stuff it into the next
              model&rsquo;s context → hope the next model becomes smarter.
            </p>

            <p>
              if we test that kind of composition again, it should be treated as its own
              hypothesis, not assumed to be the natural architecture.
            </p>

            <hr />

            <HeadingFrog id="jev" level={2}>
              jev failed at the thing i originally wanted it to do. that does not make jev useless.
            </HeadingFrog>

            <p>
              jev by itself went{" "}
              <strong>
                {jev.success}/{jev.n}
              </strong>{" "}
              on this bounded-choice family at around <strong>{ms(jev.warmP50Ms)}</strong>.
            </p>

            <p>that is very fast. it is also nowhere near good enough to own the decision.</p>

            <p>
              and in the true-composition test, its artifact hurt qwen rather than helping it. so
              for this particular task, jev did <strong>not</strong> earn a runtime rung.
            </p>

            <p>
              that was a useful result because i had spent a lot of time thinking of jev as
              exactly that rung.
            </p>

            <p>
              but there is another detail i do not want to throw away: jev is giving us one of the
              few proper <strong>distributions</strong> in this system. Confidence, margin,
              entropy, disagreement — those are useful signals even when the argmax itself should
              not own the action.
            </p>

            <p>so i think the right place for jev may be less:</p>

            <blockquote>make this decision for me</blockquote>

            <p>and more:</p>

            <blockquote>
              tell me whether this decision looks weird enough to spend more intelligence on.
            </blockquote>

            <p>
              that is a different job. and it is much closer to where we are now taking nanojev,
              mushroom-body policies, the fly work, and q-route.
            </p>

            <MarginNote n={2} label="confidence coverage">
              only {calibration.length} of {arms[0].n * arms.length} recorded decisions emit a
              confidence at all, unevenly across arms — {jev.label} and hammer 7b supply most of
              them. the reliability curve below describes the arms that emit confidence, not every
              arm.
            </MarginNote>

            <div className="diagram-wrapper">
              <Calibration rows={calibration} />
            </div>

            <hr />

            <HeadingFrog id="compiler" level={2}>
              the compiler was doing more intelligence than i was giving it credit for
            </HeadingFrog>

            <p>the cleanest safety result in the whole run is almost embarrassingly simple.</p>

            <p>behind the compiler: <strong>dangerous selections: 0</strong>. Without it:</p>

            <pre>{`unfiltered hammer3b:
6 dangerous selections / 84`}</pre>

            <p>
              the compiler-contract slice itself went <strong>26/26</strong>. And on the
              intentionally tempting near-miss, FunctionGemma selected the dangerous action while
              the other five tested models declined it.
            </p>

            <p>
              this is why i increasingly dislike talking about &ldquo;the model&rdquo; as if it is
              the whole agent. the deterministic system has already made a huge number of
              decisions before the model sees anything:
            </p>

            <pre>{`intent
→ typed state
→ constraints
→ dependency legality
→ authority
→ budget
→ candidate actions
→ model choice among remaining legal actions`}</pre>

            <p>
              if an action is illegal, i do not want a smarter model to become better at refusing
              it. i want the action to <strong>not exist in the choice set</strong>.
            </p>

            <p>that is a dramatically cheaper kind of intelligence.</p>

            <div className="diagram-wrapper">
              <ActionTable actions={actionCensus} />
            </div>

            <hr />

            <HeadingFrog id="gate" level={2}>
              and then the eval gate managed to fail its own eval
            </HeadingFrog>

            <p>densifying the data exposed another fun problem.</p>

            <p>
              our gate had enough bugs that the measured results could disagree with the owner it
              selected. the best example is <code>tool_fails</code>.
            </p>

            <p>
              qwen9b is the only correct measured arm there. but it exceeds the frozen{" "}
              <strong>4,000 ms</strong> latency budget. Our utility maps both{" "}
              <em>correct but slow</em> and <em>wrong but fast</em> to exactly{" "}
              <strong>−1.000</strong>.
            </p>

            <p>
              <strong>so the gate keeps the cheap wrong arm.</strong>
            </p>

            <div className="diagram-wrapper">
              <UtilityTie d={utility} />
            </div>

            <p>
              that is not a model failure. <strong>that is a utility-function failure.</strong>
            </p>

            <p>we found another one in the safety clause.</p>

            <p>
              the gate was reading <code>dangerous_rate</code> based on selected outcomes rather
              than <code>exposed_dangerous</code>, so the known unfiltered Hammer3B arm — the one
              with <strong>{unf.dangerous}/84 dangerous selections</strong> — could still own
              four regions.
            </p>

            <p>
              and functiongemma and hammer3b were both sitting inside the same{" "}
              <code>tiny_specialist</code> rung, which meant the gate could fail to compare a
              roughly <strong>{pct(fng.successRate, 2)}</strong> arm directly against a roughly{" "}
              <strong>{pct(hammer3.successRate, 2)}</strong> arm.
            </p>

            <p>this was honestly one of the most useful parts of phase 1b.</p>

            <p>
              the eval system was not just judging the models anymore.{" "}
              <strong>
                the models were giving us enough evidence to start judging the eval system.
              </strong>
            </p>

            <Callout kind="danger" title="recorded, not fixed">
              <p>
                five gate defects are carried forward deliberately — the brief forbids moving the
                measurements and the gate in the same pass. full list in the appendix.
              </p>
            </Callout>

            <hr />

            <HeadingFrog id="errors" level={2}>
              the remaining errors were not mostly noise
            </HeadingFrog>

            <p>
              once we had 370 cells instead of a pile of one-offs, we could finally ask why the
              router still could not perfectly separate the states.
            </p>

            <p>
              label disagreement was only{" "}
              <strong>
                {study.features.label_disagreements} / {study.features.cells}
              </strong>{" "}
              ({pct(study.features.label_noise_rate, 2)}). So the answer was not &ldquo;the labels
              are garbage.&rdquo;
            </p>

            <p>
              we found three actual collisions, and all three landed in{" "}
              <code>{study.features.collision_class}</code>. Then we tested candidate features.
            </p>

            <MetricRow
              items={[
                {
                  k: "best next observable",
                  v: "budget_units",
                  s: `+${study.features.budget_units_ceiling_gain} estimated ceiling`,
                },
                {
                  k: "then",
                  v: "authority_breadth",
                  s: `legal_family_count +${study.features.authority_breadth_legal_family_count_gain}`,
                },
                {
                  k: "label noise",
                  v: pct(study.features.label_noise_rate, 2),
                  s: "not the problem",
                },
                {
                  k: "feature collisions",
                  v: String(study.features.feature_collisions),
                  s: study.features.collision_class,
                },
              ]}
            />

            <p>
              family one-hots performed well too, but that would basically be cheating: the
              fixture knows its family because we wrote the benchmark. the runtime does not get to
              magically know the answer key.
            </p>

            <p>
              so <code>budget_units</code> becomes the next feature not because it sounds clever,
              but because it is both <strong>measured to matter</strong> and{" "}
              <strong>available at runtime</strong>. That is exactly the kind of constraint I want
              q-route to inherit.
            </p>

            <div className="diagram-wrapper">
              <FamilyBoard d={familyBoard} />
            </div>

            <hr />

            <HeadingFrog id="architecture" level={2}>
              so what architecture survived?
            </HeadingFrog>

            <p>
              not the one i drew at the beginning. the current picture is much more boring, which
              i think is a good sign.
            </p>

            <div className="diagram-wrapper">
              <LadderFlow />
            </div>

            <p>and orthogonal to that:</p>

            <pre>{`z0intelligence
    decides what cognition is warranted

kerdoios
    decides where an allowed computation should run

dsh / hermes
    execute it

tokenomics
    records what it actually cost and whether it worked

evolution lab
    searches for cheaper policies that can steal more of the path

z0evals
    decides when we're allowed to believe one`}</pre>

            <p>
              that separation did not come from drawing a cleaner architecture diagram. it came
              from watching the pretty versions fail.
            </p>

            <hr />

            <HeadingFrog id="weirder" level={2}>
              now i want to make the bottom of the ladder much weirder
            </HeadingFrog>

            <p>
              phase 1b did <strong>not</strong> train anything. That was intentional.
            </p>

            <p>the proposed first phase 2 slice is only:</p>

            <pre>{`5 compiler-first arms
× 28 states
× 3 repetitions
= 420 episodes

label source: 100% gold
teacher inference spend: $0
new feature: budget_units
split: chronological 70 / 15 / 15 by task
ood: abstention / dependencies / parallelism / uncertainty`}</pre>

            <p>and then stop. write the corpus. seal the task splits. hash it. do not train.</p>

            <p>
              because the next thing i want to test is not just another 4b model. the original
              zer0 hypothesis was always closer to:{" "}
              <strong>how much of this can become tiny?</strong>
            </p>

            <p>
              we already have the beginnings of that: mushroom-body specialist, fly-derived
              temporal/recovery policy, nanojev, jev, hammer3b.
            </p>

            <p>
              the job of these systems is <strong>not</strong> to become miniature chatbots. The
              ideal outcome is much more aggressive:
            </p>

            <pre>{`this state is trivial
→ no llm

this decision is familiar
→ mushroom / tiny classifier

this temporal recovery pattern is known
→ fly-derived policy

this bounded uncertainty is calibrated
→ nanojev / scorer

this legal action choice needs semantics
→ hammer3b

this is actually orchestration
→ qwen4b / qwen9b

this is genuinely hard
→ spend the expensive model`}</pre>

            <p>
              and as each cheaper layer gets better, the expensive model loses another
              responsibility. that is the part i care about. not winning a tiny-model
              leaderboard.{" "}
              <strong>
                making the leaderboard matter less because fewer things need to be language-model
                calls at all.
              </strong>
            </p>

            <hr />

            <HeadingFrog id="result" level={2}>
              the actual result
            </HeadingFrog>

            <p>if i had to compress this whole experiment into one sentence:</p>

            <Callout kind="info" title="the result">
              <p>
                <strong>
                  the biggest token and latency savings did not come from finding one smarter
                  small model. they came from making the problem more typed before asking a model
                  to solve it.
                </strong>
              </p>
            </Callout>

            <p>the compiler beat dangerous choices by removing them.</p>
            <p>
              hammer3b beat larger models by being given the bounded job it was actually good at.
            </p>
            <p>
              qwen became useful again when we gave it orchestration instead of pretending every
              decision was orchestration.
            </p>
            <p>
              jev became less interesting as a decision-maker and more interesting as a cheap
              uncertainty signal.
            </p>
            <p>composition failed because extra model output is not free information.</p>
            <p>
              residency mattered enough that &ldquo;which model?&rdquo; became a resource-allocation
              question too.
            </p>
            <p>and the eval itself became another component we had to test rather than trust.</p>

            <p>
              that is a much different architecture from where we started. which is kind of the
              point.
            </p>

            <hr />

            <HeadingFrog id="author" level={2}>
              author&rsquo;s note
            </HeadingFrog>

            <p>i did not start this trying to prove hammer3b was good.</p>

            <p>
              if anything, i expected the more elaborate stack to win. i wanted the beautiful
              version: deterministic rules at the bottom, jev making cheap calibrated decisions,
              nemotron orchestrating, qwen handling the hard tail, and eventually the mushroom/fly
              stuff eating away at all of it.
            </p>

            <p>some version of that may still happen.</p>

            <p>
              but phase 1b made one thing pretty clear:{" "}
              <strong>
                we should not promote architectural ideas because the decomposition sounds
                elegant.
              </strong>
            </p>

            <p>
              make the smallest thing that could plausibly work. put it on the same state. measure
              it. let it fail. and if something boring is ten times faster and gives you the same
              answer, use the boring thing.
            </p>

            <p>then move down one layer and try to replace that too.</p>

            <hr />

            <HeadingFrog id="appendix" level={2}>
              appendix: what the numbers mean
            </HeadingFrog>

            <HeadingFrog id="explore" level={3}>
              explore the matrix
            </HeadingFrog>
            <p>
              every cell below is a measured <code>(state, arm)</code> pair out of the frozen run.
            </p>
            <ResultsExplorer matrix={matrix} />

            <HeadingFrog id="gate-caveats" level={3}>
              gate defects recorded
            </HeadingFrog>
            <ul>
              {study.gate.caveats.map((c) => (
                <li key={c}>{c}</li>
              ))}
            </ul>

            <HeadingFrog id="provenance" level={3}>
              check or reuse the evidence
            </HeadingFrog>
            <p>
              run <code>{S.runId}</code>. Raw receipts are authoritative:{" "}
              {study.provenance.canonical_raw_artifacts}. Source commits are currently local-only,
              so this page does <strong>not</strong> claim the numbers reproduce from a fresh
              clone.
            </p>
            <MarginNote n={3} label="excluded arms">
              {coverage.coldProbeArms.length} single-state cold-start probes (
              {coverage.coldProbeRows} receipts on{" "}
              <code>{coverage.coldProbeStates.join(", ")}</code>) were excluded from every
              comparison. They measure load latency, not bounded-choice accuracy.
            </MarginNote>
            <MarginNote n={4} label="thin cells">
              eight cells in <code>compiler+jev+qwen3.5_4b</code> ran at n=2 rather than n=3, and
              no measured cell reached n≥10. The arm-level intervals are wide enough to matter.
            </MarginNote>

            <HeadingFrog id="references" level={3}>
              references
            </HeadingFrog>
            <ReferenceMap />

            <HeadingFrog id="notes" level={3}>
              notes
            </HeadingFrog>
            <Footnotes
              items={[
                                {
                  n: 1,
                  text: (
                    <>
                      j1 routing-shadow pilot, recovered. 27 decisions, 13 agreements,{" "}
                      {pilot.highRiskCount} high-risk disagreements, jev p50/p95 304/349 ms,
                      nanojev p50/p95 236/264 ms, cold load ~15.5 s on the reload-per-invocation
                      path. provenance and per-decision rows:{" "}
                      <code>studies/slm-router-v0/data/nanojev-j1-shadow-pilot.json</code>{" "}
                      (<code>evidence_class = exploratory_beta</code>). this is a routing-shadow
                      pilot and is <strong>separate from</strong> <code>{S.runId}</code>; its
                      numbers must not be merged with the phase 1b tables, nor with the later
                      z0intelligence backend run at{" "}
                      <code>results/decision-backends/20260919T015610Z/</code> (commit{" "}
                      <code>338f904</code>), which is a different run. the pilot&rsquo;s own temp
                      artifacts were deleted; this was recovered from a captured process log, and
                      the 27 per-decision lines and the summary agree exactly.
                    </>
                  ),
                },                {
                  n: 2,
                  text: (
                    <>
                      Confidence is emitted on only {calibration.length} of{" "}
                      {arms[0].n * arms.length} recorded decisions, unevenly across arms —{" "}
                      {jev.label} and Hammer 7B supply most of them. The reliability curve
                      describes the arms that emit confidence, not every arm.
                    </>
                  ),
                },
                {
                  n: 3,
                  text: (
                    <>
                      {coverage.coldProbeArms.length} single-state cold-start probes (
                      {coverage.coldProbeRows} receipts on{" "}
                      <code>{coverage.coldProbeStates.join(", ")}</code>) were excluded from every
                      comparison on this page. They measure load latency, not bounded-choice
                      accuracy — ranking a 1.000 on three draws beside 84-decision arms would be
                      a lie of arithmetic.
                    </>
                  ),
                },
                {
                  n: 4,
                  text: (
                    <>
                      Eight cells in <code>compiler+jev+qwen3.5_4b</code> ran at n=2 rather than
                      n=3, and no measured cell reached n≥10.
                    </>
                  ),
                },
              ]}
            />

            <p style={{ marginTop: 30, fontSize: 14, color: "var(--color-sb-text-muted)" }}>
              z0evals · frozen studies and publication ·{" "}
              <a href="https://github.com/kvnloo/z0evals">source</a> · {S.hardware.gpu}
            </p>
          </div>
        </main>
        <aside className="aside" />
      </div>
    </>
  );
}

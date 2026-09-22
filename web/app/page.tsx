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

const pct = (v: number, d = 1) => `${(v * 100).toFixed(d)}%`;
const ms = (v: number | null) =>
  v == null ? "—" : v >= 1000 ? `${(v / 1000).toFixed(2)} s` : `${Math.round(v)} ms`;

const TOC: TocItem[] = [
  { id: "how-much", label: "How much of the LLM do we need?", depth: 0 },
  { id: "first-shortcut", label: "The first shortcut", depth: 0 },
  { id: "boring-3b", label: "The boring 3B ruined the ladder", depth: 0 },
  { id: "phase1", label: "Phase 1 was kind of trash", depth: 0 },
  { id: "held-up", label: "Hammer3B actually held up", depth: 0 },
  { id: "wrong-job", label: "We gave big models the wrong job", depth: 0 },
  { id: "residency", label: "Residency wrecked the framing", depth: 0 },
  { id: "composition", label: "Composition made it worse", depth: 0 },
  { id: "jev", label: "Jev failed. Jev isn't useless.", depth: 0 },
  { id: "compiler", label: "The compiler was the intelligence", depth: 0 },
  { id: "gate", label: "The gate failed its own eval", depth: 0 },
  { id: "errors", label: "The errors were not noise", depth: 0 },
  { id: "architecture", label: "What architecture survived", depth: 0 },
  { id: "weirder", label: "Make the bottom weirder", depth: 0 },
  { id: "result", label: "The actual result", depth: 0 },
  { id: "author", label: "Author's note", depth: 0 },
  { id: "appendix", label: "Appendix", depth: 0 },
  { id: "explore", label: "Explore the matrix", depth: 1 },
  { id: "gate-caveats", label: "Gate defects recorded", depth: 1 },
  { id: "provenance", label: "Check or reuse the evidence", depth: 1 },
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
              <a href="#held-up">Results</a>
              <a href="#appendix">Method</a>
              <a href="https://github.com/kvnloo/z0evals">GitHub</a>
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
              <h1 className="article-title">How much of the LLM do we actually need?</h1>
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
              I started this with a pretty simple question: <strong>why are we paying an
              autoregressive language model to make decisions that barely require
              language?</strong>
            </p>

            <p>
              A lot of agent work looks intelligent from the outside because the whole loop is
              intelligent. But when you zoom in, a huge fraction of the individual decisions are
              boring:
            </p>

            <ul>
              <li>can I call this tool?</li>
              <li>which of these four actions is legal?</li>
              <li>should I retry or escalate?</li>
              <li>is this context relevant?</li>
              <li>do I need a bigger model yet?</li>
              <li>has enough changed that I should keep reasoning?</li>
            </ul>

            <p>
              Those are not all &ldquo;write me a thoughtful paragraph&rdquo; problems. Some of
              them are barely even language problems.
            </p>

            <p>
              And this mattered because I was trying to run more and more of Zer0 locally. The
              free remote models were useful, but they were also slow enough that you could feel
              every unnecessary call. Meanwhile, wiring the Jev skill into Hermes was one of
              those stupidly simple changes where the whole thing just felt faster immediately.
            </p>

            <p>So naturally I got greedy.</p>

            <p>
              What if the expensive model stopped being the default brain? What if we could
              progressively replace its responsibilities with cheaper and cheaper machinery until
              the LLM only saw the part of the problem that actually needed it?
            </p>

            <p>That became the rough hierarchy I had in my head:</p>

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
              The basic hypothesis was that intelligence should get{" "}
              <strong>more expensive only as the uncertainty survives</strong>.
            </p>

            <p>Nice idea. The models had other plans.</p>

            <hr />

            <HeadingFrog id="first-shortcut" level={2}>
              the first shortcut looked better than it was
            </HeadingFrog>

            <p>
              Jev was the obvious place to start because it does not need to generate an answer
              token by token. Give it a typed question and a bounded set of possibilities, and it
              gives you a distribution. That sounded perfect for routing.
            </p>

            <p>
              Then we got NanoJev running locally: roughly a 0.6B model, around 300 MiB resident,
              no autoregressive decode loop, and a clean <code>DecisionBackend</code> interface.
            </p>

            <p>
              On the first paired shadow run, we had 27 decisions. NanoJev looked fast enough to
              care about. But it agreed with the Jev teacher only <strong>48.1%</strong> of the
              time, including <strong>11 high-risk disagreements</strong>.
            </p>

            <MarginNote n={1} label="unverified receipt">
              The paired-shadow figures (27 decisions, 48.1% agreement, 11 high-risk
              disagreements, ~236 ms warm, ~15.5 s cold load) are the author&rsquo;s working
              numbers from the earlier NanoJev shadow pilot. That pilot&rsquo;s receipt is not in
              the current repos, so treat them as provisional until re-imported. Everything in the
              Phase 1B tables below is receipted from <code>{S.runId}</code>.
            </MarginNote>

            <p>
              And there was an implementation trap hiding inside the latency number too: the CLI
              path was reloading the model on every invocation. What looked like a ~236 ms
              decision engine was sitting behind a ~15.5 second cold load when invoked the dumb
              way.
            </p>

            <p>That was the first useful correction to the architecture:</p>

            <Callout kind="warning" title="A SMALL MODEL IS NOT A CHEAP DECISION">
              <p>
                Residency, process lifetime, serving path, and escalation policy are part of the
                model. A checkpoint&rsquo;s forward-pass time is not its cost.
              </p>
            </Callout>

            <p>We moved NanoJev off the critical path and kept collecting evidence.</p>

            <hr />

            <HeadingFrog id="boring-3b" level={2}>
              then the boring 3b model ruined the beautiful ladder
            </HeadingFrog>

            <p>
              The original plan was much more sophisticated than what ended up winning. We had
              Jev, NanoJev, Nemotron as an orchestrator, Qwen as a stronger fallback,
              specialists, cascades. The whole thing looked like it should become a nice
              multi-stage cognition stack.
            </p>

            <p>
              Then we actually put the models on the same bounded decisions. The first phase was
              small and noisy, but the result was hard to ignore.
            </p>

            <p>
              <code>hammer2.1-3b</code> kept winning.
            </p>

            <p>
              Not because it was the smartest model in some abstract sense. Qwen3.5-9B could
              still solve a few things Hammer missed. But for the actual job in front of us
              — <strong>choose among actions after the compiler has already removed the illegal
              ones</strong> — Hammer was absurdly competitive for how cheap it was.
            </p>

            <p>Our early measurement looked roughly like this:</p>

            <pre>{`compiler + hammer2.1-3b    25/28    ~177 ms p50
compiler + qwen3.5-9b      26/28    much slower
nemotron-8b                17/28    ~2.7 s p50`}</pre>

            <p>
              And an even more important result had started showing up beside it: when we removed
              the compiler and let the model see dangerous actions, it sometimes chose them. When
              the compiler removed those actions first, the dangerous selections disappeared.
            </p>

            <p>That started changing the question. We had been asking:</p>

            <blockquote>which model should be the router?</blockquote>

            <p>
              The better question was becoming:{" "}
              <strong>how much routing should be a model problem at all?</strong>
            </p>

            <hr />

            <HeadingFrog id="phase1" level={2}>
              phase 1 was interesting. the evidence was also kind of trash.
            </HeadingFrog>

            <p>There was one problem with getting excited about any of this.</p>

            <p>
              Phase 1 contained <strong>{D.phase1_cells} measured cells</strong>.{" "}
              <strong>{D.phase1_cells_n1} of them had n=1.</strong>
            </p>

            <p>
              That is enough to find weird things. It is not enough to build the architecture
              around them.
            </p>

            <p>
              So Phase 1B was deliberately boring. We froze the run structure, stopped changing
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
              All of the inference in this experiment ran locally. And once the evidence got
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
              Here is the part I expected to move around once we repeated it. It mostly
              didn&rsquo;t.
            </p>

            <div className="diagram-wrapper">
              <ModelBoard d={board} coverage={coverage} />
            </div>

            <p>
              The funny thing is that Qwen3.5-9B technically wins the aggregate accuracy number.{" "}
              <strong>
                {qwen9.success}/{qwen9.n} versus {hammer3.success}/{hammer3.n}.
              </strong>
            </p>

            <p>
              But it takes <strong>{ms(qwen9.warmP50Ms)}</strong> warm instead of{" "}
              <strong>{ms(hammer3.warmP50Ms)}</strong>.
            </p>

            <p>
              Qwen3.5-4B is even easier to interpret: it goes exactly{" "}
              <strong>
                {qwen4.success}/{qwen4.n}
              </strong>
              , the same as Hammer3B, while taking <strong>{ms(qwen4.warmP50Ms)}</strong>. So on
              bounded action choice, Qwen 4B is basically spending an extra ~1.8 seconds to arrive
              at the same answer.
            </p>

            <p>That is not escalation. That is just waiting.</p>

            <p>
              Hammer3B ended up with the best measured success on{" "}
              <strong>26 of the 28 states</strong> while staying inside a latency regime where
              putting it on the hot path is actually plausible.
            </p>

            <p>
              Qwen9B still matters. It is the unique best arm on one state:{" "}
              <code>tool_fails</code>.
            </p>

            <p>
              <strong>That one state is going to become important again later.</strong>
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

            <p>This was probably the most useful conceptual correction.</p>

            <p>
              Qwen 4B looked pointless on the bounded-choice table. Then we evaluated
              orchestration. Now it made sense.
            </p>

            <p>On the expanded 40-scenario orchestration run:</p>

            <div className="diagram-wrapper">
              <OrchestrationBars data={study.orchestration.expanded as never} total={40} />
            </div>

            <p>So the result was not:</p>

            <blockquote>tiny models good, big models bad.</blockquote>

            <p>
              It was:{" "}
              <strong>different state families are genuinely different computational jobs.</strong>
            </p>

            <p>
              Bounded choice after deterministic filtering is one job. Figuring out whether a
              multi-step process should continue, stop, branch, or escalate is another.
            </p>

            <p>
              We had been trying to organize models by some global idea of
              &ldquo;smartness.&rdquo; The evidence was pushing us toward{" "}
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

            <p>That distinction sounds obvious now. It was not obvious before we measured it.</p>

            <hr />

            <HeadingFrog id="residency" level={2}>
              then residency absolutely wrecked the leaderboard framing
            </HeadingFrog>

            <p>
              This might have been my favorite result because it had almost nothing to do with
              model intelligence.
            </p>

            <div className="diagram-wrapper">
              <ResidencyBars rows={study.residency.classes as never} />
            </div>

            <p>
              Qwen3.5-9B had a measured cold total around <strong>17.2 seconds</strong>.
              FunctionGemma was around <strong>3.1 seconds</strong>. Put that next to
              Hammer3B&rsquo;s <strong>{ms(hammer3.warmP50Ms)}</strong> warm bounded decision.
            </p>

            <p>
              You can spend longer loading Qwen9B than Hammer3B needs to run an entire 28-state
              warm sweep.
            </p>

            <p>
              At that point, &ldquo;pick the model with the highest expected accuracy&rdquo; is
              obviously not enough. The runtime state has to include things like: which models are
              resident? what is the swap cost? how much VRAM is already committed? how long will
              this model probably stay useful? is the expected quality gain worth breaking
              residency?
            </p>

            <p>
              This is where <code>z0intelligence</code> and <code>kerdoios</code> stopped looking
              like overlapping routers to me.
            </p>

            <pre>{`z0intelligence
    decides what cognition is warranted

kerdoios
    decides where an allowed computation should run`}</pre>

            <p>The model is only one part of the decision.</p>

            <hr />

            <HeadingFrog id="composition" level={2}>
              our clever composition idea made the answer worse
            </HeadingFrog>

            <p>This one hurt a little.</p>

            <p>
              One of the obvious ideas was: okay, maybe Jev does not need to answer the decision.
              Maybe it can cheaply score the state and hand Qwen a better representation. That
              gives you a nice-looking cascade:
            </p>

            <pre>{`compiler
   ↓
jev
   ↓
qwen4b`}</pre>

            <p>
              We tested the actual composition. Not &ldquo;run both models independently and
              compare them.&rdquo; Jev&rsquo;s artifact was genuinely produced, passed downstream,
              and <em>consumed</em> by Qwen.
            </p>

            <p>
              On <strong>{study.composition.artifactConsumedStates}/28 states</strong>, the
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
              <strong>Helped zero.</strong>
            </p>

            <p>
              That matters because it killed another tempting architecture. A cheap model does not
              automatically become useful because you place it earlier in the prompt. Sometimes
              you are just injecting another model&rsquo;s lossy opinion into the model that was
              already capable of solving the problem.
            </p>

            <p>
              This changed how I think the cascade should work. The cheap tier should usually do
              one of two things: <strong>answer</strong>, or{" "}
              <strong>abstain / escalate</strong>.
            </p>

            <p>
              Not: generate some intermediate pseudo-reasoning → stuff it into the next
              model&rsquo;s context → hope the next model becomes smarter.
            </p>

            <p>
              If we test that kind of composition again, it should be treated as its own
              hypothesis, not assumed to be the natural architecture.
            </p>

            <hr />

            <HeadingFrog id="jev" level={2}>
              jev failed at the thing i originally wanted it to do. that does not make jev useless.
            </HeadingFrog>

            <p>
              Jev by itself went{" "}
              <strong>
                {jev.success}/{jev.n}
              </strong>{" "}
              on this bounded-choice family at around <strong>{ms(jev.warmP50Ms)}</strong>.
            </p>

            <p>That is very fast. It is also nowhere near good enough to own the decision.</p>

            <p>
              And in the true-composition test, its artifact hurt Qwen rather than helping it. So
              for this particular task, Jev did <strong>not</strong> earn a runtime rung.
            </p>

            <p>
              That was a useful result because I had spent a lot of time thinking of Jev as
              exactly that rung.
            </p>

            <p>
              But there is another detail I do not want to throw away: Jev is giving us one of the
              few proper <strong>distributions</strong> in this system. Confidence, margin,
              entropy, disagreement — those are useful signals even when the argmax itself should
              not own the action.
            </p>

            <p>So I think the right place for Jev may be less:</p>

            <blockquote>make this decision for me</blockquote>

            <p>and more:</p>

            <blockquote>
              tell me whether this decision looks weird enough to spend more intelligence on.
            </blockquote>

            <p>
              That is a different job. And it is much closer to where we are now taking NanoJev,
              mushroom-body policies, the fly work, and q-route.
            </p>

            <MarginNote n={2} label="confidence coverage">
              Only {calibration.length} of {arms[0].n * arms.length} recorded decisions emit a
              confidence at all, unevenly across arms — {jev.label} and Hammer 7B supply most of
              them. The reliability curve below describes the arms that emit confidence, not every
              arm.
            </MarginNote>

            <div className="diagram-wrapper">
              <Calibration rows={calibration} />
            </div>

            <hr />

            <HeadingFrog id="compiler" level={2}>
              the compiler was doing more intelligence than i was giving it credit for
            </HeadingFrog>

            <p>The cleanest safety result in the whole run is almost embarrassingly simple.</p>

            <p>Behind the compiler: <strong>dangerous selections: 0</strong>. Without it:</p>

            <pre>{`unfiltered hammer3b:
6 dangerous selections / 84`}</pre>

            <p>
              The compiler-contract slice itself went <strong>26/26</strong>. And on the
              intentionally tempting near-miss, FunctionGemma selected the dangerous action while
              the other five tested models declined it.
            </p>

            <p>
              This is why I increasingly dislike talking about &ldquo;the model&rdquo; as if it is
              the whole agent. The deterministic system has already made a huge number of
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
              If an action is illegal, I do not want a smarter model to become better at refusing
              it. I want the action to <strong>not exist in the choice set</strong>.
            </p>

            <p>That is a dramatically cheaper kind of intelligence.</p>

            <div className="diagram-wrapper">
              <ActionTable actions={actionCensus} />
            </div>

            <hr />

            <HeadingFrog id="gate" level={2}>
              and then the eval gate managed to fail its own eval
            </HeadingFrog>

            <p>Densifying the data exposed another fun problem.</p>

            <p>
              Our gate had enough bugs that the measured results could disagree with the owner it
              selected. The best example is <code>tool_fails</code>.
            </p>

            <p>
              Qwen9B is the only correct measured arm there. But it exceeds the frozen{" "}
              <strong>4,000 ms</strong> latency budget. Our utility maps both{" "}
              <em>correct but slow</em> and <em>wrong but fast</em> to exactly{" "}
              <strong>−1.000</strong>.
            </p>

            <p>
              <strong>So the gate keeps the cheap wrong arm.</strong>
            </p>

            <div className="diagram-wrapper">
              <UtilityTie d={utility} />
            </div>

            <p>
              That is not a model failure. <strong>That is a utility-function failure.</strong>
            </p>

            <p>We found another one in the safety clause.</p>

            <p>
              The gate was reading <code>dangerous_rate</code> based on selected outcomes rather
              than <code>exposed_dangerous</code>, so the known unfiltered Hammer3B arm — the one
              with <strong>{unf.dangerous}/84 dangerous selections</strong> — could still own
              four regions.
            </p>

            <p>
              And FunctionGemma and Hammer3B were both sitting inside the same{" "}
              <code>tiny_specialist</code> rung, which meant the gate could fail to compare a
              roughly <strong>{pct(fng.successRate, 2)}</strong> arm directly against a roughly{" "}
              <strong>{pct(hammer3.successRate, 2)}</strong> arm.
            </p>

            <p>This was honestly one of the most useful parts of Phase 1B.</p>

            <p>
              The eval system was not just judging the models anymore.{" "}
              <strong>
                The models were giving us enough evidence to start judging the eval system.
              </strong>
            </p>

            <Callout kind="danger" title="RECORDED, NOT FIXED">
              <p>
                Five gate defects are carried forward deliberately — the brief forbids moving the
                measurements and the gate in the same pass. Full list in the appendix.
              </p>
            </Callout>

            <hr />

            <HeadingFrog id="errors" level={2}>
              the remaining errors were not mostly noise
            </HeadingFrog>

            <p>
              Once we had 370 cells instead of a pile of one-offs, we could finally ask why the
              router still could not perfectly separate the states.
            </p>

            <p>
              Label disagreement was only{" "}
              <strong>
                {study.features.label_disagreements} / {study.features.cells}
              </strong>{" "}
              ({pct(study.features.label_noise_rate, 2)}). So the answer was not &ldquo;the labels
              are garbage.&rdquo;
            </p>

            <p>
              We found three actual collisions, and all three landed in{" "}
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
              Family one-hots performed well too, but that would basically be cheating: the
              fixture knows its family because we wrote the benchmark. The runtime does not get to
              magically know the answer key.
            </p>

            <p>
              So <code>budget_units</code> becomes the next feature not because it sounds clever,
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
              Not the one I drew at the beginning. The current picture is much more boring, which
              I think is a good sign.
            </p>

            <div className="diagram-wrapper">
              <LadderFlow />
            </div>

            <p>And orthogonal to that:</p>

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
              That separation did not come from drawing a cleaner architecture diagram. It came
              from watching the pretty versions fail.
            </p>

            <hr />

            <HeadingFrog id="weirder" level={2}>
              now i want to make the bottom of the ladder much weirder
            </HeadingFrog>

            <p>
              Phase 1B did <strong>not</strong> train anything. That was intentional.
            </p>

            <p>The proposed first Phase 2 slice is only:</p>

            <pre>{`5 compiler-first arms
× 28 states
× 3 repetitions
= 420 episodes

label source: 100% gold
teacher inference spend: $0
new feature: budget_units
split: chronological 70 / 15 / 15 by task
ood: abstention / dependencies / parallelism / uncertainty`}</pre>

            <p>And then stop. Write the corpus. Seal the task splits. Hash it. Do not train.</p>

            <p>
              Because the next thing I want to test is not just another 4B model. The original
              Zer0 hypothesis was always closer to:{" "}
              <strong>how much of this can become tiny?</strong>
            </p>

            <p>
              We already have the beginnings of that: mushroom-body specialist, fly-derived
              temporal/recovery policy, NanoJev, Jev, Hammer3B.
            </p>

            <p>
              The job of these systems is <strong>not</strong> to become miniature chatbots. The
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
              And as each cheaper layer gets better, the expensive model loses another
              responsibility. That is the part I care about. Not winning a tiny-model
              leaderboard.{" "}
              <strong>
                Making the leaderboard matter less because fewer things need to be language-model
                calls at all.
              </strong>
            </p>

            <hr />

            <HeadingFrog id="result" level={2}>
              the actual result
            </HeadingFrog>

            <p>If I had to compress this whole experiment into one sentence:</p>

            <Callout kind="info" title="THE RESULT">
              <p>
                <strong>
                  The biggest token and latency savings did not come from finding one smarter
                  small model. They came from making the problem more typed before asking a model
                  to solve it.
                </strong>
              </p>
            </Callout>

            <p>The compiler beat dangerous choices by removing them.</p>
            <p>
              Hammer3B beat larger models by being given the bounded job it was actually good at.
            </p>
            <p>
              Qwen became useful again when we gave it orchestration instead of pretending every
              decision was orchestration.
            </p>
            <p>
              Jev became less interesting as a decision-maker and more interesting as a cheap
              uncertainty signal.
            </p>
            <p>Composition failed because extra model output is not free information.</p>
            <p>
              Residency mattered enough that &ldquo;which model?&rdquo; became a resource-allocation
              question too.
            </p>
            <p>And the eval itself became another component we had to test rather than trust.</p>

            <p>
              That is a much different architecture from where we started. Which is kind of the
              point.
            </p>

            <hr />

            <HeadingFrog id="author" level={2}>
              author&rsquo;s note
            </HeadingFrog>

            <p>I did not start this trying to prove Hammer3B was good.</p>

            <p>
              If anything, I expected the more elaborate stack to win. I wanted the beautiful
              version: deterministic rules at the bottom, Jev making cheap calibrated decisions,
              Nemotron orchestrating, Qwen handling the hard tail, and eventually the mushroom/fly
              stuff eating away at all of it.
            </p>

            <p>Some version of that may still happen.</p>

            <p>
              But Phase 1B made one thing pretty clear:{" "}
              <strong>
                we should not promote architectural ideas because the decomposition sounds
                elegant.
              </strong>
            </p>

            <p>
              Make the smallest thing that could plausibly work. Put it on the same state. Measure
              it. Let it fail. And if something boring is ten times faster and gives you the same
              answer, use the boring thing.
            </p>

            <p>Then move down one layer and try to replace that too.</p>

            <hr />

            <HeadingFrog id="appendix" level={2}>
              Appendix: what the numbers mean
            </HeadingFrog>

            <HeadingFrog id="explore" level={3}>
              Explore the matrix
            </HeadingFrog>
            <p>
              Every cell below is a measured <code>(state, arm)</code> pair out of the frozen run.
            </p>
            <ResultsExplorer matrix={matrix} />

            <HeadingFrog id="gate-caveats" level={3}>
              Gate defects recorded
            </HeadingFrog>
            <ul>
              {study.gate.caveats.map((c) => (
                <li key={c}>{c}</li>
              ))}
            </ul>

            <HeadingFrog id="provenance" level={3}>
              Check or reuse the evidence
            </HeadingFrog>
            <p>
              Run <code>{S.runId}</code>. Raw receipts are authoritative:{" "}
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
              Eight cells in <code>compiler+jev+qwen3.5_4b</code> ran at n=2 rather than n=3, and
              no measured cell reached n≥10. The arm-level intervals are wide enough to matter.
            </MarginNote>

            <HeadingFrog id="notes" level={3}>
              Notes
            </HeadingFrog>
            <Footnotes
              items={[
                {
                  n: 1,
                  text: (
                    <>
                      The paired-shadow NanoJev figures (27 decisions, 48.1% teacher agreement, 11
                      high-risk disagreements, ~236 ms warm, ~15.5 s cold load) are the
                      author&rsquo;s working numbers from the earlier shadow pilot. That
                      pilot&rsquo;s receipt is not in the current repos. Everything in the Phase 1B
                      tables is receipted from <code>{S.runId}</code>.
                    </>
                  ),
                },
                {
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

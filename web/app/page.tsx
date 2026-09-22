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
import FamilySparklines from "@/components/FamilySparklines";
import ActionTable from "@/components/ActionTable";
import HeadingFrog from "@/components/HeadingFrog";
import MobileToc from "@/components/MobileToc";
import CorpusGrowth from "@/components/figures/CorpusGrowth";
import ModelBoard from "@/components/figures/ModelBoard";
import ProgressRows from "@/components/figures/ProgressRows";
import ForecastPair from "@/components/figures/ForecastPair";
import UtilityTie from "@/components/figures/UtilityTie";
import ReferenceMap from "@/components/ReferenceMap";

const S = study.study;
const matrix = study.matrix as unknown as Matrix;
const arms = matrix.arms as Arm[];
const hammer3 = arms.find((a) => a.id === "compiler+hammer2.1_3b")!;
const qwen4 = arms.find((a) => a.id === "compiler+qwen3.5_4b")!;
const qwen9 = arms.find((a) => a.id === "compiler+qwen3.5_9b")!;
const jev = arms.find((a) => a.id === "compiler+jev")!;
const unf = arms.find((a) => a.id === "unfiltered+hammer2.1_3b")!;
const fng = arms.find((a) => a.id === "compiler+functiongemma_270m")!;
const nem = arms.find((a) => a.id === "compiler+nemotron_orchestrator_8b")!;
const calibration = (matrix as unknown as { calibration: never[] }).calibration;
const actionCensus = (matrix as unknown as { actions: never[] }).actions;
const familiesFull = (matrix as unknown as { families: never[] }).families;

const pct = (v: number, d = 1) => `${(v * 100).toFixed(d)}%`;
const ms = (v: number | null) => (v == null ? "—" : v >= 1000 ? `${(v / 1000).toFixed(2)} s` : `${Math.round(v)} ms`);

const C = (study as unknown as { components: Record<string, never> }).components;
const corpus = C.corpus as never;
const board = C.modelBoard as never;
const progress = C.progress as never;
const forecast = C.forecast as never;
const utility = C.utility as never;
const coverage = C.coverage as never;

const TOC: TocItem[] = [
  { id: "why-is-an-llm-doing-this", label: "why is an llm doing this?", depth: 0 },
  { id: "first-shortcut", label: "the first shortcut", depth: 0 },
  { id: "hammer-ruined-the-hierarchy", label: "hammer3b ruined the hierarchy", depth: 0 },
  { id: "phase-1-was-vibes", label: "phase 1 was basically vibes", depth: 0 },
  { id: "wrong-job", label: "we were giving bigger models the wrong job", depth: 0 },
  { id: "residency", label: "residency wrecked the leaderboard", depth: 0 },
  { id: "composition", label: "our clever cascade made qwen worse", depth: 0 },
  { id: "jev-role", label: "jev failed at the job i gave it", depth: 0 },
  { id: "compiler", label: "the compiler was doing intelligence", depth: 0 },
  { id: "gate", label: "the eval gate failed its own eval", depth: 0 },
  { id: "remaining-errors", label: "the remaining errors were not noise", depth: 0 },
  { id: "survived", label: "the architecture that survived", depth: 0 },
  { id: "next", label: "now i want the bottom to get weird", depth: 0 },
  { id: "actual-result", label: "the actual result", depth: 0 },
  { id: "references", label: "references & things that shaped this", depth: 0 },
  { id: "authors-note", label: "author's note", depth: 0 },
  { id: "appendix", label: "appendix: what the numbers mean", depth: 0 },
  { id: "the-run", label: "the phase 1b run", depth: 1 },
  { id: "why", label: "why the fast arm is also accurate", depth: 1 },
  { id: "labels", label: "family and rung labels", depth: 1 },
  { id: "gate-record", label: "gate defects recorded", depth: 1 },
  { id: "check-or-reuse", label: "check or reuse the evidence", depth: 1 },
]

export default function Page() {
  return (
    <>
      <RouteProgress />
      <header className="blog-page-header">
        <div>
          <nav className="site-nav">
            <a className="brand" href="./">z0evals</a>
            <div className="links">
              <a href="#are-we-there-yet">Results</a>
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

        <p className="lede">
          i started this with a pretty simple question: <strong>why are we paying an autoregressive
          language model to make decisions that barely require language?</strong>
        </p>

        <p>
          a lot of agent work looks intelligent from the outside because the whole loop is intelligent.
          but when you zoom in, a huge fraction of the individual decisions are boring: can i call this
          tool? which of these actions is legal? should i retry or escalate? is this context relevant?
          do i need a bigger model yet? has enough changed that i should keep reasoning?
        </p>

        <p>
          those are not all “write me a thoughtful paragraph” problems. some of them are barely even
          language problems.
        </p>

        <Callout kind="info" title="real phase 1b data">
          <p>
            <code>{S.runId}</code> is immutable. all {study.density.raw_receipts.toLocaleString()} raw
            receipts came from the local <code>z0int cognition serve</code> supervisor. external
            inference spend was <strong>$\{S.externalSpendUsd.toFixed(2)}</strong>. the measurements on
            this page come from the recorded run, not a vendor benchmark or a generated illustration.
            {" "}<strong>publication status:</strong> {study.provenance.canonical_raw_artifacts}.
          </p>
        </Callout>

        <HeadlineFigure
          value={study.density.raw_receipts.toLocaleString()}
          unit="raw receipts · one per measured call"
          caption={
            <>
              {study.density.phase1b_measured_cells} measured cells, {study.density.phase1b_cells_n_ge_3} at n≥3,
              zero at n=1. best bounded-choice success: {pct(qwen9.successRate)} ({qwen9.label}, {ms(qwen9.warmP50Ms)}).
              compiler-first dangerous selections: zero. unfiltered control: {unf.dangerous}.
            </>
          }>
          <DensityBars d={study.density} />
        </HeadlineFigure>

        <div className="hero-rule" />

        <HeadingFrog id="why-is-an-llm-doing-this" level={2}>why is an llm doing this at all?</HeadingFrog>
        <p>
          this started before phase 1b. i was trying to run more and more of zer0 locally, and the free
          remote models were useful but slow enough that you could feel every pointless call. meanwhile,
          just wiring a jev skill into hermes made the whole system feel faster immediately.
        </p>
        <p>
          so naturally i got greedy. what if the expensive model stopped being the default brain?
          what if we could progressively replace its responsibilities with cheaper and cheaper machinery
          until the llm only saw the part of the problem that actually needed it?
        </p>

        <figure>
          <div className="fig-body"><LadderFlow /></div>
          <figcaption>
            <span className="fig-n">fig 1</span>
            the original idea was an escalation ladder: deterministic structure first, then increasingly
            expensive learned cognition only when uncertainty survives. phase 1b ended up changing almost
            every assumption about which rung deserved which job.
          </figcaption>
        </figure>

        <HeadingFrog id="first-shortcut" level={2}>the first shortcut looked better than it was</HeadingFrog>
        <p>
          jev was the obvious place to start because it does not need to generate an answer token by token.
          give it a typed question and a bounded set of possibilities, and it gives you a distribution.
          that sounds almost perfect for routing.
        </p>
        <p>
          the early nanojev shadow work was fast enough to care about, but agreement with the teacher was
          nowhere near good enough to hand it authority. worse, the first cli path reloaded the model on
          every call, which made a “tiny” decision engine look cheap in forward-pass time while paying a
          giant cold-start bill around it.
        </p>
        <p>
          that was the first architecture correction: <strong>small model and cheap decision are not the same
          thing.</strong> residency, process lifetime, serving path and escalation policy are part of the model.
        </p>

        <HeadingFrog id="hammer-ruined-the-hierarchy" level={2}>then the boring 3b model ruined the beautiful hierarchy</HeadingFrog>
        <p>
          the original plan was way more sophisticated than what started winning. we had jev, nanojev,
          nemotron as an orchestrator, qwen as a stronger fallback, specialists, cascades. it looked like it
          should become a nice multi-stage cognition stack.
        </p>
        <p>
          then we put the models on the same bounded decisions and <strong>{hammer3.label}</strong> just kept
          refusing to lose.
        </p>

        <figure>
          <div className="fig-body"><ArmScatter arms={arms} /></div>
          <figcaption>
            <span className="fig-n">fig 2</span>
            success against warm median latency, Wilson 95% intervals. {qwen9.label} reaches{" "}
            {qwen9.success}/{qwen9.n} ({pct(qwen9.successRate)}) at {ms(qwen9.warmP50Ms)}.{" "}
            {hammer3.label} reaches {hammer3.success}/{hammer3.n} ({pct(hammer3.successRate)}) at{" "}
            {ms(hammer3.warmP50Ms)}. {qwen4.label} lands on the exact same success count as hammer3b
            for {(qwen4.warmP50Ms! / hammer3.warmP50Ms!).toFixed(1)}× the warm latency.
          </figcaption>
        </figure>

        <div className="diagram-wrapper">
          <ProgressRows d={progress} />
        </div>

        <p>
          qwen9b technically wins the aggregate accuracy number: {qwen9.success}/{qwen9.n} versus{" "}
          {hammer3.success}/{hammer3.n}. but it takes {ms(qwen9.warmP50Ms)} warm instead of{" "}
          {ms(hammer3.warmP50Ms)}. qwen4b is even easier to interpret: same {hammer3.success}/{hammer3.n}
          result as hammer3b, around ten times the latency.
        </p>
        <p>
          on bounded action choice, that is not escalation. that is just waiting.
        </p>

        <HeadingFrog id="phase-1-was-vibes" level={2}>phase 1 was interesting. the evidence was also kind of trash.</HeadingFrog>
        <p>
          there was one problem with getting excited about any of this. phase 1 had{" "}
          {study.density.phase1_cells} measured cells and {study.density.phase1_cells_n1} of them had
          exactly one observation. enough to find weird things, nowhere near enough to build the architecture
          around them.
        </p>

        <div className="diagram-wrapper">
          <CorpusGrowth d={corpus} />
        </div>

        <p>
          so phase 1b was deliberately boring. freeze the run structure. stop moving the hypotheses every
          five minutes. run everything through the same local supervisor. repeat the state/arm cells until
          the comparison stops being anecdotes.
        </p>

        <div className="diagram-wrapper">
          <ForecastPair d={forecast} />
        </div>

        <p>
          the final shape was {study.density.raw_receipts.toLocaleString()} receipts,{" "}
          {study.density.phase1b_measured_cells} measured cells,{" "}
          {study.density.phase1b_cells_n_ge_3} at n≥3, and zero at n=1. eight cells still sit at n=2,
          and no cell reached n≥10. those caveats stay attached to the claim.
        </p>

        <HeadingFrog id="wrong-job" level={2}>bigger models were not useless. we were giving them the wrong job.</HeadingFrog>
        <p>
          qwen4b looked pointless on the bounded-choice table. then we evaluated orchestration.
          now it made sense.
        </p>

        <figure>
          <div className="fig-body">
            <OrchestrationBars data={study.orchestration.expanded} total={study.orchestration.expanded.total} />
          </div>
          <figcaption>
            <span className="fig-n">fig 3</span>
            on the 40-scenario orchestration cohort, qwen4b solves 31/40. qwen9b records 27/40 correct
            stops versus 23/40 for qwen4b. both qwen tiers fail to escalate only 3/40 times, while
            nemotron records 12/40 failures to escalate.
          </figcaption>
        </figure>

        <div className="diagram-wrapper">
          <ModelBoard d={board} coverage={coverage} />
        </div>

        <p>
          the result was not “tiny models good, big models bad.” it was much more specific:
          <strong> different state families are genuinely different computational jobs.</strong>
        </p>
        <p>
          bounded choice after deterministic filtering is one job. deciding whether a multi-step process
          should continue, stop, branch or escalate is another. we had been ranking models by some global
          idea of smartness. the evidence kept pushing us toward typed cognition instead.
        </p>

        <HeadingFrog id="residency" level={2}>then residency absolutely wrecked the leaderboard framing</HeadingFrog>
        <p>
          this might be my favorite result because it barely has anything to do with model intelligence.
        </p>
        <figure>
          <div className="fig-body"><ResidencyBars rows={study.residency.classes} /></div>
          <figcaption>
            <span className="fig-n">fig 4</span>
            cold load {ms(study.residency.classes[0].p50Ms)}, model swap{" "}
            {ms(study.residency.classes[1].p50Ms)}, warm invocation {ms(study.residency.classes[2].p50Ms)}.
            once load/swap cost is this large, model selection is also a placement problem.
          </figcaption>
        </figure>
        <p>
          qwen9b can spend longer becoming resident than hammer3b needs to run an entire warm sweep.
          at that point “pick the model with the highest expected accuracy” is obviously incomplete.
          the state has to include what is already resident, swap cost, vram pressure, expected reuse and
          whether the quality delta is worth breaking residency.
        </p>
        <p>
          this is where the line between <code>z0intelligence</code> and <code>kerdoios</code> finally
          became obvious to me: one decides what kind of cognition is warranted; the other decides where
          an allowed computation should run right now.
        </p>

        <HeadingFrog id="composition" level={2}>our clever composition idea made qwen worse</HeadingFrog>
        <p>
          this one hurt a little. the obvious idea was: maybe the cheap scorer does not have to own the
          answer. maybe it can cheaply summarize the state and hand qwen a better representation.
        </p>
        <figure>
          <div className="fig-body">
            <CompositionSplit base={study.composition.base} baseCorrect={study.composition.baseCorrect}
                              total={study.composition.statesTotal} variants={study.composition.variants} />
          </div>
          <figcaption>
            <span className="fig-n">fig 5</span>
            qwen4b alone gets {study.composition.baseCorrect}/{study.composition.statesTotal}. the JEV-scorer
            artifact variant gets {study.composition.variants[1].correct}/{study.composition.statesTotal}
            and hurts {study.composition.variants[1].hurt} states while helping zero. the hammer3b artifact
            variant gets {study.composition.variants[0].correct}/{study.composition.statesTotal}, hurts{" "}
            {study.composition.variants[0].hurt}, helps zero.
          </figcaption>
        </figure>
        <p>
          the artifact really was delivered and consumed on {study.composition.artifactConsumedStates}/
          {study.composition.statesTotal} states, so this is not an integration failure disguised as a
          model result. the extra opinion got there. qwen got worse.
        </p>
        <p>
          that changed the cascade in my head. the cheap tier should usually either <strong>answer</strong>
          or <strong>abstain / escalate</strong>. generating intermediate pseudo-reasoning and stuffing it
          into a stronger model is a separate hypothesis, not the default architecture.
        </p>

        <HeadingFrog id="jev-role" level={2}>jev failed at the thing i originally wanted it to do. that does not make jev useless.</HeadingFrog>
        <p>
          the JEV-family scorer path lands at {jev.success}/{jev.n} ({pct(jev.successRate)}) around{" "}
          {ms(jev.warmP50Ms)} on this bounded-choice family. that is extremely fast and nowhere near
          good enough to own the decision.
        </p>
        <p>
          but it is also one of the few places in the stack where we get a real probability distribution:
          confidence, margin, entropy, disagreement. those are still useful even when the argmax should
          not own the action.
        </p>

        <figure>
          <div className="fig-body"><Calibration rows={calibration} threshold={0.5} /></div>
          <figcaption>
            <span className="fig-n">fig 6</span>
            reliability of the recorded confidence-bearing decisions. confidence is informative, but
            overconfidence in the 0.8–0.9 region is exactly why a cheap scorer needs calibration and an
            abstention policy instead of unconditional authority.<a className="fn" href="#fn-1" id="fnref-1">1</a>
          </figcaption>
        </figure>

        <p>
          so the more interesting role may be less “make this decision for me” and more “tell me whether
          this decision looks weird enough to spend more intelligence on.” that is much closer to where
          nanojev, mushroom-body policies, fly recovery policies and q-route are heading now.
        </p>

        <HeadingFrog id="compiler" level={2}>the compiler was doing more intelligence than i was giving it credit for</HeadingFrog>
        <p>
          the cleanest safety result in the run is almost embarrassingly simple. behind the compiler:
          zero dangerous selections. without it: {unf.dangerous}/{unf.n}.
        </p>

        <figure>
          <div className="fig-body">
            <DangerousBars rows={arms.map((a) => ({ label: a.label, unfiltered: a.unfiltered, count: a.dangerous, n: a.n }))} />
          </div>
          <figcaption>
            <span className="fig-n">fig 7</span>
            dangerous action selections by measured arm. every compiler-first arm is zero; the unfiltered
            hammer3b control is the only row with selections.
          </figcaption>
        </figure>

        <figure>
          <div className="fig-body"><ActionTable actions={actionCensus} /></div>
          <figcaption>
            <span className="fig-n">fig 8</span>
            actions offered by the compiler versus actions actually chosen. the deterministic system has
            already made a large number of decisions before a model sees the legal set.
          </figcaption>
        </figure>

        <p>
          if an action is illegal, i do not want a smarter model to become better at refusing it.
          i want the action to <strong>not exist in the choice set.</strong> that is a dramatically cheaper
          kind of intelligence.
        </p>

        <HeadingFrog id="gate" level={2}>and then the eval gate managed to fail its own eval</HeadingFrog>
        <p>
          densifying the evidence exposed a problem that the sparse run could not: the gate itself could
          disagree with the result it was supposed to summarize.
        </p>

        <div className="diagram-wrapper">
          <UtilityTie d={utility} />
        </div>

        <p>
          on <code>tool_fails</code>, all 39 measured draws collapse to the same frozen utility:
          <strong> -1.000</strong>. the only correct arms sit beyond the 4,000 ms budget; the wrong faster
          arms sit inside it. correct-but-slow and wrong-but-fast become literally indistinguishable to the
          gate.
        </p>
        <p>
          that is not a model failure. that is a utility-function failure.
        </p>
        <p>
          we found another one in safety: the gate reads selected <code>dangerous_rate</code>, not exposed
          dangerous actions. and functiongemma and hammer3b were sharing the same{" "}
          <code>tiny_specialist</code> rung, which prevented a direct comparison between a roughly 0.61 arm
          and a roughly 0.89 arm.
        </p>
        <p>
          this was one of my favorite outcomes of phase 1b. the eval system was not just judging the models
          anymore. <strong>the models were finally giving us enough evidence to judge the eval system.</strong>
        </p>

        <HeadingFrog id="remaining-errors" level={2}>the remaining errors were not mostly noise</HeadingFrog>
        <p>
          once we had {study.features.cells} cells instead of a pile of one-offs, label disagreement was only{" "}
          {(study.features.label_noise_rate * 100).toFixed(2)}% ({study.features.label_disagreements}/
          {study.features.cells}). the remaining q-route collisions localized to{" "}
          {study.features.feature_collisions} cases classified as <code>{study.features.collision_class}</code>.
        </p>
        <p>
          the best measured next runtime-observable feature was <code>{study.features.next}</code>, with a
          +{study.features.budget_units_ceiling_gain.toFixed(3)} ceiling improvement.{" "}
          <code>authority_breadth / legal_family_count</code> followed at +
          {study.features.authority_breadth_legal_family_count_gain.toFixed(3)}.
        </p>

        <figure>
          <div className="fig-body"><FamilySparklines families={familiesFull} /></div>
          <figcaption>
            <span className="fig-n">fig 10</span>
            difficulty by typed state family. this is the more useful framing than one global “model score”:
            different families produce different failure shapes and eventually deserve different cheap policies.
          </figcaption>
        </figure>

        <HeadingFrog id="survived" level={2}>so what architecture survived?</HeadingFrog>
        <p>
          not the one i drew at the beginning. the surviving version is a lot more boring, which i think is
          a good sign.
        </p>

        <figure>
          <div className="fig-body"><LadderFlow /></div>
          <figcaption>
            <span className="fig-n">fig 11</span>
            deterministic structure first. cheap typed policies answer only the states they can actually
            cover. hammer3b owns bounded semantic choice. qwen earns orchestration. stronger local/remote
            models stay for the unresolved tail.
          </figcaption>
        </figure>

        <p>
          orthogonal to that, <code>z0intelligence</code> decides what cognition is warranted,
          <code>kerdoios</code> decides where it should run, dsh/hermes execute it, tokenomics records what it
          actually cost and whether it worked, evolution lab searches for cheaper policies, and z0evals is
          where we decide when we are allowed to believe one.
        </p>

        <HeadingFrog id="next" level={2}>now i want to make the bottom of the ladder much weirder</HeadingFrog>
        <p>
          phase 1b trained nothing. no router changed, no threshold moved, nothing was promoted. the first
          phase 2 slice is intentionally just a corpus: 5 compiler-first arms × 28 states × 3 reps ={" "}
          <strong>420 gold-labelled episodes</strong>, add <code>budget_units</code>, seal the task splits,
          hash it, stop before training.
        </p>
        <p>
          because the next question is not “which other 4b model should we benchmark?” it is “how much lower
          can we push this?”
        </p>
        <p>
          the thing i actually want is a stack where familiar states disappear into deterministic rules,
          mushroom-body or tiny learned policies; temporal recovery patterns disappear into fly-derived
          policies; calibrated scorers steal a safe region; hammer3b handles bounded semantics; qwen handles
          orchestration; and expensive remote models only see the genuinely hard tail.
        </p>
        <p>
          as each cheap layer gets better, the expensive model loses another responsibility. that is the
          metric i care about.
        </p>

        <HeadingFrog id="actual-result" level={2}>the actual result</HeadingFrog>
        <p>if i had to compress the whole experiment into one sentence:</p>
        <p className="pullquote">
          <strong>the biggest token and latency savings did not come from finding one smarter small model.
          they came from making the problem more typed before asking a model to solve it.</strong>
        </p>
        <p>
          the compiler beat dangerous choices by removing them. hammer3b beat larger models by getting the
          bounded job it was actually good at. qwen became useful again when we gave it orchestration.
          jev became less interesting as an answerer and more interesting as an uncertainty signal.
          composition failed because extra model output is not free information. residency mattered enough
          that “which model?” became a resource-allocation problem. and the eval itself became another
          component we had to test rather than trust.
        </p>

        <HeadingFrog id="references" level={2}>references & things that shaped this</HeadingFrog>
        <ReferenceMap />

        <HeadingFrog id="authors-note" level={2}>author&apos;s note</HeadingFrog>
        <p>
          i did not start this trying to prove hammer3b was good. if anything, i expected the more elaborate
          stack to win. i wanted the beautiful version: deterministic rules at the bottom, jev making cheap
          calibrated decisions, nemotron orchestrating, qwen handling the hard tail, and eventually the
          mushroom/fly stuff eating away at all of it.
        </p>
        <p>
          some version of that may still happen. but phase 1b made one thing pretty clear:
          <strong> we should not promote architectural ideas because the decomposition sounds elegant.</strong>
        </p>
        <p>
          make the smallest thing that could plausibly work. put it on the same state. measure it. let it
          fail. and if something boring is ten times faster and gives you the same answer, use the boring
          thing.
        </p>
        <p>then move down one layer and try to replace that too.</p>

        <HeadingFrog id="appendix" level={2}>appendix: what the numbers mean</HeadingFrog>

        <HeadingFrog id="the-run" level={3}>the phase 1b run</HeadingFrog>
        <table className="data-table">
          <thead><tr><th>field</th><th>value</th></tr></thead>
          <tbody>
            <tr><td>run id</td><td className="num">{S.runId}</td></tr>
            <tr><td>states × arms × reps</td><td className="num">{matrix.states.length} × {arms.length} × 3</td></tr>
            <tr><td>raw receipts</td><td className="num">{study.density.raw_receipts.toLocaleString()}</td></tr>
            <tr><td>hardware</td><td className="num">{S.hardware.gpu} · {S.hardware.ram_gb} GB RAM · {S.hardware.vram_gb} GB VRAM</td></tr>
            <tr><td>external spend</td><td className="num">${S.externalSpendUsd.toFixed(2)}</td></tr>
            <tr><td>evidence status</td><td className="num">{S.evidenceStatus}</td></tr>
            <tr><td>matrix source</td><td className="num">{study.matrixOrigin}</td></tr>
            {Object.entries(study.sources).map(([k, v]) => {
              const s = v as { branch: string; before: string; after: string; visibility: string };
              return (
                <tr key={k}><td>{k}</td>
                  <td className="num">{s.branch} {s.before}→{s.after} · {s.visibility}</td></tr>
              );
            })}
          </tbody>
        </table>

        <HeadingFrog id="why" level={3}>why the fast arm is also the accurate one</HeadingFrog>
        <p>
          Both {hammer3.label} and {qwen4.label} score {pct(hammer3.successRate)} — they agree on{" "}
          {hammer3.success} of {hammer3.n} decisions. Where they differ is latency and failure shape:
          {" "}{hammer3.label} abstains on {hammer3.abstained} runs against {qwen4.abstained} for{" "}
          {qwen4.label}. Abstaining when the compiler has already narrowed the set is a defensible
          failure; guessing is not.
        </p>

        <HeadingFrog id="labels" level={3}>family and rung labels</HeadingFrog>
        <ul>
          {matrix.families.map((f) => (
            <li key={f.name}>
              <code>{f.name}</code> — {f.states} state{f.states > 1 ? "s" : ""}, {f.runs} recorded runs,{" "}
              {f.correct} correct{f.dangerous ? `, ${f.dangerous} dangerous` : ""}
            </li>
          ))}
        </ul>

        <HeadingFrog id="gate-record" level={3}>gate defects recorded</HeadingFrog>
        <Callout kind="warning" title={`Gate decision: ${study.gate.decision}`}>
          <ul>
            {study.gate.caveats.map((c: string) => <li key={c}>{c}</li>)}
          </ul>
        </Callout>

        <HeadingFrog id="check-or-reuse" level={3}>check or reuse the evidence</HeadingFrog>
        <p>
          Raw receipts remain authoritative once imported; until then the matrix on this page is a
          transcription of them. Tests at this commit: z0intelligence{" "}
          {study.tests.z0intelligence.passed} passed / {study.tests.z0intelligence.failed} known
          pre-existing failure, Evolution Lab {study.tests.evolution_lab.passed} passed,{" "}
          {study.tests.sha256sum.ok}/{study.tests.sha256sum.total} artifacts hashed.
        </p>
        <HeadingFrog id="notes" level={3}>Notes</HeadingFrog>
        <ol className="footnotes">
          <li id="fn-1">
            Only {calibration.length} of the {arms[0].n * arms.length} recorded decisions report a
            confidence at all, and they are unevenly distributed across arms &mdash; {jev.label} and
            Hammer 7B supply most of them. The reliability curve is therefore an observation about
            the arms that emit confidence, not about every arm.
            <a className="fn" href="#fnref-1">&nbsp;&#8617;</a>
          </li>
        </ol>

        <p style={{ marginTop: 30, fontSize: 14, color: "var(--color-sb-text-muted)" }}>
          z0evals · frozen studies and publication ·{" "}
          <a href="https://github.com/kvnloo/z0evals">source</a>
        </p>
        </div>
      </main>
      <aside className="aside" />
      </div>
    </>
  );
}

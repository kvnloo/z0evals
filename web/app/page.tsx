import study from "@/data/study.json";
import type { Arm, Matrix } from "@/data/types";
import RouteProgress from "@/components/RouteProgress";
import Toc, { type TocItem } from "@/components/Toc";
import Callout from "@/components/Callout";
import MetricRow from "@/components/MetricRow";
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

const TOC: TocItem[] = [
  { id: "are-we-there-yet", label: "Are we there yet?" },
  { id: "inside-the-receipts", label: `Inside ${study.density.raw_receipts.toLocaleString()} receipts` },
  { id: "do-the-arms-agree", label: "Do the arms agree?" },
  { id: "does-confidence-mean-anything", label: "Does confidence mean anything?" },
  { id: "actions", label: "What the compiler removed" },
  { id: "families", label: "Where the difficulty lives" },
  { id: "authors-note", label: "Author's note" },
  { id: "appendix", label: "Appendix: what the numbers mean" },
];

export default function Page() {
  return (
    <>
      <RouteProgress />
      <header className="site-nav">
        <a className="brand" href="./">z0evals</a>
        <nav className="links">
          <a href="#are-we-there-yet">Results</a>
          <a href="#appendix">Method</a>
          <a href="https://github.com/kvnloo/z0evals">GitHub</a>
        </nav>
      </header>

      <div className="shell">
      <div className="rail"><Toc items={TOC} /></div>
      <main className="article">
        <div className="article-header">
          <h1>{S.title}</h1>
          <div className="article-meta">
            {S.author}<span className="sep">·</span>{S.date}
            <span className="sep">·</span>
            <span style={{ fontFamily: "var(--font-mono)" }}>{S.runId}</span>
          </div>
        </div>

        <p className="lede">
          We keep being told a small local model can route an agent&rsquo;s next move. We measured
          eight of them, {arms[0].n} decisions each, behind the same deterministic compiler, on one
          {` ${S.hardware.gpu}`}. Here is what actually happened.
        </p>

        <Callout kind="info" title="REAL PHASE 1B DATA">
          <p>
            <code>{S.runId}</code> is immutable. All {study.density.raw_receipts.toLocaleString()} raw
            receipts came from the local <code>z0int cognition serve</code> supervisor. External
            inference spend was <strong>${S.externalSpendUsd.toFixed(2)}</strong>. Nothing on this page
            is modelled, extrapolated, or copied from a vendor claim.
            {" "}<strong>Draft:</strong> {study.provenance.canonical_raw_artifacts}.
          </p>
        </Callout>

        <MetricRow items={[
          { k: "raw receipts", v: study.density.raw_receipts.toLocaleString(), s: "one per model call" },
          { k: "measured cells", v: String(study.density.phase1b_measured_cells), s: `${study.density.phase1b_cells_n_ge_3} at n≥3` },
          { k: "best success", v: pct(qwen9.successRate), s: `${qwen9.label} · ${ms(qwen9.warmP50Ms)}` },
          { k: "dangerous selected", v: String(unf.dangerous), s: `unfiltered · every compiler arm: 0` },
        ]} />

        <div className="hero-rule" />

        <h2 id="are-we-there-yet">Are we there yet?</h2>
        <p>
          An agent turn is mostly not reasoning. It is choosing one action from the ones that are
          legal, with arguments. The first run we did told us which small models <em>looked</em>
          promising: 522 <code>(state, arm)</code> cells, 460 of them holding a single observation.
          That is not evidence, it is a first impression.
        </p>

        <h3 id="option-1-just-ask">Option 1: Just ask</h3>
        <p>
          Give the whole job to one capable model and let it read everything. It works, and it is what
          everyone does. On this hardware it costs {ms(qwen4.warmP50Ms)} per decision for {qwen4.label}
          and {ms(qwen9.warmP50Ms)} for {qwen9.label}, and it never tells you how sure it is.
        </p>

        <h3 id="option-2-break-into-phases">Option 2: Break into phases</h3>
        <p>
          Compile the legal action set first, deterministically, then ask a model only to pick from
          what is left. That is the architecture under test here: every bounded arm in this study sits
          behind the same compiler, except one deliberately unfiltered control.
        </p>
        <p>
          The compiler is not a cost optimisation. It is the safety mechanism —
          <a href="#safety"> see Fig 4</a>.
        </p>

        <h3 id="scaling-up">Scaling up</h3>
        <p>
          Phase 1B re-ran the cells with repeats and kept one raw receipt per call, so the distribution
          can be recomputed later without re-running anything.
        </p>
        <figure>
          <div className="fig-body"><DensityBars d={study.density} /></div>
          <figcaption>
            <span className="fig-n">Fig 1</span>
            The evidence base. Phase 1B removed every single-observation cell and pushed{" "}
            {study.density.phase1b_cells_n_ge_3} of {study.density.phase1b_measured_cells} cells to
            n≥3. The honest residue: {study.density.cells_n2} cells remain at n=2 and{" "}
            <strong>no cell reached n≥10</strong>, so no arm here is estimated better than its interval.
          </figcaption>
        </figure>

        <h2 id="inside-the-receipts">Inside {study.density.raw_receipts.toLocaleString()} receipts</h2>
        <p>
          Eight arms, {hammer3.n} decisions each, {matrix.states.length} bounded-choice states. Two
          results matter more than the rest.
        </p>
        <figure>
          <div className="fig-body"><ArmScatter arms={arms} /></div>
          <figcaption>
            <span className="fig-n">Fig 2</span>
            Success against warm median latency, log scale, Wilson 95% intervals. {qwen9.label} is
            best at {pct(qwen9.successRate)} for {ms(qwen9.warmP50Ms)}.{" "}
            <strong>{hammer3.label} ties {qwen4.label} at {pct(hammer3.successRate)} for{" "}
            {(qwen4.warmP50Ms! / hammer3.warmP50Ms!).toFixed(1)}× less latency</strong> — the cheapest
            arm that is not dominated.
          </figcaption>
        </figure>

        <h3 id="jev-versus-text-models">Calibrated scorers versus text models</h3>
        <p>
          {jev.label} answers a typed question in {ms(jev.warmP50Ms)} — three orders of magnitude
          under the text models — and it is the only arm on this page that returns a calibrated
          probability rather than a choice. It is also, on this fixture set, {pct(jev.successRate)}.
          Cheap and confident is not the same as correct.
        </p>
        <p>
          {fng.label} is the other cheap rung: {ms(fng.warmP50Ms)} and {pct(fng.successRate)}. Both sit
          far below the text models on quality while sitting far below them on cost, which is exactly
          the trade the escalation ladder exists to arbitrate.
        </p>

        <h2 id="safety">The compiler is the safety property</h2>
        <p>
          {unf.label} selected a dangerous action <strong>{unf.dangerous} times in {unf.n}</strong>.
          Every compiler-first arm selected zero — including {fng.label}, which succeeds only{" "}
          {pct(fng.successRate)}. A weak model behind a correct compiler fails safe; a strong model
          without one does not.
        </p>

        <h2 id="explore">Explore the matrix</h2>
        <p>
          Everything below is driven by the recorded receipts. Pick arms, replay the sweep, scrub to a
          state, switch family, and switch the matrix metric.
        </p>
        <ResultsExplorer matrix={matrix} />

        <h2 id="residency">Residency dominates everything</h2>
        <p>
          A router that ignores load cost will bounce between two models on a{" "}
          {S.hardware.vram_gb} GB card and pay a full load every turn.
        </p>
        <figure>
          <div className="fig-body"><ResidencyBars rows={study.residency.classes} /></div>
          <figcaption>
            <span className="fig-n">Fig 9</span>
            Cold load {ms(study.residency.classes[0].p50Ms)}, model swap{" "}
            {ms(study.residency.classes[1].p50Ms)}, warm {ms(study.residency.classes[2].p50Ms)}. The
            choice of model matters far less than whether it is already resident — a placement
            problem, not a model-quality problem.
          </figcaption>
        </figure>

        <h2 id="do-the-arms-agree">Do the arms agree?</h2>
        <p>
          Composing routers is the obvious next idea: put a cheap scorer in front of a strong model and
          grade its output. On these fixtures it made things worse.
        </p>
        <figure>
          <div className="fig-body">
            <CompositionSplit base={study.composition.base} baseCorrect={study.composition.baseCorrect}
                              total={study.composition.statesTotal} variants={study.composition.variants} />
          </div>
          <figcaption>
            <span className="fig-n">Fig 10</span>
            Adding Hammer 3B or NanoJev in front of Qwen 4B{" "}
            <strong>helped zero states and hurt{" "}
            {study.composition.variants[0].hurt + study.composition.variants[1].hurt}</strong>. The
            artifact is delivered and consumed on {study.composition.artifactConsumedStates} of{" "}
            {study.composition.statesTotal} states, so this is not a plumbing failure.
          </figcaption>
        </figure>
        <p>
          On orchestration, {qwen4.label} and {qwen9.label} are the only arms that both solve and stop.
          {nem.label} fails to know when to stop, which is why it cannot hold the top of a ladder.
        </p>
        <figure>
          <div className="fig-body">
            <OrchestrationBars data={study.orchestration.expanded} total={study.orchestration.expanded.total} />
          </div>
          <figcaption>
            <span className="fig-n">Fig 11</span>
            Solved, correct stops and failures-to-escalate on the {study.orchestration.expanded.total}
            -scenario cohort.
          </figcaption>
        </figure>

        <figure>
          <div className="fig-body"><LadderFlow /></div>
          <figcaption>
            <span className="fig-n">Fig 12</span>
            The escalation ladder. A case descends only until a rung accepts it; latencies are warm p50
            from this run.
          </figcaption>
        </figure>

        <h2 id="does-confidence-mean-anything">Does the confidence mean anything?</h2>
        <p>
          {jev.label} is the only arm on this page that returns a probability rather than a choice,
          which makes it the only one whose number can be checked. If a 0.8 does not mean roughly
          eight times in ten, the escalation policy has nothing to threshold on.
        </p>
        <figure>
          <div className="fig-body"><Calibration rows={calibration} threshold={0.5} /></div>
          <figcaption>
            <span className="fig-n">Fig 13</span>
            Top: observed accuracy in each confidence decade against perfect calibration (dashed).
            Bottom: every recorded decision at its stated confidence; the red line is the abstain
            threshold the policy would set. The curve is above the diagonal at the low end and
            <strong> below it in the 0.8&ndash;0.9 decade</strong>&hairsp;&mdash;&hairsp;the arms are
            overconfident exactly where a router would be tempted to trust them.<a className="fn" href="#fn-1" id="fnref-1">1</a>
          </figcaption>
        </figure>
        <p>
          That is the same shape the reference reports for its own observer: confidence is
          informative, but not yet a number a policy can take at face value. It is a gate to be
          <em>calibrated</em>, not an answer to be trusted.
        </p>

        <h2 id="actions">What the compiler removed</h2>
        <p>
          Every bounded arm was handed the same compiled legal set. Comparing what was offered
          against what was chosen shows the compiler doing its job: <code>fs.read</code> was
          available on {actionCensus[0] ? String(Math.max(...actionCensus.map((a: { offered: number }) => a.offered))).toLocaleString() : "hundreds of"} runs and chosen far less often, while the
          abstain and escalation paths absorb the cases the arms could not settle.
        </p>
        <figure>
          <div className="fig-body"><ActionTable actions={actionCensus} /></div>
          <figcaption>
            <span className="fig-n">Fig 14</span>
            Offered (grey) against chosen (green) per action. The dangerous selections are all in
            the unfiltered control, which never had a compiled set to begin with.
          </figcaption>
        </figure>

        <h2 id="families">Where the difficulty lives</h2>
        <figure>
          <div className="fig-body"><FamilySparklines families={familiesFull} /></div>
          <figcaption>
            <span className="fig-n">Fig 15</span>
            One row per state family, with a sparkline of per-state mean success across all arms.
            <strong> recovery</strong> is the weak family: two of its four states sit near 20%
            success, and no family except routing has every state solved by every arm.
          </figcaption>
        </figure>

        <h2 id="authors-note">Author&rsquo;s note</h2>
        <p>
          The result I did not expect is that the fastest arm and the second-most-accurate arm are the
          same arm. {hammer3.label} ties {qwen4.label} on success at{" "}
          {(qwen4.warmP50Ms! / hammer3.warmP50Ms!).toFixed(0)}× the speed, which means the honest
          recommendation on this hardware is not &ldquo;use the biggest model that fits&rdquo; but
          &ldquo;use the smallest model whose failures the compiler already caught&rdquo;.
        </p>
        <p>
          The result I did expect and still dislike: composition did not pay. Two routers in series
          lost to the stronger one alone on every state that changed. That is worth remembering before
          building a third stage.
        </p>
        <p>
          And the caveat that matters most: {jev.label} is the only calibrated signal in the system and
          it is not accurate enough to decide alone. Its value is as a gate — a number a policy can
          threshold — not as an answer.
        </p>

        <h2 id="appendix">Appendix: what the numbers mean</h2>

        <h3 id="the-run">The Phase 1B run</h3>
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

        <h3 id="why">Why the fast arm is also the accurate one</h3>
        <p>
          Both {hammer3.label} and {qwen4.label} score {pct(hammer3.successRate)} — they agree on{" "}
          {hammer3.success} of {hammer3.n} decisions. Where they differ is latency and failure shape:
          {" "}{hammer3.label} abstains on {hammer3.abstained} runs against {qwen4.abstained} for{" "}
          {qwen4.label}. Abstaining when the compiler has already narrowed the set is a defensible
          failure; guessing is not.
        </p>

        <h3 id="labels">Family and rung labels</h3>
        <ul>
          {matrix.families.map((f) => (
            <li key={f.name}>
              <code>{f.name}</code> — {f.states} state{f.states > 1 ? "s" : ""}, {f.runs} recorded runs,{" "}
              {f.correct} correct{f.dangerous ? `, ${f.dangerous} dangerous` : ""}
            </li>
          ))}
        </ul>

        <h3 id="gate">Gate defects recorded</h3>
        <Callout kind="warning" title={`Gate decision: ${study.gate.decision}`}>
          <ul>
            {study.gate.caveats.map((c: string) => <li key={c}>{c}</li>)}
          </ul>
        </Callout>

        <h3 id="check-or-reuse">Check or reuse the evidence</h3>
        <p>
          Raw receipts remain authoritative once imported; until then the matrix on this page is a
          transcription of them. Tests at this commit: z0intelligence{" "}
          {study.tests.z0intelligence.passed} passed / {study.tests.z0intelligence.failed} known
          pre-existing failure, Evolution Lab {study.tests.evolution_lab.passed} passed,{" "}
          {study.tests.sha256sum.ok}/{study.tests.sha256sum.total} artifacts hashed.
        </p>
        <h3 id="notes">Notes</h3>
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
      </main>
      <aside className="aside" />
      </div>
    </>
  );
}

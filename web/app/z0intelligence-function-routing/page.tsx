import type { Metadata } from "next";
import data from "@/data/z0intelligence-function-routing.json";
import StoryShell, { type StoryMeta, type StoryBanner } from "@/components/StoryShell";
import type { TocItem } from "@/components/Toc";
import MetricReveal, { type MetricRevealStage } from "@/components/MetricReveal";
import EvidencePipeline, { type PipelineStage } from "@/components/EvidencePipeline";
import CapabilityMap, { type CapabilityEntry } from "@/components/CapabilityMap";
import RoutingTrace, { type ProviderRow, type AdmissionTest } from "@/components/RoutingTrace";
import Callout from "@/components/Callout";
import MetricRow from "@/components/MetricRow";
import { MarginNote } from "@/components/Notes";
import ResearchDeepDive from "@/components/ResearchDeepDive";

export const metadata: Metadata = {
  title: "what actually deserves a model? — z0evals",
  description:
    "we kept trying to make routing smarter. the useful part was figuring out which decisions "
    + "should not be model problems at all.",
};

const M = data.meta;
const P = data.pipeline;
const N = data.nanojev;
const J = data.jev;
const CM = data.capabilityMap;
const PR = data.providers;
const FT = data.freeTier;
const CB = data.cerebras;
const RD = data.routeDemo;
const ID = data.imageDecision;
const MP = data.measurementProvenance;
const JU = data.juliaUpdate;
const TR = data.traceRouting;
const DD = data.decisionDatasetV2;
const EX = data.explore;

// JSON array indexing is `T | undefined` under strict mode. Narrow once, here,
// rather than sprinkling non-null assertions through the JSX.
const jb0 = J.benchmarks[0]!;
const jb1 = J.benchmarks[1]!;
const jb0s0 = jb0.systems[0]!;
const jb0s1 = jb0.systems[1]!;
const jb0s2 = jb0.systems[2]!;
const jbs = jb0.binary_slice!;
const jbg = jb1.class_gap!;
const jbss0 = jbs.systems[0]!;
const jbss1 = jbs.systems[1]!;
const jb1s0 = jb1.systems[0]!;
const jb1s1 = jb1.systems[1]!;
const cbe0 = CB.equal_cache[0]!;
const cbe1 = CB.equal_cache[1]!;
const cbcoh0 = CB.cohorts[0]!;
const tk = (a: number[], i: number): number => a[i]!;

const n = (v: number, d = 4) => v.toFixed(d);
const pct = (v: number, d = 2) => `${(v * 100).toFixed(d)}%`;
const ms = (v: number) => `${v.toLocaleString("en-US")} ms`;

/* ---- derived views (everything below is computed from the JSON above) ---- */

const pipelineStages: PipelineStage[] = P.stages.map((s) => ({
  id: s.id,
  label: s.label,
  gloss: s.gloss,
  ev: s.ev,
  failed: s.failed,
}));

const jevStages: MetricRevealStage[] = [
  {
    k: "authored144 · famBalAcc",
    v: n(jb0s0.fba),
    s: "recomputed from the raw per-example file",
    kind: "good",
  },
  {
    k: "authored144 · ECE",
    v: n(jb0s0.ece),
    s: "calibration, not just accuracy",
    kind: "good",
  },
  {
    k: "withheld: AUROC",
    v: n(jbss0.auroc),
    s: "only on the 48-example binary slice — see below",
    kind: "good",
  },
];

const cerebrasStages: MetricRevealStage[] = [
  { k: "worker raw quality", v: "60/60", s: "zero required repairs or fallbacks", kind: "good" },
  { k: "worker latency p50", v: "625 ms", s: "p95 1,149 ms", kind: "good" },
  {
    k: "parent tokens, equal cache",
    v: `+${cbe0.delta.toFixed(1)}`,
    s: "report summary, 12 pairs",
    kind: "bad",
  },
  {
    k: "parent tokens, equal cache",
    v: `+${cbe1.delta.toFixed(1)}`,
    s: "evidence gate, 8 pairs",
    kind: "bad",
  },
];

const capabilityEntries: CapabilityEntry[] = CM.functions.map((f) => ({
  id: f.id,
  label: f.label,
  route: f.route,
  implementation: f.implementation,
  status: f.status as CapabilityEntry["status"],
  basis: f.basis,
  consumers: f.consumers,
  caveat: f.caveat,
}));

const routeEntries: CapabilityEntry[] = RD.cases.map((c) => ({
  id: c.id,
  label: `${c.task}  ·  ${c.shape}`,
  route: c.route,
  implementation: c.implementation,
  status: c.evidence_level as CapabilityEntry["status"],
  basis: `${c.reason} — observed: ${c.observed}`,
  caveat: c.caveat,
}));

const providerRows: ProviderRow[] = PR.exercised.map((p) => ({
  provider: p.provider,
  model: p.model,
  tasks: p.tasks,
  cap: p.cap,
  capMeasured: false,
  headroom: p.cap === null ? "UNKNOWN" : undefined,
}));

const admission: AdmissionTest = {
  admitted: PR.saturation.admitted,
  capped: PR.saturation.capped_before_provider_http,
  peak: PR.saturation.peak_inflight,
  fixture: PR.saturation.fixture,
};

const toc: TocItem[] = M.toc;

const story = (
  <>
    <h2 id="green">everything was green. that was the problem.</h2>
    <p>
      the first version of this looked great. outputs came back, the harness said success,
      and the totals looked believable. then a fallback serialization bug showed us something
      annoying: the path we were reporting on was not always the path that actually ran.
    </p>
    <p>
      i kept that busted batch in the evidence set instead of deleting it. it is basically the
      reason this whole post exists. <strong>selected is not executed.</strong> if i cannot prove
      the worker physically ran, i do not get to count it.
    </p>
    <EvidencePipeline stages={pipelineStages} caption={P.caption} />
    <p>
      hover or tab through that thing. every step has been wrong at least once. that is way more
      useful than a pretty green pipeline pretending nothing weird ever happened.
    </p>

    <h2 id="nanojev">nanojev was fast. it was also taking the wrong test.</h2>
    <p>
      {N.checkpoint} looked awesome at first: about {N.speed_ms_p50_cpu} ms p50 on cpu, the right
      interface, and an early auroc that looked promising.
    </p>
    <p>
      then i checked what it was actually trained to do. {N.trained_on.join(", ")}. action choice.
      the boolean / ordered-score stuff was an interface affordance, not the training objective.
      lol.
    </p>
    <Callout kind="danger" title="the boolean path was not a real measurement">
      <pre><code>{N.boolean_defect.code}</code></pre>
      <p>{N.boolean_defect.why}</p>
      <p><strong>{N.boolean_defect.consequence}.</strong></p>
    </Callout>
    <p><strong>fast is not the same as trained for the job.</strong> an interface can fit perfectly while the capability underneath it is totally wrong.</p>
    <MarginNote n={1} label="trainer not located">
      {N.trainer_location}.
    </MarginNote>

    <h2 id="jev">jev was the part that actually survived</h2>
    <p>
      also, the first “reproduction” was not really a reproduction. we had tested proxy models
      instead of the model from the paper. reproducing a different system very carefully is still
      reproducing a different system.
    </p>
    <MetricReveal
      stages={jevStages}
      caption="recomputed from the raw per-example capability-evidence file. not copied from a nice-looking summary number."
    />
    <Callout kind="warning" title="0.9982 auroc is real, but only on that exact slice">
      <p>{jbs.caveat}</p>
    </Callout>
    <MetricRow
      items={[
        { k: "authored144", v: `${jb0.n}`, s: "3 families x 48" },
        { k: "direct qwen3.5-4b", v: n(jb0s1.fba), s: `ece ${n(jb0s1.ece)}` },
        { k: "reranker", v: n(jb0s2.fba), s: `ece ${n(jb0s2.ece)}` },
        { k: "perturbations108", v: n(jb1s0.fba), s: `ece ${n(jb1s0.ece)}` },
      ]}
    />
    <Callout kind="warning" title="1.0000 on perturbations108 looks cooler than it is">
      <p>{jbg.disclosure}</p>
      <p>gold ids present: <code>{jbg.gold_ids_present.join(", ")}</code>.</p>
    </Callout>
    <p>
      i also dropped the original 146:4 abstention slice as the main target. it is not in this
      checkout, and with a 97% majority class the headline accuracy mostly tells you the majority
      class exists. not super helpful for the three-way runtime contract we actually route on.
    </p>

    <ResearchDeepDive />

    <h2 id="capability">i stopped asking which model is best</h2>
    <p>
      this was the architecture change. asking <em>which model is best?</em> is kind of a fake
      question. best at what? verification? tool choice? image choice? cheap worker stuff?
    </p>
    <p>
      now z0intelligence asks the smaller question: <strong>what implementation has evidence for
      this exact job?</strong>
    </p>
    <CapabilityMap
      functions={capabilityEntries}
      caption="same idea everywhere: do not ask which model wins globally. ask what has evidence for this exact job."
    />

    <h2 id="image-decisions">the image lane is real. the benchmark win is extremely not real.</h2>
    <p>
      we do have a pinned multimodal decision path now: <strong>{ID.system}</strong>, backed by{" "}
      <code>{ID.backbone}</code> at <code>{ID.model_revision.slice(0, 12)}</code>. it maps whatever
      options the task gives us into a bounded label set and reads the option logits directly.
      no prose parsing. no pretending a generated paragraph is a probability distribution.
    </p>
    <MetricRow items={[
      { k: "published examples", v: `${ID.public_examples.correct}/${ID.public_examples.total}`, s: ID.public_examples.scope },
      { k: "generated answer tokens", v: String(ID.generated_answer_tokens_normal_path), s: "normal single-label path" },
      { k: "local target", v: "3080 ti", s: "12 gb" },
      { k: "official score", v: "unknown", s: ID.benchmark_status },
    ]} />
    <Callout kind="warning" title="4/8 is a smoke result. please do not turn it into a benchmark headline">
      <p>{ID.note}</p>
      <p>still unclaimed: {ID.not_claimed.join("; ")}.</p>
    </Callout>

    <h2 id="measurement-state">a token count needs a provenance tag too</h2>
    <p>
      another stupid bug class: counting the last assistant message and calling it the whole run.
      omp now accumulates provider-reported input/output usage across the whole trace, and it only
      gets to say <code>complete</code> when every observed turn actually carried provider usage.
    </p>
    <Callout kind="info" title="complete and partial are not synonyms">
      <p>missing provider usage stays partial. the char-count fallback stays labeled as a proxy.</p>
      <p>the two-turn proof closes at 21 tokens: 10+2, then 7+2.</p>
      <p>that measurement state also survives into tokenomics instead of getting quietly upgraded later.</p>
    </Callout>

    <h2 id="providers">routing is boring until you prove the worker actually ran</h2>
    <p>
      one measured batch returned <strong>{PR.batch.outputs}</strong> outputs.{" "}
      <strong>{PR.batch.providers_completing_real_work} providers</strong> physically completed
      work across {PR.batch.physical_attempts} attempts, with {PR.batch.successful_fallbacks} real
      fallbacks. that is the number i care about now, not just “router said provider x.”
    </p>
    <RoutingTrace
      providers={providerRows}
      admission={admission}
      caption="six providers physically did work. the cap numbers are policy inputs; only the 32-admission test is measured here."
    />
    <p>
      we also forced a real failure. an invalid groq credential produced{" "}
      <strong>{PR.fallback_proof.observed}</strong>. {PR.fallback_proof.also}.
    </p>
    <Callout kind="info" title="one estimate i am still not promoting to a fact">
      <p>
        the report computes “estimated codex-parent tokens avoided:{" "}
        {PR.batch.estimated_parent_tokens_avoided.toLocaleString("en-US")}”. that is a{" "}
        {PR.batch.estimate_basis}
      </p>
    </Callout>
    <Callout kind="warning" title="unknown headroom means unknown. not tiny. not zero. unknown.">
      <p>{PR.saturation.headroom.detail}</p>
      <p>{PR.saturation.local_serialization}</p>
    </Callout>

    <h2 id="freetier">free is nice. free is also not an architecture.</h2>
    <p>
      the free path is intentionally boring: compiled python route, one authority, one executor.
      replay and conflict rejection were proven by replacing the pod instead of trusting an assertion.
    </p>
    <MetricRow
      items={[
        { k: "provider / model", v: FT.execution.model.replace("nvidia/", ""), s: FT.execution.provider },
        { k: "returned", v: FT.execution.output, s: `${FT.execution.tokens.input} in / ${FT.execution.tokens.output} out` },
        { k: "provider-reported cost", v: `$${FT.execution.cost_usd.toFixed(2)}`, s: "free_only route" },
        { k: "receipt latency", v: ms(FT.execution.latency_ms), s: `${FT.execution.latency_observations} observation` },
      ]}
    />
    <ol className="ft-path">
      {FT.path.map((step) => (
        <li key={step.id}>
          <strong>{step.label}</strong> <span>{step.detail}</span>
        </li>
      ))}
    </ol>
    <div className="x-table-wrap">
      <table className="x-table">
        <caption>the three boring invariants that keep duplicate work from becoming real money</caption>
        <thead><tr><th>rule</th><th>status</th><th>evidence</th></tr></thead>
        <tbody>
          {FT.invariants.map((value) => (
            <tr key={value.rule}>
              <td>{value.rule}</td>
              <td><span className="x-status" data-s="MEASURED">{value.status}</span></td>
              <td>{value.evidence}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
    <Callout kind="info" title="free credit is not the same thing as a zero-priced route">
      <p>{FT.excluded.reason}</p>
    </Callout>

    <h2 id="cerebras">cerebras was good. delegation still lost.</h2>
    <p>{CB.caption}</p>
    <MetricReveal
      stages={cerebrasStages}
      caption="same frozen 60-pair cohort. positive parent delta means delegation made the parent do more work."
    />
    <div className="x-table-wrap">
      <table className="x-table">
        <caption>uncached parent input + output, parent-only (a) vs delegated (b)</caption>
        <thead><tr><th>measure</th><th className="num">a</th><th className="num">b</th></tr></thead>
        <tbody>
          <tr><td>uncached parent input</td><td className="num">{CB.tokens.A_uncached_parent_input.toLocaleString("en-US")}</td><td className="num">{CB.tokens.B_uncached_parent_input.toLocaleString("en-US")}</td></tr>
          <tr><td>parent output</td><td className="num">{CB.tokens.A_parent_output.toLocaleString("en-US")}</td><td className="num">{CB.tokens.B_parent_output.toLocaleString("en-US")}</td></tr>
          <tr><td>cached parent input</td><td className="num">{CB.tokens.A_cached_parent_input.toLocaleString("en-US")}</td><td className="num">{CB.tokens.B_cached_parent_input.toLocaleString("en-US")}</td></tr>
          <tr><td><strong>uncached input + output</strong></td><td className="num"><strong>{CB.tokens.A_uncached_input_plus_output.toLocaleString("en-US")}</strong></td><td className="num"><strong>{CB.tokens.B_uncached_input_plus_output.toLocaleString("en-US")}</strong></td></tr>
          <tr><td>worker input / output</td><td className="num">0 / 0</td><td className="num">{CB.tokens.worker_input.toLocaleString("en-US")} / {CB.tokens.worker_output.toLocaleString("en-US")}</td></tr>
        </tbody>
      </table>
    </div>
    <Callout kind="warning" title={`raw aggregate is +${CB.raw_aggregate_delta.toLocaleString("en-US")} and it stays positive after cache control`}>
      <p>{CB.cache_controlled.note}</p>
      <p>
        equal-cache subset: report summary <strong>+{cbe0.delta.toFixed(1)}</strong>{" "}
        [{cbe0.lo.toFixed(1)}, {cbe0.hi.toFixed(1)}]; evidence gate{" "}
        <strong>+{cbe1.delta.toFixed(1)}</strong> [{cbe1.lo.toFixed(1)}, {cbe1.hi.toFixed(1)}].
      </p>
    </Callout>
    <p>
      <strong>the parent cannot save tokens if it still reads the whole original task plus a giant worker response.</strong>
      the next thing to test is typed / compressed worker output, not just an even better worker model.
    </p>
    <p>{CB.nemotron.note}</p>
    <MarginNote n={2} label="excluded cohort">{cbcoh0.why}</MarginNote>
    <MarginNote n={3} label="grading correction">{CB.grading_note} billing: {CB.billing}</MarginNote>

    <h2 id="trace-routing">then five lines of dumb rules beat the learned routers</h2>
    <p>
      this is the result that made me laugh. on a grouped sealed split of{" "}
      <strong>{TR.sealed_n} real decision states</strong>, the deterministic keyword rule beat
      both learned fast paths.
    </p>
    <div className="x-table-wrap">
      <table className="x-table">
        <caption>sealed real-trace tool-family routing · {TR.classes} classes · chance {pct(TR.chance, 0)}</caption>
        <thead><tr><th>system</th><th className="num">accuracy</th><th className="num">macro f1</th><th className="num">p50</th></tr></thead>
        <tbody>
          {TR.systems.map((row) => (
            <tr key={row.system}>
              <td>{row.system}</td>
              <td className="num">{pct(row.accuracy, 2)}</td>
              <td className="num">{n(row.macro_f1)}</td>
              <td className="num">{"p50_ms" in row ? `${row.p50_ms} ms` : "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
    <Callout kind="warning" title="the dumb baseline won by a lot">
      <p>
        keyword rule <strong>74.03%</strong>. laya <strong>19.48%</strong>. julia{" "}
        <strong>10.39%</strong>. julia also lost the binary delegate gate:{" "}
        {pct(TR.delegate_gating.julia_accuracy, 2)} vs {pct(TR.delegate_gating.majority_accuracy, 2)}
        for the majority baseline.
      </p>
      <p>{TR.note}</p>
    </Callout>

    <h2 id="decision-dataset">julia was not broken. honestly that made the result more useful.</h2>
    <p>
      before throwing julia away, i fixed the adapter to render state exactly the way julia does.
      typed cpu went back to <strong>{JU.publisher_claim_reproduction.typed_cpu.correct}/
      {JU.publisher_claim_reproduction.typed_cpu.total}</strong>, exactly matching the publisher.
      ag news reproduced too at <strong>{JU.publisher_claim_reproduction.ag_news.correct}/
      {JU.publisher_claim_reproduction.ag_news.total}</strong>.
    </p>
    <p>
      so this is not “oops the adapter was bad.” the model is integrated faithfully. it just does
      not fit this decision domain. confidence did not save it either: authored144 uncertainty
      aurocs sit around chance ({n(JU.selective_risk.authored144_auroc.p1, 3)} p1,{" "}
      {n(JU.selective_risk.authored144_auroc.entropy, 3)} entropy), with only{" "}
      <strong>{pct(JU.selective_risk.coverage_at_le_10pct_error.authored144, 2)}</strong> coverage
      at the ≤10% error budget. {JU.selective_risk.note}.
    </p>
    <MetricRow
      items={[
        { k: "session files sampled", v: DD.files_scanned.toLocaleString("en-US"), s: `of ${DD.files_total.toLocaleString("en-US")}` },
        { k: "outcome-backed actions", v: DD.action_rows.toLocaleString("en-US"), s: `${DD.sessions} sessions` },
        { k: "compactions", v: DD.compactions.toLocaleString("en-US"), s: "observable events" },
        { k: "reachable capabilities", v: `${DD.milestone.reachable_count}/5`, s: "at the requested >=500-row bar" },
      ]}
    />
    <p>
      decision dataset v2 rebuilds per-turn state from omp transcripts and pairs each tool call to
      its real <code>toolResult</code>. four capabilities already have enough outcome-backed rows:
      <code>{DD.milestone.reachable.join(", ")}</code>.
    </p>
    <Callout kind="info" title="the fifth capability is not a modeling problem yet">
      <p>{DD.milestone.verdict}.</p>
      <p>
        <code>verification_needed</code>: {DD.milestone.missing.verification_needed}.{" "}
        <code>rlm.worker_needed</code>: {DD.milestone.missing["rlm.worker_needed"]}.
      </p>
      <p>{DD.privacy}.</p>
    </Callout>

    <h2 id="route-demo">so what would z0 actually do?</h2>
    <p>
      pick a task shape and this shows the route the frozen cohort actually produced, plus the
      reason it recorded. no imaginary “ideal router” in this widget.
    </p>
    <CapabilityMap
      functions={routeEntries}
      caption="frozen decisions from the measured cohorts. the status is evidence level, not a vibes score."
    />
  </>
);

const explore = (
  <>
    <h2 id="explore-tables">show me the tables</h2>

    <div className="explore-block">
      <h3>did the verifier actually hold up?</h3>
      <div className="x-table-wrap">
        <table className="x-table">
          <caption>authored144 — recomputed from the raw per-example file</caption>
          <thead>
            <tr>
              <th scope="col">system</th>
              <th scope="col">role</th>
              <th scope="col" className="num">famBalAcc</th>
              <th scope="col" className="num">macro F1</th>
              <th scope="col" className="num">ECE</th>
            </tr>
          </thead>
          <tbody>
            {jb0.systems.map((s) => (
              <tr key={s.system}>
                <td>{s.system}</td>
                <td>{s.role}</td>
                <td className="num">{n(s.fba)}</td>
                <td className="num">{n(s.macro_f1)}</td>
                <td className="num">{n(s.ece)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="x-table-wrap">
        <table className="x-table">
          <caption>
            Binary abstention slice — {jbs.family}, n=
            {jbs.n}, positives={jbs.positives},
            score={jbs.score}
          </caption>
          <thead>
            <tr>
              <th scope="col">system</th>
              <th scope="col" className="num">AUROC</th>
              <th scope="col" className="num">balanced accuracy</th>
            </tr>
          </thead>
          <tbody>
            {jbs.systems.map((s) => (
              <tr key={s.system}>
                <td>{s.system}</td>
                <td className="num">{n(s.auroc)}</td>
                <td className="num">{n(s.balanced_accuracy)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="x-table-wrap">
        <table className="x-table">
          <caption>
            perturbations108 — gold ids {jbg.gold_ids_present.join(", ")}; no
            `insufficient` label
          </caption>
          <thead>
            <tr>
              <th scope="col">system</th>
              <th scope="col" className="num">famBalAcc</th>
              <th scope="col" className="num">macro F1</th>
              <th scope="col" className="num">ECE</th>
            </tr>
          </thead>
          <tbody>
            {jb1.systems.map((s) => (
              <tr key={s.system}>
                <td>{s.system}</td>
                <td className="num">{n(s.fba)}</td>
                <td className="num">{n(s.macro_f1)}</td>
                <td className="num">{n(s.ece)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {J.omitted.map((o) => (
        <p key={o.claim}>
          <span className="x-status" data-s="UNKNOWN">
            omitted
          </span>{" "}
          <strong>{o.claim}</strong> — {o.why}
        </p>
      ))}
    </div>

    <div className="explore-block">
      <h3>the delegation runs</h3>
      <div className="x-table-wrap">
        <table className="x-table">
          <caption>Cerebras qwen-3.8-27b · reasoning_effort=none · 30 repeats each of two tasks</caption>
          <thead>
            <tr>
              <th scope="col">task</th>
              <th scope="col" className="num">equal-cache pairs</th>
              <th scope="col" className="num">mean parent delta</th>
              <th scope="col" className="num">95% interval</th>
            </tr>
          </thead>
          <tbody>
            {CB.equal_cache.map((e) => (
              <tr key={e.task}>
                <td>{e.task}</td>
                <td className="num">{e.pairs}</td>
                <td className="num">+{e.delta.toFixed(1)}</td>
                <td className="num">
                  +{e.lo.toFixed(1)} to +{e.hi.toFixed(1)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="x-table-wrap">
        <table className="x-table">
          <caption>Nemotron free route · 2 sequential pairs · same fresh parent</caption>
          <thead>
            <tr>
              <th scope="col">task</th>
              <th scope="col" className="num">+uncached input</th>
              <th scope="col" className="num">+wall seconds</th>
              <th scope="col" className="num">worker tokens</th>
              <th scope="col">worker quality</th>
            </tr>
          </thead>
          <tbody>
            {CB.nemotron.per_task.map((t) => (
              <tr key={t.task}>
                <td>{t.task}</td>
                <td className="num">+{t.delta_uncached_parent_input}</td>
                <td className="num">+{t.added_wall_s.toFixed(2)}</td>
                <td className="num">{t.worker_tokens.toLocaleString("en-US")}</td>
                <td>{t.worker_quality}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="x-table-wrap">
        <table className="x-table">
          <caption>Cohort disposition — the excluded one is kept, not pooled</caption>
          <thead>
            <tr>
              <th scope="col">cohort</th>
              <th scope="col" className="num">completed</th>
              <th scope="col">status</th>
              <th scope="col">why</th>
            </tr>
          </thead>
          <tbody>
            {CB.cohorts.map((c) => (
              <tr key={c.id}>
                <td>{c.id}</td>
                <td className="num">
                  {c.completed}/{c.target}
                </td>
                <td>
                  <span className="x-status" data-s={c.status === "MEASURED" ? "MEASURED" : "UNKNOWN"}>
                    {c.status}
                  </span>
                </td>
                <td>{c.why}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>

    <div className="explore-block">
      <h3>who actually ran what?</h3>
      <div className="x-table-wrap">
        <table className="x-table">
          <caption>Four concurrent HTTP clients. Labels are clients, not claims of installed integration.</caption>
          <thead>
            <tr>
              <th scope="col">client</th>
              <th scope="col">route</th>
              <th scope="col">model</th>
              <th scope="col" className="num">latency</th>
              <th scope="col" className="num">tokens</th>
            </tr>
          </thead>
          <tbody>
            {PR.harness_routes.map((r) => (
              <tr key={r.client}>
                <td>{r.client}</td>
                <td>{r.route}</td>
                <td>{r.model}</td>
                <td className="num">{ms(r.latency_ms)}</td>
                <td className="num">
                  {tk(r.tokens, 0)}/{tk(r.tokens, 1)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>

    <h2 id="claims">what can i actually claim?</h2>
    <p>
      Every claim carries its evidence level. <strong>UNKNOWN</strong> is a first-class value: it
      means we did not reproduce the evidence, not that the number is small.
    </p>
    <div className="x-table-wrap">
      <table className="x-table">
        <thead>
          <tr>
            <th scope="col">claim</th>
            <th scope="col">status</th>
            <th scope="col">evidence</th>
          </tr>
        </thead>
        <tbody>
          {EX.claims.map((c) => (
            <tr key={c.id}>
              <td>{c.text}</td>
              <td>
                <span className="x-status" data-s={c.status}>
                  {c.status}
                </span>
              </td>
              <td>{c.evidence}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>

    <h2 id="methods">how i measured this</h2>
    <div className="x-table-wrap">
      <table className="x-table">
        <thead>
          <tr>
            <th scope="col">dimension</th>
            <th scope="col">value</th>
            <th scope="col">note</th>
          </tr>
        </thead>
        <tbody>
          {EX.methods.map((m) => (
            <tr key={m.k}>
              <td>{m.k}</td>
              <td>{m.v}</td>
              <td>{m.s}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>

    <h2 id="limitations">where this could still be wrong</h2>
    <ul>
      {EX.limitations.map((l) => (
        <li key={l}>{l}</li>
      ))}
    </ul>

    <h2 id="sources">source pins + receipts</h2>
    <div className="x-table-wrap">
      <table className="x-table">
        <caption>Pinned revisions</caption>
        <thead>
          <tr>
            <th scope="col">repo</th>
            <th scope="col">commit</th>
            <th scope="col">role</th>
          </tr>
        </thead>
        <tbody>
          {EX.sources.map((s) => (
            <tr key={s.commit + s.role}>
              <td>{s.repo}</td>
              <td>
                <code>{s.commit.slice(0, 12)}</code>
              </td>
              <td>{s.role}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
    <ul className="x-receipts">
      {EX.receipts.map((r) => (
        <li key={r.ref}>
          <strong>{r.label}</strong>
          <code>{r.ref}</code>
        </li>
      ))}
    </ul>
  </>
);

export default function Page() {
  return (
    <StoryShell
      meta={M as StoryMeta}
      banner={M.banner as StoryBanner}
      toc={toc}
      story={story}
      explore={explore}
    />
  );
}

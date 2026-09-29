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

export const metadata: Metadata = {
  title: "from model routing to evidence-backed function routing — z0evals",
  description:
    "Eight days of measurements on Jev, Julia, image decisions, real-trace routing, provider execution, "
    + "and what should stay deterministic.",
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
    <h2 id="green">Everything was green</h2>
    <p>
      The first headline to fall was our own. An earlier automatic-routing batch looked green:
      outputs came back, the harness reported success, and the totals were plausible. Then a
      fallback serialization bug surfaced in that same batch — and it became clear the harness had
      been reporting on a path that was not the path that ran.
    </p>
    <p>
      That batch is still in the evidence set, next to its successor, rather than deleted. The rule
      we took from it is the spine of everything below: a route being <em>selected</em> is not
      evidence it <em>executed</em>.
    </p>
    <EvidencePipeline stages={pipelineStages} caption={P.caption} />
    <p>
      Hover or tab through the stages. Each one carries the point at which it was falsified at least
      once in this study — the failure note is part of the pipeline, because a figure that only
      showed forward progress would repeat the mistake the study is about.
    </p>

    <h2 id="nanojev">NanoJev: a fast model answering the wrong question</h2>
    <p>
      {N.checkpoint} looked like a win: ~{N.speed_ms_p50_cpu} ms p50 on CPU, interface-compatible
      with our decision contract, and an initial AUROC that pointed the right way.
    </p>
    <p>
      It was trained on {N.trained_on.join(", ")} — action-choice tasks. The publisher&apos;s own
      model card describes boolean and ordered-score support as an <em>interface affordance</em>,
      never a training objective.
    </p>
    <Callout kind="danger" title="The boolean path was not a measurement">
      <pre>
        <code>{N.boolean_defect.code}</code>
      </pre>
      <p>{N.boolean_defect.why}</p>
      <p>
        <strong>{N.boolean_defect.consequence}.</strong>
      </p>
    </Callout>
    <p>
      <strong>{N.lesson}</strong>
    </p>
    <MarginNote n={1} label="trainer not located">
      {N.trainer_location}.
    </MarginNote>

    <h2 id="jev">The real model, and the slice that matters</h2>
    <p>{J.proxy_correction}</p>
    <MetricReveal stages={jevStages} caption="Recomputed from the raw per-example capability-evidence file, not copied from a shipped summary constant." />
    <Callout kind="warning" title="AUROC 0.9982 is slice-dependent — quote it with its slice">
      <p>{jbs.caveat}</p>
    </Callout>
    <MetricRow
      items={[
        { k: "authored144", v: `${jb0.n}`, s: "3 families x 48" },
        { k: "direct Qwen3.5-4B", v: n(jb0s1.fba), s: `ECE ${n(jb0s1.ece)}` },
        { k: "reranker", v: n(jb0s2.fba), s: `ECE ${n(jb0s2.ece)}` },
        { k: "perturbations108", v: n(jb1s0.fba), s: `ECE ${n(jb1s0.ece)}` },
      ]}
    />
    <Callout kind="warning" title="perturbations108 scores 1.0000 — and proves less than it looks">
      <p>{jbg.disclosure}</p>
      <p>
        Gold ids present: <code>{jbg.gold_ids_present.join(", ")}</code>.
      </p>
    </Callout>
    <p>{J.abandoned_target.text}</p>

    <h2 id="capability">Functions, not models</h2>
    <p>
      The architectural conclusion from the falsifications above: stop asking a global question. A
      model router asks <em>&ldquo;which model is best?&rdquo;</em> — a question with no stable
      answer, because &ldquo;best&rdquo; depends on the function.
    </p>
    <p>
      z0intelligence now asks: <strong>which implementation has evidence for this exact
      function?</strong>
    </p>
    <CapabilityMap functions={capabilityEntries} caption={CM.caption} />

    <h2 id="image-decisions">The first image-decision lane is real — the benchmark score is not</h2>
    <p>
      z0intelligence now has a pinned multimodal decision path: <strong>{ID.system}</strong>,
      backed by <code>{ID.backbone}</code> at revision <code>{ID.model_revision.slice(0, 12)}</code>.
      It keeps images out of the text-only DecisionBackend contract and returns a categorical
      distribution over arbitrary supplied options rather than parsing generated prose.
    </p>
    <MetricRow items={[
      { k: "published examples", v: `${ID.public_examples.correct}/${ID.public_examples.total}`, s: ID.public_examples.scope },
      { k: "generated answer tokens", v: String(ID.generated_answer_tokens_normal_path), s: "normal single-label path" },
      { k: "local target", v: "3080 Ti", s: "12 GB" },
      { k: "official score", v: "UNKNOWN", s: ID.benchmark_status },
    ]} />
    <Callout kind="warning" title="4/8 is disclosure, not Image JevBench">
      <p>{ID.note}</p>
      <p>Still unclaimed: {ID.not_claimed.join("; ")}.</p>
    </Callout>

    <h2 id="measurement-state">A token count now carries its measurement state</h2>
    <p>
      The OMP bridge no longer treats a last-message estimate as if it covered the whole turn
      sequence. {MP.provider_usage.behavior}. {MP.provider_usage.complete_rule}.
    </p>
    <Callout kind="info" title="Complete and partial are different data">
      <p>{MP.provider_usage.fallback}.</p>
      <p>{MP.provider_usage.proof}.</p>
      <p>{MP.tokenomics.behavior}. {MP.tokenomics.rule}.</p>
    </Callout>

    <h2 id="providers">Routing that physically executed</h2>
    <p>
      Selection is cheap. Execution is the claim that needs proof. One batch returned{" "}
      <strong>{PR.batch.outputs}</strong> outputs with <strong>
        {PR.batch.providers_completing_real_work} distinct providers
      </strong>{" "}
      completing real work across {PR.batch.physical_attempts} physical attempts and{" "}
      {PR.batch.successful_fallbacks} successful fallbacks.
    </p>
    <RoutingTrace providers={providerRows} admission={admission} caption={PR.caption} />
    <p>
      Fallbacks are load-bearing and were tested with a real failure: an invalid test-process Groq
      credential produced a <strong>{PR.fallback_proof.observed}</strong>.{" "}
      {PR.fallback_proof.also}.
    </p>
    <Callout kind="info" title="A caution on our own estimate">
      <p>
        That report also computes &ldquo;estimated Codex-parent tokens avoided:{" "}
        {PR.batch.estimated_parent_tokens_avoided.toLocaleString("en-US")}&rdquo;. That is a{" "}
        {PR.batch.estimate_basis}
      </p>
    </Callout>
    <Callout kind="warning" title="Provider headroom is UNKNOWN, not small">
      <p>{PR.saturation.headroom.detail}</p>
      <p>{PR.saturation.local_serialization}</p>
    </Callout>

    <h2 id="freetier">Free tier, one authority, three invariants</h2>
    <p>{FT.caption}</p>
    <MetricRow
      items={[
        { k: "provider / model", v: FT.execution.model.replace("nvidia/", ""), s: FT.execution.provider },
        { k: "returned", v: FT.execution.output, s: `${FT.execution.tokens.input} in / ${FT.execution.tokens.output} out` },
        { k: "provider-reported cost", v: `$${FT.execution.cost_usd.toFixed(2)}`, s: "free_only route" },
        { k: "receipt latency", v: ms(FT.execution.latency_ms), s: `${FT.execution.latency_observations} observation` },
      ]}
    />
    <ol className="ft-path">
      {FT.path.map((s) => (
        <li key={s.id}>
          <strong>{s.label}</strong> <span>{s.detail}</span>
        </li>
      ))}
    </ol>
    <div className="x-table-wrap">
      <table className="x-table">
        <caption>Idempotency invariants — each proven by replacing the pod, not by asserting them</caption>
        <thead>
          <tr>
            <th scope="col">rule</th>
            <th scope="col">status</th>
            <th scope="col">evidence</th>
          </tr>
        </thead>
        <tbody>
          {FT.invariants.map((v) => (
            <tr key={v.rule}>
              <td>{v.rule}</td>
              <td>
                <span className="x-status" data-s="MEASURED">
                  {v.status}
                </span>
              </td>
              <td>{v.evidence}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
    <Callout kind="info" title="Free credit is not a zero-priced route">
      <p>{FT.excluded.reason}</p>
    </Callout>

    <h2 id="cerebras">Cerebras: a great worker that made the parent do more</h2>
    <p>{CB.caption}</p>
    <MetricReveal stages={cerebrasStages} caption="Worker quality and parent-work delta come from the same frozen 60-pair cohort. Positive parent delta means delegation used MORE parent work." />
    <div className="x-table-wrap">
      <table className="x-table">
        <caption>Uncached parent input + output, parent-only (A) vs delegated (B)</caption>
        <thead>
          <tr>
            <th scope="col">measure</th>
            <th scope="col" className="num">A</th>
            <th scope="col" className="num">B</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>uncached parent input</td>
            <td className="num">{CB.tokens.A_uncached_parent_input.toLocaleString("en-US")}</td>
            <td className="num">{CB.tokens.B_uncached_parent_input.toLocaleString("en-US")}</td>
          </tr>
          <tr>
            <td>parent output</td>
            <td className="num">{CB.tokens.A_parent_output.toLocaleString("en-US")}</td>
            <td className="num">{CB.tokens.B_parent_output.toLocaleString("en-US")}</td>
          </tr>
          <tr>
            <td>cached parent input</td>
            <td className="num">{CB.tokens.A_cached_parent_input.toLocaleString("en-US")}</td>
            <td className="num">{CB.tokens.B_cached_parent_input.toLocaleString("en-US")}</td>
          </tr>
          <tr>
            <td>
              <strong>uncached input + output</strong>
            </td>
            <td className="num">
              <strong>{CB.tokens.A_uncached_input_plus_output.toLocaleString("en-US")}</strong>
            </td>
            <td className="num">
              <strong>{CB.tokens.B_uncached_input_plus_output.toLocaleString("en-US")}</strong>
            </td>
          </tr>
          <tr>
            <td>worker input / output</td>
            <td className="num">0 / 0</td>
            <td className="num">
              {CB.tokens.worker_input.toLocaleString("en-US")} /{" "}
              {CB.tokens.worker_output.toLocaleString("en-US")}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <Callout kind="warning" title={`Raw aggregate is +${CB.raw_aggregate_delta.toLocaleString("en-US")} — and still positive after cache control`}>
      <p>{CB.cache_controlled.note}</p>
      <p>
        Equal-cache subset: report summary{" "}
        <strong>+{cbe0.delta.toFixed(1)}</strong> [{cbe0.lo.toFixed(1)},{" "}
        {cbe0.hi.toFixed(1)}]; evidence gate{" "}
        <strong>+{cbe1.delta.toFixed(1)}</strong> [{cbe1.lo.toFixed(1)},{" "}
        {cbe1.hi.toFixed(1)}].
      </p>
    </Callout>
    <p>
      <strong>{CB.hypothesis}</strong> {CB.next}
    </p>
    <p>{CB.nemotron.note}</p>
    <MarginNote n={2} label="excluded cohort">
      {cbcoh0.why}
    </MarginNote>
    <MarginNote n={3} label="grading correction">
      {CB.grading_note} Billing: {CB.billing}
    </MarginNote>

    <h2 id="trace-routing">Real traces made the deterministic baseline win</h2>
    <p>
      The next question was more important than another synthetic verifier score: can these
      decision engines predict what z0 actually needs to do on real traces? On a grouped sealed
      split of <strong>{TR.sealed_n} decision states</strong>, the answer was no.
    </p>
    <div className="x-table-wrap">
      <table className="x-table">
        <caption>Sealed real-trace tool-family routing · {TR.classes} classes · chance {pct(TR.chance, 0)}</caption>
        <thead>
          <tr>
            <th scope="col">system</th>
            <th scope="col" className="num">accuracy</th>
            <th scope="col" className="num">macro F1</th>
            <th scope="col" className="num">p50</th>
          </tr>
        </thead>
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
    <Callout kind="warning" title="Five lines of deterministic routing beat both learned fast paths">
      <p>
        The keyword rule reached <strong>74.03%</strong>. Laya reached <strong>19.48%</strong>;
        Julia reached <strong>10.39%</strong>. Julia also lost the binary delegate-gating task:
        {pct(TR.delegate_gating.julia_accuracy, 2)} versus a {pct(TR.delegate_gating.majority_accuracy, 2)}
        majority baseline.
      </p>
      <p>{TR.note}</p>
    </Callout>

    <h2 id="decision-dataset">Julia reproduced; the missing capability is now instrumentation</h2>
    <p>
      Before rejecting Julia, we fixed the adapter to render state exactly as Julia does. That
      restored the publisher&apos;s typed CPU result exactly: <strong>
        {JU.publisher_claim_reproduction.typed_cpu.correct}/{JU.publisher_claim_reproduction.typed_cpu.total}
      </strong>. AG News also reproduced exactly at{" "}
      <strong>{JU.publisher_claim_reproduction.ag_news.correct}/{JU.publisher_claim_reproduction.ag_news.total}</strong>.
      The model is integrated faithfully; the negative result is about fit to z0&apos;s decisions,
      not a broken adapter.
    </p>
    <p>
      Confidence did not rescue it. On authored144, Julia&apos;s inference-time uncertainty
      AUROCs sit around chance ({n(JU.selective_risk.authored144_auroc.p1, 3)} p1;{" "}
      {n(JU.selective_risk.authored144_auroc.entropy, 3)} entropy), and coverage at a ≤10% empirical
      error budget was only <strong>{pct(JU.selective_risk.coverage_at_le_10pct_error.authored144, 2)}</strong>.
      {JU.selective_risk.note}.
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
      Decision Dataset v2 reconstructs per-turn state from OMP transcripts and pairs each tool call
      to its real <code>toolResult</code> by id. Four target capabilities now have enough
      outcome-backed rows to study: <code>{DD.milestone.reachable.join(", ")}</code>.
    </p>
    <Callout kind="info" title="The fifth capability is a recording gap">
      <p>{DD.milestone.verdict}.</p>
      <p>
        <code>verification_needed</code>: {DD.milestone.missing.verification_needed}.{" "}
        <code>rlm.worker_needed</code>: {DD.milestone.missing["rlm.worker_needed"]}.
      </p>
      <p>{DD.privacy}.</p>
    </Callout>

    <h2 id="route-demo">What would z0 route this task to?</h2>
    <p>{RD.caption}</p>
    <CapabilityMap functions={routeEntries} caption="Frozen decisions transcribed from the measured cohorts. Status is the evidence level, not a confidence score." />
  </>
);

const explore = (
  <>
    <h2 id="explore-tables">Exact tables</h2>

    <div className="explore-block">
      <h3>Verifier quality</h3>
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
      <h3>Delegation cohorts</h3>
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
      <h3>Harness route matrix</h3>
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

    <h2 id="claims">Claim status</h2>
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

    <h2 id="methods">Methodology</h2>
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

    <h2 id="limitations">Limitations</h2>
    <ul>
      {EX.limitations.map((l) => (
        <li key={l}>{l}</li>
      ))}
    </ul>

    <h2 id="sources">Sources &amp; receipts</h2>
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

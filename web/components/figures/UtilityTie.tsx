/**
 * Figure — one state where the frozen gate cannot tell right from wrong.
 *
 * Reference component: the reference's crowded dot layer — the `corpusPlot`
 * circles (r 3, `var(--sb-secondary)`) and the `replayPlot` per-event marks —
 * carried over as a beeswarm, in the reference's own `.figure` shell.
 *
 * The vertical axis is a real measured dimension: `decision_ms`, on the same
 * log scale as the corpus figure. The horizontal stagger is not noise and not
 * a random number — it is `sha256(run_id + state_id + arm + repetition)`
 * folded into a fixed offset, computed once at build time and shipped in
 * `phase1b-components.json`. Nothing here is generated in the browser.
 *
 * What the figure shows is the pathology the densification exposed:
 * on `tool_fails` the frozen 4000 ms utility returns **exactly -1.000** for
 * every one of the 39 draws — the one arm that answers correctly, and every
 * arm that answers incorrectly, alike. The gate therefore sees no utility
 * difference between the right answer and the wrong answer.
 */

export type UtilityPoint = {
  arm: string;
  alias: string | null;
  ms: number;
  correct: boolean;
  withinBudget: boolean;
  utility: number;
  jitter: number;
  rep: number;
};

export type UtilityData = {
  state: string;
  budgetMs: number;
  frozenUtility: number;
  distinctUtilities: number[];
  title: string;
  points: UtilityPoint[];
  correctArms: string[];
  wrongArms: string[];
  correctP50Ms: number | null;
  wrongMedianMs: number | null;
};

const W = 500;
const H = 254;
const X0 = 40;
const X1 = 470;
const TOP = 40;
const BASE = 214;

export default function UtilityTie({ d }: { d: UtilityData }) {
  const ms = d.points.map((p) => p.ms).filter((m) => m > 0);
  const lo = Math.floor(Math.log10(Math.min(...ms, d.budgetMs)));
  const hi = Math.ceil(Math.log10(Math.max(...ms, d.budgetMs)));

  // One lane per arm so points never collide vertically; the horizontal
  // offset within the lane is the build-time sha256 jitter.
  const arms = [...new Set(d.points.map((p) => p.arm))].sort();
  const lane = (arm: string) => arms.indexOf(arm) / Math.max(1, arms.length - 1);
  const xOf = (m: number) =>
    X0 + ((Math.log10(Math.max(m, 1e-6)) - lo) / (hi - lo)) * (X1 - X0);
  const yOf = (arm: string) => TOP + lane(arm) * (BASE - TOP);

  const budgetX = xOf(d.budgetMs);

  return (
    <figure className="figure">
      <p className="corpusTitle">{d.title}</p>
      <p className="corpusHeadline">
        <span>
          state <code>{d.state}</code>
        </span>
        <span className="corpusHeadline-sep"> · </span>
        <span>{d.points.length} draws</span>
        <span className="corpusHeadline-sep"> · </span>
        <span>
          distinct frozen utilities: {d.distinctUtilities.map((u) => u.toFixed(3)).join(", ")}
        </span>
      </p>

      <svg
        className="corpusPlot"
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label={`Beeswarm of ${d.points.length} draws on state ${d.state} by measured decision latency, one lane per arm. Every draw scores the same frozen utility of ${d.frozenUtility}, including the only arm that answers correctly, which lands past the ${d.budgetMs} ms budget.`}
      >
        <rect
          x={budgetX}
          y={TOP - 14}
          width={X1 - budgetX}
          height={BASE - TOP + 32}
          fill="var(--sb-error)"
          fillOpacity={0.05}
        />
        <line x1={budgetX} y1={TOP - 14} x2={budgetX} y2={BASE + 18} stroke="var(--sb-error)" strokeDasharray="3 3" />
        <text className="corpusLabel" x={X1} y={TOP - 20} textAnchor="end">
          past the {d.budgetMs.toLocaleString()} ms budget → utility {d.frozenUtility.toFixed(3)}
        </text>

        {[0, 1, 2, 3].map((i) => {
          const e = lo + ((hi - lo) / 3) * i;
          const x = X0 + ((e - lo) / (hi - lo)) * (X1 - X0);
          return (
            <g key={e}>
              <line x1={x} y1={TOP - 8} x2={x} y2={BASE + 14} stroke="var(--sb-bg-muted)" />
              <text className="corpusLabel" x={x} y={BASE + 30} textAnchor="middle">
                {10 ** e >= 1000 ? `${10 ** e / 1000}k` : `${10 ** e}`}
              </text>
            </g>
          );
        })}
        <text className="corpusNumber" x={X1} y={BASE + 48} textAnchor="end">
          decision latency · ms, log scale
        </text>

        {d.points.map((p, i) => (
          <circle
            key={`${p.arm}-${p.rep}-${i}`}
            cx={xOf(p.ms) + p.jitter * 26}
            cy={yOf(p.arm) + (p.jitter * 8)}
            r={3}
            fill={p.correct ? "var(--sb-secondary)" : "var(--sb-text-light)"}
            stroke={p.correct ? "var(--sb-secondary)" : "var(--sb-text-light)"}
            strokeWidth={1.2}
            fillOpacity={0.85}
          >
            <title>
              {p.arm} · rep {p.rep} · {p.ms} ms ·{" "}
              {p.correct ? "correct" : "incorrect"} · utility {p.utility.toFixed(3)}
            </title>
          </circle>
        ))}

        {arms.map((a) => (
          <text
            key={a}
            className="corpusLabel"
            x={X0 - 6}
            y={yOf(a) + 3}
            textAnchor="end"
          >
            {a.replace(/^(compiler|unfiltered)\+/, "").slice(0, 16)}
          </text>
        ))}
      </svg>

      <div className="corpusLegend">
        <span>
          <i />
          answered correctly
        </span>
        <span>
          <i />
          answered incorrectly
        </span>
        <span>
          <i className="swatch-rule" />
          {d.budgetMs.toLocaleString()} ms budget
        </span>
      </div>

      <figcaption>
        one state, {d.points.length} draws, and a single frozen utility value:{" "}
        <strong>
          {d.distinctUtilities.map((u) => u.toFixed(3)).join(" / ")}
        </strong>
        . The only arms that answer <code>{d.state}</code> correctly are the two Qwen3.5-9B arms,
        at a median {d.correctP50Ms?.toLocaleString()} ms — past the frozen{" "}
        {d.budgetMs.toLocaleString()} ms budget, so the utility clamps and returns{" "}
        {d.frozenUtility.toFixed(3)}. The arms that answer it <em>incorrectly</em> inside the
        budget score exactly the same {d.frozenUtility.toFixed(3)}. <strong>correct-but-slow and
        wrong-but-fast are indistinguishable to the gate on this state</strong>, so the gate keeps
        the cheap incorrect arm. On 26 of 28 states the gate&rsquo;s owner is correct in all three
        draws; <code>{d.state}</code> is one of the two where it is not, and it is the one state
        where the owner is worse in success than the best measured arm. This is reported, not
        fixed: the brief forbids moving the measurements and the gate in the same pass.
      </figcaption>
    </figure>
  );
}

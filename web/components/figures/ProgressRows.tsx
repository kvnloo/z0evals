/**
 * Figure — how far each arm gets through the suite.
 *
 * Reference component: the study module's `progressRow` / `progressLabel` /
 * `progressPlot` / `progressScale` / `progressValue` / `replayAxisY`.
 *
 * Geometry is the reference's:
 *   viewBox              0 0 564 96
 *   preserveAspectRatio  none          (the drawing is stretched, by design)
 *   .progressRow grid    138px minmax(0,1fr) 7ch, gap --space-4
 *   .progressPlot        height --space-24 (96px)
 *   .progressScale       uppercase, letter-spacing .04em, 10px, --sb-text-light
 *   .progressValue       mono, --text-xs, --sb-text-muted, right aligned
 *
 * Each row is a real cumulative trajectory: walk the 28 states in a fixed
 * order and count states the arm got right on a majority of its three
 * repetitions. That is a majority-of-three reading, not a best-of-three one;
 * a single reading per arm would hide exactly the disagreement the next
 * figure is about.
 */

export type ProgressRow = {
  arm: string;
  label: string;
  alias: string | null;
  solved: number;
  total: number;
  compilerFirst: boolean;
  points: [number, number][];
};

export type ProgressData = {
  title: string;
  axisLabel: string;
  total: number;
  rows: ProgressRow[];
};

const W = 564;
const H = 96;

export default function ProgressRows({ d }: { d: ProgressData }) {
  return (
    <figure className="figure">
      <p className="corpusTitle">{d.title}</p>

      <div className="progressScale">
        <span>0 states</span>
        <span>{d.axisLabel}</span>
        <span>{d.total} states</span>
      </div>

      {d.rows.map((r) => {
        const path = r.points
          .map(([x, y], i) => `${i === 0 ? "M" : "L"}${((x / 100) * W).toFixed(2)} ${(H - (y / r.total) * H).toFixed(2)}`)
          .join(" ");
        return (
          <div className="progressRow" key={r.arm}>
            <span className="progressLabel">
              <span>{r.label}</span>
              <span>{r.compilerFirst ? "compiler-first" : "unfiltered"}</span>
            </span>
            <svg
              className="progressPlot"
              viewBox={`0 0 ${W} ${H}`}
              preserveAspectRatio="none"
              role="img"
              aria-label={`${r.label}: ${r.solved} of ${r.total} states solved on a majority of three repetitions.`}
            >
              <line x1={0} y1={H} x2={W} y2={H} stroke="var(--sb-border)" />
              <line x1={0} y1={0} x2={W} y2={0} stroke="var(--sb-bg-muted)" />
              <path
                d={`${path} L${W} ${H} L0 ${H} Z`}
                fill="var(--sb-highlight-soft)"
                stroke="none"
              />
              <path
                d={path}
                fill="none"
                stroke={r.compilerFirst ? "var(--sb-secondary)" : "var(--sb-text-light)"}
                strokeWidth={1.5}
                vectorEffect="non-scaling-stroke"
              />
            </svg>
            <span className="progressValue">
              {r.solved}/{r.total}
            </span>
          </div>
        );
      })}

      <figcaption>
        Cumulative states solved as the suite is walked in a fixed order, counting a state only
        when the arm got it right on a majority of its three repetitions. The two Qwen3.5-9B arms
        finish at {d.rows[0]?.solved ?? 0}/{d.total} and are indistinguishable here; what separates
        them is not how many states they solve but whether the compiler is standing in front of
        them, which the dangerous-selection column above settles.{" "}
        <strong>PreserveAspectRatio is none</strong> on these plots, as in the reference: the
        viewBox is a coordinate system, not an aspect contract, so the stroke is pinned with
        <code> non-scaling-stroke</code> to stay 1.5px however wide the column gets.
      </figcaption>
    </figure>
  );
}

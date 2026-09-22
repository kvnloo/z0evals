/**
 * Figure — every arm on the same 28 states.
 *
 * Reference component: the study module's `modelBoard` / `modelHead` /
 * `modelRow` / `modelName` / `modelCell` / `modelTrack` / `modelReadings`,
 * inside a `.figure`.
 *
 * Markup is the reference's, element for element:
 *
 *   .modelBoard
 *     .modelHead[aria-hidden]   <span/> + one <span> per metric
 *     .modelRow[data-model]
 *       .modelName
 *       .modelCell  > .modelTrack[aria-hidden] > span[style=width]  +  <strong>
 *       …
 *     .modelReadings
 *
 * Track geometry is the reference's: the track is `--space-2` (8px) tall,
 * chamfered with `clip-path: polygon(0 0, 97% 0, 100% 35%, 100% 100%, 3% 100%, 0 65%)`,
 * and the fill carries `var(--sb-secondary)` on the reference arm and
 * `var(--sb-text-muted)` on the others.
 *
 * Warm p50 is computed with exactly the definition behind the headline
 * numbers — median `decision_ms` over `cold_or_warm == "warm_invocation"`
 * rows, rounded — verified against the summary (195 / 1993 / 3603 ms).
 */

export type BoardCell = { value: string; frac: number; hot: boolean; sub?: string };

export type BoardRow = {
  arm: string;
  label: string;
  alias: string | null;
  n: number;
  correct: number;
  wrong: number;
  trials: number;
  successRate: number;
  medianMs: number | null;
  medianBasis: string;
  warmCalls: number;
  dangerous: number;
  compilerFirst: boolean;
  readings: string;
  cells: BoardCell[];
};

export type ModelBoardData = {
  title: string;
  columns: string[];
  rows: BoardRow[];
};

export type Coverage = {
  comparisonArms: number;
  comparisonRows: number;
  coldProbeArms: string[];
  coldProbeRows: number;
  coldProbeStates: string[];
  armsBelowThreeRepetitions: Record<string, string[]>;
  note: string;
};

export default function ModelBoard({
  d,
  coverage,
}: {
  d: ModelBoardData;
  coverage: Coverage;
}) {
  const short = Object.entries(coverage.armsBelowThreeRepetitions);

  return (
    <figure className="figure">
      <p className="corpusTitle">{d.title}</p>
      <p className="corpusHeadline">
        <span>{coverage.comparisonArms} comparison arms</span>
        <span className="corpusHeadline-sep"> · </span>
        <span>{coverage.comparisonRows.toLocaleString()} receipts</span>
        <span className="corpusHeadline-sep"> · </span>
        <span>28 states × 3 repetitions</span>
      </p>

      <div className="modelBoard">
        <div className="modelHead" aria-hidden="true">
          <span />
          {d.columns.map((c) => (
            <span key={c}>{c}</span>
          ))}
        </div>

        {d.rows.map((r) => (
          <div className="modelRow" data-model={r.compilerFirst ? "jev" : undefined} key={r.arm}>
            <span className="modelName">{r.label}</span>
            {r.cells.map((c, i) => (
              <span className="modelCell" key={d.columns[i]}>
                <span className="modelTrack" aria-hidden="true">
                  <span
                    style={{
                      width: `${(c.frac * 100).toFixed(4)}%`,
                      background: r.compilerFirst
                        ? "var(--sb-secondary)"
                        : "var(--sb-text-muted)",
                    }}
                  />
                </span>
                <strong data-hot={c.hot || undefined}>
                  {c.value}
                  {c.sub && <small className="modelCellSub">{c.sub}</small>}
                </strong>
              </span>
            ))}
          </div>
        ))}
      </div>

      <div className="modelReadings">
        {d.rows.map((r) => (
          <span key={r.arm}>
            <strong>{r.label}</strong> — {r.readings}
          </span>
        ))}
      </div>

      <figcaption>
        {coverage.comparisonArms} arms walked all 28 states three times each.{" "}
        <strong>{coverage.coldProbeArms.length} further arms are deliberately absent</strong>:
        they are single-state cold-start probes ({coverage.coldProbeRows} receipts on{" "}
        <code>{coverage.coldProbeStates.join(", ")}</code>), which measure load latency, not
        bounded-choice accuracy — ranking a 1.000 on three draws beside the 84-decision arms
        would be a lie of arithmetic.
        {short.length > 0 && (
          <>
            {" "}
            {short.map(([arm, states]) => (
              <span key={arm}>
                <code>{arm}</code> carries {states.length} states at n=2 rather than n=3 (
                {states.join(", ")}), so its row is a 76-receipt reading, not 84.
              </span>
            ))}
          </>
        )}{" "}
        the dangerous column is the count of draws that <em>selected</em> a dangerous action:
        six, all from unfiltered hammer3b, which is why every compiler-first row reads zero.
        exposed-but-not-selected draws are recorded on every row and counted elsewhere.
      </figcaption>
    </figure>
  );
}

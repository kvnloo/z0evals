/**
 * Figure pair — what one reading licenses versus what 84 readings license.
 *
 * Reference components: `forecastPair` (`forecastCurve`, viewBox 0 0 300 200,
 * preserveAspectRatio none, one shaded polygon plus three polylines) and
 * `errorPlot` / `errorSpread` (viewBox 0 0 300 68, preserveAspectRatio none,
 * a thick 12px interval bar with a centre marker and a vertical reference
 * rule in `var(--sb-text-light)`).
 *
 * Both figures are the reference's own geometry. Every interval is a Wilson
 * 95% score interval computed from the measured counts in this run — no
 * normal approximation, no bootstrap, no resampling.
 *
 * The argument the pair makes is the one the reference makes: an interval
 * drawn from three draws is ~56 points wide and tells you almost nothing,
 * while the same estimator over 84 draws is ~11 points wide. The holdout
 * control is the interval on a single state's three repetitions.
 */

export type ErrRow = {
  arm: string;
  label: string;
  alias: string | null;
  n: number;
  correct: number;
  rate: number;
  lo: number;
  hi: number;
  singleLo: number;
  singleHi: number;
};

export type ForecastData = {
  title: string;
  referenceRate: number;
  referenceArm: string | null;
  curve: [number, number, number, number][];
  errors: ErrRow[];
};

const CW = 300;
const CH = 200;
const EW = 300;
const EH = 68;
const PAD_X = 6;
const PAD_Y = 10;

const pct = (v: number) => `${(v * 100).toFixed(1)}%`;

export default function ForecastPair({ d }: { d: ForecastData }) {
  const cx = (p: number) => PAD_X + (p / 100) * (CW - PAD_X * 2);
  const cy = (v: number) => CH - PAD_Y - v * (CH - PAD_Y * 2);

  const band = d.curve.length
    ? [
        d.curve.map(([x, , hi]) => `${cx(x)},${cy(hi)}`).join(" "),
        [...d.curve].reverse().map(([x, lo]) => `${cx(x)},${cy(lo)}`).join(" "),
      ].join(" ")
    : "";
  const mid = d.curve.map(([x, , , r]) => `${cx(x)},${cy(r)}`).join(" ");

  const worst = d.errors.reduce<ErrRow | null>(
    (a, b) => (a === null || b.hi - b.lo > a.hi - a.lo ? b : a),
    null,
  );
  const best = d.errors.reduce<ErrRow | null>(
    (a, b) => (a === null || b.hi - b.lo < a.hi - a.lo ? b : a),
    null,
  );

  return (
    <figure className="figure">
      <p className="corpusTitle">{d.title}</p>

      <div className="forecastPair">
        <div className="forecastPane">
          <div className="plotMeta">
            <span>{d.referenceArm}</span>
            <span>{d.curve.length} receipts</span>
          </div>
          <svg
            className="forecastCurve"
            viewBox={`0 0 ${CW} ${CH}`}
            preserveAspectRatio="none"
            role="img"
            aria-label={`Wilson 95% interval on the best measured arm as its receipts accumulate, ending at ${pct(d.referenceRate)}.`}
          >
            {[0, 0.25, 0.5, 0.75, 1].map((g) => (
              <line
                key={g}
                x1={PAD_X}
                y1={cy(g)}
                x2={CW - PAD_X}
                y2={cy(g)}
                stroke="var(--sb-bg-muted)"
              />
            ))}
            <polygon points={band} fill="var(--sb-highlight-soft)" />
            {d.curve.length > 0 && (
              <>
                <polyline
                  points={d.curve.map(([x, lo]) => `${cx(x)},${cy(lo)}`).join(" ")}
                  fill="none"
                  stroke="var(--sb-secondary)"
                  strokeWidth={1}
                  vectorEffect="non-scaling-stroke"
                />
                <polyline
                  points={d.curve.map(([x, , hi]) => `${cx(x)},${cy(hi)}`).join(" ")}
                  fill="none"
                  stroke="var(--sb-secondary)"
                  strokeWidth={1}
                  vectorEffect="non-scaling-stroke"
                />
              </>
            )}
            <polyline
              points={mid}
              fill="none"
              stroke="var(--sb-text)"
              strokeWidth={1.5}
              vectorEffect="non-scaling-stroke"
            />
          </svg>
        </div>

        <div className="forecastPane">
          <div className="plotMeta">
            <span>per-arm 95% interval</span>
            <span>n = {best?.n ?? 0}</span>
          </div>
          <div className="errorPlot">
          <svg
            className="errorSpread"
            viewBox={`0 0 ${EW} ${EH}`}
            preserveAspectRatio="none"
            role="img"
            aria-label="wilson 95% intervals for every arm, narrowest to widest."
          >
            <line
              x1={EW * d.referenceRate}
              y1={0}
              x2={EW * d.referenceRate}
              y2={EH}
              stroke="var(--sb-text-light)"
              vectorEffect="non-scaling-stroke"
            />
            {d.errors.map((e, i) => {
              const y = 10 + i * ((EH - 20) / Math.max(1, d.errors.length - 1));
              const w = Math.max(0.5, e.hi - e.lo);
              return (
                <g key={e.arm}>
                  <line
                    x1={EW * e.lo}
                    y1={y}
                    x2={EW * e.hi}
                    y2={y}
                    stroke={e.rate === d.referenceRate ? "var(--sb-secondary)" : "var(--sb-text-muted)"}
                    strokeWidth={Math.max(1, (12 / Math.max(1, d.errors.length)) * 1.6)}
                    strokeOpacity={0.5}
                    vectorEffect="non-scaling-stroke"
                  >
                    <title>
                      {e.label}: {pct(e.rate)} (95% ci {pct(e.lo)}–{pct(e.hi)}), n={e.n},
                      width {pct(w)}
                    </title>
                  </line>
                  <circle cx={EW * e.rate} cy={y} r={1.6} fill="var(--sb-text)" />
                </g>
              );
            })}
          </svg>
          </div>
        </div>
      </div>

      <div className="errorLabels">
        <span>single reading (3 draws): {pct(d.errors[0]?.singleLo ?? 0)}–{pct(d.errors[0]?.singleHi ?? 0)}</span>
        <span>
          widest arm interval: {worst ? pct(worst.hi - worst.lo) : "—"}{" "}
          <span className="quiet">({worst?.label})</span>
        </span>
        <span>
          narrowest: {best ? pct(best.hi - best.lo) : "—"}{" "}
          <span className="quiet">({best?.label})</span>
        </span>
      </div>

      <div className="legend">
        <span>
          <i className="swatch-line" style={{ borderTopColor: "var(--sb-secondary)" }} />
          interval edge
        </span>
        <span>
          <i className="swatch-line" style={{ borderTopColor: "var(--sb-text)" }} />
          running point estimate
        </span>
        <span>
          <i className="swatch-rule" />
          best measured arm
        </span>
      </div>

      <figcaption>
        intervals are wilson 95% score intervals over the measured counts in this run. the
        left panel walks {d.referenceArm} receipt by receipt; the shaded band is the interval
        the data licenses at each point, and it only commits to ±{((best?.hi ?? 0) - (best?.lo ?? 0)) * 50 < 0 ? 0 : Math.round(((best?.hi ?? 0) - (best?.lo ?? 0)) * 50)} points once the
        receipts accumulate. the right panel is the same estimator on every arm at once: the
        widest honest interval on this page is {worst ? pct(worst.hi - worst.lo) : "—"} wide, on
        an arm with only {worst?.n ?? 0} draws.{" "}
        <strong>one reading is not a forecast.</strong> A single state at three repetitions
        licenses {pct(d.errors[0]?.singleLo ?? 0)}–{pct(d.errors[0]?.singleHi ?? 0)}, which is
        consistent with almost any true rate; that is why no arm is ranked on fewer than 76
        receipts and why the six cold-start probes are excluded from every comparison.
      </figcaption>
    </figure>
  );
}

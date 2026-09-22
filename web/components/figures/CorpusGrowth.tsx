/**
 * Figure — where the 1,102 receipts sit.
 *
 * Reference component: the study module's `corpusPlot` + `corpusTitle` +
 * `corpusHeadline` + `corpusLegend`, inside a `.figure`.
 *
 * Geometry is the reference's, read back from a real browser:
 *   viewBox       0 0 500 254
 *   plot area     x 110 → 486, baseline y 140, top y 36
 *   bar pitch     17.9px (reference measured 17.3px for ~22 bars)
 *   bar fill      var(--sb-border)
 *   flag dots     r 3, fill + stroke var(--sb-secondary), stroke-width 1.2
 *   gridlines     stroke var(--sb-bg-muted)
 *   axis text     .corpusLabel, 10px sans, fill var(--sb-text-muted)
 *
 * Data is every one of the 1,102 recorded receipts, placed at its own measured
 * `decision_ms` on the log axis. The dots are the draws that actually selected
 * a dangerous action — six of them, all from `unfiltered+hammer2.1_3b`. The
 * deterministic compiler's rules-only baseline (0.006 ms) is excluded from the
 * histogram so it does not pull the axis three decades left; that is stated in
 * the caption rather than hidden.
 */

export type CorpusHistogram = {
  loExp: number;
  hiExp: number;
  bins: number[];
  max: number;
  xTicks: number[];
  xTickLabels: string[];
  flags: { ms: number; arm: string; state: string; exposed: boolean }[];
  flagLabel: string;
  axisXLabel: string;
};

export type CorpusData = {
  title: string;
  headline: string[];
  legend: { label: string; kind: string }[];
  viewBox: [number, number];
  bars: { label: string; receipts: number; dangerous: boolean; deterministic: boolean }[];
  histogram: CorpusHistogram;
};

const W = 500;
const H = 254;
const X0 = 110;
const X1 = 486;
const BASE_Y = 140;
const TOP_Y = 36;
const GRIDLINES = 4;

const log10 = (v: number) => Math.log10(v);

export default function CorpusGrowth({ d }: { d: CorpusData }) {
  const h = d.histogram;
  const span = h.hiExp - h.loExp;
  const xOf = (ms: number) =>
    X0 + ((log10(Math.max(ms, 10 ** h.loExp)) - h.loExp) / span) * (X1 - X0);

  const pitch = (X1 - X0) / h.bins.length;
  const barW = Math.max(2, pitch - 3.5);
  const yOf = (n: number) => BASE_Y - (n / h.max) * (BASE_Y - TOP_Y);

  return (
    <figure className="figure">
      <p className="corpusTitle">{d.title}</p>
      <p className="corpusHeadline">
        {d.headline.map((s, i) => (
          <span key={s}>
            {i > 0 && <span className="corpusHeadline-sep"> · </span>}
            <span>{s}</span>
          </span>
        ))}
      </p>

      <svg
        className="corpusPlot"
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label={`Histogram of ${h.bins.reduce((a, b) => a + b, 0)} recorded decisions by measured decision latency on a log scale, with ${h.flags.length} draws that selected a dangerous action marked.`}
      >
        {Array.from({ length: GRIDLINES + 1 }, (_, i) => {
          const y = TOP_Y + ((BASE_Y - TOP_Y) / GRIDLINES) * i;
          return (
            <line key={i} x1={X0} y1={y} x2={X1} y2={y} stroke="var(--sb-bg-muted)" />
          );
        })}

        {h.bins.map((n, i) =>
          n === 0 ? null : (
            <rect
              key={i}
              x={X0 + i * pitch + (pitch - barW) / 2}
              y={yOf(n)}
              width={barW}
              height={BASE_Y - yOf(n)}
              fill="var(--sb-border)"
            />
          ),
        )}

        {h.xTicks.map((t, i) =>
          i % 2 === 0 ? (
            <text key={t} className="corpusLabel" x={xOf(t)} y={BASE_Y + 26} textAnchor="middle">
              {h.xTickLabels[i]}
            </text>
          ) : null,
        )}
        <text className="corpusNumber" x={X1} y={BASE_Y + 48} textAnchor="end">
          {h.axisXLabel}
        </text>

        {h.flags.map((f, i) => (
          <circle
            key={i}
            cx={xOf(f.ms)}
            cy={TOP_Y + 8}
            r={3}
            fill="var(--sb-secondary)"
            stroke="var(--sb-secondary)"
            strokeWidth={1.2}
          >
            <title>
              {f.state} · {f.arm} · {f.ms} ms · selected a dangerous action
            </title>
          </circle>
        ))}
        <text className="corpusNumber" x={X0} y={TOP_Y - 6}>
          {h.flagLabel} ({h.flags.length})
        </text>
      </svg>

      <div className="corpusLegend">
        {d.legend.map((l) => (
          <span key={l.label}>
            <i />
            {l.label}
          </span>
        ))}
      </div>

      <figcaption>
        every one of the 1,102 receipts, at its own recorded <code>decision_ms</code>. The
        distribution is genuinely bimodal: in-process decisions land in single-digit
        milliseconds, model calls between roughly 100 ms and 4 s, with nothing in between —
        the empty bins are measured emptiness, not a smoothing artefact. The {h.flags.length}{" "}
        marked draws are the whole of the dangerous-selection count, and every one of them
        sits under 250 ms, faster than the median reasoned call. The deterministic
        compiler&rsquo;s rules-only baseline (0.006 ms, 84 receipts) is left out of the
        histogram so it does not pull the axis three decades left.
      </figcaption>
    </figure>
  );
}

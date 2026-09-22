"use client";
import { useMemo, useState } from "react";
import { useReveal } from "./useReveal";

export type CalRow = {
  arm: string; family: string; stateId: string;
  confidence: number; correct: boolean; dangerous: boolean;
};

const W = 820, TOP_H = 210, GAP = 54, BEE_H = 150;
const L = 58, R = 168, T = 24, B = 40;
const H = TOP_H + GAP + BEE_H;

/**
 * Reliability of the stated confidence.
 *
 * The reference's severity plot puts every scored item on a common axis against
 * a threshold. Ours does the same with our one calibrated signal: each point is
 * one recorded decision at its reported confidence, and the curve above asks
 * whether that number means anything.
 */
export default function Calibration({ rows, threshold = 0.5 }: {
  rows: CalRow[]; threshold?: number;
}) {
  const { ref, shown } = useReveal<HTMLDivElement>();
  const [hover, setHover] = useState<{ x: number; y: number; r: CalRow } | null>(null);

  const x = (v: number) => L + v * (W - L - R);

  const bins = useMemo(() => {
    const b = Array.from({ length: 10 }, (_, i) => ({ lo: i / 10, hi: (i + 1) / 10, n: 0, k: 0 }));
    for (const r of rows) {
      const i = Math.min(9, Math.max(0, Math.floor(r.confidence * 10)));
      b[i].n += 1;
      if (r.correct) b[i].k += 1;
    }
    return b.filter((x) => x.n > 0);
  }, [rows]);

  const topY = (acc: number) => TOP_H - B - acc * (TOP_H - T - B);

  // beeswarm: stack dots that share a confidence bucket
  const bees = useMemo(() => {
    const used: number[][] = [];
    const out: { r: CalRow; cx: number; cy: number }[] = [];
    const sorted = [...rows].sort((a, b) => a.confidence - b.confidence);
    for (const r of sorted) {
      const cx = x(r.confidence);
      const slot = Math.round(cx / 7);
      if (!used[slot]) used[slot] = [];
      let level = 0;
      while (used[slot].includes(level)) level += 1;
      used[slot].push(level);
      out.push({ r, cx, cy: TOP_H + GAP + 16 + Math.min(level, 11) * 9.5 });
    }
    return out;
  }, [rows]);

  const overconf = bins.filter((b) => b.n >= 3 && b.k / b.n < b.lo);

  return (
    <div ref={ref} style={{ position: "relative" }}>
      <svg viewBox={`0 0 ${W} ${H}`} className="chart-svg" role="img"
           aria-label="reliability of reported confidence against observed accuracy">
        {/* reliability panel */}
        {[0, 0.25, 0.5, 0.75, 1].map((t) => (
          <g key={t}>
            <line className="grid" x1={L} x2={W - R} y1={topY(t)} y2={topY(t)} />
            <text x={L - 9} y={topY(t) + 3.5} textAnchor="end" fontSize="10.5" fill="#888">
              {Math.round(t * 100)}%
            </text>
          </g>
        ))}
        <line className="axis" x1={L} x2={W - R} y1={TOP_H - B} y2={TOP_H - B} />
        <line className="axis" x1={L} x2={L} y1={T} y2={TOP_H - B} />
        <line x1={L} y1={topY(0)} x2={W - R} y2={topY(1)} stroke="#1a3029"
              strokeWidth="1" strokeDasharray="3 3" opacity="0.5" />
        <text x={W - R + 8} y={topY(1) + 4} fontSize="10.5" fill="#1a3029">perfect calibration</text>
        <text transform={`translate(13 ${T + (TOP_H - T - B) / 2}) rotate(-90)`} textAnchor="middle"
              fontSize="11" fill="#676767">observed accuracy</text>

        {bins.map((b, i) => {
          const cx = x((b.lo + b.hi) / 2);
          const acc = b.k / b.n;
          return (
            <g key={b.lo} className="mark"
               onMouseEnter={() => setHover({ x: cx, y: topY(acc), r: null as unknown as CalRow })}
               onMouseLeave={() => setHover(null)}>
              <line x1={cx} y1={TOP_H - B} x2={cx} y2={topY(acc)} stroke="#29916e" strokeWidth="1" opacity="0.25" />
              <circle cx={cx} cy={topY(acc)} r={3 + Math.min(4, Math.sqrt(b.n) / 2.4)} fill="#29916e"
                      style={{ opacity: shown ? 1 : 0, transition: `opacity .4s ease ${i * 60}ms` }} />
              <text x={cx} y={topY(acc) - 9} textAnchor="middle" fontSize="9.5" fill="#29916e">n={b.n}</text>
            </g>
          );
        })}

        {/* beeswarm panel */}
        <text x={L} y={TOP_H + GAP - 10} fontSize="11" fill="#888">
          every recorded decision at its stated confidence
        </text>
        <line x1={x(threshold)} x2={x(threshold)} y1={TOP_H + GAP} y2={H - B + 6}
              stroke="#b91c1c" strokeWidth="1" strokeDasharray="4 3" opacity="0.8" />
        <text x={x(threshold) + 5} y={TOP_H + GAP - 10 + 12} fontSize="10" fill="#b91c1c">
          abstain below {threshold.toFixed(2)}
        </text>
        <line className="axis" x1={L} x2={W - R} y1={H - B + 6} y2={H - B + 6} />
        <text x={(L + W - R) / 2} y={H - 10} textAnchor="middle" fontSize="11.5" fill="#676767">
          reported confidence
        </text>

        {bees.map(({ r, cx, cy }, i) => (
          <circle key={`${r.stateId}-${r.arm}-${i}`} className="mark"
                  cx={cx} cy={cy} r="2.6"
                  fill={r.correct ? "#29916e" : "#b91c1c"}
                  style={{ opacity: shown ? 0.85 : 0, transition: `opacity .5s ease ${Math.min(i, 60) * 8}ms` }}
                  onMouseEnter={() => setHover({ x: cx, y: cy, r })}
                  onMouseLeave={() => setHover(null)} />
        ))}

        {[0, 0.25, 0.5, 0.75, 1].map((t) => (
          <text key={t} x={x(t)} y={H - B + 22} textAnchor="middle" fontSize="10.5" fill="#888">
            {t.toFixed(2)}
          </text>
        ))}
      </svg>

      {hover?.r ? (
        <div className="tooltip" style={{ left: `${(hover.x / W) * 100}%`, top: `${(hover.y / H) * 100}%`,
                                          transform: "translate(10px,-130%)" }}>
          {hover.r.stateId} · {hover.r.arm} · conf {hover.r.confidence.toFixed(3)} ·{" "}
          {hover.r.correct ? "correct" : "wrong"}
        </div>
      ) : null}

      <div className="legend">
        <span><i className="swatch" style={{ background: "#29916e" }} />verified correct</span>
        <span><i className="swatch" style={{ background: "#b91c1c" }} />wrong</span>
        <span>
          {rows.length} decisions carry a confidence
          {overconf.length ? ` · ${overconf.length} bins overstate it` : ""}
        </span>
      </div>
    </div>
  );
}

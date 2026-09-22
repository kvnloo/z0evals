"use client";
import { useReveal } from "./useReveal";

type Row = { label: string; unfiltered: boolean; count: number; n: number };

/** The safety result: the compiler removes every dangerous selection. */
export default function DangerousBars({ rows }: { rows: Row[] }) {
  const { ref, shown } = useReveal<HTMLDivElement>();
  const W = 820, rowH = 30, L = 208, R = 66, T = 28, B = 22;
  const H = T + rows.length * rowH + B;
  const max = Math.max(...rows.map((r) => r.count), 1);
  const bw = (v: number) => (v / max) * (W - L - R);

  return (
    <div ref={ref}>
      <svg viewBox={`0 0 ${W} ${H}`} className="chart-svg" role="img"
           aria-label="dangerous action selections per measured arm">
        <text x={L} y={14} fontSize="11" fill="#888">selections of a dangerous action</text>
        {rows.map((r, i) => {
          const yy = T + i * rowH;
          const c = r.unfiltered ? "#b91c1c" : "#29916e";
          const w = bw(r.count);
          return (
            <g key={r.label} className="mark">
              <text x={L - 12} y={yy + 15} textAnchor="end" fontSize="11.5" fill="#3c3836">{r.label}</text>
              <rect x={L} y={yy + 3} width={shown ? w : 0} height={15} fill={c} fillOpacity="0.85" rx="2"
                    style={{ transition: `width .6s cubic-bezier(.2,.7,.2,1) ${i * 45}ms` }} />
              <text x={L + w + 8} y={yy + 15} fontSize="11" fill={c} fontWeight="700">
                {r.count}{r.count === 0 ? ` / ${r.n}` : ` / ${r.n}`}
              </text>
            </g>
          );
        })}
        <line className="axis" x1={L} x2={L} y1={T - 6} y2={T + rows.length * rowH} />
      </svg>
      <div className="legend">
        <span><i className="swatch" style={{ background: "#29916e" }} />compiler-first: zero dangerous selections</span>
        <span><i className="swatch" style={{ background: "#b91c1c" }} />unfiltered: the legal set was never enforced</span>
      </div>
    </div>
  );
}

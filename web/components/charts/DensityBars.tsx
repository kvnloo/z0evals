"use client";
import { useReveal } from "./useReveal";

/** The evidence base itself: Phase 1 vs Phase 1B. */
export default function DensityBars({ d }: {
  d: { phase1_cells: number; phase1_cells_n1: number; phase1b_cells_n1: number;
       phase1b_cells_n_ge_3: number; phase1b_measured_cells: number; cells_n2: number;
       cells_n_ge_10: number; raw_receipts: number };
}) {
  const { ref, shown } = useReveal<HTMLDivElement>();
  const groups = [
    { label: "phase 1", cells: d.phase1_cells, n1: d.phase1_cells_n1, ge3: d.phase1_cells - 4, colour: "#a8a8a8" },
    { label: "phase 1b", cells: d.phase1b_measured_cells, n1: d.phase1b_cells_n1, ge3: d.phase1b_cells_n_ge_3, colour: "#29916e" },
  ];
  const W = 820, H = 220, L = 62, R = 150, T = 26, B = 30;
  const max = d.phase1_cells;
  const bw = (v: number) => (v / max) * (W - L - R);
  const rowH = 54;

  return (
    <div ref={ref}>
      <svg viewBox={`0 0 ${W} ${H}`} className="chart-svg" role="img"
           aria-label="cells at n=1 versus n at least 3, phase 1 and phase 1b">
        <text x={L} y={14} fontSize="11" fill="#888">(state, arm) cells</text>
        {groups.map((g, i) => {
          const yy = T + i * rowH;
          const w1 = bw(g.n1), w3 = bw(g.ge3);
          return (
            <g key={g.label} className="mark">
              <text x={L - 12} y={yy + 24} textAnchor="end" fontSize="11.5" fill="#3c3836">{g.label}</text>
              <rect x={L} y={yy + 8} width={shown ? w1 : 0} height={16} fill="#d9d9d9" rx="2"
                    style={{ transition: `width .6s ease ${i * 90}ms` }} />
              <text x={L + w1 + 8} y={yy + 20} fontSize="11" fill="#888">n=1: {g.n1}</text>
              <rect x={L} y={yy + 28} width={shown ? w3 : 0} height={16} fill={g.colour} rx="2"
                    style={{ transition: `width .6s ease ${i * 90 + 60}ms` }} />
              <text x={L + w3 + 8} y={yy + 40} fontSize="11" fill={g.colour} fontWeight="700">n≥3: {g.ge3}</text>
            </g>
          );
        })}
        <line className="axis" x1={L} x2={L} y1={T} y2={T + groups.length * rowH} />
      </svg>
      <div className="legend">
        <span><i className="swatch" style={{ background: "#d9d9d9" }} />single observation</span>
        <span><i className="swatch" style={{ background: "#29916e" }} />repeated ≥3 times</span>
        <span>{d.raw_receipts.toLocaleString()} receipts · {d.cells_n2} cells at n=2 · {d.cells_n_ge_10} cells at n≥10</span>
      </div>
    </div>
  );
}

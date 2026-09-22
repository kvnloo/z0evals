"use client";
import { fmtMs } from "./util";
import { useReveal } from "./useReveal";

type Row = { label: string; p50Ms: number };

/** Why residency dominates: a cold load costs more than every warm call combined. */
export default function ResidencyBars({ rows }: { rows: Row[] }) {
  const { ref, shown } = useReveal<HTMLDivElement>();
  const W = 820, H = 250, L = 46, R = 132, T = 28, B = 46;
  const max = Math.max(...rows.map((r) => r.p50Ms)) * 1.12;
  const bh = (v: number) => (v / max) * (H - T - B);
  const slot = (W - L - R) / rows.length;
  const warm = rows.find((r) => r.label.toLowerCase().includes("warm"));

  return (
    <div ref={ref}>
      <svg viewBox={`0 0 ${W} ${H}`} className="chart-svg" role="img"
           aria-label="Median milliseconds for each residency class">
        {[0, 0.5, 1].map((f) => (
          <g key={f}>
            <line className="grid" x1={L} x2={W - R} y1={H - B - f * (H - T - B)} y2={H - B - f * (H - T - B)} />
            <text x={L - 8} y={H - B - f * (H - T - B) + 3.5} textAnchor="end" fontSize="10.5" fill="#888">
              {((f * max) / 1000).toFixed(0)}s
            </text>
          </g>
        ))}
        <line className="axis" x1={L} x2={W - R} y1={H - B} y2={H - B} />
        {rows.map((r, i) => {
          const h = bh(r.p50Ms);
          const x = L + i * slot + slot * 0.22;
          const w = slot * 0.56;
          const cold = r.label.toLowerCase().includes("cold") || r.label.toLowerCase().includes("swap");
          return (
            <g key={r.label} className="mark">
              <rect x={x} y={H - B - (shown ? h : 0)} width={w} height={shown ? h : 0}
                    fill={cold ? "#1a3029" : "#29916e"} rx="2"
                    style={{ transition: `y .6s cubic-bezier(.2,.7,.2,1) ${i * 70}ms, height .6s cubic-bezier(.2,.7,.2,1) ${i * 70}ms` }} />
              <text x={x + w / 2} y={H - B + 17} textAnchor="middle" fontSize="11" fill="#3c3836">{r.label}</text>
              <text x={x + w / 2} y={H - B - h - 7} textAnchor="middle" fontSize="11.5" fontWeight="700"
                    fill={cold ? "#1a3029" : "#29916e"}>{fmtMs(r.p50Ms)}</text>
            </g>
          );
        })}
        {warm ? (
          <line x1={L} x2={W - R} y1={H - B - bh(warm.p50Ms)} y2={H - B - bh(warm.p50Ms)}
                stroke="#b91c1c" strokeWidth="1" strokeDasharray="4 3" opacity="0.7" />
        ) : null}
      </svg>
      <div className="legend">
        <span><i className="swatch" style={{ background: "#1a3029" }} />pay once (cold load / model swap)</span>
        <span><i className="swatch" style={{ background: "#29916e" }} />pay per call (warm)</span>
      </div>
    </div>
  );
}

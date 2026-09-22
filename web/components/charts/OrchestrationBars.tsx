"use client";
import { useReveal } from "./useReveal";

type Trio = Record<string, number | null>;
type Sets = { solved: Trio; correct_stops: Trio; failures_to_escalate: Trio };

/** Orchestration on the expanded cohort: solved, correct stops, escalation failures. */
export default function OrchestrationBars({ data, total }: { data: Sets; total: number }) {
  const { ref, shown } = useReveal<HTMLDivElement>();
  const models = Object.keys(data.solved);
  const metrics: [string, Trio, string][] = [
    ["solved", data.solved, "#29916e"],
    ["correct stops", data.correct_stops, "#1a3029"],
    ["failures to escalate", data.failures_to_escalate, "#b91c1c"],
  ];
  const W = 820, H = 260, L = 44, R = 18, T = 34, B = 44;
  const groupW = (W - L - R) / models.length;
  const barW = Math.min(28, (groupW - 26) / metrics.length);
  const bh = (v: number) => (v / total) * (H - T - B);

  return (
    <div ref={ref}>
      <svg viewBox={`0 0 ${W} ${H}`} className="chart-svg" role="img"
           aria-label="Orchestration outcomes per model on the expanded cohort">
        {[0, 0.25, 0.5, 0.75, 1].map((f) => (
          <g key={f}>
            <line className="grid" x1={L} x2={W - R} y1={H - B - f * (H - T - B)} y2={H - B - f * (H - T - B)} />
            <text x={L - 8} y={H - B - f * (H - T - B) + 3.5} textAnchor="end" fontSize="10.5" fill="#888">
              {Math.round(f * total)}
            </text>
          </g>
        ))}
        <line className="axis" x1={L} x2={W - R} y1={H - B} y2={H - B} />
        {models.map((m, mi) => {
          const gx = L + mi * groupW;
          return (
            <g key={m}>
              {metrics.map(([label, vals, colour], k) => {
                const v = vals[m];
                const x = gx + (groupW - barW * metrics.length) / 2 + k * barW;
                if (v == null) {
                  return (
                    <g key={label}>
                      <rect x={x} y={H - B - 2} width={barW - 5} height={2} fill="#d9d9d9" />
                      <text x={x + (barW - 5) / 2} y={H - B - 8} textAnchor="middle" fontSize="10" fill="#a8a8a8">n/a</text>
                    </g>
                  );
                }
                const h = bh(v);
                return (
                  <g key={label}>
                    <rect x={x} y={H - B - (shown ? h : 0)} width={barW - 5} height={shown ? h : 0}
                          fill={colour} fillOpacity="0.88" rx="2"
                          style={{ transition: `y .55s cubic-bezier(.2,.7,.2,1) ${(mi * 3 + k) * 45}ms, height .55s cubic-bezier(.2,.7,.2,1) ${(mi * 3 + k) * 45}ms` }} />
                    <text x={x + (barW - 5) / 2} y={H - B - h - 5} textAnchor="middle" fontSize="10.5"
                          fill={colour} fontWeight="700">{v}</text>
                  </g>
                );
              })}
              <text x={gx + groupW / 2} y={H - B + 18} textAnchor="middle" fontSize="11.5" fill="#3c3836">{m}</text>
            </g>
          );
        })}
      </svg>
      <div className="legend">
        {metrics.map(([label, , colour]) => (
          <span key={label}><i className="swatch" style={{ background: colour }} />{label}</span>
        ))}
        <span>of {total} scenarios · n/a = not measured</span>
      </div>
    </div>
  );
}

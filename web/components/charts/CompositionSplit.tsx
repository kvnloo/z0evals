"use client";
import { useReveal } from "./useReveal";

type Variant = { id: string; label: string; correct: number; helped: number; hurt: number };

/** Composition did not pay: both variants helped zero states and hurt several. */
export default function CompositionSplit({
  base, baseCorrect, total, variants,
}: { base: string; baseCorrect: number; total: number; variants: Variant[] }) {
  const { ref, shown } = useReveal<HTMLDivElement>();
  const rows = [{ id: base, label: "Qwen 4B alone", correct: baseCorrect, helped: 0, hurt: 0 }, ...variants];
  const W = 820, rowH = 62, L = 158, R = 96, T = 30, B = 26;
  const H = T + rows.length * rowH + B;
  const mid = L + (W - L - R) / 2;
  const half = (W - L - R) / 2;
  const scale = (v: number) => (v / total) * half;

  return (
    <div ref={ref}>
      <svg viewBox={`0 0 ${W} ${H}`} className="chart-svg" role="img"
           aria-label="Correct states, and states helped or hurt, per composition">
        <text x={mid - 10} y={16} textAnchor="end" fontSize="10.5" fill="#888">helped</text>
        <text x={mid + 10} y={16} textAnchor="start" fontSize="10.5" fill="#888">hurt</text>
        <line className="axis" x1={mid} x2={mid} y1={T - 14} y2={H - B} />
        {rows.map((r, i) => {
          const yy = T + i * rowH;
          const hurtW = scale(r.hurt);
          return (
            <g key={r.id} className="mark">
              <text x={L - 12} y={yy + 20} textAnchor="end" fontSize="11.5" fill="#3c3836">{r.label}</text>
              <text x={L - 12} y={yy + 36} textAnchor="end" fontSize="10.5" fill="#888">
                {r.correct}/{total} correct
              </text>
              {r.hurt > 0 ? (
                <>
                  <rect x={mid} y={yy + 6} width={shown ? hurtW : 0} height={22} fill="#b91c1c" fillOpacity="0.85" rx="2"
                        style={{ transition: `width .6s cubic-bezier(.2,.7,.2,1) ${i * 80}ms` }} />
                  <text x={mid + hurtW + 8} y={yy + 21} fontSize="11" fill="#b91c1c" fontWeight="700">
                    {r.hurt} hurt
                  </text>
                  <text x={mid + 8} y={yy + 38} fontSize="10.5" fill="#888">0 helped</text>
                </>
              ) : (
                <text x={mid + 8} y={yy + 21} fontSize="11" fill="#888">baseline</text>
              )}
            </g>
          );
        })}
      </svg>
      <div className="legend">
        <span>states out of {total} on which the upstream artifact was delivered and consumed</span>
      </div>
    </div>
  );
}

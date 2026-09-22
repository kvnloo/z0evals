"use client";
import type { Family } from "@/data/types";
import { useReveal } from "./charts/useReveal";

/**
 * Per-family rows with an inline sparkline and a score, matching the reference's
 * task rows ("Brief writing · 27.5 min · 166 runs · ▁▂▃ · 8/8").
 *
 * The sparkline is the per-state mean success rate within the family, in sweep
 * order. The score is how many of the family's states every measured arm got
 * right — the same "8/8" shape, over states instead of runs.
 */
export default function FamilySparklines({ families, selected = null, onSelect }: {
  families: (Family & { sparkline?: number[]; fullySolvedStates?: number })[];
  selected?: string | null;
  /** Optional: omitted when rendered from a server component. */
  onSelect?: (f: string | null) => void;
}) {
  const pick = (f: string | null) => onSelect?.(f);
  const { ref, shown } = useReveal<HTMLDivElement>(0.2);
  const SW = 88, SH = 22;

  const spark = (vals: number[]) => {
    if (!vals.length) return null;
    const n = vals.length;
    const sx = (i: number) => (n === 1 ? SW / 2 : (i / (n - 1)) * (SW - 3) + 1.5);
    const sy = (v: number) => SH - 2 - v * (SH - 4);
    return {
      d: vals.map((v, i) => `${i ? "L" : "M"}${sx(i).toFixed(1)},${sy(v).toFixed(1)}`).join(" "),
      dots: vals.map((v, i) => ({ cx: sx(i), cy: sy(v), v })),
    };
  };

  return (
    <div ref={ref}>
      <div className="fam-rows">
        {families.map((f, i) => {
          const vals = f.sparkline ?? [];
          const sp = spark(vals);
          const solved = f.fullySolvedStates ?? 0;
          const active = selected === f.name;
          const worst = vals.length ? Math.min(...vals) : null;
          return (
            <div key={f.name} className="fam-row" data-active={active}
                 role="button" tabIndex={0}
                 onClick={() => pick(active ? null : f.name)}
                 onKeyDown={(e) => { if (e.key === "Enter") pick(active ? null : f.name); }}>
              <div className="fam-name">
                {f.name.replace(/_/g, " ")}
                <span className="fam-sub">{f.states} state{f.states > 1 ? "s" : ""}</span>
              </div>
              <div className="fam-runs">{f.runs} runs</div>
              <div className="fam-spark">
                {sp ? (
                  <svg viewBox={`0 0 ${SW} ${SH}`} width={SW} height={SH} aria-hidden="true">
                    <path d={sp.d} fill="none" stroke="#29916e" strokeWidth="1.4"
                          style={{ opacity: shown ? 1 : 0, transition: `opacity .5s ease ${i * 60}ms` }} />
                    {sp.dots.map((d, k) => (
                      <circle key={k} cx={d.cx} cy={d.cy} r="1.9"
                              fill={d.v === 1 ? "#29916e" : d.v < 0.5 ? "#b91c1c" : "#b45309"} />
                    ))}
                  </svg>
                ) : <span style={{ color: "#ccc" }}>—</span>}
              </div>
              <div className="fam-score">
                <strong>{solved}/{f.states}</strong>
                {worst !== null && worst < 0.5 ? <span className="fam-flag">weakest {(worst * 100).toFixed(0)}%</span> : null}
              </div>
            </div>
          );
        })}
      </div>
      <div className="legend">
        <span>sparkline = per-state mean success across all measured arms, in sweep order</span>
        <span>score = states every arm solved</span>
        <span>click a family to filter</span>
      </div>
    </div>
  );
}

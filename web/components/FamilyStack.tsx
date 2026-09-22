"use client";
import { useEffect, useRef, useState } from "react";
import type { Family } from "@/data/types";

/** Stacked activity per state family — the reference's task-family summary bars. */
export default function FamilyStack({ families, selected, onSelect }: {
  families: Family[]; selected: string | null; onSelect: (f: string | null) => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [shown, setShown] = useState(true);
  useEffect(() => {
    const n = ref.current; if (!n) return;
    if (n.getBoundingClientRect().top > window.innerHeight * 0.92) {
      setShown(false);
      const io = new IntersectionObserver((e) => { if (e[0]?.isIntersecting) { setShown(true); io.disconnect(); } }, { threshold: 0.3 });
      io.observe(n);
      return () => io.disconnect();
    }
  }, []);

  const W = 860, rowH = 30, L = 132, R = 128, T = 30, B = 10;
  const H = T + families.length * rowH + B;
  const max = Math.max(...families.map((f) => f.runs));
  const total = (f: Family) => f.runs;
  const seg = (v: number) => (v / max) * (W - L - R);
  const PARTS: [keyof Family, string, string][] = [
    ["correct", "correct", "#29916e"],
    ["abstained", "abstained", "#64748b"],
    ["invalid", "invalid call", "#b45309"],
    ["dangerous", "dangerous", "#b91c1c"],
  ];

  return (
    <div ref={ref}>
      <svg viewBox={`0 0 ${W} ${H}`} className="chart-svg" role="img"
           aria-label="Stacked outcome counts per state family">
        <text x={L} y={16} fontSize="11" fill="#888">recorded runs (all arms)</text>
        {families.map((f, i) => {
          const yy = T + i * rowH;
          let dx = L;
          const active = selected === f.name;
          return (
            <g key={f.name} className="mark" style={{ cursor: "pointer", opacity: selected && !active ? 0.45 : 1 }}
               onClick={() => onSelect(active ? null : f.name)}>
              <text x={L - 10} y={yy + 15} textAnchor="end" fontSize="11.5"
                    fill={active ? "#1a3029" : "#3c3836"} fontWeight={active ? 700 : 400}>
                {f.name.replace(/_/g, " ")}
              </text>
              <text x={L - 10} y={yy + 27} textAnchor="end" fontSize="9.5" fill="#a8a8a8">
                {f.states} state{f.states > 1 ? "s" : ""}
              </text>
              {PARTS.map(([key, , colour]) => {
                const v = f[key] as number;
                const w = seg(v);
                const el = v > 0 ? (
                  <rect key={key} x={dx} y={yy + 4} width={shown ? w : 0} height={15}
                        fill={colour} fillOpacity="0.9" rx={key === "dangerous" ? 2 : 0}
                        style={{ transition: `width .5s cubic-bezier(.2,.7,.2,1) ${i * 40}ms` }}>
                    <title>{`${f.name} · ${key}: ${v}`}</title>
                  </rect>
                ) : null;
                dx += w;
                return el;
              })}
              <text x={W - R + 10} y={yy + 15} fontSize="10.5" fill="#888"
                    style={{ fontFamily: "var(--font-mono)" }}>
                {total(f)} runs
              </text>
            </g>
          );
        })}
        <line className="axis" x1={L} x2={L} y1={T - 4} y2={T + families.length * rowH - 4} />
      </svg>
      <div className="legend">
        {PARTS.map(([key, label, colour]) => (
          <span key={key}><i className="swatch" style={{ background: colour }} />{label}</span>
        ))}
        <span>click a family to filter the page</span>
      </div>
    </div>
  );
}

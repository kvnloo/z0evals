"use client";

import { useState } from "react";
import { useReveal } from "../charts/useReveal";

/**
 * Figure — every state family, with the states inside it.
 *
 * This is the reference's dense task-row shape
 * (`Brief writing · 27.5 min · 166 runs · ▁▂▃ · 8/8`) mapped onto the ten typed
 * state families this run actually measured, not a generic progress view:
 *
 *   family · receipts · success · p50 · sparkline · solved/total
 *      └─ expandable → one row per constituent state, worst-first
 *
 * The sparkline is per-state success *within* the family, so its shape is the
 * family's internal difficulty profile. The score is arms that solved each
 * state on a majority of their repetitions.
 *
 * Expansion is the point: `security` looks like one number until you open it
 * and see that all six dangerous selections live there, and `uncertainty` looks
 * merely low until you see that one of its two states is solved by **no** arm.
 */

export type FamilyStateRow = {
  state: string;
  n: number;
  arms: number;
  solvedArms: number;
  successRate: number;
  latencyP50Ms: number | null;
  dangerous: number;
  deterministic: boolean;
};

export type FamilyRow = {
  family: string;
  states: number;
  receipts: number;
  successRate: number;
  latencyP50Ms: number | null;
  dangerous: number;
  sparkline: number[];
  stateRows: FamilyStateRow[];
};

export type FamilyBoardData = {
  title: string;
  columns: string[];
  rows: FamilyRow[];
  totalStates: number;
  totalReceipts: number;
};

const SW = 88;
const SH = 22;

const pct = (v: number) => `${(v * 100).toFixed(0)}%`;
const msFmt = (v: number | null) =>
  v == null ? "—" : v >= 1000 ? `${(v / 1000).toFixed(1)} s` : `${v} ms`;

function sparkPath(vals: number[]) {
  if (!vals.length) return null;
  const n = vals.length;
  const sx = (i: number) => (n === 1 ? SW / 2 : (i / (n - 1)) * (SW - 3) + 1.5);
  const sy = (v: number) => SH - 2 - v * (SH - 4);
  return {
    d: vals.map((v, i) => `${i ? "l" : "m"}${sx(i).toFixed(1)},${sy(v).toFixed(1)}`).join(" "),
    dots: vals.map((v, i) => ({ cx: sx(i), cy: sy(v), v })),
  };
}

export default function FamilyBoard({ d }: { d: FamilyBoardData }) {
  const [open, setOpen] = useState<Set<string>>(new Set());
  const { ref, shown } = useReveal<HTMLDivElement>(0.12);

  const toggle = (fam: string) =>
    setOpen((prev) => {
      const next = new Set(prev);
      if (next.has(fam)) next.delete(fam);
      else next.add(fam);
      return next;
    });

  const allOpen = open.size === d.rows.length;

  return (
    <figure className="figure">
      <p className="corpusTitle">{d.title}</p>
      <p className="corpusHeadline">
        <span>{d.rows.length} typed families</span>
        <span className="corpusHeadline-sep"> · </span>
        <span>{d.totalStates} states</span>
        <span className="corpusHeadline-sep"> · </span>
        <span>{d.totalReceipts.toLocaleString()} receipts</span>
      </p>

      <div className="fam-head" aria-hidden="true">
        <span>family</span>
        <span>receipts</span>
        <span>success</span>
        <span>p50</span>
        <span>per-state</span>
        <span>solved</span>
      </div>

      <div ref={ref} className="fam-rows">
        {d.rows.map((f, i) => {
          const sp = sparkPath(f.sparkline);
          const isOpen = open.has(f.family);
          const solved = f.stateRows.reduce((a, s) => a + s.solvedArms, 0);
          const solvedMax = f.stateRows.reduce((a, s) => a + s.arms, 0);
          return (
            <div key={f.family} className="fam-block">
              <div
                className="fam-row"
                data-active={isOpen}
                role="button"
                tabIndex={0}
                aria-expanded={isOpen}
                onClick={() => toggle(f.family)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    toggle(f.family);
                  }
                }}
              >
                <div className="fam-name">
                  <span className="fam-caret" aria-hidden="true">
                    {isOpen ? "▾" : "▸"}
                  </span>
                  {f.family.replace(/_/g, " ")}
                  <span className="fam-sub">
                    {f.states} state{f.states > 1 ? "s" : ""}
                    {f.dangerous > 0 && (
                      <span className="fam-danger"> · {f.dangerous} dangerous</span>
                    )}
                  </span>
                </div>
                <div className="fam-runs">{f.receipts}</div>
                <div className="fam-score">{pct(f.successRate)}</div>
                <div className="fam-p50">{msFmt(f.latencyP50Ms)}</div>
                <div className="fam-spark">
                  {sp ? (
                    <svg viewBox={`0 0 ${SW} ${SH}`} width={SW} height={SH} aria-hidden="true">
                      <path
                        d={sp.d}
                        fill="none"
                        stroke="var(--color-sb-secondary)"
                        strokeWidth="1.4"
                        style={{ opacity: shown ? 1 : 0, transition: `opacity .5s ease ${i * 60}ms` }}
                      />
                      {sp.dots.map((dot, k) => (
                        <circle
                          key={k}
                          cx={dot.cx}
                          cy={dot.cy}
                          r="1.9"
                          fill={dot.v === 1 ? "var(--color-sb-secondary)"
                            : dot.v < 0.5 ? "var(--color-sb-error)" : "#b45309"}
                        />
                      ))}
                    </svg>
                  ) : (
                    <span className="fam-empty">—</span>
                  )}
                </div>
                <div className="fam-solved">
                  <strong>
                    {solved}/{solvedMax}
                  </strong>
                </div>
              </div>

              {isOpen && (
                <div className="fam-states">
                  {f.stateRows.map((s) => (
                    <div className="fam-state-row" key={s.state}>
                      <span className="fam-state-name">
                        {s.state.replace(/_/g, " ")}
                        {s.deterministic && <em className="fam-state-tag"> deterministic</em>}
                      </span>
                      <span className="fam-state-n">{s.n}</span>
                      <span
                        className="fam-state-succ"
                        data-weak={s.successRate < 0.2 ? "true" : undefined}
                      >
                        {s.solvedArms}/{s.arms}
                      </span>
                      <span className="fam-state-p50">{msFmt(s.latencyP50Ms)}</span>
                      <span className="fam-state-dang">
                        {s.dangerous > 0 ? `${s.dangerous} dangerous` : ""}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="fam-controls">
        <button
          type="button"
          className="quietButton"
          onClick={() => setOpen(allOpen ? new Set() : new Set(d.rows.map((r) => r.family)))}
        >
          {allOpen ? "collapse all" : "expand all"}
        </button>
        <span className="fam-controls-note">
          per-state success = arms that solved it on a majority of their repetitions
        </span>
      </div>

      <figcaption>
        ten families, {d.totalStates} states, {d.totalReceipts.toLocaleString()} receipts.
        open <code>security</code> and all six dangerous selections in the entire run are
        inside it. open <code>uncertainty</code> and one of its two states is solved by{" "}
        <strong>no arm at all</strong> — that is the state where the frozen gate&rsquo;s owner is
        wrong in every draw. a family-level average would have hidden both facts, which is
        why these rows expand.
      </figcaption>
    </figure>
  );
}

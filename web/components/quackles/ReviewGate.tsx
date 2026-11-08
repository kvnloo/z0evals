"use client";

import { useState } from "react";
import type { Trial } from "./types";
import { OUTCOME_COLOR, THEME_LABEL } from "./types";

const ORDER = ["promoted", "held", "tie", "split", "lost", "stopped", "rejected"];

/**
 * One night of the review gate. A tally on top, then every decision in log
 * order as a chip; selecting one opens what was tried, against what, what the
 * two reviewers said and why it landed where it did.
 */
export default function ReviewGate({ trials, counts, total }: { trials: Trial[]; counts: Record<string, number>; total: number }) {
  const [sel, setSel] = useState(trials.findIndex((t) => t.lesson === "measure before hypothesising"));
  const [scene, setScene] = useState<string | null>(null);
  const t = trials[sel] ?? trials[0];
  const scenes = Array.from(new Set(trials.map((x) => x.scene)));
  return (
    <div className="qk-gate">
      <div className="qk-tally" role="img" aria-label={ORDER.filter((o) => counts[o]).map((o) => `${counts[o]} ${o}`).join(", ")}>
        {ORDER.filter((o) => counts[o]).map((o) => (
          <div key={o} className="qk-tally-seg" style={{ flexGrow: counts[o], background: OUTCOME_COLOR[o] }}>
            <span>
              {counts[o]} {o}
            </span>
          </div>
        ))}
      </div>
      <div className="es-controls" role="group" aria-label="filter by scene">
        <button type="button" className="es-btn" aria-pressed={scene === null} onClick={() => setScene(null)}>
          all {total}
        </button>
        {scenes.map((s) => (
          <button key={s} type="button" className="es-btn" aria-pressed={scene === s} onClick={() => setScene(s)}>
            {THEME_LABEL[s]}
          </button>
        ))}
      </div>
      <div className="qk-chips" role="list" aria-label="decisions in log order">
        {trials.map((x, i) => (
          <div role="listitem" key={i} hidden={scene !== null && x.scene !== scene}>
            <button
              type="button"
              className="qk-chip"
              aria-pressed={i === sel}
              style={{ ["--c" as string]: OUTCOME_COLOR[x.outcome] }}
              onClick={() => setSel(i)}
              title={`${x.t} ${THEME_LABEL[x.scene]}: ${x.candidate}`}
            >
              <span className="qk-chip-t">{x.t}</span>
              <span className="qk-chip-o">
                {x.outcome}
                {x.count ? ` ×${x.count}` : ""}
              </span>
            </button>
          </div>
        ))}
      </div>
      <div className="qk-trial" aria-live="polite">
        <div className="qk-trial-head">
          <span className="es-chip" data-tone={t.outcome === "promoted" ? "pass" : ["lost", "rejected", "stopped"].includes(t.outcome) ? "fail" : "hold"}>
            {t.outcome}
          </span>
          <span className="es-readout">
            {t.t} CDT · {THEME_LABEL[t.scene]}
          </span>
        </div>
        <dl>
          <dt>tried</dt>
          <dd>{t.candidate}</dd>
          <dt>against</dt>
          <dd>{t.against}</dd>
          <dt>reviewers</dt>
          <dd>{t.reviewers}</dd>
          <dt>why</dt>
          <dd>{t.why}</dd>
          {t.lesson ? (
            <>
              <dt>lesson</dt>
              <dd className="qk-lesson">{t.lesson}</dd>
            </>
          ) : null}
        </dl>
      </div>
    </div>
  );
}

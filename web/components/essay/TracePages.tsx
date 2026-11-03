"use client";

import { useCallback, useId, useRef, useState, type KeyboardEvent, type ReactNode } from "react";

export type TraceItem = {
  /** tab label */
  label: string;
  /** optional group shown above a run of tabs */
  group?: string;
  /** what was asked, one sentence */
  ask: ReactNode;
  /** what came with the ask (inputs, constraints) */
  given?: ReactNode;
  /** the answer or decision, short */
  answer: ReactNode;
  /** verdict chip: free text, styled by tone */
  verdict?: { text: string; tone: "pass" | "fail" | "hold" | "neutral" };
  /** key steps of the reasoning or review, in order */
  steps: ReactNode[];
  /** the long form, behind a fold */
  full?: ReactNode;
  /** image / replay above the card */
  media?: ReactNode;
  /** one line under the card: tokens, runs, source path */
  foot?: ReactNode;
};

/** One tab per item; left/right arrows switch tabs. */
export default function TracePages({
  items,
  label,
  columns = ["ask", "answer", "reasoning"],
}: {
  items: TraceItem[];
  label: string;
  /** headings for the three columns */
  columns?: [string, string, string];
}) {
  const [i, setI] = useState(0);
  const base = useId();
  const tabs = useRef<(HTMLButtonElement | null)[]>([]);
  const go = useCallback(
    (n: number) => {
      const k = (n + items.length) % items.length;
      setI(k);
      tabs.current[k]?.focus();
    },
    [items.length],
  );
  const onKey = (e: KeyboardEvent) => {
    if (e.key === "ArrowRight") go(i + 1);
    else if (e.key === "ArrowLeft") go(i - 1);
  };
  const it = items[i];
  let lastGroup: string | undefined;
  return (
    <div className="es-trace">
      <div className="es-trace-tabs" role="tablist" aria-label={label} onKeyDown={onKey}>
        {items.map((t, k) => {
          const showGroup = t.group && t.group !== lastGroup;
          lastGroup = t.group;
          return (
            <span key={k} className="es-trace-tabwrap">
              {showGroup ? <span className="es-trace-group">{t.group}</span> : null}
              <button
                ref={(el) => {
                  tabs.current[k] = el;
                }}
                type="button"
                role="tab"
                id={`${base}-t${k}`}
                aria-selected={k === i}
                aria-controls={`${base}-p`}
                tabIndex={k === i ? 0 : -1}
                className="es-trace-tab"
                onClick={() => setI(k)}
              >
                {t.label}
              </button>
            </span>
          );
        })}
      </div>
      <div className="es-trace-card" role="tabpanel" id={`${base}-p`} aria-labelledby={`${base}-t${i}`}>
        {it.media ? <div className="es-trace-media">{it.media}</div> : null}
        <div className="es-trace-grid">
          <div className="es-trace-part">
            <div className="es-trace-k">{columns[0]}</div>
            <div>{it.ask}</div>
            {it.given ? <div className="es-trace-given">{it.given}</div> : null}
          </div>
          <div className="es-trace-part">
            <div className="es-trace-k">{columns[1]}</div>
            <div>{it.answer}</div>
            {it.verdict ? (
              <span className="es-chip" data-tone={it.verdict.tone}>
                {it.verdict.text}
              </span>
            ) : null}
          </div>
          <div className="es-trace-part es-trace-steps">
            <div className="es-trace-k">{columns[2]}</div>
            <ol>
              {it.steps.map((s, k) => (
                <li key={k}>{s}</li>
              ))}
            </ol>
            {it.full ? (
              <details className="es-fold">
                <summary>read the full record</summary>
                <div className="es-fold-body">{it.full}</div>
              </details>
            ) : null}
          </div>
        </div>
        {it.foot ? <div className="es-trace-foot">{it.foot}</div> : null}
      </div>
    </div>
  );
}

// Interactive-essay kit. Server-safe pieces live here; the pieces that need
// state (Teaser bars, SetupFigure, TracePages, Citation copy) are in their own
// "use client" files and re-exported below so a page imports one module.
//
// Pattern, after the distill-style research post: a boxed tl;dr, a three-panel
// teaser that states the result before the argument, numbered experiments, a
// figure whose setup folds behind a pill, a trace viewer for the actual
// exchanges, and a citation box. Every number on screen still has to come from
// a frozen study file, never from the page.
import type { ReactNode } from "react";
import "./essay.css";

export { default as Teaser, GrowBars } from "./Teaser";
export { default as SetupFigure } from "./SetupFigure";
export { default as TracePages, type TraceItem } from "./TracePages";
export { default as Citation } from "./Citation";
export { default as KitEmbed } from "./KitEmbed";

export function Tldr({ children }: { children: ReactNode }) {
  return (
    <div className="es-tldr" role="note">
      <span className="es-tldr-tag">tl;dr</span>
      <div className="es-tldr-body">{children}</div>
    </div>
  );
}

export function ExpHead({ n, id, children }: { n: number | string; id?: string; children: ReactNode }) {
  return (
    <div className="es-exp-head">
      <span className="es-exp-num">experiment {n}</span>
      <h3 id={id}>{children}</h3>
    </div>
  );
}

/** A provenance badge that keeps the five evidence kinds from AGENTS.md distinct. */
export type EvidenceKind = "source-reported" | "reproduced" | "prediction" | "completed" | "verified";
export function Evidence({ kind, children }: { kind: EvidenceKind; children?: ReactNode }) {
  return (
    <span className="es-evidence" data-kind={kind}>
      {kind}
      {children ? <span className="es-evidence-note">{children}</span> : null}
    </span>
  );
}

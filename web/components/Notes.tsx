import type { ReactNode } from "react";

/**
 * Reference-style footnote and margin-note system.
 *
 * The point is to get methodological caveats *out of the narration* without
 * hiding them: a claim stays readable in the body, and the qualification that
 * makes it honest sits immediately beside it.
 *
 * Two placements, one source of truth:
 *
 *   <MarginNote n={2} label="n = 2">
 *     Eight cells ran at n=2 rather than n=3.
 *   </MarginNote>
 *
 * renders as a superscript marker in the flow plus a note in the right gutter
 * on wide viewports (reflowing inline below 1200px), and the same numbered
 * entry is collected by <Footnotes /> for the appendix and for printing.
 *
 * `n` is stable: the marker and the collected entry must agree, so the note is
 * addressed by number rather than by position.
 */

export function MarginNote({
  n,
  label,
  children,
}: {
  n?: number;
  label?: string;
  children: ReactNode;
}) {
  return (
    <aside className="margin-note" id={n ? `mn-${n}` : undefined}>
      {label && <span className="margin-note-label">{label}</span>}
      {children}
      {n && (
        <a className="fn" href={`#fn-${n}`} aria-label={`Footnote ${n}`}>
          [{n}]
        </a>
      )}
    </aside>
  );
}

/** Inline superscript marker. Links to the collected entry. */
export function Fn({ n, title }: { n: number; title?: string }) {
  return (
    <a className="fn" href={`#fn-${n}`} id={`fnref-${n}`} title={title}>
      [{n}]
    </a>
  );
}

export type FootnoteItem = { n: number; text: ReactNode };

/** The collected list. Kept in sync with the markers by explicit number. */
export function Footnotes({ items }: { items: FootnoteItem[] }) {
  const sorted = [...items].sort((a, b) => a.n - b.n);
  return (
    <ol className="footnotes">
      {sorted.map((it) => (
        <li key={it.n} id={`fn-${it.n}`} value={it.n}>
          {it.text}{" "}
          <a className="fn" href={`#fnref-${it.n}`} aria-label="Back to reference">
            ↩
          </a>
        </li>
      ))}
    </ol>
  );
}

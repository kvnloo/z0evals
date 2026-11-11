"use client";

import type { ReactNode, RefObject } from "react";
import type { TocItem } from "@/components/Toc";

/**
 * Sticky 44px glass bar under the header (< 1024px). Current section label crossfades
 * on change, a 2px gold hairline shows reading progress (written by ArticleFrame in rAF
 * as transform: scaleX), and a tap opens the contents sheet. Replaces the frog FAB.
 */
export default function SectionBar({
  items,
  active,
  onOpen,
  toggle,
  buttonRef,
}: {
  items: TocItem[];
  active: string;
  onOpen: () => void;
  toggle?: ReactNode;
  buttonRef: RefObject<HTMLButtonElement | null>;
}) {
  const label = items.find((i) => i.id === active)?.label ?? items[0]?.label ?? "contents";
  return (
    <div className="section-bar">
      <div className="section-bar-row">
        <button
          ref={buttonRef}
          type="button"
          className="section-bar-button"
          data-press="row"
          aria-haspopup="dialog"
          aria-controls="toc-sheet"
          onClick={onOpen}
        >
          <span className="section-bar-kicker">on this page</span>
          <span className="section-bar-label" key={label} aria-live="off">{label}</span>
          <svg className="section-bar-chev" width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
            <path d="M2 4.5 6 8l4-3.5" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </button>
        {toggle ? <div className="section-bar-toggle">{toggle}</div> : null}
      </div>
      <span className="section-bar-progress" data-progress aria-hidden="true" />
    </div>
  );
}

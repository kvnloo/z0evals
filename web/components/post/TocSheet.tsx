"use client";

import { useEffect, useRef, type RefObject } from "react";
import Sheet from "@/components/site/Sheet";
import { haptic } from "@/lib/ux/haptics";
import type { TocItem } from "@/components/Toc";

/** Bottom sheet with every heading. Picking one closes the sheet, then scrolls once. */
export default function TocSheet({
  open,
  items,
  active,
  onClose,
  onPick,
  returnFocus,
}: {
  open: boolean;
  items: TocItem[];
  active: string;
  onClose: () => void;
  onPick: (id: string | null) => void; // null = back to top
  returnFocus: RefObject<HTMLElement | null>;
}) {
  const pending = useRef<string | null | undefined>(undefined);
  const list = useRef<HTMLUListElement>(null);

  // keep the active heading in view inside the sheet when it opens
  useEffect(() => {
    if (!open || !list.current) return;
    const el = list.current.querySelector<HTMLElement>('[data-active="true"]');
    const body = list.current.closest<HTMLElement>(".sheet-body");
    if (el && body) body.scrollTop = Math.max(0, el.offsetTop - body.clientHeight / 2);
  }, [open, active]);

  const pick = (id: string | null) => {
    haptic.select();
    pending.current = id;
    onClose();
  };

  return (
    <Sheet
      open={open}
      onClose={onClose}
      onClosed={() => {
        if (pending.current !== undefined) onPick(pending.current);
        pending.current = undefined;
      }}
      label="contents"
      returnFocus={returnFocus}
      id="toc-sheet"
      className="toc-sheet"
    >
      <nav aria-label="contents">
        <ul ref={list} className="toc-sheet-list">
          <li>
            <a href="#main" className="toc-sheet-row toc-sheet-top" data-press="row"
              onClick={(e) => { e.preventDefault(); pick(null); }}>
              ↑ top
            </a>
          </li>
          {items.map((it) => (
            <li key={it.id} style={(it.depth ?? 0) > 0 ? { paddingLeft: `${0.9 * (it.depth ?? 0)}rem` } : undefined}>
              <a
                href={`#${it.id}`}
                className="toc-sheet-row"
                data-press="row"
                data-active={active === it.id}
                aria-current={active === it.id ? "location" : undefined}
                onClick={(e) => { e.preventDefault(); pick(it.id); }}
              >
                {it.label}
              </a>
            </li>
          ))}
        </ul>
      </nav>
    </Sheet>
  );
}

"use client";
import { useEffect, useRef, type ReactNode } from "react";
import { useActiveHeading } from "@/lib/ux/useActiveHeading";

export type TocItem = { id: string; label: string; depth?: number };

/**
 * Desktop contents rail. Sticky below the header, scrolls inside itself when the list
 * is longer than the viewport (overscroll contained), and marks the active heading with
 * one gold gel bar that slides between rows (transform only). Without JS it is a plain
 * <nav> of anchor links.
 */
export default function Toc({
  items,
  onNavigate,
  active: activeProp,
  header,
}: {
  items: TocItem[];
  onNavigate?: (id: string) => void;
  active?: string;
  header?: ReactNode;
}) {
  const own = useActiveHeading(activeProp === undefined ? items.map((i) => i.id) : []);
  const active = activeProp ?? own;
  const nav = useRef<HTMLElement>(null);
  const bar = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const root = nav.current;
    const b = bar.current;
    if (!root || !b) return;
    const link = root.querySelector<HTMLElement>(`a[data-active="true"]`);
    if (!link) {
      b.style.opacity = "0";
      return;
    }
    // offsetParent is .toc-scrollable-inner (position: relative)
    b.style.opacity = "1";
    b.style.transform = `translateY(${link.offsetTop}px) scaleY(${link.offsetHeight / 32})`;
    // keep the active row inside the rail's own scroll box
    const r = link.getBoundingClientRect();
    const box = root.getBoundingClientRect();
    if (r.top < box.top + 24 || r.bottom > box.bottom - 24) {
      root.scrollTo({ top: Math.max(0, root.scrollTop + (r.top - box.top) - root.clientHeight / 3) });
    }
  }, [active]);

  return (
    <nav ref={nav} className="toc toc-sidebar toc-scrollable-container" aria-label="contents">
      {header}
      <div className="toc-scrollable-inner">
        <span ref={bar} className="toc-gel" aria-hidden="true" />
        <ul>
          {items.map((it) => (
            <li key={it.id} style={(it.depth ?? 0) > 0 ? { paddingLeft: `${0.75 * (it.depth ?? 0)}rem` } : undefined}>
              <a
                href={`#${it.id}`}
                className="toc-link"
                data-active={active === it.id}
                aria-current={active === it.id ? "location" : undefined}
                onClick={(event) => {
                  if (!onNavigate) return;
                  event.preventDefault();
                  onNavigate(it.id);
                }}
              >
                {it.label}
              </a>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
}

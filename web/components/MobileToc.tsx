"use client";

import { useEffect, useRef, useState } from "react";
import { FrogGlyph } from "./Frog";
import type { TocItem } from "./Toc";

/**
 * The reference's small-screen contents control: a fixed 64px action button
 * that opens a bottom sheet. The desktop rail is `display:none` under 890px
 * and this takes over, rather than the contents simply disappearing.
 *
 * Geometry and motion are the reference's: 64x64 button at
 * `bottom/right: 1.5rem`; backdrop fading to `#0000004d` over `.25s`; drawer
 * capped at `60vh` with `border-radius: 16px 16px 0 0` entering on
 * `transform .3s cubic-bezier(.32,.72,0,1)`.
 */
export default function MobileToc({ items }: { items: TocItem[] }) {
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState<string>(items[0]?.id ?? "");
  const drawer = useRef<HTMLDivElement>(null);

  // Scroll spy, sharing the reference's rootMargin. The rail owns the desktop
  // case; this keeps the sheet's own highlight honest when it is opened.
  useEffect(() => {
    const targets = items
      .map((i) => document.getElementById(i.id))
      .filter((el): el is HTMLElement => Boolean(el));
    if (!targets.length) return;
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) setActive(e.target.id);
        });
      },
      { rootMargin: "-100px 0px -66% 0px" },
    );
    targets.forEach((t) => io.observe(t));
    return () => io.disconnect();
  }, [items]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  // Indent nested entries the way the reference indents its `li`s.
  const depth = (label: string) => (/^\d+\.\d+/.test(label) ? 1 : 0);

  return (
    <>
      <div className="mobile-toc-fab-wrapper">
        <button
          type="button"
          className="mobile-toc-fab"
          aria-label={open ? "Close contents" : "Open contents"}
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
        >
          <FrogGlyph width={26} height={18} />
        </button>
      </div>

      <div
        className={`mobile-toc-backdrop${open ? " mobile-toc-backdrop-visible" : ""}`}
        onClick={() => setOpen(false)}
        aria-hidden="true"
      />

      <div
        ref={drawer}
        className={`mobile-toc-drawer${open ? " mobile-toc-drawer-open" : ""}`}
        role="dialog"
        aria-modal="true"
        aria-label="contents"
      >
        <div className="mobile-toc-drawer-head">
          <span>contents</span>
          <button
            type="button"
            className="mobile-toc-close"
            onClick={() => setOpen(false)}
            aria-label="close contents"
          >
            close
          </button>
        </div>
        <nav className="mobile-toc-nav">
          <ul>
            {items.map((i) => (
              <li key={i.id} style={{ paddingLeft: `${depth(i.label) * 0.75}rem` }}>
                <a
                  href={`#${i.id}`}
                  className="toc-link-frog"
                  data-active={active === i.id}
                  onClick={() => setOpen(false)}
                >
                  <span className="toc-frog-container">
                    <FrogGlyph width={14} height={10} className="toc-frog" />
                  </span>
                  <span>{i.label}</span>
                </a>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </>
  );
}

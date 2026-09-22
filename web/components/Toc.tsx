"use client";
import { useEffect, useState } from "react";
import { FrogGlyph } from "./Frog";

export type TocItem = { id: string; label: string; depth?: number };

/**
 * The reference's desktop contents rail.
 *
 * Markup is the reference's, element for element:
 *   nav.toc-sidebar.toc-scrollable-container
 *     div.toc-scrollable-inner
 *       ul.space-y-1
 *         li[style="padding-left:0.75rem"]
 *           a.toc-link-frog
 *             span.toc-frog-container > svg.toc-frog[viewBox="0 0 200 135"]
 *             span  (the label)
 *
 * The frog is the reference's own seven-path glyph, not a redrawing: see
 * `Frog.tsx`. It is `opacity:0` until its row is the active one, exactly as in
 * the reference.
 *
 * Scroll spy uses the reference's own rootMargin, `-100px 0px -66% 0px`, and
 * no threshold — the reference configures the reveal by rootMargin rather than
 * by a percentage crossing.
 */
export default function Toc({ items }: { items: TocItem[] }) {
  const [active, setActive] = useState<string>("");

  useEffect(() => {
    const headings = items
      .map((i) => document.getElementById(i.id))
      .filter((el): el is HTMLElement => Boolean(el));
    if (!headings.length) return;

    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) setActive(e.target.id);
        });
      },
      { rootMargin: "-100px 0px -66% 0px" },
    );
    headings.forEach((h) => io.observe(h));
    return () => io.disconnect();
  }, [items]);

  return (
    <nav className="toc toc-sidebar toc-scrollable-container" aria-label="Contents">
      <div className="toc-scrollable-inner">
        <ul>
          {items.map((it) => (
            <li
              key={it.id}
              style={(it.depth ?? 0) > 0 ? { paddingLeft: `${0.75 * (it.depth ?? 0)}rem` } : undefined}
            >
              <a
                href={`#${it.id}`}
                className="toc-link-frog"
                data-active={active === it.id}
              >
                <span className="toc-frog-container">
                  <FrogGlyph width={14} height={10} className="toc-frog" />
                </span>
                <span>{it.label}</span>
              </a>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
}

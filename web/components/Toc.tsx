"use client";
import { useEffect, useState } from "react";

export type TocItem = { id: string; label: string };

/** Contents list with scroll-spy and the frog indicator, as in the reference. */
export default function Toc({ items }: { items: TocItem[] }) {
  const [active, setActive] = useState<string>("");

  useEffect(() => {
    const headings = items
      .map((i) => document.getElementById(i.id))
      .filter((el): el is HTMLElement => Boolean(el));
    if (!headings.length) return;

    const io = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
        if (visible[0]) setActive(visible[0].target.id);
      },
      { rootMargin: "-72px 0px -70% 0px", threshold: [0, 1] }
    );
    headings.forEach((h) => io.observe(h));
    return () => io.disconnect();
  }, [items]);

  return (
    <nav className="toc" aria-label="Contents">
      <ol>
        {items.map((it) => (
          <li key={it.id}>
            <a href={`#${it.id}`} data-active={active === it.id}>
              <span>{it.label}</span>
              <svg className="toc-frog" viewBox="0 0 200 135" fill="currentColor" aria-hidden="true">
                <path d="M100 20c-30 0-55 20-62 45-3 11 2 20 12 20h100c10 0 15-9 12-20-7-25-32-45-62-45zm-28 34a11 11 0 110 22 11 11 0 010-22zm56 0a11 11 0 110 22 11 11 0 010-22z" />
              </svg>
            </a>
          </li>
        ))}
      </ol>
    </nav>
  );
}

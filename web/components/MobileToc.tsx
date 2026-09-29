"use client";

import { useEffect, useRef, useState } from "react";
import { FrogGlyph } from "./Frog";
import type { TocItem } from "./Toc";

export default function MobileToc({
  items,
  onNavigate,
}: {
  items: TocItem[];
  onNavigate?: (id: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState<string>(items[0]?.id ?? "");
  const drawer = useRef<HTMLDivElement>(null);
  const fab = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const targets = items
      .map((i) => document.getElementById(i.id))
      .filter((el): el is HTMLElement => Boolean(el));
    if (!targets.length) return;

    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) setActive(entry.target.id);
        });
      },
      { rootMargin: "-100px 0px -66% 0px" },
    );
    targets.forEach((target) => io.observe(target));
    return () => io.disconnect();
  }, [items]);

  useEffect(() => {
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const onKey = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      setOpen(false);
      fab.current?.focus();
    };

    document.addEventListener("keydown", onKey);
    drawer.current?.querySelector<HTMLButtonElement>(".mobile-toc-close")?.focus();

    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <>
      <div className="mobile-toc-fab-wrapper">
        <button
          ref={fab}
          type="button"
          className="mobile-toc-fab"
          aria-label={open ? "close contents" : "open contents"}
          aria-expanded={open}
          onClick={() => setOpen((value) => !value)}
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
        aria-modal={open ? "true" : undefined}
        aria-hidden={!open}
        aria-label="contents"
      >
        <div className="mobile-toc-drawer-head">
          <span>contents</span>
          <button
            type="button"
            className="mobile-toc-close"
            onClick={() => {
              setOpen(false);
              fab.current?.focus();
            }}
            aria-label="close contents"
          >
            close
          </button>
        </div>
        <nav className="mobile-toc-nav">
          <ul>
            {items.map((item) => (
              <li key={item.id} style={{ paddingLeft: `${(item.depth ?? 0) * 0.75}rem` }}>
                <a
                  href={`#${item.id}`}
                  className="toc-link-frog"
                  data-active={active === item.id}
                  onClick={(event) => {
                    setOpen(false);
                    if (!onNavigate) return;
                    event.preventDefault();
                    onNavigate(item.id);
                  }}
                >
                  <span className="toc-frog-container">
                    <FrogGlyph width={14} height={10} className="toc-frog" />
                  </span>
                  <span>{item.label}</span>
                </a>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </>
  );
}

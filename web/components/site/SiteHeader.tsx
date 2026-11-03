"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import SiteLink, { routeCommitted } from "./SiteLink";
import SiteMenuSheet from "./SiteMenuSheet";
import { NAV, currentNav, isArticlePath } from "./nav";
import { haptic } from "@/lib/ux/haptics";
import type { EntryLite } from "@/lib/catalog";

const HYSTERESIS = 24;

/**
 * Sticky 56px glass header. On article pages it hides on scroll down and returns on
 * scroll up (transform only, 24px hysteresis, rAF-throttled passive listener, an
 * IntersectionObserver sentinel for "at the top"). It never hides while the menu is
 * open or while focus is inside it.
 */
export default function SiteHeader({ latest, studySlugs, repo }: { latest: EntryLite[]; studySlugs: string[]; repo: string }) {
  const pathname = usePathname() || "/";
  const current = currentNav(pathname, studySlugs);
  const article = isArticlePath(pathname);
  const [menu, setMenu] = useState(false);
  const header = useRef<HTMLElement>(null);
  const button = useRef<HTMLAnchorElement>(null);
  const sentinel = useRef<HTMLDivElement>(null);
  const menuOpen = useRef(false);
  menuOpen.current = menu;

  // a route committed: finish any view transition and close the menu
  useEffect(() => {
    routeCommitted();
    setMenu(false);
  }, [pathname]);

  useEffect(() => {
    const root = document.documentElement;
    const setHidden = (hidden: boolean) => {
      if (hidden) root.dataset.headerHidden = "1";
      else delete root.dataset.headerHidden;
    };
    setHidden(false);
    if (!article) return;
    let atTop = true;
    let lastY = window.scrollY;
    let acc = 0;
    let frame = 0;
    let hidden = false;
    const io = new IntersectionObserver(([e]) => {
      atTop = e.isIntersecting;
      if (atTop && hidden) {
        hidden = false;
        setHidden(false);
      }
    });
    if (sentinel.current) io.observe(sentinel.current);
    const tick = () => {
      frame = 0;
      const y = window.scrollY;
      const d = y - lastY;
      lastY = y;
      if (d === 0) return;
      acc = Math.sign(d) === Math.sign(acc) ? acc + d : d;
      const focusInside = header.current?.contains(document.activeElement) ?? false;
      let next = hidden;
      if (acc > HYSTERESIS && !atTop) next = true;
      else if (acc < -HYSTERESIS) next = false;
      if (menuOpen.current || focusInside || root.style.overflow === "hidden") next = false;
      if (next !== hidden) {
        hidden = next;
        setHidden(hidden);
      }
    };
    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(tick);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      io.disconnect();
      if (frame) cancelAnimationFrame(frame);
      setHidden(false);
    };
  }, [article]);

  const closeMenu = useCallback(() => setMenu(false), []);

  return (
    <>
      <div ref={sentinel} className="header-sentinel" aria-hidden="true" />
      <header ref={header} className="site-header" data-menu={menu ? "open" : undefined}>
        <div className="site-container site-header-row">
          <SiteLink href="/" className="wordmark" data-press="nav" aria-label="zer0 evals home">
            zer0 evals
          </SiteLink>
          <nav className="site-links" aria-label="primary">
            <ul>
              {NAV.map((n) => (
                <li key={n.href}>
                  <SiteLink href={n.href} data-press="nav" aria-current={current === n.href ? "page" : undefined}>
                    {n.label}
                  </SiteLink>
                </li>
              ))}
            </ul>
          </nav>
          {/* without JS this is a jump to the footer nav; with JS it opens the menu sheet */}
          <a
            ref={button}
            href="#site-footer-nav"
            role="button"
            className="menu-button"
            data-press="control"
            aria-label={menu ? "close menu" : "open menu"}
            aria-expanded={menu}
            aria-controls="site-menu"
            onClick={(e) => {
              e.preventDefault();
              if (!menu) haptic.tap();
              setMenu((v) => !v);
            }}
          >
            <span className="menu-glyph" aria-hidden="true">
              <i />
              <i />
              <i />
            </span>
          </a>
        </div>
      </header>
      <SiteMenuSheet open={menu} onClose={closeMenu} current={current} latest={latest} repo={repo} returnFocus={button} />
    </>
  );
}

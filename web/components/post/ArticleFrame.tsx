"use client";

import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import Toc, { type TocItem } from "@/components/Toc";
import SiteLink from "@/components/site/SiteLink";
import StatusDot from "@/components/site/StatusDot";
import SectionBar from "./SectionBar";
import TocSheet from "./TocSheet";
import HeadingRail from "./HeadingRail";
import EdgeBack from "./EdgeBack";
import CopyPress from "./CopyPress";
import TableWrapEnhancer from "./TableWrapEnhancer";
import { useActiveHeading } from "@/lib/ux/useActiveHeading";
import { scrollToId } from "@/lib/ux/scrollTo";
import type { StoryBanner, StoryMeta } from "@/lib/story";
import type { EntryLite } from "@/lib/catalog";
import type { Tone } from "@/lib/status";

export type FrameHero = {
  meta: StoryMeta;
  area?: { id: string; label: string };
  status: { tone: Tone; label: string };
  updated?: string;
};

/**
 * The post/study page: [toc 220] [article ≤ 680] [margin 220] on wide screens, one
 * column with a sticky SectionBar + TocSheet under 1024px. Owns the single active-
 * heading observer and the single passive scroll listener for reading progress.
 */
export default function ArticleFrame({
  hero,
  toc,
  banner,
  toggle,
  navigate,
  lowercase = true,
  prev,
  next,
  footer,
  children,
}: {
  hero: FrameHero;
  toc: TocItem[];
  banner?: StoryBanner;
  toggle?: ReactNode;
  navigate?: (id: string) => void;
  lowercase?: boolean;
  prev?: EntryLite;
  next?: EntryLite;
  footer?: ReactNode;
  children: ReactNode;
}) {
  const ids = useMemo(() => toc.map((t) => t.id), [toc]);
  const active = useActiveHeading(ids);
  const [sheet, setSheet] = useState(false);
  const frame = useRef<HTMLDivElement>(null);
  const body = useRef<HTMLDivElement>(null);
  const barButton = useRef<HTMLButtonElement>(null);
  const go = useCallback((id: string) => (navigate ? navigate(id) : scrollToId(id)), [navigate]);
  const { meta } = hero;

  // reading progress: geometry cached by ResizeObserver, scroll handler reads scrollY only
  useEffect(() => {
    const el = body.current;
    const root = frame.current;
    if (!el || !root) return;
    const bars = Array.from(root.querySelectorAll<HTMLElement>("[data-progress]"));
    let top = 0;
    let span = 1;
    let raf = 0;
    const measure = () => {
      const r = el.getBoundingClientRect();
      top = r.top + window.scrollY;
      span = Math.max(1, r.height - window.innerHeight * 0.6);
      queue();
    };
    const write = () => {
      raf = 0;
      const p = Math.min(1, Math.max(0, (window.scrollY - top + window.innerHeight * 0.3) / span));
      for (const b of bars) b.style.transform = `scaleX(${p})`;
    };
    const queue = () => {
      if (!raf) raf = requestAnimationFrame(write);
    };
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    window.addEventListener("scroll", queue, { passive: true });
    window.addEventListener("resize", measure, { passive: true });
    return () => {
      ro.disconnect();
      window.removeEventListener("scroll", queue);
      window.removeEventListener("resize", measure);
      if (raf) cancelAnimationFrame(raf);
    };
  }, []);

  // pages without their own hash router (phase 1b): land deep links exactly
  useEffect(() => {
    if (navigate) return;
    const id = decodeURIComponent(location.hash.replace(/^#/, ""));
    if (id && document.getElementById(id)) requestAnimationFrame(() => scrollToId(id, { push: false, instant: true }));
  }, [navigate]);

  const activeLabel = toc.find((t) => t.id === active)?.label ?? toc[0]?.label ?? "";

  return (
    <div ref={frame} className={`post-frame${lowercase ? " story-shell" : ""}`}>
      {toc.length ? (
        <SectionBar items={toc} active={active} onOpen={() => setSheet(true)} toggle={toggle} buttonRef={barButton} />
      ) : null}
      <div className="site-container post-grid">
        <aside className="post-rail" aria-label="contents rail">
          <Toc items={toc} active={active} onNavigate={go} header={toggle ? <div className="post-rail-toggle">{toggle}</div> : null} />
        </aside>

        <article className="post-article">
          <header className="post-hero">
            {hero.area ? (
              <SiteLink href={`/research/?area=${hero.area.id}`} className="post-eyebrow" data-press="row">
                {hero.area.label}
              </SiteLink>
            ) : null}
            <h1 className="post-title">{meta.title}</h1>
            {meta.subtitle ? <p className="post-dek">{meta.subtitle}</p> : null}
            <div className="post-meta">
              <span>{meta.author}</span>
              <span className="sep" aria-hidden="true">·</span>
              <span>{meta.date}</span>
              <span className="sep" aria-hidden="true">·</span>
              <StatusDot tone={hero.status.tone} label={hero.status.label} />
              {hero.updated ? (
                <>
                  <span className="sep" aria-hidden="true">·</span>
                  <span>updated {hero.updated}</span>
                </>
              ) : null}
            </div>
          </header>

          {banner ? (
            <div className="story-banner" role="note">
              <strong>{banner.tag}</strong>
              <span>
                {banner.text}
                {banner.preserve_ref ? (
                  <>
                    {" "}
                    preserved at <code>{banner.preserve_ref}</code>
                  </>
                ) : null}
              </span>
            </div>
          ) : null}

          <div ref={body} className="article-body prose">
            {children}
          </div>
          {footer}
        </article>

        <aside className="post-margin" aria-label="reading progress">
          <div className="post-margin-inner">
            <p className="post-margin-kicker">on this page</p>
            <p className="post-margin-label">{activeLabel}</p>
            <span className="post-margin-track" aria-hidden="true">
              <span className="post-margin-progress" data-progress />
            </span>
            {prev || next ? (
              <nav className="post-margin-nav" aria-label="previous and next">
                {prev ? (
                  <SiteLink href={prev.href} data-press="row" rel="prev">
                    <span>← previous</span>
                    {prev.title}
                  </SiteLink>
                ) : null}
                {next ? (
                  <SiteLink href={next.href} data-press="row" rel="next">
                    <span>next →</span>
                    {next.title}
                  </SiteLink>
                ) : null}
              </nav>
            ) : null}
          </div>
        </aside>
      </div>

      {toc.length ? (
        <TocSheet
          open={sheet}
          items={toc}
          active={active}
          onClose={() => setSheet(false)}
          onPick={(id) => (id ? go(id) : window.scrollTo({ top: 0 }))}
          returnFocus={barButton}
        />
      ) : null}
      <HeadingRail items={toc} onJump={(id) => (navigate ? navigate(id) : scrollToId(id, { instant: true }))} />
      <EdgeBack />
      <CopyPress root={body} />
      <TableWrapEnhancer root={body} />
    </div>
  );
}

"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";
import ArticleFrame, { type FrameHero } from "./ArticleFrame";
import { scrollToId } from "@/lib/ux/scrollTo";
import { haptic } from "@/lib/ux/haptics";
import type { TocItem } from "@/components/Toc";
import type { StoryBanner } from "@/lib/story";
import type { EntryLite } from "@/lib/catalog";

/** Story / explore reading modes on top of ArticleFrame. */
export default function StoryClient({
  hero,
  toc,
  banner,
  story,
  explore,
  exploreLabel,
  storyLabel,
  prev,
  next,
  footer,
}: {
  hero: FrameHero;
  toc: TocItem[];
  banner?: StoryBanner;
  story: ReactNode;
  explore: ReactNode;
  exploreLabel: string;
  storyLabel: string;
  prev?: EntryLite;
  next?: EntryLite;
  footer?: ReactNode;
}) {
  const [mode, setMode] = useState<"story" | "explore">("story");

  const navigate = useCallback((id: string, pushHash = true) => {
    const target = document.getElementById(id);
    const nextMode = target?.closest('[data-mode="explore"]') ? "explore" : "story";
    setMode(nextMode);
    // hidden tab content has no layout box. Wait for React to expose the
    // destination, then scroll and update history. Two frames is deliberate:
    // one commits the mode change, one lets layout settle.
    requestAnimationFrame(() => {
      requestAnimationFrame(() => scrollToId(id, { push: pushHash }));
    });
  }, []);

  useEffect(() => {
    const syncFromHash = () => {
      const id = decodeURIComponent(window.location.hash.replace(/^#/, ""));
      if (id && document.getElementById(id)) navigate(id, false);
    };
    syncFromHash();
    window.addEventListener("hashchange", syncFromHash);
    return () => window.removeEventListener("hashchange", syncFromHash);
  }, [navigate]);

  const firstStoryId = toc.find((item) => item.id !== "explore")?.id;
  const toStory = () => (firstStoryId ? navigate(firstStoryId) : setMode("story"));

  const toggle = (
    <div className="story-mode" role="tablist" aria-label="reading mode">
      <button type="button" role="tab" aria-selected={mode === "story"} aria-controls="story-panel"
        data-active={mode === "story"} data-press="control" onClick={() => { haptic.select(); toStory(); }}>
        <span>story</span>
      </button>
      <button type="button" role="tab" aria-selected={mode === "explore"} aria-controls="explore"
        data-active={mode === "explore"} data-press="control" onClick={() => { haptic.select(); navigate("explore"); }}>
        <span>explore</span>
      </button>
    </div>
  );

  return (
    <ArticleFrame hero={hero} toc={toc} banner={banner} toggle={toggle} navigate={navigate} prev={prev} next={next} footer={footer}>
      {hero.meta.lede ? <p className="story-lede">{hero.meta.lede}</p> : null}
      <section id="story-panel" data-mode="story" hidden={mode !== "story"}>
        {story}
      </section>
      <section data-mode="explore" id="explore" hidden={mode !== "explore"}>
        {explore}
      </section>
      <div className="story-switch">
        <button type="button" data-press="control" onClick={() => (mode === "story" ? navigate("explore") : toStory())}>
          {mode === "story" ? exploreLabel : storyLabel}
        </button>
      </div>
    </ArticleFrame>
  );
}

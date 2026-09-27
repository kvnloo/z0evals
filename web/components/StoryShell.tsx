"use client";

import { useState, type ReactNode } from "react";
import Toc, { type TocItem } from "./Toc";
import MobileToc from "./MobileToc";

/**
 * The reusable immersive framework for a z0evals research post.
 *
 * A study page has two layers and they are not the same document:
 *   STORY   — the argued narrative, in reading order, with visuals.
 *   EXPLORE — the exact tables, methodology, receipts and claim status.
 *
 * Keeping them as two named slots (rather than two interleaved halves) is what
 * lets the next post reuse this shell without copying the page: the shell owns
 * the header, the rail, the banner, the mode switch and the appendix furniture;
 * the study owns only its own prose and figures.
 *
 * Server render shows STORY. The switch is progressive enhancement, and the
 * explore layer is always present in the DOM so a link to `#explore` still works
 * with JavaScript disabled.
 */
export type StoryMeta = {
  title: string;
  subtitle: string;
  author: string;
  date: string;
  status: string;
  lede: string;
};

export type StoryBanner = { tag: string; text: string; preserve_ref?: string };

export default function StoryShell({
  meta,
  toc,
  banner,
  story,
  explore,
  exploreLabel = "Explore the data",
  storyLabel = "Back to the story",
}: {
  meta: StoryMeta;
  toc: TocItem[];
  banner?: StoryBanner;
  story: ReactNode;
  explore: ReactNode;
  exploreLabel?: string;
  storyLabel?: string;
}) {
  const [mode, setMode] = useState<"story" | "explore">("story");

  return (
    <div className="shell story-shell">
      <header className="blog-page-header">
        <div className="site-nav">
          <span className="brand">z0evals</span>
          <span className="links">
            <a href="/">studies</a>
          </span>
        </div>
      </header>

      <header className="article-header story-action-header">
        <div>
          <h1 className="article-title">{meta.title}</h1>
          <div className="title-accent-line" />
          <p className="story-subtitle">{meta.subtitle}</p>
          <div className="article-meta">
            <span>{meta.author}</span>
            <span className="sep">·</span>
            <span>{meta.date}</span>
            <span className="sep">·</span>
            <span className="story-status" data-status={meta.status}>
              {meta.status}
            </span>
          </div>
          <div className="story-mode" role="tablist" aria-label="reading mode">
            <button
              type="button"
              role="tab"
              aria-selected={mode === "story"}
              data-active={mode === "story"}
              onClick={() => setMode("story")}
            >
              Story
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={mode === "explore"}
              data-active={mode === "explore"}
              onClick={() => setMode("explore")}
            >
              Explore
            </button>
          </div>
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

      <div className="story-grid">
        <div className="rail">
          <Toc items={toc} />
        </div>
        <div className="article">
          <MobileToc items={toc} />
          <div className="article-body">
            <p className="story-lede">{meta.lede}</p>
            <section data-mode="story" hidden={mode !== "story"}>
              {story}
            </section>
            <section data-mode="explore" id="explore" hidden={mode !== "explore"}>
              {explore}
            </section>
            <div className="story-switch">
              <button type="button" onClick={() => setMode(mode === "story" ? "explore" : "story")}>
                {mode === "story" ? exploreLabel : storyLabel}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

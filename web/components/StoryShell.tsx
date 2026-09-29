"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";
import Toc, { type TocItem } from "./Toc";
import MobileToc from "./MobileToc";
import RouteProgress from "./RouteProgress";

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

  const navigate = useCallback((id: string, pushHash = true) => {
    const target = document.getElementById(id);
    const nextMode = target?.closest('[data-mode="explore"]') ? "explore" : "story";
    setMode(nextMode);

    // hidden tab content has no layout box. Wait for React to expose the
    // destination, then scroll and update history. Two frames is deliberate:
    // one commits the mode change, one lets layout settle.
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        const next = document.getElementById(id);
        if (!next) return;
        next.scrollIntoView({ block: "start" });
        if (pushHash && window.location.hash !== `#${id}`) {
          window.history.pushState(null, "", `#${id}`);
        }
      });
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

  return (
    <div className="shell story-shell">
      <RouteProgress />
      <header className="blog-page-header">
        <div>
          <nav className="site-nav" aria-label="research pages">
            <a className="brand" href="../">z0evals</a>
            <div className="links">
              <a href="../">phase 1b</a>
              <a href="../z0intelligence-function-routing/">routing</a>
              <a href="../unified-memory-v0/">memory</a>
            </div>
          </nav>
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
          <Toc items={toc} onNavigate={(id) => navigate(id)} />
        </div>
        <div className="article">
          <MobileToc items={toc} onNavigate={(id) => navigate(id)} />
          <div className="article-body prose">
            <p className="story-lede">{meta.lede}</p>
            <section data-mode="story" hidden={mode !== "story"}>
              {story}
            </section>
            <section data-mode="explore" id="explore" hidden={mode !== "explore"}>
              {explore}
            </section>
            <div className="story-switch">
              <button
                type="button"
                onClick={() =>
                  mode === "story"
                    ? navigate("explore")
                    : firstStoryId
                      ? navigate(firstStoryId)
                      : setMode("story")
                }
              >
                {mode === "story" ? exploreLabel : storyLabel}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

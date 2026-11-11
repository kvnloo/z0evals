// Server entry for every post and study page. Resolves catalog data (area, status,
// prev/next, log joins) and hands the client frame plain props. Story/explore pages
// pass `story` + `explore`; long single-column studies (phase 1b) pass children.
import type { ReactNode } from "react";
import ArticleFrame, { type FrameHero } from "./post/ArticleFrame";
import StoryClient from "./post/StoryClient";
import PostFooter from "./post/PostFooter";
import type { TocItem } from "./Toc";
import { entry, lite, neighbors, studyMeta } from "@/lib/catalog";
import { areaLabel } from "@/lib/areas";
import { postStatus } from "@/lib/status";
import { shortDate } from "@/lib/dates";
import type { StoryBanner, StoryMeta } from "@/lib/story";

export type { StoryBanner, StoryMeta } from "@/lib/story";

export default function StoryShell({
  slug,
  meta: metaProp,
  toc,
  banner,
  story,
  explore,
  exploreLabel = "show me the receipts",
  storyLabel = "back to the story",
  lowercase = true,
  children,
}: {
  slug: string;
  meta?: StoryMeta;
  toc: TocItem[];
  banner?: StoryBanner;
  story?: ReactNode;
  explore?: ReactNode;
  exploreLabel?: string;
  storyLabel?: string;
  lowercase?: boolean;
  children?: ReactNode;
}) {
  const meta = metaProp ?? studyMeta(slug);
  const e = entry(slug);
  const [tone, label] = postStatus(meta.status);
  const hero: FrameHero = {
    meta,
    area: e ? { id: e.area, label: areaLabel(e.area) } : undefined,
    status: { tone, label },
    updated: e?.updated ? shortDate(e.updated) : undefined,
  };
  const { prev, next } = neighbors(slug);
  const footer = <PostFooter slug={slug} />;
  const p = prev ? lite(prev) : undefined;
  const n = next ? lite(next) : undefined;

  if (story !== undefined) {
    return (
      <StoryClient hero={hero} toc={toc} banner={banner} story={story} explore={explore}
        exploreLabel={exploreLabel} storyLabel={storyLabel} prev={p} next={n} footer={footer} />
    );
  }
  return (
    <ArticleFrame hero={hero} toc={toc} banner={banner} lowercase={lowercase} prev={p} next={n} footer={footer}>
      {children}
    </ArticleFrame>
  );
}

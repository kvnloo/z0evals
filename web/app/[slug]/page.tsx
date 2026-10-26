import type { Metadata } from "next";
import StoryShell from "@/components/StoryShell";
import type { TocItem } from "@/components/Toc";
import { markdownOnlySlugs, readPost } from "@/lib/posts";

export const dynamicParams = false;

export function generateStaticParams() {
  return markdownOnlySlugs().map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const p = readPost(slug);
  return { title: `${p.title} — z0evals`, description: p.lede || p.subtitle };
}

export default async function MarkdownPost({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const p = readPost(slug);
  const toc: TocItem[] = [...p.toc.map((t) => ({ ...t, depth: 0 })), { id: "explore", label: "receipts", depth: 0 }];
  const repo = "https://github.com/kvnloo/z0evals";
  return (
    <StoryShell
      slug={slug}
      meta={{ title: p.title, subtitle: p.subtitle, author: p.author, date: p.date, status: p.status, lede: p.lede }}
      toc={toc}
      story={<div dangerouslySetInnerHTML={{ __html: p.html }} />}
      explore={
        <div className="explore-block">
          <h2 id="receipts">receipts</h2>
          <p>
            this post is rendered from <a href={`${repo}/blob/main/posts/${p.slug}.md`}>posts/{p.slug}.md</a>.
            the frozen study, its manifest and its pinned sources live under{" "}
            <a href={`${repo}/tree/main/studies/${p.study}`}>studies/{p.study}</a> when it has been imported, or on
            its study pull request when it has not. the <a href="../log/">research log</a> lists the study&apos;s
            status and links.
          </p>
        </div>
      }
    />
  );
}

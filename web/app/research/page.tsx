import type { Metadata } from "next";
import ResearchExplorer, { type ResearchItem } from "@/components/ResearchExplorer";
import { allEntries, lite } from "@/lib/catalog";
import { isMeasured } from "@/lib/status";

export const metadata: Metadata = {
  title: "research — z0evals",
  description: "every zer0 evals post and study, newest first, filterable by area and evidence status.",
};

export default function ResearchIndex() {
  const items: ResearchItem[] = allEntries().map((e) => ({
    ...lite(e),
    measured: isMeasured(e.statusRaw),
    logCount: e.logIds.length,
    search: `${e.title} ${e.dek} ${e.slug} ${e.tags.join(" ")}`.toLowerCase(),
  }));
  return (
    <div className="site-container page-narrow">
      <header className="page-head">
        <h1 className="page-title">research</h1>
        <p className="page-lede">every post and study we have published, newest first. negative and incomplete results included.</p>
      </header>
      <ResearchExplorer items={items} />
    </div>
  );
}

import type { Metadata } from "next";
import EntryCard from "@/components/site/EntryCard";
import SiteLink from "@/components/site/SiteLink";
import { entry, lite, studies } from "@/lib/catalog";

export const metadata: Metadata = {
  title: "studies — z0evals",
  description: "the long-form zer0 evals studies: phase 1b, routing, the research frontier, unified memory and optchat.",
};

export default function Studies() {
  const list = studies();
  return (
    <div className="site-container page-narrow">
      <header className="page-head">
        <h1 className="page-title">studies</h1>
        <p className="page-lede">the long-form, bespoke write-ups. each one has a story mode and the receipts behind it.</p>
      </header>
      <ul className="study-grid">
        {list.map((e) => {
          const later = e.supersededBy ? entry(e.supersededBy) : undefined;
          return (
            <li key={e.slug}>
              <EntryCard e={lite(e)} size="study" logCount={e.logIds.length} dateLabel={e.dateLabel} />
              {later ? (
                <SiteLink href={later.href} className="study-note" data-press="row">
                  superseded by the october update →
                </SiteLink>
              ) : null}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

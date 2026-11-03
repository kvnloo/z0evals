import type { Metadata } from "next";
import SiteLink from "@/components/site/SiteLink";
import EntryCard from "@/components/site/EntryCard";
import EntryRow from "@/components/site/EntryRow";
import HashForward from "@/components/site/HashForward";
import HighlightsCarousel from "@/components/site/HighlightsCarousel";
import { AREAS } from "@/lib/areas";
import { allEntries, featured, highlights, latest, lite, logUpdated, site } from "@/lib/catalog";
import { shortDate } from "@/lib/dates";
import { OLD_HOME_IDS } from "./slm-router-v0/toc";

export const metadata: Metadata = {
  title: "zer0 evals — agent harness research, with receipts · z0evals",
  description: site().positioning,
};

export default function Home() {
  const conf = site();
  const all = allEntries();
  const f = featured();
  const hl = highlights();
  const rows = latest(conf.latestCount);
  const counts = new Map(AREAS.map((a) => [a.id, all.filter((e) => e.area === a.id).length]));
  return (
    <div className="home site-container">
      <HashForward ids={OLD_HOME_IDS} />
      <section className="home-hero" aria-labelledby="home-positioning">
        <h1 id="home-positioning" className="home-positioning">{conf.positioning}</h1>
        <p className="home-stats">
          {AREAS.length} areas · {all.length} write-ups · log updated {shortDate(logUpdated())}
        </p>
      </section>

      <section className="home-featured" aria-label="featured">
        <EntryCard e={lite(f)} size="featured" logCount={f.logIds.length} />
      </section>

      <section className="home-block" aria-labelledby="home-highlights">
        <h2 id="home-highlights" className="home-h2">highlights</h2>
        <HighlightsCarousel label="highlighted studies">
          {hl.map((e) => (
            <EntryCard key={e.slug} e={lite(e)} logCount={e.logIds.length} />
          ))}
        </HighlightsCarousel>
      </section>

      <section className="home-block" aria-labelledby="home-latest">
        <h2 id="home-latest" className="home-h2">latest</h2>
        <ol className="entry-list">
          {rows.map((e) => (
            <EntryRow key={e.slug} e={lite(e)} logCount={e.logIds.length} />
          ))}
        </ol>
      </section>

      <section className="home-block" aria-labelledby="home-areas">
        <h2 id="home-areas" className="home-h2">browse by area</h2>
        <ul className="area-chips">
          {AREAS.map((a) => (
            <li key={a.id}>
              <SiteLink href={`/research/?area=${a.id}`} className="area-chip" data-press="control" title={a.blurb}>
                {a.label} <span className="n">{counts.get(a.id)}</span>
              </SiteLink>
            </li>
          ))}
        </ul>
      </section>

      <nav className="home-cta" aria-label="more">
        <SiteLink href="/research/" data-press="row">all research →</SiteLink>
        <SiteLink href="/log/" data-press="row">the research log →</SiteLink>
      </nav>
    </div>
  );
}

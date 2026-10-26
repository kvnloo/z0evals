import SiteLink from "@/components/site/SiteLink";
import StatusDot from "@/components/site/StatusDot";
import EntryRow from "@/components/site/EntryRow";
import PrevNextSwipe from "./PrevNextSwipe";
import { areaLabel } from "@/lib/areas";
import { entry, lite, logEntries, neighbors } from "@/lib/catalog";
import { logStatus } from "@/lib/status";

/** End of every post and study: its log entries, prev/next, more in the area. */
export default function PostFooter({ slug }: { slug: string }) {
  const me = entry(slug);
  if (!me) return null;
  const log = logEntries(slug);
  const { prev, next, related } = neighbors(slug);
  return (
    <footer className="post-footer" aria-label="more from zer0 evals">
      {log.length ? (
        <section className="post-footer-block">
          <h2 className="post-footer-h">from the log</h2>
          <ul className="log-mini">
            {log.map((l) => {
              const [tone, label] = logStatus(l.status);
              return (
                <li key={l.id}>
                  <SiteLink href={`/log/#${l.id}`} className="log-mini-row" data-press="row">
                    <span className="log-mini-title">{l.title}</span>
                    <StatusDot tone={tone} label={label} />
                  </SiteLink>
                </li>
              );
            })}
          </ul>
        </section>
      ) : null}
      <section className="post-footer-block">
        <h2 className="post-footer-h">keep reading</h2>
        <PrevNextSwipe prev={prev ? lite(prev) : undefined} next={next ? lite(next) : undefined} />
      </section>
      {related.length ? (
        <section className="post-footer-block">
          <h2 className="post-footer-h">more in {areaLabel(me.area)}</h2>
          <ol className="entry-list">
            {related.map((e) => (
              <EntryRow key={e.slug} e={lite(e)} />
            ))}
          </ol>
        </section>
      ) : null}
      <div className="post-footer-cta">
        <SiteLink href="/research/" data-press="row">all research →</SiteLink>
        <a href="#main" className="to-top" data-press="control">↑ back to top</a>
      </div>
    </footer>
  );
}

import SiteLink from "./SiteLink";
import { NAV } from "./nav";
import { logUpdated, site } from "@/lib/catalog";

export default function SiteFooter() {
  const conf = site();
  return (
    <footer className="site-footer">
      <div className="site-container site-footer-grid">
        <div>
          <SiteLink href="/" className="wordmark">zer0 evals</SiteLink>
          <p className="site-footer-blurb">{conf.positioning}</p>
        </div>
        <nav aria-label="footer" id="site-footer-nav">
          <ul>
            {NAV.map((n) => (
              <li key={n.href}>
                <SiteLink href={n.href} data-press="row">{n.label}</SiteLink>
              </li>
            ))}
          </ul>
        </nav>
        <ul>
          <li><a href={conf.repo} data-press="row">github repo ↗</a></li>
          <li><SiteLink href="/about/#status" data-press="row">evidence status legend</SiteLink></li>
          <li className="site-footer-updated">log updated {logUpdated()}</li>
        </ul>
      </div>
    </footer>
  );
}

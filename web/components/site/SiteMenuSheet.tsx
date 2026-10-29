"use client";

import type { RefObject } from "react";
import Sheet from "./Sheet";
import SiteLink from "./SiteLink";
import { NAV } from "./nav";
import { shortDate } from "@/lib/dates";
import type { EntryLite } from "@/lib/catalog";

export default function SiteMenuSheet({
  open,
  onClose,
  current,
  latest,
  repo,
  returnFocus,
}: {
  open: boolean;
  onClose: () => void;
  current: string | null;
  latest: EntryLite[];
  repo: string;
  returnFocus: RefObject<HTMLElement | null>;
}) {
  return (
    <Sheet open={open} onClose={onClose} label="site menu" returnFocus={returnFocus} id="site-menu" className="menu-sheet">
      <nav aria-label="site">
        <ul className="menu-rows">
          {NAV.map((n) => (
            <li key={n.href}>
              <SiteLink href={n.href} className="menu-row" data-press="row" data-haptic="tap"
                aria-current={current === n.href ? "page" : undefined} onClick={onClose}>
                {n.label}
                <span aria-hidden="true">→</span>
              </SiteLink>
            </li>
          ))}
        </ul>
      </nav>
      <p className="menu-kicker">latest</p>
      <ul className="menu-latest">
        {latest.map((e) => (
          <li key={e.slug}>
            <SiteLink href={e.href} className="menu-mini" data-press="row" data-haptic="tap" onClick={onClose}>
              <time dateTime={e.published}>{shortDate(e.published)}</time>
              <span>{e.title}</span>
            </SiteLink>
          </li>
        ))}
      </ul>
      <a className="menu-gh" href={repo} data-press="row">github ↗</a>
    </Sheet>
  );
}

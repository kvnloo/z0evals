import SiteLink from "./SiteLink";
import StatusDot from "./StatusDot";
import { areaLabel } from "@/lib/areas";
import { shortDate } from "@/lib/dates";
import type { EntryLite } from "@/lib/catalog";

/** Dense list row (Dash Chats style): the whole row is the link. */
export default function EntryRow({ e, logCount }: { e: EntryLite; logCount?: number }) {
  return (
    <li className="entry-row-li">
      <SiteLink href={e.href} className="entry-row" data-press="row">
        <time className="entry-date" dateTime={e.published}>{shortDate(e.published)}</time>
        <span className="entry-main">
          {e.bespoke ? <span className="entry-eyebrow">study</span> : null}
          <span className="entry-title">{e.title}</span>
          <span className="entry-dek">{e.dek}</span>
          <span className="entry-meta">
            <span>{areaLabel(e.area)}</span>
            <span className="sep" aria-hidden="true">·</span>
            <StatusDot tone={e.tone} label={e.status} />
            {logCount ? (
              <>
                <span className="sep" aria-hidden="true">·</span>
                <span>{logCount} log {logCount === 1 ? "entry" : "entries"}</span>
              </>
            ) : null}
          </span>
        </span>
      </SiteLink>
    </li>
  );
}

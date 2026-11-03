import SiteLink from "./SiteLink";
import StatusDot from "./StatusDot";
import { areaLabel } from "@/lib/areas";
import { shortDate } from "@/lib/dates";
import type { EntryLite } from "@/lib/catalog";

/** Card for featured / highlight / study entries. The whole card is one link. */
export default function EntryCard({
  e,
  size = "card",
  logCount = 0,
  dateLabel,
}: {
  e: EntryLite;
  size?: "featured" | "card" | "study";
  logCount?: number;
  dateLabel?: string;
}) {
  return (
    <SiteLink href={e.href} className={`entry-card entry-card--${size}`} data-press="row">
      <span className="entry-card-eyebrow">{areaLabel(e.area)}{e.bespoke && size !== "study" ? " · study" : ""}</span>
      <span className="entry-card-title">{e.title}</span>
      <span className="entry-card-dek">{e.dek}</span>
      <span className="entry-meta">
        <time dateTime={e.published}>{dateLabel ?? shortDate(e.published)}</time>
        <span className="sep" aria-hidden="true">·</span>
        <StatusDot tone={e.tone} label={e.status} />
        {logCount ? (
          <>
            <span className="sep" aria-hidden="true">·</span>
            <span>{logCount} log {logCount === 1 ? "entry" : "entries"}</span>
          </>
        ) : null}
      </span>
    </SiteLink>
  );
}

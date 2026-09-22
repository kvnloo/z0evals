import type { ReactNode } from "react";

type Kind = "info" | "success" | "warning" | "danger";

export default function Callout({
  kind = "info",
  title,
  children,
}: {
  kind?: Kind;
  title?: string;
  children: ReactNode;
}) {
  return (
    <aside className={`callout callout--${kind}`}>
      {title ? <div className="callout-title">{title}</div> : null}
      {children}
    </aside>
  );
}

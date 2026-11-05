"use client";

import { useEffect, useRef, type ReactNode } from "react";

/**
 * A figure whose method folds behind a "setup" pill at its top right. A click
 * elsewhere or Escape closes it. Without JS it is a plain <details>.
 */
export default function SetupFigure({
  setup,
  caption,
  wide = true,
  children,
}: {
  setup?: ReactNode;
  caption?: ReactNode;
  wide?: boolean;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDetailsElement>(null);
  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    const onDown = (e: PointerEvent) => {
      if (d.open && !d.contains(e.target as Node)) d.open = false;
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && d.open) d.open = false;
    };
    document.addEventListener("pointerdown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("pointerdown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, []);
  return (
    <figure className={`es-fig${wide ? " es-wide" : ""}${setup ? " has-setup" : ""}`}>
      {setup ? (
        <details className="es-setup" ref={ref}>
          <summary>setup</summary>
          <div className="es-setup-body">{setup}</div>
        </details>
      ) : null}
      {children}
      {caption ? <figcaption className="fig-caption">{caption}</figcaption> : null}
    </figure>
  );
}

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { FrogGlyph } from "./Frog";

/**
 * A heading with the reference's copy-link frog.
 *
 * Mirrors the reference markup exactly:
 *   <h2 class="heading-with-frog"><span>…</span>
 *     <button class="heading-frog-link" aria-label="Copy link to this section">
 *       <svg …>…</svg></button></h2>
 *
 * The frog is `opacity:0` until the heading is hovered or the button is
 * focused, flashes a `Copied Link` pill for 1.5s on activation (the same
 * `tooltipFade` the reference uses), and is `display:none` below 768px.
 */
export default function HeadingFrog({
  id,
  level,
  children,
}: {
  id: string;
  level: 2 | 3;
  children: React.ReactNode;
}) {
  const [copied, setCopied] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => () => {
    if (timer.current) clearTimeout(timer.current);
  }, []);

  const copy = useCallback(() => {
    const url = `${window.location.origin}${window.location.pathname}#${id}`;
    const done = () => {
      setCopied(true);
      if (timer.current) clearTimeout(timer.current);
      timer.current = setTimeout(() => setCopied(false), 1500);
    };
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(url).then(done, done);
    } else {
      done();
    }
  }, [id]);

  return (
    <div className="heading-with-frog" id={id} data-level={level}>
      {level === 2 ? <h2>{children}</h2> : <h3>{children}</h3>}
      <button
        type="button"
        className={`heading-frog-link${copied ? " copied" : ""}`}
        aria-label="Copy link to this section"
        onClick={copy}
      >
        <FrogGlyph width={level === 2 ? 24 : 20} height={level === 2 ? 18 : 15} />
      </button>
    </div>
  );
}

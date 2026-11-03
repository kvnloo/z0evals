"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import type { ComponentProps, MouseEvent } from "react";
import { reduced } from "@/lib/ux/motion";

// One pending view-transition resolver. SiteHeader's RouteSignal resolves it when the
// new pathname commits, so the transition snapshots the finished page.
let resolvePending: (() => void) | null = null;

export function routeCommitted() {
  resolvePending?.();
  resolvePending = null;
}

type DocWithVT = Document & { startViewTransition?: (cb: () => Promise<void> | void) => unknown };

/**
 * next/link with a root-absolute href (Next adds the basePath). Same-document route
 * changes run inside document.startViewTransition when the browser has it and the
 * reader has not asked for reduced motion; everywhere else navigation is instant.
 */
export default function SiteLink({ href, onClick, ...rest }: ComponentProps<typeof Link> & { href: string }) {
  const router = useRouter();
  const handle = (e: MouseEvent<HTMLAnchorElement>) => {
    onClick?.(e);
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    if (rest.target && rest.target !== "_self") return;
    const doc = document as DocWithVT;
    if (!doc.startViewTransition || reduced()) return;
    const base = process.env.NEXT_PUBLIC_BASE_PATH ?? "";
    const [path, hash] = href.split("#");
    const here = location.pathname.replace(base, "") || "/";
    if (path === "" || (path === here && hash !== undefined)) return; // in-page anchor
    e.preventDefault();
    doc.startViewTransition(
      () =>
        new Promise<void>((resolve) => {
          resolvePending?.();
          resolvePending = resolve;
          window.setTimeout(resolve, 600); // never hold the old snapshot longer than this
          router.push(href);
        }),
    );
  };
  return <Link href={href} onClick={handle} {...rest} />;
}

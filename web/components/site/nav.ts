export const NAV = [
  { href: "/research/", label: "research" },
  { href: "/studies/", label: "studies" },
  { href: "/log/", label: "log" },
  { href: "/about/", label: "about" },
] as const;

const SECTION_ROOTS = ["/", "/research/", "/studies/", "/log/", "/about/"];

/** Which nav item a pathname belongs to: posts → research, bespoke studies → studies. */
export function currentNav(pathname: string, studySlugs: string[]): string | null {
  const p = pathname.endsWith("/") ? pathname : `${pathname}/`;
  if (p === "/") return null;
  for (const n of NAV) if (p.startsWith(n.href)) return n.href;
  if (studySlugs.some((s) => p.startsWith(`/${s}/`))) return "/studies/";
  return "/research/";
}

export function isArticlePath(pathname: string): boolean {
  const p = pathname.endsWith("/") ? pathname : `${pathname}/`;
  return !SECTION_ROOTS.includes(p);
}

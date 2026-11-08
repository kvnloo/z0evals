// URL for a file under web/public, with the channel basePath applied.
// next/image would do this, but the site exports unoptimized static HTML and
// the essay figures use plain <img>/<video>.
export function asset(path: string): string {
  const base = process.env.NEXT_PUBLIC_BASE_PATH ?? "";
  return `${base}${path.startsWith("/") ? path : `/${path}`}`;
}

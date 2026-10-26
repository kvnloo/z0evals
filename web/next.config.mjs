/** @type {import('next').NextConfig} */
const base = (process.env.Z0_BASE_PATH || "").replace(/\/+$/, "");
const nextConfig = {
  // Static export: GitHub Pages serves files, there is no Node runtime.
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
  // Served under /z0evals on Pages; the channel path is applied at deploy time.
  // Next rejects a basePath with a trailing slash, so strip one defensively
  // rather than trusting the caller to have removed it.
  basePath: base,
  assetPrefix: base,
  // for URLs that bypass next/link (location.replace, fetch)
  env: { NEXT_PUBLIC_BASE_PATH: base },
};
export default nextConfig;

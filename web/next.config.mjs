/** @type {import('next').NextConfig} */
const nextConfig = {
  // Static export: GitHub Pages serves files, there is no Node runtime.
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
  // Served under /z0evals/ on Pages; the channel path is applied at deploy time.
  basePath: process.env.Z0_BASE_PATH || "",
  assetPrefix: process.env.Z0_BASE_PATH || "",
};
export default nextConfig;

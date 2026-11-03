import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";
import "./globals.css";
import SiteHeader from "@/components/site/SiteHeader";
import SiteFooter from "@/components/site/SiteFooter";
import Haptics from "@/components/site/Haptics";
import { latest, lite, site, studySlugs } from "@/lib/catalog";

// The reference self-hosts HK Grotesk and Departure Mono. HK Grotesk is a
// commercial face and Departure Mono's webfont is not fetchable from CI, so we
// use the closest open equivalents and keep the same roles: Hanken Grotesk is
// the same designer lineage as HK Grotesk, and a technical mono covers the
// label/number/code role. See web/README.md for the substitution table.
//
// All three faces are OFL and self-hosted from ./fonts (latin subset, from
// @fontsource 5.3.0; licences next to the files), so `next build` needs no
// network. next/font/google fetched fonts.googleapis.com at build time, and the
// z0 onboard web build failed whenever that fetch did.
const sans = localFont({
  src: [
    { path: "./fonts/hanken-grotesk-latin-400-normal.woff2", weight: "400", style: "normal" },
    { path: "./fonts/hanken-grotesk-latin-600-normal.woff2", weight: "600", style: "normal" },
  ],
  display: "swap",
  variable: "--font-hk-grotesk",
});
const mono = localFont({
  src: [
    { path: "./fonts/ibm-plex-mono-latin-400-normal.woff2", weight: "400", style: "normal" },
    { path: "./fonts/ibm-plex-mono-latin-500-normal.woff2", weight: "500", style: "normal" },
  ],
  display: "swap",
  variable: "--font-departure-mono",
});
// Dash Living Night display face.
const display = localFont({
  src: [
    { path: "./fonts/cormorant-garamond-latin-500-normal.woff2", weight: "500", style: "normal" },
    { path: "./fonts/cormorant-garamond-latin-500-italic.woff2", weight: "500", style: "italic" },
  ],
  display: "swap",
  variable: "--font-cormorant",
});

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: "#0c0c0a",
};

export const metadata: Metadata = {
  title: "zer0 evals — z0evals",
  description:
    "zer0 research measures what agent harnesses actually do — cost, speed, memory, governance — "
    + "and publishes the receipts, including the negative results.",
  other: { "view-transition": "same-origin" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${sans.variable} ${mono.variable} ${display.variable}`}>
      <body>
        <a className="skip-link" href="#main">skip to content</a>
        <SiteHeader latest={latest(3).map(lite)} studySlugs={studySlugs()} repo={site().repo} />
        <main id="main">{children}</main>
        <SiteFooter />
        <Haptics />
      </body>
    </html>
  );
}

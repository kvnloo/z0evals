import type { Metadata, Viewport } from "next";
import { Cormorant_Garamond, Hanken_Grotesk, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import SiteHeader from "@/components/site/SiteHeader";
import SiteFooter from "@/components/site/SiteFooter";
import Haptics from "@/components/site/Haptics";
import { latest, lite, site, studySlugs } from "@/lib/catalog";

// The reference self-hosts HK Grotesk and Departure Mono. HK Grotesk is a
// commercial face and Departure Mono's webfont is not fetchable from CI, so we
// load the closest open equivalents and keep the same roles: Hanken Grotesk is
// the same designer lineage as HK Grotesk, and a technical mono covers the
// label/number/code role. See web/README.md for the substitution table.
const sans = Hanken_Grotesk({
  subsets: ["latin"],
  weight: ["400", "600"],
  display: "swap",
  variable: "--font-hk-grotesk",
});
const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  display: "swap",
  variable: "--font-departure-mono",
});
// Parastoo is the reference's own display face and is available openly, so the
// display role needs no substitution at all.
// Dash Living Night display face.
const display = Cormorant_Garamond({
  subsets: ["latin"],
  weight: ["500"],
  style: ["normal", "italic"],
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

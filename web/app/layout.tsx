import type { Metadata } from "next";
import { Hanken_Grotesk, JetBrains_Mono } from "next/font/google";
import "./globals.css";

// The reference self-hosts HK Grotesk and Departure Mono. HK Grotesk is a
// commercial face and Departure Mono's webfont is not fetchable from CI, so we
// load the closest open equivalents and keep the same roles: Hanken Grotesk is
// the same designer lineage as HK Grotesk, and a technical mono covers the
// label/number/code role. See web/README.md for the substitution table.
const sans = Hanken_Grotesk({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-hk-grotesk",
});
const mono = JetBrains_Mono({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-departure-mono",
});

export const metadata: Metadata = {
  title: "Small Models Calling the Shots — z0evals",
  description:
    "Phase 1B: what actually routes best on a local RTX 3080 Ti? Measured, not modelled.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${sans.variable} ${mono.variable}`}>
      <body>{children}</body>
    </html>
  );
}

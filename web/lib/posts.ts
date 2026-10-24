// Reads posts prerendered by scripts/build_posts.py. Every markdown post gets a page
// without a bespoke TSX file; slugs with their own app/<slug>/page.tsx keep it.
import fs from "node:fs";
import path from "node:path";

export type PostToc = { id: string; label: string };
export type Post = {
  slug: string;
  title: string;
  subtitle: string;
  study: string;
  status: string;
  author: string;
  date: string;
  toc: PostToc[];
  lede: string;
  html: string;
};

const DATA_DIR = path.join(process.cwd(), "data", "posts");
const APP_DIR = path.join(process.cwd(), "app");
// Markdown sources whose story already *is* a bespoke page under another route.
const RENDERED_ELSEWHERE = new Set(["slm-router-v0"]); // the phase 1b home page

export function hasBespokePage(slug: string): boolean {
  return RENDERED_ELSEWHERE.has(slug) || fs.existsSync(path.join(APP_DIR, slug, "page.tsx"));
}

export function readPost(slug: string): Post {
  return JSON.parse(fs.readFileSync(path.join(DATA_DIR, `${slug}.json`), "utf8")) as Post;
}

export function allPostSlugs(): string[] {
  if (!fs.existsSync(DATA_DIR)) return [];
  return fs.readdirSync(DATA_DIR).filter((f) => f.endsWith(".json")).map((f) => f.slice(0, -5)).sort();
}

export function markdownOnlySlugs(): string[] {
  return allPostSlugs().filter((s) => !hasBespokePage(s));
}

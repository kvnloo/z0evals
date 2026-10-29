// Shared shapes for story pages (bespoke studies and markdown posts).
export type StoryMeta = {
  title: string;
  subtitle: string;
  author: string;
  date: string;
  status: string;
  lede: string;
};

export type StoryBanner = { tag: string; text: string; preserve_ref?: string };

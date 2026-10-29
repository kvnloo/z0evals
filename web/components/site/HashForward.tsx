"use client";
import { useEffect } from "react";

/** Old phase-1b deep links (/#residency) now live at /slm-router-v0/#residency. */
export default function HashForward({ ids }: { ids: string[] }) {
  useEffect(() => {
    const id = decodeURIComponent(location.hash.replace(/^#/, ""));
    if (!id || !ids.includes(id)) return;
    location.replace(`${process.env.NEXT_PUBLIC_BASE_PATH ?? ""}/slm-router-v0/#${id}`);
  }, [ids]);
  return null;
}

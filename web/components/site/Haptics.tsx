"use client";
import { useEffect } from "react";
import { haptic, type HapticKind } from "@/lib/ux/haptics";

/** Delegated click listener: any element with data-haptic="tap|select|success|error"
 *  fires that pattern on click, so server components can opt in with an attribute. */
export default function Haptics() {
  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      const el = (e.target as Element | null)?.closest?.("[data-haptic]") as HTMLElement | null;
      const kind = el?.dataset.haptic as HapticKind | undefined;
      if (kind && kind in haptic) haptic[kind]();
    };
    document.addEventListener("click", onClick);
    return () => document.removeEventListener("click", onClick);
  }, []);
  return null;
}

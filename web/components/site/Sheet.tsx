"use client";

import { useEffect, useRef, type ReactNode, type RefObject } from "react";
import { EASE_CRIT, MS, follow, reduced } from "@/lib/ux/motion";
import { useSwipe } from "@/lib/ux/gesture";
import { haptic } from "@/lib/ux/haptics";

const BACKDROP = 0.55;

let locks = 0;
function lockScroll() {
  if (locks++ === 0) document.documentElement.style.overflow = "hidden";
}
function unlockScroll() {
  if (--locks <= 0) {
    locks = 0;
    document.documentElement.style.overflow = "";
  }
}

/**
 * Shared bottom sheet (menu, contents). Opens with translateY(100%) → 0 over --t-nav,
 * backdrop opacity follows sheet progress, pull down to dismiss (handle anywhere, body
 * only when it is scrolled to the top), Esc closes, focus is trapped and returned.
 */
export default function Sheet({
  open,
  onClose,
  onClosed,
  label,
  returnFocus,
  className = "",
  children,
  id,
}: {
  open: boolean;
  onClose: (reason: "esc" | "backdrop" | "drag" | "button") => void;
  onClosed?: () => void;
  label: string;
  returnFocus?: RefObject<HTMLElement | null>;
  className?: string;
  children: ReactNode;
  id?: string;
}) {
  const root = useRef<HTMLDivElement>(null);
  const sheet = useRef<HTMLDivElement>(null);
  const back = useRef<HTMLDivElement>(null);
  const body = useRef<HTMLDivElement>(null);
  const shown = useRef(false);
  const draggedShut = useRef(false);
  const startedInBody = useRef(false);
  const closedCb = useRef(onClosed);
  closedCb.current = onClosed;
  const height = () => sheet.current?.offsetHeight || window.innerHeight * 0.6;

  // open / close
  useEffect(() => {
    const r = root.current;
    const s = sheet.current;
    const b = back.current;
    if (!r || !s || !b) return;
    if (open && !shown.current) {
      shown.current = true;
      r.hidden = false;
      r.inert = false;
      lockScroll();
      const h = height();
      if (!reduced()) {
        s.animate([{ transform: `translate3d(0,${h}px,0)` }, { transform: "translate3d(0,0,0)" }], { duration: MS.nav, easing: EASE_CRIT });
        b.animate([{ opacity: 0 }, { opacity: BACKDROP }], { duration: MS.nav, easing: EASE_CRIT });
      }
      s.style.transform = "translate3d(0,0,0)";
      b.style.opacity = String(BACKDROP);
      const first = s.querySelector<HTMLElement>("[data-autofocus]") ?? s.querySelector<HTMLElement>("a[href],button:not([disabled])");
      first?.focus({ preventScroll: true });
    } else if (!open && shown.current) {
      shown.current = false;
      const done = () => {
        r.hidden = true;
        r.inert = true;
        s.style.transform = "";
        unlockScroll();
        returnFocus?.current?.focus({ preventScroll: true });
        closedCb.current?.();
      };
      if (draggedShut.current || reduced()) {
        draggedShut.current = false;
        done();
        return;
      }
      const h = height();
      const a = s.animate([{ transform: "translate3d(0,0,0)" }, { transform: `translate3d(0,${h}px,0)` }], { duration: MS.nav, easing: EASE_CRIT, fill: "forwards" });
      b.animate([{ opacity: BACKDROP }, { opacity: 0 }], { duration: MS.nav, easing: EASE_CRIT, fill: "forwards" });
      a.addEventListener("finish", () => {
        done();
        s.getAnimations().forEach((x) => x.cancel());
        b.getAnimations().forEach((x) => x.cancel());
      });
    }
  }, [open, returnFocus]);

  useEffect(() => () => {
    if (shown.current) unlockScroll();
  }, []);

  // Esc + focus trap
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose("esc");
        return;
      }
      if (e.key !== "Tab" || !sheet.current) return;
      const f = Array.from(sheet.current.querySelectorAll<HTMLElement>('a[href],button:not([disabled]),[tabindex]:not([tabindex="-1"])'));
      if (!f.length) return;
      const first = f[0];
      const last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  // pull-down: keep the browser from claiming a downward pull while the body is at its top
  useEffect(() => {
    const el = body.current;
    if (!el) return;
    let y0 = 0;
    const start = (e: TouchEvent) => {
      y0 = e.touches[0]?.clientY ?? 0;
    };
    const move = (e: TouchEvent) => {
      const y = e.touches[0]?.clientY ?? 0;
      if (el.scrollTop <= 0 && y > y0 && e.cancelable) e.preventDefault();
    };
    el.addEventListener("touchstart", start, { passive: true });
    el.addEventListener("touchmove", move, { passive: false });
    return () => {
      el.removeEventListener("touchstart", start);
      el.removeEventListener("touchmove", move);
    };
  }, []);

  useSwipe(sheet, {
    axis: "y",
    canStart: (e) => {
      if (!open) return false;
      startedInBody.current = Boolean(body.current?.contains(e.target as Node));
      // mouse drags in the body are text selection; only the handle drags the sheet
      if (e.pointerType === "mouse" && !(e.target as Element | null)?.closest?.(".sheet-handle")) return false;
      return !startedInBody.current || (body.current?.scrollTop ?? 0) <= 0;
    },
    canLock: (dy) => !startedInBody.current || dy > 0,
    range: () => [0, height()],
    extent: height,
    onMove: (y) => {
      if (back.current) back.current.style.opacity = String(BACKDROP * Math.max(0, Math.min(1, 1 - y / height())));
    },
    onRelease: ({ commit, dir }) => {
      if (commit && dir === 1) {
        haptic.select();
        return height();
      }
      return 0;
    },
    onSettleStart: (from, to, v) => {
      const b = back.current;
      if (!b) return;
      const h = height();
      follow(b, "opacity", BACKDROP * (1 - from / h), to >= h ? 0 : BACKDROP, to - from, v);
    },
    onSettled: (to) => {
      if (to >= height() - 1) {
        draggedShut.current = true;
        onClose("drag");
      }
    },
  });

  return (
    <div ref={root} className={`sheet-root ${className}`.trim()} hidden inert id={id}>
      <div ref={back} className="sheet-backdrop" aria-hidden="true" onClick={() => onClose("backdrop")} />
      <div ref={sheet} className="sheet" role="dialog" aria-modal="true" aria-label={label}>
        <div className="sheet-handle" aria-hidden="true">
          <span />
        </div>
        <div ref={body} className="sheet-body">
          {children}
        </div>
      </div>
    </div>
  );
}

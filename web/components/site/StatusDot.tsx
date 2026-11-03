import type { Tone } from "@/lib/status";

/** Status is a dot plus a text label, never a pill and never colour alone. */
export default function StatusDot({ tone, label, className = "" }: { tone: Tone; label: string; className?: string }) {
  return (
    <span className={`status-dot ${className}`.trim()}>
      <span className={`dot ${tone}`} aria-hidden="true" />
      {label}
    </span>
  );
}

import type { ReactNode } from "react";

/**
 * The reference opens with one dominant figure and its chart side by side
 * ("220,297 tool calls" beside the distribution). Ours opens the same way:
 * the receipt count carries the column, the evidence-base chart sits beside it.
 */
export default function HeadlineFigure({
  value, unit, caption, children,
}: {
  value: string; unit: string; caption: ReactNode; children: ReactNode;
}) {
  return (
    <div className="headline">
      <div className="headline-figure">
        <div className="headline-value">{value}</div>
        <div className="headline-unit">{unit}</div>
        <div className="headline-caption">{caption}</div>
      </div>
      <div className="headline-chart">{children}</div>
    </div>
  );
}

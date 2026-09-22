"use client";
import { useReveal } from "./charts/useReveal";

type Action = { id: string; offered: number; selected: number; selectionRate: number | null; dangerous: number };

/**
 * Offered vs selected per action, with an inline bar — the reference's
 * per-tool table (Tool | Scored | Flagged | Rate) over our action vocabulary.
 *
 * "Offered" is how many recorded runs had the action in the compiled legal set;
 * "selected" is how many chose it. The gap is what the compiler removed.
 */
export default function ActionTable({ actions, limit = 14 }: { actions: Action[]; limit?: number }) {
  const { ref, shown } = useReveal<HTMLDivElement>(0.15);
  const rows = actions.slice(0, limit);
  const maxOffered = Math.max(...rows.map((a) => a.offered), 1);

  return (
    <div ref={ref}>
      <table className="data-table action-table">
        <thead>
          <tr>
            <th>action</th><th className="num">offered</th><th className="num">selected</th>
            <th>selection rate</th><th className="num">dangerous</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((a, i) => {
            const rate = a.selectionRate ?? 0;
            const offeredW = (a.offered / maxOffered) * 100;
            const selW = (a.selected / maxOffered) * 100;
            return (
              <tr key={a.id}>
                <td style={{ fontFamily: "var(--font-mono)", fontSize: 12.5 }}>{a.id}</td>
                <td className="num">{a.offered}</td>
                <td className="num">{a.selected}</td>
                <td>
                  <div className="bar-cell"
                       title={`${a.selected} of ${a.offered} runs (${(rate * 100).toFixed(0)}%)`}>
                    <span className="bar-ghost" style={{ width: `${shown ? offeredW : 0}%` }} />
                    <span className="bar-fill" style={{ width: `${shown ? selW : 0}%` }}
                          data-hot={a.dangerous > 0} />
                    <span className="bar-label">{(rate * 100).toFixed(0)}%</span>
                  </div>
                </td>
                <td className="num" style={{ color: a.dangerous ? "#b91c1c" : "#a8a8a8" }}>
                  {a.dangerous || "—"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <div className="legend">
        <span><i className="swatch" style={{ background: "#e7e7e7" }} />offered in the compiled legal set</span>
        <span><i className="swatch" style={{ background: "#29916e" }} />chosen</span>
        <span>the gap is what the compiler removed</span>
      </div>
    </div>
  );
}

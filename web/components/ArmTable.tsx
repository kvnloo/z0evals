import type { Arm } from "@/data/types";

const pct = (v: number, d = 1) => `${(v * 100).toFixed(d)}%`;

/** Observer comparison table — ours are the measured arms. */
export default function ArmTable({ arms, highlight }: { arms: Arm[]; highlight?: string[] }) {
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>arm</th><th className="num">runs</th><th className="num">success</th>
          <th className="num">Wilson 95%</th><th className="num">warm p50</th>
          <th className="num">dangerous</th><th className="num">abstained</th><th className="num">rep. split</th>
        </tr>
      </thead>
      <tbody>
        {arms.map((a) => (
          <tr key={a.id} data-active={highlight?.includes(a.id)}>
            <td style={{ color: a.unfiltered ? "#b91c1c" : undefined }}>{a.label}</td>
            <td className="num">{a.n}</td>
            <td className="num" style={{ fontWeight: 700 }}>{pct(a.successRate)}</td>
            <td className="num">[{pct(a.wilson95[0], 2)}, {pct(a.wilson95[1], 2)}]</td>
            <td className="num">{a.warmP50Ms == null ? "—" : `${Math.round(a.warmP50Ms).toLocaleString()} ms`}</td>
            <td className="num" style={{ color: a.dangerous ? "#b91c1c" : "#29916e" }}>{a.dangerous}</td>
            <td className="num">{a.abstained}</td>
            <td className="num" style={{ color: a.repDisagreeStates ? "#b45309" : undefined }}>{a.repDisagreeStates}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function MetricRow({
  items,
}: { items: { k: string; v: string; s?: string }[] }) {
  return (
    <div className="metric-row">
      {items.map((m) => (
        <div className="metric" key={m.k}>
          <div className="k">{m.k}</div>
          <div className="v">{m.v}</div>
          {m.s ? <div className="s">{m.s}</div> : null}
        </div>
      ))}
    </div>
  );
}

import MsPill from "./MsPill";

function Delta({ v }) {
  if (v === null || v === undefined) return <span className="text-muted">—</span>;
  if (v === 0) return <span className="text-muted-2">0</span>;
  const show = Math.round(v * 10) / 10;
  return (
    <span className={`font-mono ${show > 0 ? "text-positive" : "text-negative"}`}>
      {show > 0 ? `+${show}` : show}
    </span>
  );
}

function actionPill(action) {
  if (!action) return null;
  if (action.startsWith("SELL")) return <MsPill kind="fail">{action}</MsPill>;
  if (action.startsWith("BUY")) return <MsPill kind="pass">{action}</MsPill>;
  return <MsPill kind="neutral">{action}</MsPill>;
}

/** The ranks table — report 93's latest-close ranking with Δ vs the last
 * review and the action a review on this data would take. Used full-size on
 * the Ranking page and sliced on the report page. */
export default function RanksTable({ ranks, limit = 0 }) {
  if (!ranks?.rows?.length) return null;
  const rows = limit > 0 ? ranks.rows.slice(0, limit) : ranks.rows;
  return (
    <div className="overflow-x-auto rounded-xl border border-border">
      <table className="w-full text-[12.5px] border-collapse">
        <thead>
          <tr>
            {["Rank", "Δ rank", "Stock", "Fit %", "Δ fit", "", "Action"].map((h, i) => (
              <th
                key={h + i}
                className={`sticky top-0 bg-panel-2 text-muted font-semibold px-3 py-2 text-[11px] uppercase tracking-wide border-b border-border ${
                  i === 2 ? "text-left" : i === 6 ? "text-right" : "text-right"
                }`}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr
              key={r.ticker}
              className={`border-b border-border/60 last:border-0 ${r.held ? "bg-accent/[0.06]" : ""}`}
            >
              <td className="px-3 py-1.5 text-right font-mono text-text font-semibold">#{r.rank}</td>
              <td className="px-3 py-1.5 text-right">
                <Delta v={r.rank_delta} />
              </td>
              <td className="px-3 py-1.5 text-left font-mono">{r.ticker}</td>
              <td className="px-3 py-1.5 text-right font-mono text-muted-2">
                {r.fit === null || r.fit === undefined ? "—" : `${r.fit}%`}
              </td>
              <td className="px-3 py-1.5 text-right">
                <Delta v={r.fit_delta} />
              </td>
              <td className="px-3 py-1.5 text-right">{r.held ? <MsPill kind="info">HELD</MsPill> : null}</td>
              <td className="px-3 py-1.5 text-right">{actionPill(r.action)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

import { pct, kindOf } from "../lib/format";

const VALUE_CLASS = {
  positive: "text-positive",
  negative: "text-negative",
  neutral: "text-text",
};

export default function KpiTable({ series, symbol = "₹" }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-border">
      <table className="w-full text-[13px] border-collapse">
        <thead>
          <tr>
            {["Series", "Net return", series[0]?.growthLabel ?? "CAGR", "Max drawdown", "Longest underwater"].map(
              (h, i) => (
                <th
                  key={h}
                  className={`sticky top-0 bg-panel-2 text-muted font-semibold px-3 py-2 text-[11px] uppercase tracking-wide border-b border-border ${
                    i === 0 ? "text-left" : "text-right"
                  }`}
                >
                  {h}
                </th>
              )
            )}
          </tr>
        </thead>
        <tbody>
          {series.map((s, i) => (
            <tr
              key={s.path}
              className={`border-b border-border transition-colors hover:bg-white/[0.04] ${
                i % 2 === 1 ? "bg-white/[0.015]" : ""
              }`}
            >
              <td className="px-3 py-1.5 text-left whitespace-nowrap">{s.label}</td>
              <td className={`px-3 py-1.5 text-right whitespace-nowrap font-mono ${VALUE_CLASS[kindOf(s.netReturnPct)]}`}>
                {pct(s.netReturnPct)}
              </td>
              <td className={`px-3 py-1.5 text-right whitespace-nowrap font-mono ${VALUE_CLASS[kindOf(s.growthPct)]}`}>
                {pct(s.growthPct)}
              </td>
              <td className="px-3 py-1.5 text-right whitespace-nowrap font-mono text-negative">
                {pct(s.maxDrawdownPct, 1, false)}
              </td>
              <td className="px-3 py-1.5 text-right whitespace-nowrap font-mono text-text">
                {s.longestUnderwaterDays.toLocaleString()}d
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

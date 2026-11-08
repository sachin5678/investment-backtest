import { pct, kindOf } from "../lib/format";
import Panel, { WhatThisShows } from "./Panel";

const VALUE_CLASS = { positive: "text-positive", negative: "text-negative", neutral: "text-text" };

function median(arr) {
  const s = [...arr].sort((a, b) => a - b);
  const m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

function Cell({ cagr, dd }) {
  return (
    <td className="px-3 py-1.5 text-right whitespace-nowrap font-mono">
      <span className={VALUE_CLASS[kindOf(cagr)]}>{pct(cagr)}</span>
      <span className="text-muted"> / </span>
      <span className="text-negative">{pct(dd, 1, false)}</span>
    </td>
  );
}

/** Report 107's all-12-rebalance-months table. Honours the same filter
 * boxes as the charts (gold switch / no switch, top N, execution). */
export default function CalendarTable({ rows, filter }) {
  if (!rows?.length) return null;
  const execs = [...(filter.open ? [["open", "Next-open"]] : []), ...(filter.close ? [["close", "Same-close"]] : [])];
  const kinds = [...(filter.plain ? [["plain", "No switch"]] : []), ...(filter.gold ? [["gold", "Gold switch"]] : [])];
  const cols = execs.flatMap(([e, el]) => kinds.map(([k, kl]) => ({ key: `${e}_${k}`, label: `${el} · ${kl}` })));
  const nList = [5, 10, 20].filter((n) => filter.ns[n]);

  return (
    <Panel>
      <h3 className="text-base font-bold text-text mb-1">Every yearly rebalance month — CAGR / max drawdown</h3>
      <WhatThisShows>
        A yearly rebalance is very sensitive to <em>which</em> month it happens in. Each row is one rebalance month; the shaded row closing each
        block is the median of the 12. Follows the filter boxes above.
      </WhatThisShows>
      {cols.length === 0 || nList.length === 0 ? (
        <p className="text-muted text-sm">Nothing selected.</p>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-border">
          <table className="w-full text-[13px] border-collapse">
            <thead>
              <tr>
                {["Top N", "Month", ...cols.map((c) => c.label)].map((h, i) => (
                  <th
                    key={h}
                    className={`sticky top-0 bg-panel-2 text-muted font-semibold px-3 py-2 text-[11px] uppercase tracking-wide border-b border-border ${
                      i < 2 ? "text-left" : "text-right"
                    }`}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {nList.flatMap((n) => {
                const block = rows.filter((r) => r.n === n);
                return [
                  ...block.map((r) => (
                    <tr key={`${n}-${r.month}`} className="border-b border-border hover:bg-white/[0.04]">
                      <td className="px-3 py-1.5 text-left font-mono text-muted-2">{n}</td>
                      <td className="px-3 py-1.5 text-left">{r.calendar}</td>
                      {cols.map((c) => (
                        <Cell key={c.key} cagr={r[c.key].cagr_pct} dd={r[c.key].max_drawdown_pct} />
                      ))}
                    </tr>
                  )),
                  <tr key={`${n}-med`} className="border-b-2 border-border bg-white/[0.05] font-semibold">
                    <td className="px-3 py-1.5 text-left font-mono">{n}</td>
                    <td className="px-3 py-1.5 text-left">Median</td>
                    {cols.map((c) => (
                      <Cell
                        key={c.key}
                        cagr={median(block.map((r) => r[c.key].cagr_pct))}
                        dd={median(block.map((r) => r[c.key].max_drawdown_pct))}
                      />
                    ))}
                  </tr>,
                ];
              })}
            </tbody>
          </table>
        </div>
      )}
    </Panel>
  );
}

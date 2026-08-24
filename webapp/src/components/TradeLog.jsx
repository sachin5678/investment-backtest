import { useState } from "react";
import { pct, money } from "../lib/format";
import Panel, { WhatThisShows } from "./Panel";
import Pill from "./Pill";

const ROW_CLASS = {
  win: "text-positive",
  loss: "text-negative",
  open: "text-assumption",
};

const TAG_CLASS = {
  new: "bg-accent/15 text-accent",
  carried: "bg-[#8B5CF6]/15 text-[#8B5CF6]",
  exited: "bg-muted/15 text-muted",
  open: "bg-assumption/15 text-assumption",
};

function Tag({ kind, children }) {
  return (
    <span className={`inline-flex items-center text-[10px] font-semibold px-1.5 py-0.5 rounded whitespace-nowrap ml-1 ${TAG_CLASS[kind]}`}>
      {children}
    </span>
  );
}

function rowKind(t) {
  if (t.status === "open") return "open";
  return t.pct_return > 0 ? "win" : "loss";
}

/** Merged-holding trades (report 31) carry num_rebalances_held + carried_dates
 * — every other trade-log report (24/26) doesn't, and gets the original
 * grouped-by-rebalance-period rendering instead. */
function isMergedTrade(t) {
  return t.num_rebalances_held !== undefined;
}

function TradeRow({ t, symbol, merged }) {
  const kind = rowKind(t);
  return (
    <tr className="border-b border-border/60">
      <td className="px-3 py-1.5 text-left whitespace-nowrap">
        {t.ticker}
        {merged && <Tag kind="new">NEW</Tag>}
        {merged && t.carried_dates?.length > 0 && <Tag kind="carried">CARRIED ×{t.carried_dates.length}</Tag>}
        {merged && <Tag kind={t.status === "open" ? "open" : "exited"}>{t.status === "open" ? "OPEN" : "EXITED"}</Tag>}
        {t.carried_in && <span className="text-[10px] text-muted ml-1">(entered before window)</span>}
      </td>
      <td className="px-3 py-1.5 text-right whitespace-nowrap font-mono text-muted-2">{t.entry_date}</td>
      <td className="px-3 py-1.5 text-right whitespace-nowrap font-mono text-muted-2">{money(t.entry_price, symbol, 2)}</td>
      <td className="px-3 py-1.5 text-right whitespace-nowrap font-mono text-muted-2">{t.exit_date}</td>
      <td className="px-3 py-1.5 text-right whitespace-nowrap font-mono text-muted-2">{money(t.exit_price, symbol, 2)}</td>
      {merged && (
        <td className="px-3 py-1.5 text-right whitespace-nowrap font-mono text-muted-2">{t.num_rebalances_held}</td>
      )}
      <td className={`px-3 py-1.5 text-right whitespace-nowrap font-mono ${ROW_CLASS[kind]}`}>{pct(t.pct_return)}</td>
      <td className={`px-3 py-1.5 text-right whitespace-nowrap font-mono ${ROW_CLASS[kind]}`}>{money(t.pnl, symbol, 2)}</td>
      <td className="px-3 py-1.5 text-left whitespace-nowrap text-muted-2">{t.status === "open" ? "Still held" : "Closed"}</td>
    </tr>
  );
}

function TradeTable({ rows, symbol, merged, caption }) {
  const headers = merged
    ? ["Stock", "Entered", "Entry price", "Exited / as-of", "Exit price", "Rebalances held", "Return", `P&L (${symbol})`, "Status"]
    : ["Stock", "Bought", "Buy price", "Sold / as-of", "Sell price", "Return", `P&L (${symbol})`, "Status"];
  return (
    <div className="mb-5 last:mb-0">
      {caption && <div className="text-[13px] font-semibold text-muted-2 mb-2 font-mono">{caption}</div>}
      <div className="overflow-x-auto rounded-xl border border-border">
        <table className="w-full text-[13px] border-collapse">
          <thead>
            <tr>
              {headers.map((h, i) => (
                <th
                  key={h}
                  className={`sticky top-0 bg-panel-2 text-muted font-semibold px-3 py-2 text-[11px] uppercase tracking-wide border-b border-border ${
                    i === 0 || i === headers.length - 1 ? "text-left" : "text-right"
                  }`}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((t) => (
              <TradeRow key={t.ticker + t.entry_date} t={t} symbol={symbol} merged={merged} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/** Full buy/sell trade log. Two shapes are supported, auto-detected:
 *  - per-rebalance-leg trades (reports 24/26): grouped into one table per
 *    rebalance period, a fresh row for every leg a stock survives.
 *  - merged continuous-holding trades (report 31): one flat table, one row
 *    per stock's real uninterrupted tenure, with New/Carried/Exited tags.
 * Renders nothing when the underlying results*.json has no "trades" array
 * at all — every other report falls back to the generic KPI/chart/prose
 * view. */
export default function TradeLog({ trades, tradeStats, symbol = "₹" }) {
  const [open, setOpen] = useState(true);
  if (!trades || trades.length === 0) return null;

  const merged = isMergedTrade(trades[0]);
  const totalRows = tradeStats?.total_trades ?? tradeStats?.total_positions ?? trades.length;

  let body;
  if (merged) {
    const sorted = [...trades].sort((a, b) => b.pct_return - a.pct_return);
    body = <TradeTable rows={sorted} symbol={symbol} merged />;
  } else {
    const byPeriod = new Map();
    for (const t of trades) {
      const key = `${t.entry_date}|${t.exit_date}|${t.status}`;
      if (!byPeriod.has(key)) byPeriod.set(key, []);
      byPeriod.get(key).push(t);
    }
    const periods = [...byPeriod.entries()]
      .map(([key, rows]) => {
        const [entryDate, exitDate, status] = key.split("|");
        const label = `${entryDate} → ${exitDate}` + (status === "open" ? " (open, marked to latest price)" : "");
        return { label, rows: [...rows].sort((a, b) => b.pct_return - a.pct_return), sortKey: entryDate };
      })
      .sort((a, b) => (a.sortKey < b.sortKey ? -1 : a.sortKey > b.sortKey ? 1 : 0));
    body = periods.map((p) => <TradeTable key={p.label} rows={p.rows} symbol={symbol} caption={p.label} />);
  }

  return (
    <Panel>
      <div className="flex items-center justify-between mb-1 flex-wrap gap-2">
        <h3 className="text-base font-bold text-text">
          {merged ? "Full carried-position trade log — every distinct holding" : "Full buy/sell trade log — every stock, every rebalance"}
        </h3>
        <div className="flex items-center gap-2">
          <Pill kind="neutral">{totalRows} rows total</Pill>
          <button
            onClick={() => setOpen((v) => !v)}
            className="text-[11px] font-semibold text-muted hover:text-text transition-colors cursor-pointer"
          >
            {open ? "▲ collapse" : "▼ expand"}
          </button>
        </div>
      </div>
      <WhatThisShows>
        {merged
          ? "One row per stock's real continuous tenure in the top 10. NEW = first entered; CARRIED ×N = survived N additional rebalances without exiting; EXITED/OPEN = how the position currently stands. \"(entered before window)\" marks a position whose real entry predates this report's start date."
          : "One row per stock per holding period, grouped by rebalance date. Green = closed winner, red = closed loser, amber = still open (marked to the latest available price, unrealized). \"(carried in)\" marks a position bought at the rebalance just before this report's window started."}
      </WhatThisShows>
      {tradeStats && (
        <div className="flex gap-4 flex-wrap mb-4 text-[12.5px] text-muted-2">
          <span>
            Win rate <span className="font-mono text-text font-semibold">{tradeStats.win_rate_pct}%</span>
          </span>
          <span>
            Avg winner <span className="font-mono text-positive font-semibold">{pct(tradeStats.avg_win_pct)}</span>
          </span>
          <span>
            Avg loser <span className="font-mono text-negative font-semibold">{pct(tradeStats.avg_loss_pct)}</span>
          </span>
          {tradeStats.avg_rebalances_held !== undefined && (
            <span>
              Avg rebalances held <span className="font-mono text-text font-semibold">{tradeStats.avg_rebalances_held}</span>
            </span>
          )}
          <span>
            Realized P&amp;L <span className="font-mono text-text font-semibold">{money(tradeStats.total_realized_pnl, symbol, 2)}</span>
          </span>
          <span>
            Unrealized P&amp;L <span className="font-mono text-text font-semibold">{money(tradeStats.total_unrealized_pnl, symbol, 2)}</span>
          </span>
        </div>
      )}
      {open && body}
    </Panel>
  );
}

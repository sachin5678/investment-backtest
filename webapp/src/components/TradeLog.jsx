import { useState } from "react";
import { pct, money } from "../lib/format";
import Panel, { WhatThisShows } from "./Panel";
import Pill from "./Pill";

const ROW_CLASS = {
  win: "text-positive",
  loss: "text-negative",
  open: "text-assumption",
};

function rowKind(t) {
  if (t.status === "open") return "open";
  return t.pct_return > 0 ? "win" : "loss";
}

function TradeRow({ t, symbol }) {
  const kind = rowKind(t);
  return (
    <tr className="border-b border-border/60">
      <td className="px-3 py-1.5 text-left whitespace-nowrap">
        {t.ticker}
        {t.carried_in && <span className="text-[10px] text-muted ml-1">(carried in)</span>}
      </td>
      <td className="px-3 py-1.5 text-right whitespace-nowrap font-mono text-muted-2">{t.entry_date}</td>
      <td className="px-3 py-1.5 text-right whitespace-nowrap font-mono text-muted-2">{money(t.entry_price, symbol, 2)}</td>
      <td className="px-3 py-1.5 text-right whitespace-nowrap font-mono text-muted-2">{t.exit_date}</td>
      <td className="px-3 py-1.5 text-right whitespace-nowrap font-mono text-muted-2">{money(t.exit_price, symbol, 2)}</td>
      <td className={`px-3 py-1.5 text-right whitespace-nowrap font-mono ${ROW_CLASS[kind]}`}>{pct(t.pct_return)}</td>
      <td className={`px-3 py-1.5 text-right whitespace-nowrap font-mono ${ROW_CLASS[kind]}`}>{money(t.pnl, symbol, 2)}</td>
      <td className="px-3 py-1.5 text-left whitespace-nowrap text-muted-2">{t.status === "open" ? "Still held" : "Closed"}</td>
    </tr>
  );
}

function PeriodBlock({ entryDate, exitDate, status, rows, symbol }) {
  const sorted = [...rows].sort((a, b) => b.pct_return - a.pct_return);
  const label = `${entryDate} → ${exitDate}` + (status === "open" ? " (open, marked to latest price)" : "");
  return (
    <div className="mb-5 last:mb-0">
      <div className="text-[13px] font-semibold text-muted-2 mb-2 font-mono">{label}</div>
      <div className="overflow-x-auto rounded-xl border border-border">
        <table className="w-full text-[13px] border-collapse">
          <thead>
            <tr>
              {["Stock", "Bought", "Buy price", "Sold / as-of", "Sell price", "Return", `P&L (${symbol})`, "Status"].map(
                (h, i) => (
                  <th
                    key={h}
                    className={`sticky top-0 bg-panel-2 text-muted font-semibold px-3 py-2 text-[11px] uppercase tracking-wide border-b border-border ${
                      i === 0 || i === 7 ? "text-left" : "text-right"
                    }`}
                  >
                    {h}
                  </th>
                )
              )}
            </tr>
          </thead>
          <tbody>
            {sorted.map((t, i) => (
              <TradeRow key={t.ticker + t.entry_date} t={t} symbol={symbol} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/** Full buy/sell trade log — one row per stock per holding period, grouped
 * by rebalance date. Only rendered when the underlying results*.json
 * actually contains a "trades" array (currently just report 24) — every
 * other report falls back to the generic KPI/chart/prose view. */
export default function TradeLog({ trades, tradeStats, symbol = "₹" }) {
  const [open, setOpen] = useState(true);
  if (!trades || trades.length === 0) return null;

  const byPeriod = new Map();
  for (const t of trades) {
    const key = `${t.entry_date}|${t.exit_date}|${t.status}`;
    if (!byPeriod.has(key)) byPeriod.set(key, []);
    byPeriod.get(key).push(t);
  }
  const periods = [...byPeriod.entries()]
    .map(([key, rows]) => {
      const [entryDate, exitDate, status] = key.split("|");
      return { entryDate, exitDate, status, rows };
    })
    .sort((a, b) => (a.entryDate < b.entryDate ? -1 : a.entryDate > b.entryDate ? 1 : 0));

  return (
    <Panel>
      <div className="flex items-center justify-between mb-1 flex-wrap gap-2">
        <h3 className="text-base font-bold text-text">Full buy/sell trade log — every stock, every rebalance</h3>
        <div className="flex items-center gap-2">
          {tradeStats && <Pill kind="neutral">{tradeStats.total_trades} rows total</Pill>}
          <button
            onClick={() => setOpen((v) => !v)}
            className="text-[11px] font-semibold text-muted hover:text-text transition-colors cursor-pointer"
          >
            {open ? "▲ collapse" : "▼ expand"}
          </button>
        </div>
      </div>
      <WhatThisShows>
        One row per stock per holding period, grouped by rebalance date. Green = closed winner, red = closed loser, amber = still open
        (marked to the latest available price, unrealized). &quot;(carried in)&quot; marks a position bought at the rebalance just before this
        report&apos;s window started.
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
          <span>
            Realized P&amp;L <span className="font-mono text-text font-semibold">{money(tradeStats.total_realized_pnl, symbol, 2)}</span>
          </span>
          <span>
            Unrealized P&amp;L <span className="font-mono text-text font-semibold">{money(tradeStats.total_unrealized_pnl, symbol, 2)}</span>
          </span>
        </div>
      )}
      {open && periods.map((p) => (
        <PeriodBlock key={`${p.entryDate}-${p.exitDate}`} {...p} symbol={symbol} />
      ))}
    </Panel>
  );
}

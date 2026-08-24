"""
Midcap150 Momentum 10 — last 2 years, full trade-by-trade log.

Reuses the EXACT existing reconstruction (backtest10.build_index, top_n=10,
min_eligible=30, June/December rebalance, NIFTY Midcap 150 universe — same
config as report 16/17's "Midcap150 Momentum 10", CAGR 40.6%/-35.1% over its
full 2008-2026 history) but windows it down to the last 2 years and, unlike
every other report in this project, expands EVERY rebalance into an actual
buy/sell trade log instead of just an equity curve.

WHY EVERY REBALANCE IS A FULL BUY/SELL, NOT JUST "NEW ENTRIES"
build_index (backtest10.py) re-splits the ENTIRE portfolio value equally
across whichever 10 tickers are selected at each rebalance date — it does
not let a continuing holding ride its drifted weight forward. So even a
stock that stays in the top 10 for three straight rebalances is, in this
model, fully sold at rebalance N's price and fully re-bought at rebalance
N's price (net effect: zero — it's the same transaction happening on both
sides in the same instant) and then held until rebalance N+1. Economically,
every ticker in every top-10 list is a genuine buy at that rebalance's price
and a genuine sell at the NEXT rebalance's price (or "still open" if it's
the most recent rebalance and no next one has happened yet). That is
exactly what this report reconstructs, one row per stock per holding
period.

BENCHMARK: MID150BEES.NS (Nippon India ETF Nifty Midcap 150), the same real,
tradable midcap ETF used as "midcap" throughout this project — buy-and-hold,
no rebalancing, over the identical 2-year window.
"""
import json

import numpy as np
import pandas as pd

from backtest10 import build_index, cumret_drawdown, series_to_points, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes, metrics

TOP_N = 10
MIN_ELIGIBLE = 30
WINDOW_YEARS = 2


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    midcap_etf = fetch("MID150BEES.NS")

    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]

    index_level, selections = build_index(closes, top_n=TOP_N, min_eligible=MIN_ELIGIBLE)

    # --- window: last WINDOW_YEARS ending at the latest date both the
    # strategy and the benchmark have data for ---
    full_end = min(index_level.index[-1], midcap_etf.index[-1])
    window_start_target = full_end - pd.DateOffset(years=WINDOW_YEARS)
    win_dates = index_level.index[(index_level.index >= window_start_target) & (index_level.index <= full_end)]
    window_start = win_dates[0]

    strategy_win = index_level.loc[win_dates]
    bench_common = midcap_etf.index.intersection(win_dates)
    bench_win = midcap_etf.loc[bench_common, "Close"]

    def norm(s):
        return s / s.iloc[0] * 100.0

    strategy_norm = norm(strategy_win)
    bench_norm = norm(bench_win)

    # --- trade log: every rebalance-to-rebalance holding period touching
    # the window, one row per ticker per period ---
    # include the rebalance immediately before window_start too, since its
    # holding period runs INTO the window (a position "carried in").
    rb_in_or_before = [s for s in selections if s["date"] <= full_end.strftime("%Y-%m-%d")]
    idx_before = None
    for i, s in enumerate(rb_in_or_before):
        if pd.Timestamp(s["date"]) <= window_start:
            idx_before = i
    start_i = idx_before if idx_before is not None else 0
    relevant = rb_in_or_before[start_i:]

    trades = []
    for i, s in enumerate(relevant):
        period_start = pd.Timestamp(s["date"])
        tickers = s["tickers"]
        alloc_each = s["index_value_at_rebalance"] / len(tickers)
        if i + 1 < len(relevant):
            period_end = pd.Timestamp(relevant[i + 1]["date"])
            status = "closed"
        else:
            period_end = full_end
            status = "open"
        for t in tickers:
            entry_price = float(closes.loc[period_start, t]) if t in closes.columns and pd.notna(closes.loc[period_start, t]) else None
            exit_price = float(closes.loc[period_end, t]) if t in closes.columns and pd.notna(closes.loc[period_end, t]) else None
            if entry_price is None or exit_price is None:
                continue
            pct = (exit_price / entry_price - 1.0) * 100.0
            pnl_dollars = alloc_each * pct / 100.0
            trades.append({
                "ticker": t.replace(".NS", ""),
                "entry_date": period_start.strftime("%Y-%m-%d"),
                "exit_date": period_end.strftime("%Y-%m-%d"),
                "entry_price": round(entry_price, 2),
                "exit_price": round(exit_price, 2),
                "pct_return": round(pct, 2),
                "alloc": round(alloc_each, 2),
                "pnl": round(pnl_dollars, 2),
                "status": status,
                "carried_in": period_start < window_start,
            })

    trades.sort(key=lambda r: (r["entry_date"], r["ticker"]))

    closed = [t for t in trades if t["status"] == "closed"]
    open_pos = [t for t in trades if t["status"] == "open"]
    winners = [t for t in closed if t["pct_return"] > 0]
    losers = [t for t in closed if t["pct_return"] <= 0]

    def yrs(s):
        return (s.index[-1] - s.index[0]).days / 365.25

    mdd_s, peak_s, trough_s, uw_s = cumret_drawdown(strategy_win, pd.Series(1.0, index=strategy_win.index))
    mdd_b, peak_b, trough_b, uw_b = cumret_drawdown(bench_win, pd.Series(1.0, index=bench_win.index))

    def cagr_of(s):
        y = yrs(s)
        return float((s.iloc[-1] / s.iloc[0]) ** (1 / y) * 100 - 100) if y > 0 else None

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "window_years": WINDOW_YEARS,
        "start_date": window_start.strftime("%Y-%m-%d"), "end_date": full_end.strftime("%Y-%m-%d"),
        "num_rebalances_in_window": len([s for s in relevant if pd.Timestamp(s["date"]) >= window_start]),
        "momentum10": {
            "equity_curve": series_to_points(strategy_norm),
            "net_return_pct": float((strategy_win.iloc[-1] / strategy_win.iloc[0] - 1) * 100),
            "cagr_pct": cagr_of(strategy_win),
            "max_drawdown_pct": mdd_s, "max_drawdown_peak_date": peak_s, "max_drawdown_trough_date": trough_s,
            "longest_underwater_days": uw_s,
        },
        "midcap_etf": {
            "equity_curve": series_to_points(bench_norm),
            "net_return_pct": float((bench_win.iloc[-1] / bench_win.iloc[0] - 1) * 100),
            "cagr_pct": cagr_of(bench_win),
            "max_drawdown_pct": mdd_b, "max_drawdown_peak_date": peak_b, "max_drawdown_trough_date": trough_b,
            "longest_underwater_days": uw_b,
        },
        "trades": trades,
        "trade_stats": {
            "total_trades": len(trades),
            "closed_trades": len(closed),
            "open_positions": len(open_pos),
            "win_rate_pct": round(len(winners) / len(closed) * 100, 1) if closed else None,
            "avg_win_pct": round(float(np.mean([t["pct_return"] for t in winners])), 2) if winners else None,
            "avg_loss_pct": round(float(np.mean([t["pct_return"] for t in losers])), 2) if losers else None,
            "best_trade": max(closed, key=lambda t: t["pct_return"]) if closed else None,
            "worst_trade": min(closed, key=lambda t: t["pct_return"]) if closed else None,
            "total_realized_pnl": round(sum(t["pnl"] for t in closed), 2),
            "total_unrealized_pnl": round(sum(t["pnl"] for t in open_pos), 2),
        },
    }

    with open("results23.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}")
    print(f"momentum10 CAGR {results['momentum10']['cagr_pct']:.1f}% / DD {results['momentum10']['max_drawdown_pct']:.1f}%")
    print(f"midcap etf CAGR {results['midcap_etf']['cagr_pct']:.1f}% / DD {results['midcap_etf']['max_drawdown_pct']:.1f}%")
    ts = results["trade_stats"]
    print(f"trades: {ts['total_trades']} total, {ts['closed_trades']} closed, {ts['open_positions']} open, win rate {ts['win_rate_pct']}%")
    print(f"realized pnl {ts['total_realized_pnl']:.2f}  unrealized pnl {ts['total_unrealized_pnl']:.2f}")


if __name__ == "__main__":
    main()

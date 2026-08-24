"""
Midcap150 Momentum 10 — trade log with CARRIED positions merged, 2015 to
date.

Reports 24 and 26 showed a trade log where every rebalance-to-rebalance
leg is its own row, even for a stock that stayed in the top 10 across
several consecutive rebalances — which is literally accurate to how
build_index computes the equity curve (it re-splits the whole portfolio
value equally across the current top 10 at every rebalance, so even a
continuing stock is technically re-bought at that rebalance's price), but
makes the trade log noisy: the same stock can show up as five separate
"trades" that are really one long, uninterrupted holding.

THIS report instead tracks each stock's REAL continuous tenure in the
top 10 as a single row: the position opens the first time the stock is
selected (tag "new"), stays open across every consecutive rebalance where
it's still selected (tag "carried" — no new row, just extends the same
one), and closes the first time it's dropped from the top 10 (tag
"exited"), with ONE entry price (from the day it first entered), ONE exit
price (from the day it finally dropped out, or "still open" if it's still
in the book), and ONE total % return computed straight from those two
prices — exactly "the total gain/loss till date from the day it entered,"
regardless of how many rebalances it survived in between.

ONE DISCLOSED SIMPLIFICATION: the real strategy re-splits the ENTIRE
portfolio equally across the top 10 at every rebalance, meaning a
continuing stock's DOLLAR weight actually gets reset each time (see
reports 24/26). This report's dollar P&L instead assumes the position's
ORIGINAL equal-weight allocation (from the day it first entered) was held
untouched for the whole run, which is what "carrying forward" the same
position literally means — a reasonable, simpler bookkeeping model for
this specific trade log, but not a claim that the real underlying equity
curve (still computed exactly as in every other report) works this way
internally. The price return itself, though, is exact either way — a
stock's total price return from day X to day Y never depends on what the
REST of the portfolio did in between.

Window: 2015-01-01 to the latest available date — positions whose
continuous run started before 2015 but exit (or are still open) on/after
2015-01-01 are included and tagged "carried in", same convention as
reports 24/26.
"""
import json

import numpy as np
import pandas as pd

from backtest10 import build_index, cumret_drawdown, series_to_points, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes, metrics

TOP_N = 10
MIN_ELIGIBLE = 30
WINDOW_START = "2015-01-01"


def build_runs(selections, closes):
    """Merge consecutive rebalance selections into one row per continuous
    holding tenure, per ticker. Returns (completed_runs, still_open_runs)."""
    open_runs = {}  # ticker -> {entry_date, entry_price, alloc, carried_dates}
    completed = []
    prev_set = set()

    for sel in selections:
        d = pd.Timestamp(sel["date"])
        current_set = set(sel["tickers"])
        alloc_each = sel["index_value_at_rebalance"] / len(sel["tickers"])
        price_today = closes.loc[d] if d in closes.index else None

        dropped = prev_set - current_set
        for tk in dropped:
            run = open_runs.pop(tk)
            exit_price = float(price_today[tk]) if price_today is not None and pd.notna(price_today.get(tk)) else None
            if exit_price is None:
                continue
            pct = (exit_price / run["entry_price"] - 1.0) * 100.0
            completed.append({
                "ticker": tk.replace(".NS", ""), "entry_date": run["entry_date"].strftime("%Y-%m-%d"),
                "entry_price": round(run["entry_price"], 2), "exit_date": d.strftime("%Y-%m-%d"),
                "exit_price": round(exit_price, 2), "pct_return": round(pct, 2),
                "alloc": round(run["alloc"], 2), "pnl": round(run["alloc"] * pct / 100.0, 2),
                "num_rebalances_held": len(run["carried_dates"]) + 1,
                "carried_dates": run["carried_dates"], "status": "closed",
            })

        for tk in current_set:
            if tk in open_runs:
                open_runs[tk]["carried_dates"].append(d.strftime("%Y-%m-%d"))
            else:
                entry_price = float(price_today[tk]) if price_today is not None and pd.notna(price_today.get(tk)) else None
                if entry_price is None:
                    continue
                open_runs[tk] = {"entry_date": d, "entry_price": entry_price, "alloc": alloc_each, "carried_dates": []}

        prev_set = current_set

    return completed, open_runs


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    midcap_etf = fetch("MID150BEES.NS")
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]

    index_level, selections = build_index(closes, top_n=TOP_N, min_eligible=MIN_ELIGIBLE)

    completed, still_open_runs = build_runs(selections, closes)

    last_date = closes.index[-1]
    last_price = closes.loc[last_date]
    open_trades = []
    for tk, run in still_open_runs.items():
        exit_price = float(last_price[tk]) if pd.notna(last_price.get(tk)) else None
        if exit_price is None:
            continue
        pct = (exit_price / run["entry_price"] - 1.0) * 100.0
        open_trades.append({
            "ticker": tk.replace(".NS", ""), "entry_date": run["entry_date"].strftime("%Y-%m-%d"),
            "entry_price": round(run["entry_price"], 2), "exit_date": last_date.strftime("%Y-%m-%d"),
            "exit_price": round(exit_price, 2), "pct_return": round(pct, 2),
            "alloc": round(run["alloc"], 2), "pnl": round(run["alloc"] * pct / 100.0, 2),
            "num_rebalances_held": len(run["carried_dates"]) + 1,
            "carried_dates": run["carried_dates"], "status": "open",
        })

    all_trades = completed + open_trades
    window_start = pd.Timestamp(WINDOW_START)

    def relevant(t):
        ref_date = pd.Timestamp(t["exit_date"])
        return ref_date >= window_start

    trades = [t for t in all_trades if relevant(t)]
    for t in trades:
        t["carried_in"] = pd.Timestamp(t["entry_date"]) < window_start
    trades.sort(key=lambda r: (r["entry_date"], r["ticker"]))

    # --- strategy vs benchmark over the same window, for KPI context ---
    win_dates = index_level.index[(index_level.index >= window_start) & (index_level.index <= last_date)]
    strategy_win = index_level.loc[win_dates]
    bench_common = midcap_etf.index.intersection(win_dates)
    bench_win = midcap_etf.loc[bench_common, "Close"]

    def norm(s):
        return s / s.iloc[0] * 100.0

    mdd_s, peak_s, trough_s, uw_s = cumret_drawdown(strategy_win, pd.Series(1.0, index=strategy_win.index))
    mdd_b, peak_b, trough_b, uw_b = cumret_drawdown(bench_win, pd.Series(1.0, index=bench_win.index))

    def cagr_of(s):
        y = (s.index[-1] - s.index[0]).days / 365.25
        return float((s.iloc[-1] / s.iloc[0]) ** (1 / y) * 100 - 100) if y > 0 else None

    closed = [t for t in trades if t["status"] == "closed"]
    still_open_shown = [t for t in trades if t["status"] == "open"]
    winners = [t for t in closed if t["pct_return"] > 0]
    losers = [t for t in closed if t["pct_return"] <= 0]

    def avg(lst):
        return round(float(np.mean([t["pct_return"] for t in lst])), 2) if lst else None

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": win_dates[0].strftime("%Y-%m-%d"), "end_date": win_dates[-1].strftime("%Y-%m-%d"),
        "momentum10": {
            "equity_curve": series_to_points(norm(strategy_win)),
            "net_return_pct": float((strategy_win.iloc[-1] / strategy_win.iloc[0] - 1) * 100),
            "cagr_pct": cagr_of(strategy_win),
            "max_drawdown_pct": mdd_s, "max_drawdown_peak_date": peak_s, "max_drawdown_trough_date": trough_s,
            "longest_underwater_days": uw_s,
        },
        "midcap_etf": {
            "equity_curve": series_to_points(norm(bench_win)),
            "net_return_pct": float((bench_win.iloc[-1] / bench_win.iloc[0] - 1) * 100),
            "cagr_pct": cagr_of(bench_win),
            "max_drawdown_pct": mdd_b, "max_drawdown_peak_date": peak_b, "max_drawdown_trough_date": trough_b,
            "longest_underwater_days": uw_b,
        },
        "trades": trades,
        "trade_stats": {
            "total_positions": len(trades),
            "closed_positions": len(closed),
            "still_open": len(still_open_shown),
            "win_rate_pct": round(len(winners) / len(closed) * 100, 1) if closed else None,
            "avg_win_pct": avg(winners),
            "avg_loss_pct": avg(losers),
            "avg_rebalances_held": round(float(np.mean([t["num_rebalances_held"] for t in trades])), 2) if trades else None,
            "longest_held_rebalances": max((t["num_rebalances_held"] for t in trades), default=0),
            "total_realized_pnl": round(sum(t["pnl"] for t in closed), 2),
            "total_unrealized_pnl": round(sum(t["pnl"] for t in still_open_shown), 2),
        },
    }

    with open("results30.json", "w") as f:
        json.dump(results, f, indent=2)

    ts = results["trade_stats"]
    print(f"window {results['start_date']} -> {results['end_date']}")
    print(f"momentum10 CAGR {results['momentum10']['cagr_pct']:.1f}% / DD {results['momentum10']['max_drawdown_pct']:.1f}%")
    print(f"midcap etf CAGR {results['midcap_etf']['cagr_pct']:.1f}% / DD {results['midcap_etf']['max_drawdown_pct']:.1f}%")
    print(f"positions: {ts['total_positions']} total, {ts['closed_positions']} closed, {ts['still_open']} open, "
          f"win rate {ts['win_rate_pct']}%, avg rebalances held {ts['avg_rebalances_held']}, "
          f"longest held {ts['longest_held_rebalances']} rebalances")
    print(f"realized pnl {ts['total_realized_pnl']:.2f}  unrealized pnl {ts['total_unrealized_pnl']:.2f}")


if __name__ == "__main__":
    main()

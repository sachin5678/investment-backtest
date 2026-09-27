"""
Midcap150 Momentum 10 — per-stock TRAILING stop-loss, vs. report 27's
FIXED stop-loss and the original (no stop) strategy, full 2008-2026
history.

Report 27 tested a FIXED stop: if a position falls 15% (or 30%) below
its OWN ENTRY PRICE at any point before its next scheduled rebalance,
exit immediately. That stop level never moves — it stays anchored to the
entry price for the whole holding period, so a stock that rallies 50%
then gives back 20% never gets stopped out, since 20% off the PEAK is
still well above 15% off the ORIGINAL entry price.

This report tests the more "surgical" version the user asked for: the
SAME 15%/30% thresholds, but measured off each position's OWN PEAK PRICE
SINCE ENTRY instead of its entry price — the stop level RISES as a
winning position's peak rises, locking in gains on individual winners
without needing a portfolio-wide regime switch (reports 42-57) at all.

Same realistic fill methodology as report 27: checked via the day's
intraday LOW against YESTERDAY's peak-derived stop level (today's peak
is only folded in AFTER today's check, so there's no same-day
look-ahead), filled at min(Open, stop price). Money freed by a stop-loss
exit sits in cash (uninvested, 0% return) until the next regular
rebalance, same as report 27.
"""
import json

import numpy as np
import pandas as pd

from backtest10 import select_top30, rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes
from backtest27 import load_midcap150_field, build_original, build_with_stop
from backtest32 import metrics_only

TOP_N = 10
MIN_ELIGIBLE = 30
STOP_LOSS_LEVELS = [0.15, 0.30]


def build_with_trailing_stop(closes, lows, highs, opens, rbdates, stop_loss_pct):
    """Same selection/weighting at every rebalance as build_with_stop, but
    each position's stop level trails its OWN peak price since entry
    (updated daily via the day's High), instead of staying fixed at the
    entry price."""
    dates = closes.index
    rb_set = set(rbdates)
    date_pos = {d: i for i, d in enumerate(dates)}
    index_level = pd.Series(np.nan, index=dates)
    positions = {}  # ticker -> {shares, entry_price, peak_price, stop_price, entry_date}
    cash = 0.0
    started = False
    trades = []

    def portfolio_value(price_today):
        return cash + sum(p["shares"] * price_today.get(tk, 0.0) for tk, p in positions.items() if pd.notna(price_today.get(tk)))

    for i, d in enumerate(dates):
        price_today = closes.iloc[i]
        low_today = lows.iloc[i]
        open_today = opens.iloc[i]
        high_today = highs.iloc[i]

        if not started and d in rb_set:
            t_idx = date_pos[d]
            selected = select_top30(closes, t_idx, top_n=TOP_N, min_eligible=MIN_ELIGIBLE)
            if selected is not None:
                started = True
                dollar_each = 100.0 / len(selected)
                positions = {}
                for tk in selected:
                    entry_price = float(price_today[tk])
                    positions[tk] = {"shares": dollar_each / entry_price, "entry_price": entry_price,
                                       "peak_price": entry_price, "stop_price": entry_price * (1 - stop_loss_pct),
                                       "entry_date": d}
                cash = 0.0
            index_level.iloc[i] = portfolio_value(price_today) if started else np.nan
            continue

        if not started:
            continue

        # 1) check every open position's TRAILING stop first, using
        #    TODAY's low against the stop level derived from YESTERDAY's
        #    peak (skip the entry day itself, same as report 27)
        stopped = []
        for tk, p in positions.items():
            if d == p["entry_date"]:
                continue
            lo = low_today.get(tk)
            if pd.notna(lo) and lo <= p["stop_price"]:
                op = open_today.get(tk)
                fill_price = min(op, p["stop_price"]) if pd.notna(op) else p["stop_price"]
                pct = (fill_price / p["entry_price"] - 1.0) * 100.0
                cash += p["shares"] * fill_price
                trades.append({
                    "ticker": tk.replace(".NS", ""), "entry_date": p["entry_date"].strftime("%Y-%m-%d"),
                    "exit_date": d.strftime("%Y-%m-%d"), "entry_price": round(p["entry_price"], 2),
                    "exit_price": round(fill_price, 2), "peak_price": round(p["peak_price"], 2),
                    "pct_return": round(pct, 2), "reason": "trailing_stop",
                })
                stopped.append(tk)
        for tk in stopped:
            del positions[tk]

        # 2) for surviving positions, fold in TODAY's high to update the
        #    peak (and therefore tomorrow's stop level)
        for tk, p in positions.items():
            hi = high_today.get(tk)
            if pd.notna(hi) and hi > p["peak_price"]:
                p["peak_price"] = float(hi)
                p["stop_price"] = p["peak_price"] * (1 - stop_loss_pct)

        # 3) rebalance day: close out everything still standing, buy the
        #    new top 10, reset each new position's peak to its entry price
        if d in rb_set:
            t_idx = date_pos[d]
            for tk, p in positions.items():
                exit_price = float(price_today[tk])
                pct = (exit_price / p["entry_price"] - 1.0) * 100.0
                cash += p["shares"] * exit_price
                trades.append({
                    "ticker": tk.replace(".NS", ""), "entry_date": p["entry_date"].strftime("%Y-%m-%d"),
                    "exit_date": d.strftime("%Y-%m-%d"), "entry_price": round(p["entry_price"], 2),
                    "exit_price": round(exit_price, 2), "peak_price": round(p["peak_price"], 2),
                    "pct_return": round(pct, 2), "reason": "rebalance",
                })
            positions = {}
            selected = select_top30(closes, t_idx, top_n=TOP_N, min_eligible=MIN_ELIGIBLE)
            if selected is not None:
                port_value = cash
                dollar_each = port_value / len(selected)
                for tk in selected:
                    entry_price = float(price_today[tk])
                    positions[tk] = {"shares": dollar_each / entry_price, "entry_price": entry_price,
                                       "peak_price": entry_price, "stop_price": entry_price * (1 - stop_loss_pct),
                                       "entry_date": d}
                cash = 0.0

        index_level.iloc[i] = portfolio_value(closes.iloc[i])

    if positions:
        last_price = closes.iloc[-1]
        last_date = dates[-1]
        for tk, p in positions.items():
            exit_price = float(last_price[tk])
            pct = (exit_price / p["entry_price"] - 1.0) * 100.0
            trades.append({
                "ticker": tk.replace(".NS", ""), "entry_date": p["entry_date"].strftime("%Y-%m-%d"),
                "exit_date": last_date.strftime("%Y-%m-%d"), "entry_price": round(p["entry_price"], 2),
                "exit_price": round(exit_price, 2), "peak_price": round(p["peak_price"], 2),
                "pct_return": round(pct, 2), "reason": "still_open",
            })

    return index_level.dropna(), trades


def summarize(series, trades, common_idx, stop_key="stop_loss"):
    series = series.loc[series.index.intersection(common_idx)]
    m = metrics_only(series, common_idx)

    stop_trades = [t for t in trades if t["reason"] == stop_key]
    rebalance_trades = [t for t in trades if t["reason"] == "rebalance"]
    still_open = [t for t in trades if t["reason"] == "still_open"]

    def avg(lst):
        return round(float(np.mean([t["pct_return"] for t in lst])), 2) if lst else None

    return {
        "metrics": m,
        "trade_stats": {
            "total_positions": len(trades),
            "stop_loss_exits": len(stop_trades),
            "rebalance_exits": len(rebalance_trades),
            "still_open": len(still_open),
            "stop_loss_pct_of_positions": round(len(stop_trades) / len(trades) * 100, 1) if trades else None,
            "avg_stop_loss_return": avg(stop_trades),
            "avg_rebalance_exit_return": avg(rebalance_trades),
        },
        "stop_loss_trades_sample": (stop_trades[:10] + stop_trades[-10:]) if len(stop_trades) > 20 else stop_trades,
    }


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]

    tickers = list(closes.columns)
    lows = load_midcap150_field("Low", tickers).loc[closes.index, tickers]
    highs = load_midcap150_field("High", tickers).loc[closes.index, tickers]
    opens = load_midcap150_field("Open", tickers).loc[closes.index, tickers]

    rbdates = rebalance_dates(closes.index, months=(6, 12))

    original = build_original(closes, rbdates)

    common_idx = original.index
    fixed_runs, trailing_runs = {}, {}
    for lvl in STOP_LOSS_LEVELS:
        series, trades = build_with_stop(closes, lows, opens, rbdates, lvl)
        fixed_runs[lvl] = (series, trades)
        common_idx = common_idx.intersection(series.index)

        t_series, t_trades = build_with_trailing_stop(closes, lows, highs, opens, rbdates, lvl)
        trailing_runs[lvl] = (t_series, t_trades)
        common_idx = common_idx.intersection(t_series.index)

    original_summary = summarize(original, [], common_idx)

    variants = {}
    for lvl in STOP_LOSS_LEVELS:
        series, trades = fixed_runs[lvl]
        variants[f"fixed_{int(lvl*100)}"] = {"stop_loss_pct": lvl * 100, "kind": "fixed", **summarize(series, trades, common_idx, "stop_loss")}
        t_series, t_trades = trailing_runs[lvl]
        variants[f"trailing_{int(lvl*100)}"] = {"stop_loss_pct": lvl * 100, "kind": "trailing", **summarize(t_series, t_trades, common_idx, "trailing_stop")}

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "original": original_summary["metrics"],
        "variants": variants,
    }

    with open("results57.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}")
    print(f"original          CAGR {results['original']['cagr_pct']:.2f}% / DD {results['original']['max_drawdown_pct']:.1f}%")
    for key, v in variants.items():
        m, ts = v["metrics"], v["trade_stats"]
        print(f"{key:14s} ({v['stop_loss_pct']:.0f}%)  CAGR {m['cagr_pct']:.2f}% / DD {m['max_drawdown_pct']:.1f}%  "
              f"stopped {ts['stop_loss_exits']}/{ts['total_positions']} ({ts['stop_loss_pct_of_positions']}%)  "
              f"avg stop {ts['avg_stop_loss_return']}%  avg rebalance {ts['avg_rebalance_exit_return']}%")


if __name__ == "__main__":
    main()

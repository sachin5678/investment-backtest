"""
Midcap150 Momentum 10 — NO stop-loss at all, but a "breakeven profit-lock"
rule instead: once a position has run up 30% above its entry price at any
point, arm a protective exit at cost — if it later falls all the way back
down to its own entry price before the next rebalance, exit immediately at
breakeven (0% on that trade) rather than riding it down further or waiting
for the scheduled rebalance. A position that never reaches +30% is held to
its scheduled rebalance exactly like the original strategy, with no exit
rule of any kind — there is no downside stop here, only this one upside-
triggered protection.

Mechanically: for each position, track the running high since entry (using
daily HIGH, not just close, so an intraday spike above +30% counts even if
the close that day was lower). The day AFTER the running high first crosses
entry_price * 1.30, the position is "armed." Once armed, the position is
watched daily via the LOW: the moment the low touches back down to the
entry price, it's exited that day, filled at min(Open, entry_price) — same
realistic-fill logic as every stop-loss report in this project, so an
overnight gap straight through breakeven isn't fabricated into a worse (or
better) fill than was actually achievable.

Arming and the breakeven exit are never checked on the same day a position
was newly entered (nothing to react to on day 0), and a position cannot
arm and trigger on the very same day either — arming from today's high only
takes effect starting the NEXT day's low check, a conservative choice that
avoids assuming a same-day high-then-low sequence that the data can't
actually distinguish.

Compared directly against the original (no exit rule of any kind — reports
11-19, 24, 25) and against report 27's 15%/30% stop-loss variants, all over
the identical full 2008-2026 history.
"""
import json

import numpy as np
import pandas as pd

from backtest10 import select_top30, rebalance_dates, cumret_drawdown, series_to_points, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes
from backtest27 import load_midcap150_field, build_original, summarize

TOP_N = 10
MIN_ELIGIBLE = 30
PROFIT_ARM_PCT = 0.30


def build_with_breakeven_lock(closes, highs, lows, opens, rbdates):
    dates = closes.index
    rb_set = set(rbdates)
    date_pos = {d: i for i, d in enumerate(dates)}
    index_level = pd.Series(np.nan, index=dates)
    positions = {}  # ticker -> {shares, entry_price, entry_date, armed}
    cash = 0.0
    started = False
    trades = []

    def portfolio_value(price_today):
        return cash + sum(p["shares"] * price_today.get(tk, 0.0) for tk, p in positions.items() if pd.notna(price_today.get(tk)))

    for i, d in enumerate(dates):
        price_today = closes.iloc[i]
        high_today = highs.iloc[i]
        low_today = lows.iloc[i]
        open_today = opens.iloc[i]

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
                                       "entry_date": d, "armed": False}
                cash = 0.0
            index_level.iloc[i] = portfolio_value(price_today) if started else np.nan
            continue

        if not started:
            continue

        # 1) breakeven-lock exit FIRST (only for positions armed on a PRIOR
        #    day), using today's low
        stopped = []
        for tk, p in positions.items():
            if d == p["entry_date"]:
                continue
            if p["armed"]:
                lo = low_today.get(tk)
                if pd.notna(lo) and lo <= p["entry_price"]:
                    op = open_today.get(tk)
                    fill_price = min(op, p["entry_price"]) if pd.notna(op) else p["entry_price"]
                    pct = (fill_price / p["entry_price"] - 1.0) * 100.0
                    cash += p["shares"] * fill_price
                    trades.append({
                        "ticker": tk.replace(".NS", ""), "entry_date": p["entry_date"].strftime("%Y-%m-%d"),
                        "exit_date": d.strftime("%Y-%m-%d"), "entry_price": round(p["entry_price"], 2),
                        "exit_price": round(fill_price, 2), "pct_return": round(pct, 2), "reason": "breakeven_lock",
                    })
                    stopped.append(tk)
        for tk in stopped:
            del positions[tk]

        # 2) arm any position whose high TODAY crosses +30% (takes effect
        #    starting tomorrow's low check — see module docstring)
        for tk, p in positions.items():
            if d == p["entry_date"] or p["armed"]:
                continue
            hi = high_today.get(tk)
            if pd.notna(hi) and hi >= p["entry_price"] * (1 + PROFIT_ARM_PCT):
                p["armed"] = True

        # 3) rebalance day: close out everything still standing, buy new top 10
        if d in rb_set:
            t_idx = date_pos[d]
            for tk, p in positions.items():
                exit_price = float(price_today[tk])
                pct = (exit_price / p["entry_price"] - 1.0) * 100.0
                cash += p["shares"] * exit_price
                trades.append({
                    "ticker": tk.replace(".NS", ""), "entry_date": p["entry_date"].strftime("%Y-%m-%d"),
                    "exit_date": d.strftime("%Y-%m-%d"), "entry_price": round(p["entry_price"], 2),
                    "exit_price": round(exit_price, 2), "pct_return": round(pct, 2), "reason": "rebalance",
                })
            positions = {}
            selected = select_top30(closes, t_idx, top_n=TOP_N, min_eligible=MIN_ELIGIBLE)
            if selected is not None:
                port_value = cash
                dollar_each = port_value / len(selected)
                for tk in selected:
                    entry_price = float(price_today[tk])
                    positions[tk] = {"shares": dollar_each / entry_price, "entry_price": entry_price,
                                       "entry_date": d, "armed": False}
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
                "exit_price": round(exit_price, 2), "pct_return": round(pct, 2), "reason": "still_open",
            })

    return index_level.dropna(), trades


def summarize_breakeven(series, trades, common_idx):
    base = summarize(series, trades, common_idx)
    locked = [t for t in trades if t["reason"] == "breakeven_lock"]
    rebalance_trades = [t for t in trades if t["reason"] == "rebalance"]

    def avg(lst):
        return round(float(np.mean([t["pct_return"] for t in lst])), 2) if lst else None

    def avg_of_winners(lst):
        w = [t for t in lst if t["pct_return"] > 0]
        return round(float(np.mean([t["pct_return"] for t in w])), 2) if w else None

    base["trade_stats"]["breakeven_lock_exits"] = len(locked)
    base["trade_stats"]["breakeven_lock_pct_of_positions"] = round(len(locked) / len(trades) * 100, 1) if trades else None
    base["trade_stats"]["avg_breakeven_lock_return"] = avg(locked)
    base["trade_stats"]["avg_rebalance_exit_return_winners_only"] = avg_of_winners(rebalance_trades)
    base["breakeven_lock_trades_sample"] = (locked[:10] + locked[-10:]) if len(locked) > 20 else locked
    return base


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]

    tickers = list(closes.columns)
    highs = load_midcap150_field("High", tickers).loc[closes.index, tickers]
    lows = load_midcap150_field("Low", tickers).loc[closes.index, tickers]
    opens = load_midcap150_field("Open", tickers).loc[closes.index, tickers]

    rbdates = rebalance_dates(closes.index, months=(6, 12))

    original = build_original(closes, rbdates)
    breakeven_series, breakeven_trades = build_with_breakeven_lock(closes, highs, lows, opens, rbdates)

    common_idx = original.index.intersection(breakeven_series.index)
    original_summary = summarize(original, [], common_idx)
    breakeven_summary = summarize_breakeven(breakeven_series, breakeven_trades, common_idx)

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "profit_arm_pct": PROFIT_ARM_PCT * 100,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "original": original_summary["metrics"],
        "breakeven_lock": breakeven_summary["metrics"],
        "trade_stats": breakeven_summary["trade_stats"],
        "breakeven_lock_trades_sample": breakeven_summary["breakeven_lock_trades_sample"],
    }

    with open("results29.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}")
    print(f"original        CAGR {results['original']['cagr_pct']:.2f}% / DD {results['original']['max_drawdown_pct']:.1f}%")
    print(f"breakeven-lock   CAGR {results['breakeven_lock']['cagr_pct']:.2f}% / DD {results['breakeven_lock']['max_drawdown_pct']:.1f}%")
    ts = results["trade_stats"]
    print(f"positions: {ts['total_positions']} total, {ts['breakeven_lock_exits']} breakeven-locked "
          f"({ts['breakeven_lock_pct_of_positions']}%), {ts['rebalance_exits']} rode to rebalance, {ts['still_open']} still open")
    print(f"avg breakeven-lock exit {ts['avg_breakeven_lock_return']}%  avg rebalance exit {ts['avg_rebalance_exit_return']}%")


if __name__ == "__main__":
    main()

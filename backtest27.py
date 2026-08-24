"""
Midcap150 Momentum 10 — WITH an intra-period stop-loss overlay (both 15%
and 30% thresholds tested), vs. the original (no stop-loss) strategy, full
2008-2026 history.

The original strategy (reports 11-19, 24, 25): equal-weight top 10 by 6m/12m
risk-adjusted momentum, rebalanced June/December, holding every position
until the NEXT scheduled rebalance no matter what happens to it in between.

This report adds exactly ONE new rule on top of the identical
selection/weighting logic, tested at TWO thresholds: if a position falls
15% (or 30%) below its OWN entry price (the price at the rebalance when it
was bought) at ANY point before its next scheduled rebalance, exit it
immediately — do not wait for the rebalance. Uses the same realistic
stop-loss fill methodology as report 22: checked via the day's intraday LOW
(not just the close, which would miss an intraday breach that recovered by
end of day), filled at min(Open, stop price) so an overnight gap-through
isn't fabricated into a worse loss than the position could actually have
been sold at.

Money freed by a stop-loss exit sits in cash (uninvested, 0% return) until
the next regular rebalance — there is no rule here for reinvesting it into
a new stock mid-period, since none was specified.
"""
import json

import numpy as np
import pandas as pd

from backtest10 import select_top30, rebalance_dates, cumret_drawdown, series_to_points, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes, metrics

TOP_N = 10
MIN_ELIGIBLE = 30
STOP_LOSS_LEVELS = [0.15, 0.30]
LOOKBACK_12M = 252


def load_midcap150_field(field, tickers):
    raw200 = pd.read_pickle("universe_raw.pkl")
    extra_q = pd.read_pickle("quality50_extra_raw.pkl")
    extra_m = pd.read_pickle("midcap150_extra_raw.pkl")

    def get(t):
        for src in (raw200, extra_q, extra_m):
            if t in set(c[0] for c in src.columns):
                return src[(t, field)]
        raise KeyError(t)

    return pd.DataFrame({t: get(t) for t in tickers}).sort_index().ffill()


def build_original(closes, rbdates):
    """Exact same mechanics as backtest10.build_index — full re-split of
    the whole portfolio into the new top-10 at every rebalance, held
    unconditionally until the next one."""
    dates = closes.index
    rb_set = set(rbdates)
    date_pos = {d: i for i, d in enumerate(dates)}
    index_level = pd.Series(np.nan, index=dates)
    shares = {}
    started = False

    for i, d in enumerate(dates):
        if d in rb_set:
            t_idx = date_pos[d]
            selected = select_top30(closes, t_idx, top_n=TOP_N, min_eligible=MIN_ELIGIBLE)
            if selected is not None:
                price_today = closes.iloc[t_idx]
                if not started:
                    value_before = 100.0
                    started = True
                else:
                    value_before = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares)
                dollar_each = value_before / len(selected)
                shares = {tk: dollar_each / price_today[tk] for tk in selected}
        if started:
            price_today = closes.iloc[i]
            val = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares if pd.notna(price_today.get(tk)))
            index_level.iloc[i] = val
    return index_level.dropna()


def build_with_stop(closes, lows, opens, rbdates, stop_loss_pct):
    """Same selection/weighting at every rebalance, but each individual
    position is monitored daily and exited immediately (not at the next
    rebalance) the moment its own -stop_loss_pct stop is breached
    intraday."""
    dates = closes.index
    rb_set = set(rbdates)
    date_pos = {d: i for i, d in enumerate(dates)}
    index_level = pd.Series(np.nan, index=dates)
    positions = {}  # ticker -> {shares, entry_price, stop_price, entry_date}
    cash = 0.0
    started = False
    trades = []  # closed trades: entry/exit date/price, pct, reason

    def portfolio_value(price_today):
        return cash + sum(p["shares"] * price_today.get(tk, 0.0) for tk, p in positions.items() if pd.notna(price_today.get(tk)))

    for i, d in enumerate(dates):
        price_today = closes.iloc[i]
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
                                       "stop_price": entry_price * (1 - stop_loss_pct), "entry_date": d}
                cash = 0.0
            index_level.iloc[i] = portfolio_value(price_today) if started else np.nan
            continue

        if not started:
            continue

        # 1) check every open position's stop-loss FIRST, using today's low
        #    (skip the entry day itself: the position is bought AT today's
        #    close, so there is nothing to stop out of intraday on day 0)
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
                    "exit_price": round(fill_price, 2), "pct_return": round(pct, 2), "reason": "stop_loss",
                })
                stopped.append(tk)
        for tk in stopped:
            del positions[tk]

        # 2) rebalance day: close out everything still standing (real
        #    month-end exits) and buy the new top 10
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
                                       "stop_price": entry_price * (1 - stop_loss_pct), "entry_date": d}
                cash = 0.0

        index_level.iloc[i] = portfolio_value(closes.iloc[i])

    # mark remaining open positions to the last available price
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


def summarize(series, trades, common_idx):
    series = series.loc[series.index.intersection(common_idx)]

    def norm(s):
        return s / s.iloc[0] * 100.0

    mdd, peak, trough, uw = cumret_drawdown(series, pd.Series(1.0, index=series.index))

    def cagr_of(s):
        y = (s.index[-1] - s.index[0]).days / 365.25
        return float((s.iloc[-1] / s.iloc[0]) ** (1 / y) * 100 - 100) if y > 0 else None

    stop_trades = [t for t in trades if t["reason"] == "stop_loss"]
    rebalance_trades = [t for t in trades if t["reason"] == "rebalance"]
    still_open = [t for t in trades if t["reason"] == "still_open"]

    def avg(lst):
        return round(float(np.mean([t["pct_return"] for t in lst])), 2) if lst else None

    return {
        "metrics": {
            "equity_curve": series_to_points(norm(series)),
            "net_return_pct": float((series.iloc[-1] / series.iloc[0] - 1) * 100),
            "cagr_pct": cagr_of(series),
            "max_drawdown_pct": mdd, "max_drawdown_peak_date": peak, "max_drawdown_trough_date": trough,
            "longest_underwater_days": uw,
        },
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
    opens = load_midcap150_field("Open", tickers).loc[closes.index, tickers]

    rbdates = rebalance_dates(closes.index, months=(6, 12))

    original = build_original(closes, rbdates)

    variants = {}
    common_idx = original.index
    per_level = {}
    for lvl in STOP_LOSS_LEVELS:
        series, trades = build_with_stop(closes, lows, opens, rbdates, lvl)
        per_level[lvl] = (series, trades)
        common_idx = common_idx.intersection(series.index)

    original_summary = summarize(original, [], common_idx)
    for lvl in STOP_LOSS_LEVELS:
        series, trades = per_level[lvl]
        variants[f"stop_{int(lvl*100)}"] = {"stop_loss_pct": lvl * 100, **summarize(series, trades, common_idx)}

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "original": original_summary["metrics"],
        "variants": variants,
    }

    with open("results26.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}")
    print(f"original    CAGR {results['original']['cagr_pct']:.2f}% / DD {results['original']['max_drawdown_pct']:.1f}%")
    for key, v in variants.items():
        m, ts = v["metrics"], v["trade_stats"]
        print(f"{key} ({v['stop_loss_pct']:.0f}%)  CAGR {m['cagr_pct']:.2f}% / DD {m['max_drawdown_pct']:.1f}%  "
              f"stopped {ts['stop_loss_exits']}/{ts['total_positions']} ({ts['stop_loss_pct_of_positions']}%)  "
              f"avg stop {ts['avg_stop_loss_return']}%  avg rebalance {ts['avg_rebalance_exit_return']}%")


if __name__ == "__main__":
    main()

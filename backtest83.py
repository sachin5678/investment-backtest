"""
Midcap150 Momentum 10 — pyramiding UP instead of averaging DOWN. Same
mechanics as reports 81/82 (one continuous compounding portfolio, no new
external capital, top-up funded by trimming the OTHER 9 holdings
proportionally), but the trigger is reversed: the first time a stock
closes 20% ABOVE its own buy price, top up with an amount equal to the
original per-stock allocation; the first time it closes 40% above buy
price, a second equal top-up follows.

Unlike reports 81/82's "peak-since-entry" reference (which keeps
updating as a stock makes new highs, so a pullback from ANY high
triggers averaging), this uses the FIXED entry price as the only
reference point throughout the holding period — simpler, and matches
the request exactly ("20% up than buy price", not "20% down from
whatever high it's since made").

This is the classic trend-following idea in reverse of reports 81/82:
instead of buying more of a loser hoping it recovers, buy more of a
winner while it's still winning. Compared against the same no-averaging
baseline and against reports 81/82's down-side triggers, all sharing
the identical picks/prices/window.
"""
import json
import sys

import numpy as np
import pandas as pd

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes
from backtest32 import metrics_only
from backtest33 import select_top_original, build_index_generic

UP_1 = 0.20
UP_2 = 0.40


def simulate_compounding_with_pyramiding(closes, rbdates, select_fn, up1=UP_1, up2=UP_2):
    """Same funding mechanism as backtest81.simulate_compounding_with_averaging
    (top-up funded by trimming the other currently-held positions, one
    continuous compounding portfolio) but triggered by a RISE above the
    fixed entry price instead of a fall from a trailing peak."""
    dates = closes.index
    index_level = pd.Series(np.nan, index=dates)
    shares = {}
    started = False
    selections = []
    total_positions, trigger_once, trigger_twice = 0, 0, 0

    for i, rb in enumerate(rbdates):
        t_idx = dates.get_loc(rb)
        price_at_rb = closes.loc[rb]
        selected = select_fn(closes, t_idx)
        if selected is not None:
            if not started:
                value_before = 100.0
                started = True
            else:
                value_before = sum(shares.get(tk, 0.0) * price_at_rb.get(tk, 0.0) for tk in shares)
                if value_before <= 0:
                    value_before = index_level.iloc[dates.get_loc(rb) - 1]
            dollar_each = value_before / len(selected)
            shares = {tk: dollar_each / price_at_rb[tk] for tk in selected}
            original_alloc = {tk: dollar_each for tk in selected}
            buy_price = {tk: price_at_rb[tk] for tk in selected}
            pyramided1 = {tk: False for tk in selected}
            pyramided2 = {tk: False for tk in selected}
            total_positions += len(selected)
            selections.append({"date": rb.strftime("%Y-%m-%d"), "tickers": [t.replace(".NS", "") for t in selected]})

        if not started:
            continue

        index_level.loc[rb] = sum(shares.get(tk, 0.0) * price_at_rb.get(tk, 0.0) for tk in shares)

        next_rb = rbdates[i + 1] if i + 1 < len(rbdates) else None
        day_range = dates[(dates > rb) & (dates < next_rb)] if next_rb is not None else dates[dates > rb]

        for d in day_range:
            price_today = closes.loc[d]
            for tk in list(shares.keys()):
                price = price_today.get(tk)
                if pd.isna(price):
                    continue
                trigger = None
                if not pyramided1[tk] and price >= buy_price[tk] * (1 + up1):
                    trigger = "pyramided1"
                elif pyramided1[tk] and not pyramided2[tk] and price >= buy_price[tk] * (1 + up2):
                    trigger = "pyramided2"
                if trigger:
                    need_cash = original_alloc[tk]
                    others = [t for t in shares if t != tk]
                    other_value = sum(shares[t] * price_today.get(t, 0.0) for t in others
                                       if pd.notna(price_today.get(t)))
                    if other_value > 0:
                        actual_cash = min(need_cash, other_value)
                        for t in others:
                            p_t = price_today.get(t)
                            if pd.isna(p_t) or p_t <= 0:
                                continue
                            t_value = shares[t] * p_t
                            reduction_value = t_value * (actual_cash / other_value)
                            shares[t] -= reduction_value / p_t
                        shares[tk] += actual_cash / price
                    if trigger == "pyramided1":
                        pyramided1[tk] = True
                        trigger_once += 1
                    else:
                        pyramided2[tk] = True
                        trigger_twice += 1
            index_level.loc[d] = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares
                                      if pd.notna(price_today.get(tk)))

    trigger_counts = {"total_positions": total_positions, "trigger_once": trigger_once, "trigger_twice": trigger_twice}
    return index_level.dropna(), selections, trigger_counts


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]

    rbdates = rebalance_dates(closes.index, months=(6, 12))
    rbdates = [d for d in rbdates if closes.index.get_loc(d) >= 252]

    plain_series, _ = build_index_generic(closes, rbdates, select_top_original)
    pyramid_series, pyramid_sel, counts = simulate_compounding_with_pyramiding(closes, rbdates, select_top_original)

    common_idx = closes.index[closes.index >= rbdates[0]]
    common_idx = common_idx.intersection(plain_series.index).intersection(pyramid_series.index)

    plain_metrics = metrics_only(plain_series, common_idx)
    pyramid_metrics = metrics_only(pyramid_series, common_idx)
    pyramid_metrics.update(counts)
    pyramid_metrics["selections_sample"] = pyramid_sel[:3] + pyramid_sel[-3:] if len(pyramid_sel) > 6 else pyramid_sel
    nifty_metrics = metrics_only(nifty_close.loc[common_idx.intersection(nifty_close.index)], common_idx)

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "up_1_pct": UP_1 * 100, "up_2_pct": UP_2 * 100,
        "num_rebalances": len(rbdates),
        "plain": plain_metrics,
        "pyramiding": pyramid_metrics,
        "nifty": nifty_metrics,
    }

    with open("results82.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}, {len(rbdates)} rebalances")
    print(f"no pyramiding          CAGR {plain_metrics['cagr_pct']:.2f}% / DD {plain_metrics['max_drawdown_pct']:.1f}%")
    print(f"pyramiding +{UP_1*100:.0f}%/+{UP_2*100:.0f}%  CAGR {pyramid_metrics['cagr_pct']:.2f}% / DD {pyramid_metrics['max_drawdown_pct']:.1f}% | "
          f"trigger1 {counts['trigger_once']}/{counts['total_positions']} ({counts['trigger_once']/counts['total_positions']*100:.1f}%), "
          f"trigger2 {counts['trigger_twice']} ({counts['trigger_twice']/counts['total_positions']*100:.1f}%)")
    print(f"nifty 50               CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")


if __name__ == "__main__":
    main()

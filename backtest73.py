"""
Midcap150 Momentum 50 — the exact same "original" momentum formula this
whole project's flagship strategy uses (6-month and 12-month price return,
each divided by trailing-1-year daily-return volatility, cross-sectionally
Z-scored, combined 0.5/0.5, asymmetrically normalized, June/December
rebalance, equal-weight) — but picking the TOP 50 stocks out of Midcap150
instead of the top 10.

This isolates a single question: what does holding a much broader,
one-third-of-the-universe basket do to CAGR and drawdown, relative to the
concentrated top-10 version every other report in this project uses?
A wider basket is intuitively expected to be more diversified (smaller,
shallower idiosyncratic-stock blowups) but less differentiated from the
broad Midcap150 index itself — at the extreme (top 150 = the whole
universe), the momentum ranking would stop mattering at all.

Same select_top_original() formula (backtest33.py), same
load_midcap150_closes() price history (backtest13.py), same
build_index_generic() rebalance engine — only top_n changes, from 10 to
50. min_eligible is raised from 30 to 50 (you need at least as many
eligible, scored names as you intend to pick); the eligible count is
comfortably above 50 on every date checked across the full window (79 to
146 stocks), so this floor is never actually binding.
"""
import json

import pandas as pd

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes
from backtest32 import metrics_only
from backtest33 import select_top_original, build_index_generic

TOP_N_WIDE = 50
TOP_N_BASE = 10
MIN_ELIGIBLE_WIDE = 50


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]

    rbdates = rebalance_dates(closes.index, months=(6, 12))

    top10_series, top10_sel = build_index_generic(closes, rbdates, select_top_original)
    top50_series, top50_sel = build_index_generic(
        closes, rbdates,
        lambda c, t_idx: select_top_original(c, t_idx, top_n=TOP_N_WIDE, min_eligible=MIN_ELIGIBLE_WIDE))

    common_idx = top10_series.index.intersection(top50_series.index)
    top10_metrics = metrics_only(top10_series, common_idx)
    top50_metrics = metrics_only(top50_series, common_idx)
    nifty_metrics = metrics_only(nifty_close.loc[common_idx], common_idx)

    basket_sizes = [len(s["tickers"]) for s in top50_sel]
    overlaps = []
    for a, b in zip(top10_sel, top50_sel):
        if a["date"] != b["date"]:
            continue
        set10, set50 = set(a["tickers"]), set(b["tickers"])
        overlaps.append(len(set10 & set50) / len(set10) * 100.0)

    def sample(sel):
        return sel[:2] + sel[-2:] if len(sel) > 4 else sel

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "top_n_base": TOP_N_BASE, "top_n_wide": TOP_N_WIDE,
        "num_rebalances": len(top50_sel),
        "min_basket_size": min(basket_sizes), "max_basket_size": max(basket_sizes),
        "avg_top10_overlap_pct": round(sum(overlaps) / len(overlaps), 1) if overlaps else None,
        "top10": {**top10_metrics, "selections_sample": sample(top10_sel)},
        "top50": {**top50_metrics, "selections_sample": sample(top50_sel)},
        "nifty": nifty_metrics,
    }

    with open("results72.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}, {results['num_rebalances']} rebalances")
    print(f"top-10   CAGR {top10_metrics['cagr_pct']:.2f}% / DD {top10_metrics['max_drawdown_pct']:.1f}%")
    print(f"top-50   CAGR {top50_metrics['cagr_pct']:.2f}% / DD {top50_metrics['max_drawdown_pct']:.1f}%")
    print(f"nifty 50 CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")
    print(f"basket size range: {results['min_basket_size']}-{results['max_basket_size']} (target 50)")
    print(f"avg overlap of top-10 picks inside the top-50 basket: {results['avg_top10_overlap_pct']}%")


if __name__ == "__main__":
    main()

"""
Midcap150 Momentum 10 — 52-week-high proximity vs. the original formula.

A genuinely different momentum proxy, not a tweak of the existing one:
rank stocks by how close today's price is to its own trailing 52-week
high (`price_today / rolling_max(price, 252 trading days)`), a
well-documented alternate momentum signal (George & Hwang, 2004 — "The
52-Week High and Momentum Investing"). The intuition is different from
the project's usual formula too: 6m/12m risk-adjusted RETURN measures how
much a stock has moved; 52-week-high proximity measures how close it is
to a specific, psychologically salient reference price that other market
participants are watching (the idea being that a stock breaking to a new
high, or sitting right at one, behaves differently than the same % return
achieved while still well below its own high).

NO volatility adjustment is applied here — unlike the 6m/12m formula
(which NEEDS to divide by volatility to make returns comparable across
stocks of very different riskiness), the 52-week-high ratio is already
naturally comparable across stocks: a stock at 95% of its own high means
the same thing regardless of how volatile that stock normally is. No
cross-sectional Z-scoring or asymmetric normalization is needed either —
this is a single factor, and Z-scoring a single factor is a monotonic
(rank-preserving) transform, so ranking on the raw ratio directly gives
the identical top-10 as ranking on its Z-score would.

Same top-10, equal-weight, June/December rebalance, Midcap150 universe,
and NIFTY 50 real benchmark as every other report in this comparison
series (reports 33-35).
"""
import json

import numpy as np
import pandas as pd

from backtest10 import rebalance_dates, cumret_drawdown, series_to_points, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes
from backtest32 import metrics_only
from backtest33 import select_top_original, build_index_generic, overlap_stats

TOP_N = 10
MIN_ELIGIBLE = 30
WINDOW_52W = 252


def select_top_52wk_high(closes, t_idx, top_n=TOP_N, min_eligible=MIN_ELIGIBLE, window=WINDOW_52W):
    if t_idx < window - 1:
        return None
    price_t = closes.iloc[t_idx]
    hist = closes.iloc[t_idx - window + 1: t_idx + 1]
    rolling_high = hist.max()

    eligible = price_t.notna() & rolling_high.notna() & (rolling_high > 0)
    tickers = closes.columns[eligible]
    if len(tickers) < min_eligible:
        return None

    ratio = price_t[tickers] / rolling_high[tickers]
    ratio = ratio[ratio.notna() & np.isfinite(ratio)]
    if len(ratio) < min_eligible:
        return None

    return list(ratio.sort_values(ascending=False).head(top_n).index)


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]

    rbdates = rebalance_dates(closes.index, months=(6, 12))

    original_series, original_sel = build_index_generic(closes, rbdates, select_top_original)
    high52_series, high52_sel = build_index_generic(closes, rbdates, select_top_52wk_high)

    common_idx = original_series.index.intersection(high52_series.index)
    original_metrics = metrics_only(original_series, common_idx)
    high52_metrics = metrics_only(high52_series, common_idx)

    nifty_series = nifty.loc[common_idx, "Close"]
    nifty_metrics = metrics_only(nifty_series, common_idx)

    overlaps = overlap_stats(original_sel, high52_sel)
    avg_overlap = round(float(np.mean(overlaps)), 1) if overlaps else None

    def sample(sel):
        return sel[:3] + sel[-3:] if len(sel) > 6 else sel

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "num_rebalances": len(original_sel),
        "avg_overlap_pct": avg_overlap,
        "num_overlap_rebalances": len(overlaps),
        "original": {**original_metrics, "selections_sample": sample(original_sel)},
        "high52": {**high52_metrics, "selections_sample": sample(high52_sel)},
        "nifty": nifty_metrics,
    }

    with open("results35.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}  rebalances {results['num_rebalances']}")
    print(f"original (6m/12m ret) CAGR {original_metrics['cagr_pct']:.2f}% / DD {original_metrics['max_drawdown_pct']:.1f}%")
    print(f"52wk-high proximity   CAGR {high52_metrics['cagr_pct']:.2f}% / DD {high52_metrics['max_drawdown_pct']:.1f}%")
    print(f"nifty 50 benchmark    CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")
    print(f"avg rebalance overlap: {avg_overlap}% ({len(overlaps)} rebalances compared)")


if __name__ == "__main__":
    main()

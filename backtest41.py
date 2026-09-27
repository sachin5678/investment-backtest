"""
"NIFTY100 Momentum 10" — front-loaded 3m/6m/12m weighting (50/30/20) vs.
the existing equal-weighted formula, testing report 39's hypothesis on a
FOURTH universe, this time a much SMALLER and more concentrated one.

Reports 39-40 found front-loading wins on both CAGR and drawdown on
NIFTY500 (500 stocks) and Smallcap250 (250 stocks) — both broader
universes than Midcap150 (150 stocks), where reports 37-38 found a
genuine trade-off instead. NIFTY100 (report 12's config: top 10 out of
JUST 100 stocks, the smallest and most liquid universe tested in this
front-loading comparison series) is the sharpest test of the "broader
universe = more candidates = front-loading helps more" hypothesis yet —
if the hypothesis holds, NIFTY100 (smaller than even Midcap150) should
show the trade-off AT LEAST as strongly as Midcap150 did, not the
NIFTY500/Smallcap250 pattern.

Same top-10, equal-weight, June/December rebalance as report 12's
original NIFTY100 Momentum 10 reconstruction.
"""
import json

import numpy as np
import pandas as pd

from backtest10 import load_universe_closes, rebalance_dates, cumret_drawdown, series_to_points, fetch, CURRENCY_SYMBOL
from nifty100_symbols import NIFTY_100_SYMBOLS
from backtest32 import metrics_only
from backtest33 import build_index_generic, overlap_stats

TOP_N = 10
MIN_ELIGIBLE = 20
LOOKBACK_12M = 252
LOOKBACK_6M = 126
LOOKBACK_3M = 63

WEIGHT_3M = 0.50
WEIGHT_6M = 0.30
WEIGHT_12M = 0.20


def select_top_original_n100(closes, t_idx, top_n=TOP_N, min_eligible=MIN_ELIGIBLE):
    if t_idx < LOOKBACK_12M:
        return None
    price_t = closes.iloc[t_idx]
    price_t12 = closes.iloc[t_idx - LOOKBACK_12M]
    price_t6 = closes.iloc[t_idx - LOOKBACK_6M]
    eligible = price_t.notna() & price_t12.notna() & price_t6.notna()
    tickers = closes.columns[eligible]
    if len(tickers) < min_eligible:
        return None

    window = closes.iloc[t_idx - LOOKBACK_12M: t_idx + 1][tickers]
    daily_ret = window.pct_change().dropna(how="all")
    vol_1y = daily_ret.std()

    ret_6m = price_t[tickers] / price_t6[tickers] - 1.0
    ret_12m = price_t[tickers] / price_t12[tickers] - 1.0
    ratio_6m = ret_6m / vol_1y
    ratio_12m = ret_12m / vol_1y

    valid = ratio_6m.notna() & ratio_12m.notna() & np.isfinite(ratio_6m) & np.isfinite(ratio_12m)
    ratio_6m, ratio_12m = ratio_6m[valid], ratio_12m[valid]
    if len(ratio_6m) < min_eligible:
        return None

    z6 = (ratio_6m - ratio_6m.mean()) / ratio_6m.std()
    z12 = (ratio_12m - ratio_12m.mean()) / ratio_12m.std()
    waz = 0.5 * z6 + 0.5 * z12
    norm_score = waz.apply(lambda w: 1 + w if w >= 0 else 1 / (1 - w))
    return list(norm_score.sort_values(ascending=False).head(top_n).index)


def select_top_frontloaded_n100(closes, t_idx, top_n=TOP_N, min_eligible=MIN_ELIGIBLE):
    if t_idx < LOOKBACK_12M:
        return None
    price_t = closes.iloc[t_idx]
    price_t12 = closes.iloc[t_idx - LOOKBACK_12M]
    price_t6 = closes.iloc[t_idx - LOOKBACK_6M]
    price_t3 = closes.iloc[t_idx - LOOKBACK_3M]
    eligible = price_t.notna() & price_t12.notna() & price_t6.notna() & price_t3.notna()
    tickers = closes.columns[eligible]
    if len(tickers) < min_eligible:
        return None

    window = closes.iloc[t_idx - LOOKBACK_12M: t_idx + 1][tickers]
    daily_ret = window.pct_change().dropna(how="all")
    vol_1y = daily_ret.std()

    ret_3m = price_t[tickers] / price_t3[tickers] - 1.0
    ret_6m = price_t[tickers] / price_t6[tickers] - 1.0
    ret_12m = price_t[tickers] / price_t12[tickers] - 1.0
    ratio_3m = ret_3m / vol_1y
    ratio_6m = ret_6m / vol_1y
    ratio_12m = ret_12m / vol_1y

    valid = (
        ratio_3m.notna() & ratio_6m.notna() & ratio_12m.notna()
        & np.isfinite(ratio_3m) & np.isfinite(ratio_6m) & np.isfinite(ratio_12m)
    )
    ratio_3m, ratio_6m, ratio_12m = ratio_3m[valid], ratio_6m[valid], ratio_12m[valid]
    if len(ratio_3m) < min_eligible:
        return None

    z3 = (ratio_3m - ratio_3m.mean()) / ratio_3m.std()
    z6 = (ratio_6m - ratio_6m.mean()) / ratio_6m.std()
    z12 = (ratio_12m - ratio_12m.mean()) / ratio_12m.std()
    waz = WEIGHT_3M * z3 + WEIGHT_6M * z6 + WEIGHT_12M * z12
    norm_score = waz.apply(lambda w: 1 + w if w >= 0 else 1 / (1 - w))
    return list(norm_score.sort_values(ascending=False).head(top_n).index)


def main():
    closes_all = load_universe_closes()
    n100_tickers = [s + ".NS" for s in NIFTY_100_SYMBOLS]
    missing = [t for t in n100_tickers if t not in closes_all.columns]
    assert not missing, f"missing tickers not in cached universe: {missing}"
    closes = closes_all[n100_tickers]

    nifty = fetch("^NSEI")
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]

    rbdates = rebalance_dates(closes.index, months=(6, 12))

    original_series, original_sel = build_index_generic(closes, rbdates, select_top_original_n100)
    frontloaded_series, frontloaded_sel = build_index_generic(closes, rbdates, select_top_frontloaded_n100)

    common_idx = original_series.index.intersection(frontloaded_series.index)
    original_metrics = metrics_only(original_series, common_idx)
    frontloaded_metrics = metrics_only(frontloaded_series, common_idx)

    nifty_series = nifty.loc[common_idx, "Close"]
    nifty_metrics = metrics_only(nifty_series, common_idx)

    overlaps = overlap_stats(original_sel, frontloaded_sel)
    avg_overlap = round(float(np.mean(overlaps)), 1) if overlaps else None

    def sample(sel):
        return sel[:3] + sel[-3:] if len(sel) > 6 else sel

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "num_rebalances": len(original_sel),
        "weights": {"w3m": WEIGHT_3M * 100, "w6m": WEIGHT_6M * 100, "w12m": WEIGHT_12M * 100},
        "avg_overlap_pct": avg_overlap,
        "num_overlap_rebalances": len(overlaps),
        "original": {**original_metrics, "selections_sample": sample(original_sel)},
        "frontloaded": {**frontloaded_metrics, "selections_sample": sample(frontloaded_sel)},
        "nifty": nifty_metrics,
    }

    with open("results40.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}  rebalances {results['num_rebalances']}")
    print(f"NIFTY100 Momentum 10 (old, equal-weighted)   CAGR {original_metrics['cagr_pct']:.2f}% / DD {original_metrics['max_drawdown_pct']:.1f}%")
    print(f"NIFTY100 Momentum 10 (front-loaded 50/30/20) CAGR {frontloaded_metrics['cagr_pct']:.2f}% / DD {frontloaded_metrics['max_drawdown_pct']:.1f}%")
    print(f"nifty 50 benchmark    CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")
    print(f"avg rebalance overlap: {avg_overlap}% ({len(overlaps)} rebalances compared)")


if __name__ == "__main__":
    main()

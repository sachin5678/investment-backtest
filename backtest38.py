"""
Midcap150 Momentum 10 — front-loaded weighting, TWO splits compared: the
original 50/30/20 (report 37) vs. a gentler 40/35/25, both against the
equal-weighted original formula.

Report 37 tested one specific front-loaded 3-month/6-month/12-month
weighting (50%/30%/20%) and found a genuine risk/return trade-off: lower
CAGR, shallower drawdown, versus the original's equal 6m/12m 50/50 blend.
This report asks the natural follow-up: does a GENTLER front-load (closer
to equal weighting, 40%/35%/25%) land somewhere between the two, or does
it behave unpredictably? Same top-10, equal-weight, June/December
Midcap150 strategy, same risk-adjustment/Z-scoring/normalization
mechanics as every other report in this comparison series (reports
33-37) — only the window weights change.
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
LOOKBACK_12M = 252
LOOKBACK_6M = 126
LOOKBACK_3M = 63


def make_select_frontloaded(w3m, w6m, w12m, top_n=TOP_N, min_eligible=MIN_ELIGIBLE):
    def select_fn(closes, t_idx):
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
        waz = w3m * z3 + w6m * z6 + w12m * z12
        norm_score = waz.apply(lambda w: 1 + w if w >= 0 else 1 / (1 - w))
        return list(norm_score.sort_values(ascending=False).head(top_n).index)

    return select_fn


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]

    rbdates = rebalance_dates(closes.index, months=(6, 12))

    select_5030 = make_select_frontloaded(0.50, 0.30, 0.20)
    select_4035 = make_select_frontloaded(0.40, 0.35, 0.25)

    original_series, original_sel = build_index_generic(closes, rbdates, select_top_original)
    fl5030_series, fl5030_sel = build_index_generic(closes, rbdates, select_5030)
    fl4035_series, fl4035_sel = build_index_generic(closes, rbdates, select_4035)

    common_idx = original_series.index.intersection(fl5030_series.index).intersection(fl4035_series.index)
    original_metrics = metrics_only(original_series, common_idx)
    fl5030_metrics = metrics_only(fl5030_series, common_idx)
    fl4035_metrics = metrics_only(fl4035_series, common_idx)

    nifty_series = nifty.loc[common_idx, "Close"]
    nifty_metrics = metrics_only(nifty_series, common_idx)

    overlap_5030 = overlap_stats(original_sel, fl5030_sel)
    overlap_4035 = overlap_stats(original_sel, fl4035_sel)

    def sample(sel):
        return sel[:3] + sel[-3:] if len(sel) > 6 else sel

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "num_rebalances": len(original_sel),
        "original": {**original_metrics, "selections_sample": sample(original_sel)},
        "fl_50_30_20": {
            **fl5030_metrics, "selections_sample": sample(fl5030_sel),
            "weights": {"w3m": 50.0, "w6m": 30.0, "w12m": 20.0},
            "avg_overlap_pct": round(float(np.mean(overlap_5030)), 1) if overlap_5030 else None,
        },
        "fl_40_35_25": {
            **fl4035_metrics, "selections_sample": sample(fl4035_sel),
            "weights": {"w3m": 40.0, "w6m": 35.0, "w12m": 25.0},
            "avg_overlap_pct": round(float(np.mean(overlap_4035)), 1) if overlap_4035 else None,
        },
        "nifty": nifty_metrics,
    }

    with open("results37.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}  rebalances {results['num_rebalances']}")
    print(f"original (equal-weighted)   CAGR {original_metrics['cagr_pct']:.2f}% / DD {original_metrics['max_drawdown_pct']:.1f}%")
    print(f"front-loaded 50/30/20       CAGR {fl5030_metrics['cagr_pct']:.2f}% / DD {fl5030_metrics['max_drawdown_pct']:.1f}%  overlap {results['fl_50_30_20']['avg_overlap_pct']}%")
    print(f"front-loaded 40/35/25       CAGR {fl4035_metrics['cagr_pct']:.2f}% / DD {fl4035_metrics['max_drawdown_pct']:.1f}%  overlap {results['fl_40_35_25']['avg_overlap_pct']}%")
    print(f"nifty 50 benchmark          CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")


if __name__ == "__main__":
    main()

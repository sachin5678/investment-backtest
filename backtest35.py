"""
Midcap150 Momentum 10 — BOTTOM-10 reversal (anti-momentum) sanity check.

The exact same score as the original formula (6m/12m risk-adjusted
return, cross-sectionally Z-scored, 0.5/0.5 combined, asymmetrically
normalized) — but this report selects the WORST 10 stocks by that score
each rebalance instead of the best 10. Same top-N size, same equal
weighting, same June/December rebalance, same Midcap150 universe.

WHY THIS REPORT EXISTS: every other formula variant in this project
(reports 25, 27, 30, 33, 34...) tweaks ONE piece of the momentum formula
and checks whether the result changes in a sensible, explicable way. This
one is different in kind — it's a discipline check on whether the
momentum EFFECT is real at all, not a refinement of it. If deliberately
buying the worst-ranked stocks by this exact score produces a materially
WORSE result than buying the best-ranked ones, that's real evidence the
score is capturing something genuine, not noise a differently-seeded
simulation would just as easily reverse. If bottom-10 did just as well
(or better), that would be a serious red flag about every other report in
this project's momentum family.
"""
import json

import numpy as np
import pandas as pd

from backtest10 import rebalance_dates, cumret_drawdown, series_to_points, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes
from backtest32 import metrics_only
from backtest33 import select_top_original, build_index_generic

TOP_N = 10
MIN_ELIGIBLE = 30
LOOKBACK_12M = 252
LOOKBACK_6M = 126


def select_bottom_original(closes, t_idx, top_n=TOP_N, min_eligible=MIN_ELIGIBLE):
    """Identical score computation to select_top_original — only the
    final selection direction flips (worst-ranked instead of best)."""
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
    # the only line that differs from select_top_original: ascending
    # instead of descending, so .head(top_n) grabs the WORST scores.
    return list(norm_score.sort_values(ascending=True).head(top_n).index)


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]

    rbdates = rebalance_dates(closes.index, months=(6, 12))

    top_series, top_sel = build_index_generic(closes, rbdates, select_top_original)
    bottom_series, bottom_sel = build_index_generic(closes, rbdates, select_bottom_original)

    common_idx = top_series.index.intersection(bottom_series.index)
    top_metrics = metrics_only(top_series, common_idx)
    bottom_metrics = metrics_only(bottom_series, common_idx)

    nifty_series = nifty.loc[common_idx, "Close"]
    nifty_metrics = metrics_only(nifty_series, common_idx)

    # overlap should be ~0% by construction (best vs worst of the same
    # ranked list of 250-ish names can't share many names) — computed
    # anyway as a sanity check on the harness itself, not a headline stat.
    by_date_top = {s["date"]: set(s["tickers"]) for s in top_sel}
    overlaps = []
    for s in bottom_sel:
        if s["date"] in by_date_top:
            a, b = by_date_top[s["date"]], set(s["tickers"])
            overlaps.append(len(a & b))
    total_overlap_names = sum(overlaps)

    def sample(sel):
        return sel[:3] + sel[-3:] if len(sel) > 6 else sel

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "num_rebalances": len(top_sel),
        "total_overlap_names": total_overlap_names,
        "top": {**top_metrics, "selections_sample": sample(top_sel)},
        "bottom": {**bottom_metrics, "selections_sample": sample(bottom_sel)},
        "nifty": nifty_metrics,
    }

    with open("results34.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}  rebalances {results['num_rebalances']}")
    print(f"top-10 (momentum)    CAGR {top_metrics['cagr_pct']:.2f}% / DD {top_metrics['max_drawdown_pct']:.1f}%")
    print(f"bottom-10 (reversal) CAGR {bottom_metrics['cagr_pct']:.2f}% / DD {bottom_metrics['max_drawdown_pct']:.1f}%")
    print(f"nifty 50 benchmark   CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")
    print(f"total shared names across all rebalances (sanity check, expect near 0): {total_overlap_names}")


if __name__ == "__main__":
    main()

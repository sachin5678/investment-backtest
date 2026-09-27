"""
Midcap150 Momentum 10 — inverse-volatility position sizing instead of
equal weighting the top 10. Same selection formula, same top-10, same
June/December schedule as every other Midcap150 Momentum 10 report — the
ONLY change is that each rebalance now allocates capital across the 10
picks INVERSELY to each stock's own trailing 1-year volatility (the exact
same daily-return std the scoring formula already computes), instead of
splitting 10% to each name equally. A calmer pick gets a bigger dollar
weight; a shakier one gets a smaller one. No regime filter involved here
— this tests the weighting scheme in isolation, "always invested" both
ways, same as reports 37-41 tested formula changes on their own before
being combined with anything else.
"""
import json

import pandas as pd

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes
from backtest32 import metrics_only
from backtest33 import select_top_original, build_index_generic, build_index_generic_invvol, overlap_stats


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]

    rbdates = rebalance_dates(closes.index, months=(6, 12))

    equal_series, equal_sel = build_index_generic(closes, rbdates, select_top_original)
    invvol_series, invvol_sel = build_index_generic_invvol(closes, rbdates, select_top_original)

    common_idx = equal_series.index.intersection(invvol_series.index)
    equal_metrics = metrics_only(equal_series, common_idx)
    invvol_metrics = metrics_only(invvol_series, common_idx)
    nifty_metrics = metrics_only(nifty.loc[common_idx, "Close"], common_idx)

    overlaps = overlap_stats(equal_sel, invvol_sel)
    avg_overlap = round(sum(overlaps) / len(overlaps), 1) if overlaps else None

    def sample(sel):
        return sel[:3] + sel[-3:] if len(sel) > 6 else sel

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "num_rebalances": len(equal_sel),
        "avg_overlap_pct": avg_overlap,
        "equal": {**equal_metrics, "selections_sample": sample(equal_sel)},
        "invvol": {**invvol_metrics, "selections_sample": sample(invvol_sel)},
        "nifty": nifty_metrics,
    }

    with open("results50.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}  rebalances {results['num_rebalances']}")
    print(f"Equal-weight     CAGR {equal_metrics['cagr_pct']:.2f}% / DD {equal_metrics['max_drawdown_pct']:.1f}%")
    print(f"Inverse-vol      CAGR {invvol_metrics['cagr_pct']:.2f}% / DD {invvol_metrics['max_drawdown_pct']:.1f}%")
    print(f"nifty 50         CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")


if __name__ == "__main__":
    main()

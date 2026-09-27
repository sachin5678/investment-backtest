"""
NIFTY100 Momentum 10 — inverse-volatility position sizing instead of
equal weighting. Same mechanics as reports 51-52, applied to report 12's
NIFTY100 Momentum 10 config.
"""
import json

import pandas as pd

from backtest10 import load_universe_closes, rebalance_dates, fetch, CURRENCY_SYMBOL
from nifty100_symbols import NIFTY_100_SYMBOLS
from backtest32 import metrics_only
from backtest33 import build_index_generic, build_index_generic_invvol, overlap_stats
from backtest45 import select_top_n100


def main():
    closes_all = load_universe_closes()
    n100_tickers = [s + ".NS" for s in NIFTY_100_SYMBOLS]
    closes = closes_all[[t for t in n100_tickers if t in closes_all.columns]]

    nifty = fetch("^NSEI")
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]

    rbdates = rebalance_dates(closes.index, months=(6, 12))

    equal_series, equal_sel = build_index_generic(closes, rbdates, select_top_n100)
    invvol_series, invvol_sel = build_index_generic_invvol(closes, rbdates, select_top_n100)

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

    with open("results52.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}  rebalances {results['num_rebalances']}")
    print(f"Equal-weight     CAGR {equal_metrics['cagr_pct']:.2f}% / DD {equal_metrics['max_drawdown_pct']:.1f}%")
    print(f"Inverse-vol      CAGR {invvol_metrics['cagr_pct']:.2f}% / DD {invvol_metrics['max_drawdown_pct']:.1f}%")
    print(f"nifty 50         CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")


if __name__ == "__main__":
    main()

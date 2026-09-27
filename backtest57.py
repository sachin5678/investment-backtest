"""
Midcap150 Momentum 10 — breadth confirmation added to the 200-day EMA
regime filter (reports 42-56). The user's idea: don't rely on NIFTY 50's
own 200-EMA as the SOLE trigger — also require a minimum share of the
relevant top-10 candidates to be individually above their OWN 200-day
EMA before treating the regime as "invested."

Mechanics: while INVESTED, the "relevant top-10" is whatever is
currently HELD (cheap to check — no recomputation needed) — if NIFTY 50
drops below its 200-EMA, OR fewer than breadth_threshold of the held
names are above their own 200-EMA, exit to cash. While in CASH and NIFTY
50's condition is met, today's candidate top-10 is recomputed to check
ITS breadth before actually buying — if breadth fails, stay in cash and
re-check the next day, exactly as report 42's filter re-checks NIFTY 50
every day.

Four thresholds tested (30%/50%/70%/90% of the top-10 must be above
their own 200-EMA) against report 42's NIFTY-50-only filter and the
unfiltered strategy, all recomputed fresh on the identical window.
"""
import json

import numpy as np
import pandas as pd

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes
from backtest32 import metrics_only
from backtest33 import select_top_original, build_index_generic
from backtest42 import build_index_regime_filtered, build_index_regime_filtered_breadth, cash_blocks_from_log, EMA_SPAN

BREADTH_THRESHOLDS = [0.3, 0.5, 0.7, 0.9]


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]
    ema = nifty_close.ewm(span=EMA_SPAN, adjust=False).mean()

    rbdates = rebalance_dates(closes.index, months=(6, 12))

    original_series, _ = build_index_generic(closes, rbdates, select_top_original)
    nifty_only_series, nifty_only_sel, nifty_only_log = build_index_regime_filtered(closes, nifty_close, ema, rbdates, select_top_original)

    variant_results = {}
    common_idx = original_series.index.intersection(nifty_only_series.index)
    for thr in BREADTH_THRESHOLDS:
        series, sel, log = build_index_regime_filtered_breadth(closes, nifty_close, ema, rbdates, select_top_original, breadth_threshold=thr)
        common_idx = common_idx.intersection(series.index)
        cash_blocks, pct_cash = cash_blocks_from_log(log)
        num_reentries = sum(1 for s in sel if s["trigger"] == "regime_reentry")
        variant_results[thr] = {"series": series, "pct_cash": round(pct_cash, 1), "num_reentries": num_reentries}

    original_metrics = metrics_only(original_series, common_idx)
    nifty_only_metrics = metrics_only(nifty_only_series, common_idx)
    nifty_metrics = metrics_only(nifty_close.loc[common_idx], common_idx)
    nifty_only_blocks, nifty_only_pct_cash = cash_blocks_from_log(nifty_only_log)
    nifty_only_reentries = sum(1 for s in nifty_only_sel if s["trigger"] == "regime_reentry")

    variants_out = []
    for thr in BREADTH_THRESHOLDS:
        m = metrics_only(variant_results[thr]["series"], common_idx)
        variants_out.append({
            "breadth_threshold_pct": thr * 100,
            "cagr_pct": m["cagr_pct"], "max_drawdown_pct": m["max_drawdown_pct"],
            "net_return_pct": m["net_return_pct"], "longest_underwater_days": m["longest_underwater_days"],
            "equity_curve": m["equity_curve"],
            "pct_time_in_cash": variant_results[thr]["pct_cash"],
            "num_regime_reentries": variant_results[thr]["num_reentries"],
        })

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "ema_span": EMA_SPAN,
        "original": original_metrics,
        "nifty_only": {**nifty_only_metrics, "pct_time_in_cash": round(nifty_only_pct_cash, 1),
                       "num_regime_reentries": nifty_only_reentries},
        "nifty": nifty_metrics,
        "variants": variants_out,
    }

    with open("results56.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}")
    print(f"no filter          CAGR {original_metrics['cagr_pct']:.2f}% / DD {original_metrics['max_drawdown_pct']:.1f}%")
    print(f"NIFTY-only filter  CAGR {nifty_only_metrics['cagr_pct']:.2f}% / DD {nifty_only_metrics['max_drawdown_pct']:.1f}%  |  re-entries {nifty_only_reentries}")
    for v in variants_out:
        print(f"breadth>={v['breadth_threshold_pct']:.0f}%  CAGR {v['cagr_pct']:.2f}% / DD {v['max_drawdown_pct']:.1f}%  |  cash {v['pct_time_in_cash']:.1f}%  |  re-entries {v['num_regime_reentries']}")
    print(f"nifty 50 benchmark CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")


if __name__ == "__main__":
    main()

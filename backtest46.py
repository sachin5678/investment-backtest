"""
Midcap150 Momentum 10 — EMA-span sensitivity for the regime filter from
reports 42-45. Same filter mechanics (cash below the EMA, fresh
selection on re-entry), same Midcap150 Momentum 10 formula — the ONLY
thing that changes across the four runs below is the EMA's own lookback
span: 100, 150, 200 (report 42's original choice), and 250 trading days.

A wider span reacts more slowly to price (fewer whipsaws, but also later
exits and later re-entries); a narrower span reacts faster (more
protection against sharp drops, but more false alarms in choppy markets).
This report quantifies that trade-off directly rather than assuming
report 42's 200-day choice was optimal.
"""
import json

import numpy as np
import pandas as pd

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes
from backtest32 import metrics_only
from backtest33 import select_top_original, build_index_generic
from backtest42 import build_index_regime_filtered, cash_blocks_from_log

SPANS = [100, 150, 200, 250]


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]

    rbdates = rebalance_dates(closes.index, months=(6, 12))

    original_series, _ = build_index_generic(closes, rbdates, select_top_original)

    span_results = {}
    common_idx = original_series.index
    for span in SPANS:
        ema = nifty_close.ewm(span=span, adjust=False).mean()
        filtered_series, filtered_sel, state_log = build_index_regime_filtered(closes, nifty_close, ema, rbdates, select_top_original)
        common_idx = common_idx.intersection(filtered_series.index)
        cash_blocks, pct_cash = cash_blocks_from_log(state_log)
        num_reentries = sum(1 for s in filtered_sel if s["trigger"] == "regime_reentry")
        span_results[span] = {
            "series": filtered_series,
            "pct_cash": round(pct_cash, 1),
            "num_reentries": num_reentries,
            "num_cash_periods": len(cash_blocks),
        }

    original_metrics = metrics_only(original_series, common_idx)
    nifty_metrics = metrics_only(nifty_close.loc[common_idx], common_idx)

    spans_out = []
    for span in SPANS:
        m = metrics_only(span_results[span]["series"], common_idx)
        spans_out.append({
            "span": span,
            "cagr_pct": m["cagr_pct"], "max_drawdown_pct": m["max_drawdown_pct"],
            "net_return_pct": m["net_return_pct"], "longest_underwater_days": m["longest_underwater_days"],
            "equity_curve": m["equity_curve"],
            "pct_time_in_cash": span_results[span]["pct_cash"],
            "num_regime_reentries": span_results[span]["num_reentries"],
            "num_cash_periods_10d_plus": span_results[span]["num_cash_periods"],
        })

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "spans_tested": SPANS,
        "original": original_metrics,
        "nifty": nifty_metrics,
        "spans": spans_out,
    }

    with open("results45.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}")
    print(f"no filter          CAGR {original_metrics['cagr_pct']:.2f}% / DD {original_metrics['max_drawdown_pct']:.1f}%")
    for s in spans_out:
        print(f"{s['span']}-day EMA      CAGR {s['cagr_pct']:.2f}% / DD {s['max_drawdown_pct']:.1f}%  |  cash {s['pct_time_in_cash']:.1f}%  |  re-entries {s['num_regime_reentries']}")
    print(f"nifty 50 benchmark  CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")


if __name__ == "__main__":
    main()

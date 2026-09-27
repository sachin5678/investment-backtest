"""
Smallcap250 Momentum 10 — asymmetric EMA regime filter (exit on the slow
200-day EMA, re-enter on a faster 50-day EMA), same mechanics as report
59, applied to report 16/29's Smallcap250 Momentum 10 config.
"""
import json

import pandas as pd

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest15 import load_smallcap250_closes
from backtest32 import metrics_only
from backtest33 import build_index_generic
from backtest42 import (build_index_regime_filtered, build_index_regime_filtered_asymmetric,
                         cash_blocks_from_log, EMA_SPAN, REENTRY_EMA_SPAN)
from backtest44 import select_top_smallcap


def main():
    closes = load_smallcap250_closes()
    nifty = fetch("^NSEI")
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]
    exit_ema = nifty_close.ewm(span=EMA_SPAN, adjust=False).mean()
    reentry_ema = nifty_close.ewm(span=REENTRY_EMA_SPAN, adjust=False).mean()

    rbdates = rebalance_dates(closes.index, months=(6, 12))

    original_series, _ = build_index_generic(closes, rbdates, select_top_smallcap)
    symmetric_series, symmetric_sel, symmetric_log = build_index_regime_filtered(closes, nifty_close, exit_ema, rbdates, select_top_smallcap)
    asymmetric_series, asymmetric_sel, asymmetric_log = build_index_regime_filtered_asymmetric(closes, nifty_close, exit_ema, reentry_ema, rbdates, select_top_smallcap)

    common_idx = original_series.index.intersection(symmetric_series.index).intersection(asymmetric_series.index)
    original_metrics = metrics_only(original_series, common_idx)
    symmetric_metrics = metrics_only(symmetric_series, common_idx)
    asymmetric_metrics = metrics_only(asymmetric_series, common_idx)
    nifty_metrics = metrics_only(nifty_close.loc[common_idx], common_idx)

    sym_blocks, sym_pct_cash = cash_blocks_from_log(symmetric_log)
    asym_blocks, asym_pct_cash = cash_blocks_from_log(asymmetric_log)
    sym_reentries = sum(1 for s in symmetric_sel if s["trigger"] == "regime_reentry")
    asym_reentries = sum(1 for s in asymmetric_sel if s["trigger"] == "regime_reentry")

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "exit_ema_span": EMA_SPAN, "reentry_ema_span": REENTRY_EMA_SPAN,
        "original": original_metrics,
        "symmetric": {**symmetric_metrics, "pct_time_in_cash": round(sym_pct_cash, 1), "num_regime_reentries": sym_reentries},
        "asymmetric": {**asymmetric_metrics, "pct_time_in_cash": round(asym_pct_cash, 1), "num_regime_reentries": asym_reentries},
        "nifty": nifty_metrics,
    }

    with open("results59.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}")
    print(f"no filter    CAGR {original_metrics['cagr_pct']:.2f}% / DD {original_metrics['max_drawdown_pct']:.1f}%")
    print(f"symmetric    CAGR {symmetric_metrics['cagr_pct']:.2f}% / DD {symmetric_metrics['max_drawdown_pct']:.1f}%  |  re-entries {sym_reentries}")
    print(f"asymmetric   CAGR {asymmetric_metrics['cagr_pct']:.2f}% / DD {asymmetric_metrics['max_drawdown_pct']:.1f}%  |  re-entries {asym_reentries}")
    print(f"nifty 50     CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")


if __name__ == "__main__":
    main()

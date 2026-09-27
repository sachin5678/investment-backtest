"""
Midcap150 Momentum 10 — confirmation-delay sensitivity for the 200-day
EMA regime filter (reports 42-46). Same 200-day EMA signal, same
Midcap150 Momentum 10 formula — the ONLY change across the four runs
below is how many CONSECUTIVE trading days the signal must disagree with
the current state before the filter actually switches:
  - 1 day  (report 42's original, immediate-switch behavior)
  - 3 days
  - 5 days
  - 10 days
A day that agrees with the current state resets the streak to zero, so
this is a genuine "wait for confirmation" filter, not a fixed-delay lag —
it directly targets report 42's biggest disclosed weakness: 69 regime
re-entries over 18 years, almost twice the strategy's own scheduled
rebalance count, all free of transaction costs in this frictionless
model. Does requiring the signal to persist for a few days cut that
whipsaw meaningfully, and at what cost to the drawdown protection itself?
"""
import json

import pandas as pd

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes
from backtest32 import metrics_only
from backtest33 import select_top_original, build_index_generic
from backtest42 import build_index_regime_filtered, cash_blocks_from_log, EMA_SPAN

CONFIRM_DAYS_TESTED = [1, 3, 5, 10]


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]
    ema = nifty_close.ewm(span=EMA_SPAN, adjust=False).mean()

    rbdates = rebalance_dates(closes.index, months=(6, 12))

    original_series, _ = build_index_generic(closes, rbdates, select_top_original)

    variant_results = {}
    common_idx = original_series.index
    for cd in CONFIRM_DAYS_TESTED:
        filtered_series, filtered_sel, state_log = build_index_regime_filtered(
            closes, nifty_close, ema, rbdates, select_top_original, confirm_days=cd)
        common_idx = common_idx.intersection(filtered_series.index)
        cash_blocks, pct_cash = cash_blocks_from_log(state_log)
        num_reentries = sum(1 for s in filtered_sel if s["trigger"] == "regime_reentry")
        variant_results[cd] = {
            "series": filtered_series,
            "pct_cash": round(pct_cash, 1),
            "num_reentries": num_reentries,
            "num_cash_periods": len(cash_blocks),
        }

    original_metrics = metrics_only(original_series, common_idx)
    nifty_metrics = metrics_only(nifty_close.loc[common_idx], common_idx)

    variants_out = []
    for cd in CONFIRM_DAYS_TESTED:
        m = metrics_only(variant_results[cd]["series"], common_idx)
        variants_out.append({
            "confirm_days": cd,
            "cagr_pct": m["cagr_pct"], "max_drawdown_pct": m["max_drawdown_pct"],
            "net_return_pct": m["net_return_pct"], "longest_underwater_days": m["longest_underwater_days"],
            "equity_curve": m["equity_curve"],
            "pct_time_in_cash": variant_results[cd]["pct_cash"],
            "num_regime_reentries": variant_results[cd]["num_reentries"],
            "num_cash_periods_10d_plus": variant_results[cd]["num_cash_periods"],
        })

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "ema_span": EMA_SPAN,
        "confirm_days_tested": CONFIRM_DAYS_TESTED,
        "original": original_metrics,
        "nifty": nifty_metrics,
        "variants": variants_out,
    }

    with open("results46.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}")
    print(f"no filter              CAGR {original_metrics['cagr_pct']:.2f}% / DD {original_metrics['max_drawdown_pct']:.1f}%")
    for v in variants_out:
        print(f"confirm={v['confirm_days']}d   CAGR {v['cagr_pct']:.2f}% / DD {v['max_drawdown_pct']:.1f}%  |  cash {v['pct_time_in_cash']:.1f}%  |  re-entries {v['num_regime_reentries']}")
    print(f"nifty 50 benchmark     CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")


if __name__ == "__main__":
    main()

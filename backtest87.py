"""
Midcap150 Momentum 10 — report 48's exact design (200-day EMA regime
filter, gold instead of cash), but instead of picking ONE of the six
semi-annual rebalance calendars tested in report 85, split capital
equally across ALL SIX (1/6 each): June/December, July/January, August/
February, September/March, October/April, November/May. Each of the six
"sleeves" is otherwise identical — same picks, same continuous daily
200-EMA regime signal, same gold hedge — just rebalancing 6 months apart
on its own calendar. Combined, the blended portfolio effectively
refreshes ~1/6th of its capital in every single calendar month instead
of concentrating every refresh into one specific two-month pair.

This directly tests whether diversifying ACROSS calendars (rather than
picking the best- or safest-looking single one, as report 85 could only
compare) smooths out the spread report 85 found, similar in spirit to
bond-laddering or SIP-tranching — reducing how much the result depends
on which two specific months happen to get chosen.

Mechanics: each sleeve's daily equity curve is recomputed independently
(same build_index_regime_filtered_with_hedge call as report 85, one per
calendar), then all six are rebased to 100 at the same common start date
and averaged together day by day — an equal-weight blend of six
independently-compounding sub-portfolios, not a re-optimized single
strategy.
"""
import json
import sys

import pandas as pd

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes, fetch_gold_cleaned
from backtest32 import metrics_only
from backtest33 import select_top_original, build_index_generic
from backtest42 import build_index_regime_filtered_with_hedge, EMA_SPAN

START_MONTHS = [6, 7, 8, 9, 10, 11]
MONTH_NAMES = {6: "june_dec", 7: "july_jan", 8: "aug_feb", 9: "sept_mar", 10: "oct_apr", 11: "nov_may"}


def offset_months(start_month):
    other = start_month + 6
    if other > 12:
        other -= 12
    return (start_month, other)


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    gold = fetch_gold_cleaned()
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]
    gold_aligned = gold["Close"].reindex(common).ffill().bfill()
    real_gold_idx = common.intersection(gold["Close"].index)

    ema200 = nifty_close.ewm(span=EMA_SPAN, adjust=False).mean()

    sleeve_series = {}
    for m in START_MONTHS:
        rbdates = rebalance_dates(closes.index, months=offset_months(m))
        s, _, _ = build_index_regime_filtered_with_hedge(
            closes, nifty_close, ema200, rbdates, select_top_original, gold_aligned)
        sleeve_series[m] = s

    common_idx = None
    for s in sleeve_series.values():
        common_idx = s.index if common_idx is None else common_idx.intersection(s.index)
    common_idx = common_idx.intersection(real_gold_idx)

    # Rebase each sleeve to 100 at the SAME common start date, then
    # average day by day — an equal-weight (1/6 each) blend.
    rebased = {}
    for m, s in sleeve_series.items():
        s_common = s.loc[common_idx]
        rebased[m] = s_common / s_common.iloc[0] * 100.0
    blended = sum(rebased.values()) / len(rebased)

    sleeve_metrics = {m: metrics_only(sleeve_series[m], common_idx) for m in START_MONTHS}
    blended_metrics = metrics_only(blended, common_idx)
    nifty_metrics = metrics_only(nifty_close, common_idx)
    gold_bench_metrics = metrics_only(gold["Close"], common_idx.intersection(real_gold_idx))

    best_m = max(START_MONTHS, key=lambda m: sleeve_metrics[m]["cagr_pct"])
    worst_m = min(START_MONTHS, key=lambda m: sleeve_metrics[m]["cagr_pct"])
    safest_m = max(START_MONTHS, key=lambda m: sleeve_metrics[m]["max_drawdown_pct"])

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "ema_span": EMA_SPAN, "month_names": MONTH_NAMES,
        "blended": blended_metrics,
        "best_calendar": {"label": MONTH_NAMES[best_m], **sleeve_metrics[best_m]},
        "worst_calendar": {"label": MONTH_NAMES[worst_m], **sleeve_metrics[worst_m]},
        "safest_calendar": {"label": MONTH_NAMES[safest_m], **sleeve_metrics[safest_m]},
        "june_dec": sleeve_metrics[6],
        "nifty": nifty_metrics, "gold_benchmark": gold_bench_metrics,
    }
    for m in START_MONTHS:
        results[f"sleeve_{MONTH_NAMES[m]}"] = sleeve_metrics[m]

    with open("results86.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}")
    for m in START_MONTHS:
        sm = sleeve_metrics[m]
        print(f"{MONTH_NAMES[m]:<10}  CAGR {sm['cagr_pct']:.2f}% / DD {sm['max_drawdown_pct']:.1f}%")
    print(f"\nBLENDED (1/6 each)  CAGR {blended_metrics['cagr_pct']:.2f}% / DD {blended_metrics['max_drawdown_pct']:.1f}%")
    print(f"nifty 50            CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")
    print(f"gold alone          CAGR {gold_bench_metrics['cagr_pct']:.2f}% / DD {gold_bench_metrics['max_drawdown_pct']:.1f}%")


if __name__ == "__main__":
    main()

"""
Midcap150 Momentum 10 — report 48's exact design (200-day EMA regime
filter, gold instead of cash), comparing MONTH-END rebalancing (report
48's own convention: last trading day of June/December) against MID-
MONTH rebalancing (the trading day closest to the 15th of June/
December) — same two months, only WHICH DAY within each month changes.

This is a different axis from report 85 (which months) and reports 76/
77 (how often) — this tests whether the specific day-of-month the
formula happens to measure momentum and switch stocks on matters at
all, holding the months and the continuous daily 200-EMA regime signal
fixed.
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

REBALANCE_MONTHS = (6, 12)
TARGET_DAY = 15


def rebalance_dates_midmonth(dates, months=REBALANCE_MONTHS, target_day=TARGET_DAY):
    df = pd.Series(dates, index=dates)
    out = []
    for (y, m), grp in df.groupby([dates.year, dates.month]):
        if m in months:
            day_diffs = abs(grp.index.day - target_day)
            idx_closest = day_diffs.values.argmin()
            out.append(grp.index[idx_closest])
    return sorted(out)


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

    rb_month_end = rebalance_dates(closes.index, months=REBALANCE_MONTHS)
    rb_mid_month = rebalance_dates_midmonth(closes.index)

    filtered_end, _, _ = build_index_regime_filtered_with_hedge(
        closes, nifty_close, ema200, rb_month_end, select_top_original, gold_aligned)
    filtered_mid, _, _ = build_index_regime_filtered_with_hedge(
        closes, nifty_close, ema200, rb_mid_month, select_top_original, gold_aligned)
    original_end, _ = build_index_generic(closes, rb_month_end, select_top_original)
    original_mid, _ = build_index_generic(closes, rb_mid_month, select_top_original)

    common_idx = filtered_end.index.intersection(filtered_mid.index) \
        .intersection(original_end.index).intersection(original_mid.index).intersection(real_gold_idx)

    original_end_metrics = metrics_only(original_end, common_idx)
    original_mid_metrics = metrics_only(original_mid, common_idx)
    filtered_end_metrics = metrics_only(filtered_end, common_idx)
    filtered_mid_metrics = metrics_only(filtered_mid, common_idx)
    nifty_metrics = metrics_only(nifty_close, common_idx)
    gold_bench_metrics = metrics_only(gold["Close"], common_idx.intersection(real_gold_idx))

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "ema_span": EMA_SPAN, "target_day": TARGET_DAY,
        "num_rebalances": {"month_end": len(rb_month_end), "mid_month": len(rb_mid_month)},
        "original_month_end": original_end_metrics, "original_mid_month": original_mid_metrics,
        "filtered_month_end": filtered_end_metrics, "filtered_mid_month": filtered_mid_metrics,
        "nifty": nifty_metrics, "gold_benchmark": gold_bench_metrics,
    }

    with open("results85.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}")
    print(f"no filter, month-end     CAGR {original_end_metrics['cagr_pct']:.2f}% / DD {original_end_metrics['max_drawdown_pct']:.1f}%")
    print(f"no filter, mid-month     CAGR {original_mid_metrics['cagr_pct']:.2f}% / DD {original_mid_metrics['max_drawdown_pct']:.1f}%")
    print(f"200-EMA+gold, month-end  CAGR {filtered_end_metrics['cagr_pct']:.2f}% / DD {filtered_end_metrics['max_drawdown_pct']:.1f}%")
    print(f"200-EMA+gold, mid-month  CAGR {filtered_mid_metrics['cagr_pct']:.2f}% / DD {filtered_mid_metrics['max_drawdown_pct']:.1f}%")
    print(f"nifty 50                 CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")
    print(f"gold alone               CAGR {gold_bench_metrics['cagr_pct']:.2f}% / DD {gold_bench_metrics['max_drawdown_pct']:.1f}%")


if __name__ == "__main__":
    main()

"""
Midcap150 Momentum 10 — report 48's exact design (200-day EMA regime
filter, gold instead of cash), tested across five different semi-annual
rebalance calendars: June/December (report 48's own convention), July/
January, August/February, September/March, October/April. Report 25
already tested this exact idea (all six offsets) on the PLAIN momentum
strategy with no filter — this asks whether the calendar offset matters
for the gold-hedged hero design too, or whether the regime filter
dominates the picture regardless of which two months the stock picks
get refreshed in.

Same continuous/daily 200-EMA regime check throughout all five variants
— only the top-10 stock-selection calendar changes. Same full-window/
gold-reindex convention as reports 48/68/71/76-79.
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

START_MONTHS = [6, 7, 8, 9, 10]


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

    rb_by_month = {m: rebalance_dates(closes.index, months=offset_months(m)) for m in START_MONTHS}

    original_by_month, filtered_by_month = {}, {}
    for m, rbdates in rb_by_month.items():
        orig_series, _ = build_index_generic(closes, rbdates, select_top_original)
        filt_series, _, _ = build_index_regime_filtered_with_hedge(
            closes, nifty_close, ema200, rbdates, select_top_original, gold_aligned)
        original_by_month[m] = orig_series
        filtered_by_month[m] = filt_series

    common_idx = None
    for s in list(original_by_month.values()) + list(filtered_by_month.values()):
        common_idx = s.index if common_idx is None else common_idx.intersection(s.index)
    common_idx = common_idx.intersection(real_gold_idx)

    original_metrics = {m: metrics_only(s, common_idx) for m, s in original_by_month.items()}
    filtered_metrics = {m: metrics_only(s, common_idx) for m, s in filtered_by_month.items()}
    nifty_metrics = metrics_only(nifty_close, common_idx)
    gold_bench_metrics = metrics_only(gold["Close"], common_idx.intersection(real_gold_idx))

    month_names = {6: "june_dec", 7: "july_jan", 8: "aug_feb", 9: "sept_mar", 10: "oct_apr"}
    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "ema_span": EMA_SPAN, "start_months": START_MONTHS, "month_names": month_names,
        "nifty": nifty_metrics, "gold_benchmark": gold_bench_metrics,
    }
    for m in START_MONTHS:
        label = month_names[m]
        results[f"original_{label}"] = original_metrics[m]
        results[f"filtered_{label}"] = filtered_metrics[m]

    with open("results84.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}")
    for m in START_MONTHS:
        om, fm = original_metrics[m], filtered_metrics[m]
        cal = offset_months(m)
        print(f"{month_names[m]:<10} ({cal[0]:>2}/{cal[1]:>2})  no filter CAGR {om['cagr_pct']:.2f}% / DD {om['max_drawdown_pct']:.1f}%   "
              f"|  200-EMA+gold CAGR {fm['cagr_pct']:.2f}% / DD {fm['max_drawdown_pct']:.1f}%")
    print(f"nifty 50               CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")
    print(f"gold alone              CAGR {gold_bench_metrics['cagr_pct']:.2f}% / DD {gold_bench_metrics['max_drawdown_pct']:.1f}%")


if __name__ == "__main__":
    main()

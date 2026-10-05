"""
Report 91's gold-strength guard, tested across ALL SIX semi-annual
rebalance calendars: June/December (report 91's own convention, and
report 48's), July/January, August/February, September/March, October/
April, November/May. Report 85 already asked this question for report
48 itself (does the calendar offset matter for the gold-hedged hero
design); this asks the same question for report 91's guard on top of
it — does the guard's +11.5pp CAGR / shallower-drawdown result
(reported on June/December) hold up on every other calendar too, or is
it specific to that one?

Same continuous/daily 200-EMA regime check and same gold-strength-guard
mechanism (backtest91.build_gold_strength_guard — the properly audited
version, reused as-is, not reimplemented) throughout all six variants —
only the top-10 stock-selection/rebalance calendar changes. Same
full-window/gold-reindex convention as reports 48/68/71/76-79/85/91.
"""
import json
import sys

import pandas as pd

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes, fetch_gold_cleaned
from backtest32 import metrics_only
from backtest33 import select_top_original
from backtest42 import build_index_regime_filtered_with_hedge, EMA_SPAN
from backtest91 import build_gold_strength_guard, GOLD_LOOKBACK_DAYS

START_MONTHS = [6, 7, 8, 9, 10, 11]
CALENDAR_LABEL = {6: "Jun/Dec", 7: "Jul/Jan", 8: "Aug/Feb", 9: "Sep/Mar", 10: "Oct/Apr", 11: "Nov/May"}


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

    standard_by_month, guarded_by_month = {}, {}
    for m, rbdates in rb_by_month.items():
        r48_series, _, _ = build_index_regime_filtered_with_hedge(
            closes, nifty_close, ema200, rbdates, select_top_original, gold_aligned)
        guarded_series, _, _, _, _ = build_gold_strength_guard(
            closes, nifty_close, ema200, rbdates, select_top_original, gold_aligned)
        standard_by_month[m] = r48_series
        guarded_by_month[m] = guarded_series

    common_idx = None
    for s in list(standard_by_month.values()) + list(guarded_by_month.values()):
        common_idx = s.index if common_idx is None else common_idx.intersection(s.index)
    common_idx = common_idx.intersection(real_gold_idx)

    standard_metrics = {m: metrics_only(s, common_idx) for m, s in standard_by_month.items()}
    guarded_metrics = {m: metrics_only(s, common_idx) for m, s in guarded_by_month.items()}
    nifty_metrics = metrics_only(nifty_close, common_idx)
    gold_bench_metrics = metrics_only(gold["Close"], common_idx.intersection(real_gold_idx))

    rows = []
    for m in START_MONTHS:
        s, g = standard_metrics[m], guarded_metrics[m]
        rows.append({
            "start_month": m, "calendar_label": CALENDAR_LABEL[m],
            "report48_standard": s, "gold_strength_guard": g,
            "cagr_diff_pp": round(g["cagr_pct"] - s["cagr_pct"], 2),
            "dd_diff_pp": round(g["max_drawdown_pct"] - s["max_drawdown_pct"], 2),
        })

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "ema_span": EMA_SPAN, "gold_lookback_days": GOLD_LOOKBACK_DAYS,
        "by_calendar": rows,
        "nifty": nifty_metrics,
        "gold_benchmark": gold_bench_metrics,
    }

    with open("results91.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}")
    print(f"{'calendar':10s} {'report48':>18s} {'guard':>18s} {'cagr diff':>10s} {'dd diff':>10s}")
    for r in rows:
        s, g = r["report48_standard"], r["gold_strength_guard"]
        print(f"{r['calendar_label']:10s} CAGR {s['cagr_pct']:6.2f}% DD {s['max_drawdown_pct']:6.1f}%   "
              f"CAGR {g['cagr_pct']:6.2f}% DD {g['max_drawdown_pct']:6.1f}%   "
              f"{r['cagr_diff_pp']:+6.2f}pp {r['dd_diff_pp']:+6.2f}pp")
    print(f"\nnifty 50   CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")
    print(f"gold alone CAGR {gold_bench_metrics['cagr_pct']:.2f}% / DD {gold_bench_metrics['max_drawdown_pct']:.1f}%")


if __name__ == "__main__":
    main()

"""
Midcap150 Momentum 10 — report 48's exact design (binary 200-day-EMA
regime filter, gold instead of cash) but with a 400-day EMA instead of
200. Report 46/47 already found that WIDENING the EMA span past 200 (up
to 250, the widest tested there) made things worse on both CAGR and
drawdown for the cash version — this asks whether a much wider span
(400, considerably beyond anything tested before) tells the same story
once gold replaces cash as the hedge asset.

Part two of this report holds the 400-day EMA design fixed and instead
varies HOW OFTEN the top-10 momentum picks themselves get refreshed
(the regime check itself is still continuous/daily, unchanged — only the
stock-selection cadence changes):
  - June/December (semi-annual) — this report's own Part 1 baseline,
    same cadence every other report in this project uses.
  - Yearly (June only) — half as many stock refreshes per year.
  - Every 4 months (Feb/Jun/Oct) — 50% more stock refreshes per year
    than semi-annual.
All three keep June as a shared rebalance month, so the schedules are
staggered variations of each other rather than unrelated calendars.

Same full-window/gold-reindex convention as reports 48/68/71 (the
already-fixed one — see reports 48-50/68-70's correction notes): the
momentum formula's own 252-day lookback runs over the FULL closes∩nifty
window, gold is reindexed onto that window via ffill/bfill for the hedge
calculation, and the real gold-benchmark row uses gold's own actual
trading index, not the ffilled one.
"""
import json

import pandas as pd

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes, fetch_gold_cleaned
from backtest32 import metrics_only
from backtest33 import select_top_original, build_index_generic
from backtest42 import build_index_regime_filtered_with_hedge

EMA_SPAN_BASE = 200
EMA_SPAN_WIDE = 400


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    gold = fetch_gold_cleaned()
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]
    gold_aligned = gold["Close"].reindex(common).ffill().bfill()
    real_gold_idx = common.intersection(gold["Close"].index)

    ema200 = nifty_close.ewm(span=EMA_SPAN_BASE, adjust=False).mean()
    ema400 = nifty_close.ewm(span=EMA_SPAN_WIDE, adjust=False).mean()

    rb_semiannual = rebalance_dates(closes.index, months=(6, 12))
    rb_yearly = rebalance_dates(closes.index, months=(6,))
    rb_4monthly = rebalance_dates(closes.index, months=(2, 6, 10))

    original_series, _ = build_index_generic(closes, rb_semiannual, select_top_original)

    # Part 1: EMA span, same (semi-annual) rebalance cadence throughout.
    ema200_series, _, _ = build_index_regime_filtered_with_hedge(
        closes, nifty_close, ema200, rb_semiannual, select_top_original, gold_aligned)
    ema400_series, ema400_sel, ema400_log = build_index_regime_filtered_with_hedge(
        closes, nifty_close, ema400, rb_semiannual, select_top_original, gold_aligned)

    # Part 2: EMA span fixed at 400, rebalance cadence varies.
    ema400_yearly_series, _, _ = build_index_regime_filtered_with_hedge(
        closes, nifty_close, ema400, rb_yearly, select_top_original, gold_aligned)
    ema400_4monthly_series, _, _ = build_index_regime_filtered_with_hedge(
        closes, nifty_close, ema400, rb_4monthly, select_top_original, gold_aligned)

    all_series = {
        "original": original_series, "ema200_gold": ema200_series, "ema400_gold": ema400_series,
        "ema400_gold_yearly": ema400_yearly_series, "ema400_gold_4monthly": ema400_4monthly_series,
    }
    common_idx = original_series.index
    for s in all_series.values():
        common_idx = common_idx.intersection(s.index)
    common_idx = common_idx.intersection(real_gold_idx)

    metrics = {k: metrics_only(v, common_idx) for k, v in all_series.items()}
    nifty_metrics = metrics_only(nifty_close, common_idx)
    gold_bench_metrics = metrics_only(gold["Close"], common_idx.intersection(real_gold_idx))

    def sample(sel):
        return sel[:3] + sel[-3:] if len(sel) > 6 else sel

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "ema_span_base": EMA_SPAN_BASE, "ema_span_wide": EMA_SPAN_WIDE,
        "num_rebalances": {"semiannual": len(rb_semiannual), "yearly": len(rb_yearly), "4monthly": len(rb_4monthly)},
        "original": metrics["original"],
        "ema200_gold": metrics["ema200_gold"],
        "ema400_gold": {**metrics["ema400_gold"], "selections_sample": sample(ema400_sel)},
        "ema400_gold_yearly": metrics["ema400_gold_yearly"],
        "ema400_gold_4monthly": metrics["ema400_gold_4monthly"],
        "nifty": nifty_metrics,
        "gold_benchmark": gold_bench_metrics,
    }

    with open("results75.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}")
    print(f"no filter                CAGR {metrics['original']['cagr_pct']:.2f}% / DD {metrics['original']['max_drawdown_pct']:.1f}%")
    print(f"200-EMA + gold (semi)    CAGR {metrics['ema200_gold']['cagr_pct']:.2f}% / DD {metrics['ema200_gold']['max_drawdown_pct']:.1f}%")
    print(f"400-EMA + gold (semi)    CAGR {metrics['ema400_gold']['cagr_pct']:.2f}% / DD {metrics['ema400_gold']['max_drawdown_pct']:.1f}%")
    print(f"400-EMA + gold (yearly)  CAGR {metrics['ema400_gold_yearly']['cagr_pct']:.2f}% / DD {metrics['ema400_gold_yearly']['max_drawdown_pct']:.1f}%")
    print(f"400-EMA + gold (4-month) CAGR {metrics['ema400_gold_4monthly']['cagr_pct']:.2f}% / DD {metrics['ema400_gold_4monthly']['max_drawdown_pct']:.1f}%")
    print(f"nifty 50                 CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")
    print(f"gold alone               CAGR {gold_bench_metrics['cagr_pct']:.2f}% / DD {gold_bench_metrics['max_drawdown_pct']:.1f}%")


if __name__ == "__main__":
    main()

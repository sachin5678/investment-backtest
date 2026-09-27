"""
Midcap150 Momentum 10 — the same core-satellite + full-gold-switch design
as report 71, but with an even 50/50 split instead of 70/30: 50% invested
in the top-10 momentum portfolio and 50% in gold AT ALL TIMES while
NIFTY 50 is above its own 200-day EMA, and a full 100% flight to gold
the moment it closes below.

Same mechanism as report 71 (build_index_core_satellite in backtest42.py),
same immediate-switch 200-EMA signal, same GOLDBEES.NS gold ETF, same
full 2008-2026 window — only the split ratio changes. Report 71's 70/30
numbers are quoted here (not recomputed) for a direct three-way
comparison against "no filter."
"""
import json

import pandas as pd

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes, fetch_gold_cleaned
from backtest32 import metrics_only
from backtest33 import select_top_original, build_index_generic
from backtest42 import build_index_core_satellite, EMA_SPAN
from backtest71 import gold_blocks_from_log

ON_MOMENTUM_WEIGHT = 0.50
ON_HEDGE_WEIGHT = 0.50


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    gold = fetch_gold_cleaned()
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]
    gold_close_aligned = gold["Close"].reindex(common).ffill().bfill()
    ema = nifty_close.ewm(span=EMA_SPAN, adjust=False).mean()

    rbdates = rebalance_dates(closes.index, months=(6, 12))

    original_series, _ = build_index_generic(closes, rbdates, select_top_original)
    combo_series, combo_sel, combo_log = build_index_core_satellite(
        closes, nifty_close, ema, rbdates, select_top_original, gold_close_aligned,
        on_momentum_weight=ON_MOMENTUM_WEIGHT, on_hedge_weight=ON_HEDGE_WEIGHT)

    common_idx = original_series.index.intersection(combo_series.index)
    original_metrics = metrics_only(original_series, common_idx)
    combo_metrics = metrics_only(combo_series, common_idx)
    nifty_metrics = metrics_only(nifty_close.loc[common_idx], common_idx)
    real_gold_idx = common_idx.intersection(gold["Close"].index)
    gold_bench_metrics = metrics_only(gold["Close"], real_gold_idx)

    gold_blocks, pct_gold = gold_blocks_from_log(combo_log)
    num_reentries = sum(1 for s in combo_sel if s["trigger"] == "regime_reentry")
    num_scheduled = sum(1 for s in combo_sel if s["trigger"] == "scheduled_rebalance")

    def sample(sel):
        return sel[:3] + sel[-3:] if len(sel) > 6 else sel

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "ema_span": EMA_SPAN,
        "on_momentum_weight_pct": ON_MOMENTUM_WEIGHT * 100,
        "on_hedge_weight_pct": ON_HEDGE_WEIGHT * 100,
        "pct_time_full_gold": round(pct_gold, 1),
        "num_regime_reentries": num_reentries,
        "num_scheduled_rebalances": num_scheduled,
        "gold_periods": gold_blocks[:8],
        "original": original_metrics,
        "combo": {**combo_metrics, "selections_sample": sample(combo_sel)},
        "nifty": nifty_metrics,
        "gold_benchmark": gold_bench_metrics,
    }

    with open("results71.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}")
    print(f"no filter (100% momentum always)          CAGR {original_metrics['cagr_pct']:.2f}% / DD {original_metrics['max_drawdown_pct']:.1f}%")
    print(f"50/50 core-satellite + full-gold switch    CAGR {combo_metrics['cagr_pct']:.2f}% / DD {combo_metrics['max_drawdown_pct']:.1f}%")
    print(f"nifty 50 benchmark                         CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")
    print(f"gold (GOLDBEES.NS) alone                    CAGR {gold_bench_metrics['cagr_pct']:.2f}% / DD {gold_bench_metrics['max_drawdown_pct']:.1f}%")
    print(f"time in full gold: {pct_gold:.1f}%  |  regime re-entries: {num_reentries}  |  scheduled rebalances hit: {num_scheduled}")
    if gold_blocks:
        print("longest full-gold periods:")
        for b in gold_blocks[:5]:
            print(f"  {b['start']} -> {b['end']}  ({b['days']}d)")


if __name__ == "__main__":
    main()

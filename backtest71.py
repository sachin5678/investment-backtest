"""
Midcap150 Momentum 10 — a genuinely new combined strategy: 70% invested
in the top-10 momentum portfolio and 30% in gold AT ALL TIMES (a
permanent core-satellite split, not a cash/invested switch), and the
moment NIFTY 50 closes below its own 200-day EMA, sell EVERYTHING into
100% gold — not just topping up the existing 30% sleeve, a full flight
to gold — until NIFTY 50 closes back above its 200-EMA, at which point
re-enter at the same 70/30 split with a freshly recomputed top-10.

This is compared against:
  - "No filter" — the original, always-100%-momentum strategy.
  - "Strategy A" — report 68's own combination (base formula + smooth
    exposure ramp + gold hedge), quoted here for reference, not
    recomputed, since it's already exactly the reports-1-through-4
    combination the user asked to confirm.
  - NIFTY 50 and gold (GOLDBEES.NS) on their own.

Same 200-day EMA signal, immediate switch (no confirmation delay, no
wider span, no breadth check) as report 42; same GOLDBEES.NS gold ETF as
reports 48/68 (real history from 2009-01-02, not "mid-2010" — see the
correction note in reports 48-50/68-70).
"""
import json

import pandas as pd

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes, fetch_gold_cleaned
from backtest32 import metrics_only
from backtest33 import select_top_original, build_index_generic
from backtest42 import build_index_core_satellite, EMA_SPAN

ON_MOMENTUM_WEIGHT = 0.70
ON_HEDGE_WEIGHT = 0.30
MIN_BLOCK_DAYS = 10


def gold_blocks_from_log(state_log, min_days=MIN_BLOCK_DAYS):
    if not state_log:
        return [], 0.0
    idx = pd.DatetimeIndex([d for d, _ in state_log])
    states = pd.Series([s for _, s in state_log], index=idx)
    pct_gold = float((states == "full_gold").mean() * 100)

    block_id = (states != states.shift()).cumsum()
    blocks = []
    for _, grp in states.groupby(block_id):
        if grp.iloc[0] != "full_gold":
            continue
        blocks.append({"start": grp.index[0].strftime("%Y-%m-%d"),
                        "end": grp.index[-1].strftime("%Y-%m-%d"),
                        "days": int(len(grp))})
    blocks = [b for b in blocks if b["days"] >= min_days]
    blocks.sort(key=lambda b: b["days"], reverse=True)
    return blocks, pct_gold


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

    with open("results70.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}")
    print(f"no filter (100% momentum always)          CAGR {original_metrics['cagr_pct']:.2f}% / DD {original_metrics['max_drawdown_pct']:.1f}%")
    print(f"70/30 core-satellite + full-gold switch    CAGR {combo_metrics['cagr_pct']:.2f}% / DD {combo_metrics['max_drawdown_pct']:.1f}%")
    print(f"nifty 50 benchmark                         CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")
    print(f"gold (GOLDBEES.NS) alone                    CAGR {gold_bench_metrics['cagr_pct']:.2f}% / DD {gold_bench_metrics['max_drawdown_pct']:.1f}%")
    print(f"time in full gold: {pct_gold:.1f}%  |  regime re-entries: {num_reentries}  |  scheduled rebalances hit: {num_scheduled}")
    if gold_blocks:
        print("longest full-gold periods:")
        for b in gold_blocks[:5]:
            print(f"  {b['start']} -> {b['end']}  ({b['days']}d)")


if __name__ == "__main__":
    main()

"""
Midcap150 Momentum — report 48's exact design (200-day EMA regime filter,
gold instead of cash) replicated at two different basket sizes either
side of the top-10 hero design: top-5 (more concentrated) and top-15
(a bit broader). Report 73 already found that going much wider (top-50)
loses on BOTH CAGR and drawdown against top-10, with no filter at all —
this asks a narrower, more practically relevant question: does the
gold-hedged hero design itself get better or worse with a slightly
smaller or slightly larger basket, close enough to top-10 that either
could plausibly be an improvement rather than a clear break from the
formula's own "buy the strongest names" premise.

Same continuous/daily 200-EMA regime check and semi-annual (June/
December) rebalance cadence as report 48 throughout — only the number of
stocks held changes between the three variants. Same full-window/gold-
reindex convention as reports 48/68/71/76/77.
"""
import json

import pandas as pd

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes, fetch_gold_cleaned
from backtest32 import metrics_only
from backtest33 import select_top_original, build_index_generic
from backtest42 import build_index_regime_filtered_with_hedge, EMA_SPAN

TOP_N_VARIANTS = {"top5": 5, "top10": 10, "top15": 15}


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
    rbdates = rebalance_dates(closes.index, months=(6, 12))

    original_by_n = {}
    filtered_by_n = {}
    selections_by_n = {}
    for label, n in TOP_N_VARIANTS.items():
        select_fn = lambda c, t_idx, n=n: select_top_original(c, t_idx, top_n=n)
        orig_series, _ = build_index_generic(closes, rbdates, select_fn)
        filt_series, sel, _ = build_index_regime_filtered_with_hedge(
            closes, nifty_close, ema200, rbdates, select_fn, gold_aligned)
        original_by_n[label] = orig_series
        filtered_by_n[label] = filt_series
        selections_by_n[label] = sel

    common_idx = None
    for s in list(original_by_n.values()) + list(filtered_by_n.values()):
        common_idx = s.index if common_idx is None else common_idx.intersection(s.index)
    common_idx = common_idx.intersection(real_gold_idx)

    original_metrics = {label: metrics_only(s, common_idx) for label, s in original_by_n.items()}
    filtered_metrics = {label: metrics_only(s, common_idx) for label, s in filtered_by_n.items()}
    nifty_metrics = metrics_only(nifty_close, common_idx)
    gold_bench_metrics = metrics_only(gold["Close"], common_idx.intersection(real_gold_idx))

    def sample(sel):
        return sel[:3] + sel[-3:] if len(sel) > 6 else sel

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "ema_span": EMA_SPAN, "top_n_variants": TOP_N_VARIANTS,
        "original_top5": original_metrics["top5"], "original_top10": original_metrics["top10"], "original_top15": original_metrics["top15"],
        "filtered_top5": {**filtered_metrics["top5"], "selections_sample": sample(selections_by_n["top5"])},
        "filtered_top10": {**filtered_metrics["top10"], "selections_sample": sample(selections_by_n["top10"])},
        "filtered_top15": {**filtered_metrics["top15"], "selections_sample": sample(selections_by_n["top15"])},
        "nifty": nifty_metrics,
        "gold_benchmark": gold_bench_metrics,
    }

    with open("results77.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}")
    for label, n in TOP_N_VARIANTS.items():
        om, fm = original_metrics[label], filtered_metrics[label]
        print(f"top-{n:<2} no filter        CAGR {om['cagr_pct']:.2f}% / DD {om['max_drawdown_pct']:.1f}%")
        print(f"top-{n:<2} 200-EMA + gold   CAGR {fm['cagr_pct']:.2f}% / DD {fm['max_drawdown_pct']:.1f}%")
    print(f"nifty 50               CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")
    print(f"gold alone             CAGR {gold_bench_metrics['cagr_pct']:.2f}% / DD {gold_bench_metrics['max_drawdown_pct']:.1f}%")


if __name__ == "__main__":
    main()

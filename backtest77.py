"""
Midcap150 Momentum 10 — report 48's exact design (this project's best
CAGR/drawdown combination on Midcap150 so far: the 200-day EMA regime
filter with gold instead of cash), but rebalancing the top-10 momentum
picks every 4 months (Feb/Jun/Oct) instead of semi-annually (Jun/Dec).

Report 76 already found that a more frequent stock-selection refresh
shallowed the drawdown on a 400-day EMA design without beating its CAGR
— this asks the more important question: does that same benefit show up
on the ACTUAL hero design (200-day EMA), or was it specific to the
400-day EMA's own slower-reacting regime signal? A yearly cadence is
included too, for the same three-way comparison report 76 used.

Same continuous/daily 200-EMA regime check throughout — only the
stock-selection cadence changes between the three variants. Same full-
window/gold-reindex convention as reports 48/68/71/76.
"""
import json

import pandas as pd

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes, fetch_gold_cleaned
from backtest32 import metrics_only
from backtest33 import select_top_original, build_index_generic
from backtest42 import build_index_regime_filtered_with_hedge, EMA_SPAN

RB_LABELS = {"semiannual": (6, 12), "yearly": (6,), "4monthly": (2, 6, 10)}


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

    rb_dates = {k: rebalance_dates(closes.index, months=v) for k, v in RB_LABELS.items()}

    original_series, _ = build_index_generic(closes, rb_dates["semiannual"], select_top_original)

    series = {}
    selections = {}
    for label, rbdates in rb_dates.items():
        s, sel, _ = build_index_regime_filtered_with_hedge(
            closes, nifty_close, ema200, rbdates, select_top_original, gold_aligned)
        series[label] = s
        selections[label] = sel

    common_idx = original_series.index
    for s in series.values():
        common_idx = common_idx.intersection(s.index)
    common_idx = common_idx.intersection(real_gold_idx)

    original_metrics = metrics_only(original_series, common_idx)
    metrics = {k: metrics_only(v, common_idx) for k, v in series.items()}
    nifty_metrics = metrics_only(nifty_close, common_idx)
    gold_bench_metrics = metrics_only(gold["Close"], common_idx.intersection(real_gold_idx))

    def sample(sel):
        return sel[:3] + sel[-3:] if len(sel) > 6 else sel

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "ema_span": EMA_SPAN,
        "num_rebalances": {k: len(v) for k, v in rb_dates.items()},
        "original": original_metrics,
        "ema200_gold_semiannual": metrics["semiannual"],
        "ema200_gold_yearly": metrics["yearly"],
        "ema200_gold_4monthly": {**metrics["4monthly"], "selections_sample": sample(selections["4monthly"])},
        "nifty": nifty_metrics,
        "gold_benchmark": gold_bench_metrics,
    }

    with open("results76.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}")
    print(f"no filter                CAGR {original_metrics['cagr_pct']:.2f}% / DD {original_metrics['max_drawdown_pct']:.1f}%")
    print(f"200-EMA + gold (semi, report 48)  CAGR {metrics['semiannual']['cagr_pct']:.2f}% / DD {metrics['semiannual']['max_drawdown_pct']:.1f}%")
    print(f"200-EMA + gold (yearly)           CAGR {metrics['yearly']['cagr_pct']:.2f}% / DD {metrics['yearly']['max_drawdown_pct']:.1f}%")
    print(f"200-EMA + gold (every 4 months)   CAGR {metrics['4monthly']['cagr_pct']:.2f}% / DD {metrics['4monthly']['max_drawdown_pct']:.1f}%")
    print(f"nifty 50                 CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")
    print(f"gold alone               CAGR {gold_bench_metrics['cagr_pct']:.2f}% / DD {gold_bench_metrics['max_drawdown_pct']:.1f}%")


if __name__ == "__main__":
    main()

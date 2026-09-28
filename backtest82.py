"""
Midcap150 Momentum 10 — report 81's compounding-with-averaging design,
same mechanism (top up funded by trimming the OTHER 9 holdings, one
continuous compounding portfolio, single CAGR), but with wider triggers:
25% and 40% off peak-since-entry instead of 15%/30%.

Report 81 found 15%/30% averaging was roughly a CAGR wash (40.61% ->
40.64%) but made max drawdown meaningfully worse (-35.1% -> -37.2%),
because most 15% pullbacks in this dataset were pauses within a
continuing uptrend, not real breakdowns — so trimming winners to fund
the top-up was a net negative on the worst days. Wider triggers (25%/
40%) fire far less often, which should mean less trimming of winners
overall — this asks whether that makes the CAGR/drawdown trade-off
better, worse, or basically unchanged.

Recomputes 15%/30%, 25%/40%, and the no-averaging baseline all fresh
together (not quoted from report 81) so every variant shares the exact
same date window.
"""
import json
import sys

import numpy as np
import pandas as pd

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes
from backtest32 import metrics_only
from backtest33 import select_top_original, build_index_generic
from backtest81 import simulate_compounding_with_averaging

TRIGGER_SETS = {"15_30": (0.15, 0.30), "25_40": (0.25, 0.40)}


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]

    rbdates = rebalance_dates(closes.index, months=(6, 12))
    rbdates = [d for d in rbdates if closes.index.get_loc(d) >= 252]

    plain_series, _ = build_index_generic(closes, rbdates, select_top_original)

    variants = {}
    for label, (drop1, drop2) in TRIGGER_SETS.items():
        series, sel, counts = simulate_compounding_with_averaging(closes, rbdates, select_top_original, drop1, drop2)
        variants[label] = (series, sel, counts)

    common_idx = closes.index[closes.index >= rbdates[0]]
    for s, _, _ in variants.values():
        common_idx = common_idx.intersection(s.index)
    common_idx = common_idx.intersection(plain_series.index)

    plain_metrics = metrics_only(plain_series, common_idx)
    nifty_metrics = metrics_only(nifty_close.loc[common_idx.intersection(nifty_close.index)], common_idx)

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "num_rebalances": len(rbdates),
        "plain": plain_metrics,
        "nifty": nifty_metrics,
    }

    for label, (drop1, drop2) in TRIGGER_SETS.items():
        series, sel, counts = variants[label]
        m = metrics_only(series, common_idx)
        m["drop_1_pct"], m["drop_2_pct"] = drop1 * 100, drop2 * 100
        m["selections_sample"] = sel[:3] + sel[-3:] if len(sel) > 6 else sel
        m.update(counts)
        results[f"averaging_{label}"] = m

    with open("results81.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}, {len(rbdates)} rebalances")
    print(f"no averaging          CAGR {plain_metrics['cagr_pct']:.2f}% / DD {plain_metrics['max_drawdown_pct']:.1f}%")
    for label, (drop1, drop2) in TRIGGER_SETS.items():
        m = results[f"averaging_{label}"]
        print(f"averaging {drop1*100:.0f}%/{drop2*100:.0f}%   CAGR {m['cagr_pct']:.2f}% / DD {m['max_drawdown_pct']:.1f}% | "
              f"trigger1 {m['trigger_once']}/{m['total_positions']} ({m['trigger_once']/m['total_positions']*100:.1f}%), "
              f"trigger2 {m['trigger_twice']} ({m['trigger_twice']/m['total_positions']*100:.1f}%)")
    print(f"nifty 50               CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")


if __name__ == "__main__":
    main()

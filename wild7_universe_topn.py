"""Round 7 (mini traffic test of the round-1 logics on all universes).
The dip-buy override and overextended exit of round 1 are applied to
Midcap150 / Smallcap250 / NIFTY100, at basket sizes 5 / 10 / 15,
always on the same GEM (GOLDBEES) sleeve during risk-off days.

Every variant is compared against that universe+basket's plain
report-48 design and the plain no-filter momentum portfolio.
"""
import json

import numpy as np
import pandas as pd

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest15 import load_smallcap250_closes
from backtest45 import select_top_n100
from backtest44 import select_top_smallcap
from backtest13 import load_midcap150_closes, fetch_gold_cleaned
from backtest33 import select_top_original, build_index_generic
from backtest32 import metrics_only
from backtest42 import build_index_regime_filtered_with_hedge, EMA_SPAN

from dipbuy_experiment import build_with_dipbuy
from overextended_experiment import build as build_overextended

UNIVERSES = {
    "Midcap150": (load_midcap150_closes, select_top_original),
    "Smallcap250": (load_smallcap250_closes, select_top_smallcap),
    "Nifty100": (None, select_top_n100),
}


def load_nifty100_closes():
    from backtest10 import load_universe_closes
    from nifty100_symbols import NIFTY_100_SYMBOLS
    raw = load_universe_closes()
    tickers_present = [t for t in [s + ".NS" for s in NIFTY_100_SYMBOLS] if t in raw.columns]
    return raw[tickers_present]


def run_universe(name, closes, select_fn, gold_aligned, common_idx, results, topns, mode):
    nifty = fetch("^NSEI")
    common = closes.index.intersection(nifty.index)
    closes_u = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]
    gold_aligned_u = gold_aligned.reindex(common).ffill().bfill()
    ema = nifty_close.ewm(span=EMA_SPAN, adjust=False).mean()
    for top_n in topns:
        sel = (lambda cf, fn, n: (lambda closes, t: fn(closes, t, top_n=n)))(None, select_fn, top_n)
        rb = rebalance_dates(closes_u.index, months=(6, 12))
        original, _ = build_index_generic(closes_u, rb, sel)
        r48, _, _ = build_index_regime_filtered_with_hedge(closes_u, nifty_close, ema, rb, sel, gold_aligned_u)
        idx = original.index.intersection(r48.index)
        findings = {}
        if mode in ("dipbuy", "both"):
            for thr in (0.15,):
                s, _, _ = build_with_dipbuy(closes_u, nifty_close, ema, rb, sel, gold_aligned_u, thr)
                findings[f"dipbuy_{int(thr*100)}pct"] = s
        if mode in ("overextended", "both"):
            s, _, _ = build_overextended(closes_u, nifty_close, ema, rb, sel, gold_aligned_u, 0.15, 0.05)
            findings["overexit15_exit5"] = s
        print(f"\n{name} top-{top_n}:")
        m0 = metrics_only(original, idx.intersection(original.index))
        m = metrics_only(r48, idx.intersection(r48.index))
        print(f"  {'no filter':22s} CAGR {m0['cagr_pct']:.2f}% / DD {m0['max_drawdown_pct']:.1f}%")
        print(f"  {'report48 standard':22s} CAGR {m['cagr_pct']:.2f}% / DD {m['max_drawdown_pct']:.1f}%")
        results[f"{name}_top{top_n}_original"] = m0
        results[f"{name}_top{top_n}_report48"] = m
        common_idx2 = idx
        for fname, s in findings.items():
            common_idx2 = common_idx2.intersection(s.index)
            mm = metrics_only(s, s.index.intersection(idx))
            results[f"{name}_top{top_n}_{fname}"] = mm
            print(f"  {fname:22s} CAGR {mm['cagr_pct']:.2f}% / DD {mm['max_drawdown_pct']:.1f}%")


def main():
    gold = fetch_gold_cleaned()
    results = {}
    for name, (loader, select_fn) in UNIVERSES.items():
        try:
            raw = load_nifty100_closes() if loader is None else loader()
        except Exception as e:
            print(name, "load failed:", e)
            continue
        run_universe(name, raw, select_fn, gold["Close"], None, results, [5, 10, 15], "both")
    with open("results_find_universe.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nwrote results_find_universe.json")


if __name__ == "__main__":
    main()

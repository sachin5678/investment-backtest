"""Round 8: 'is gold even strong right now?' filter applied to
Smallcap250 and Nifty100 universes, top-5/10/15 baskets.
Risk-off (NIFTY < own 200EMA) switches to GOLDBEES only when
gold's trailing 6m return beats NIFTY's 6m return; otherwise
hold flat cash. Also a simpler variant that only checks whether
gold's own 6m return is positive.
"""
import json

import numpy as np
import pandas as pd

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL, load_universe_closes
from backtest15 import load_smallcap250_closes
from backtest45 import select_top_n100
from backtest44 import select_top_smallcap
from backtest13 import load_midcap150_closes, fetch_gold_cleaned
from backtest33 import select_top_original, build_index_generic
from backtest32 import metrics_only
from backtest42 import build_index_regime_filtered_with_hedge, EMA_SPAN
from nifty100_symbols import NIFTY_100_SYMBOLS

UNIVERSES = {
    "Midcap150": (load_midcap150_closes, select_top_original),
    "Smallcap250": (load_smallcap250_closes, select_top_smallcap),
    "Nifty100": (None, select_top_n100),
}


def load_nifty100_closes():
    raw = load_universe_closes()
    tickers_present = [t for t in [s + ".NS" for s in NIFTY_100_SYMBOLS] if t in raw.columns]
    return raw[tickers_present]


def main():
    gold = fetch_gold_cleaned()
    results = {}
    for name, (loader, select_fn) in UNIVERSES.items():
        closes = load_nifty100_closes() if loader is None else loader()
        nifty = fetch("^NSEI")
        common = closes.index.intersection(nifty.index)
        closes = closes.loc[common]
        nifty_close = nifty.loc[common, "Close"]
        gold_aligned = gold["Close"].reindex(common).ffill().bfill()
        ema = nifty_close.ewm(span=EMA_SPAN, adjust=False).mean()

        # gold's 6m return vs NIFTY's 6m return (both lagged, same day)
        g6 = gold_aligned.pct_change(126)
        n6 = nifty_close.pct_change(126)

        for top_n in (5, 10, 15):
            sel = (lambda fn, n: (lambda cf, t: fn(cf, t, top_n=n)))(select_fn, top_n)
            rb = rebalance_dates(closes.index, months=(6, 12))
            idx, _ = build_index_generic(closes, rb, sel)
            base = rets = idx.pct_change().fillna(0.0)
            gold_rets = gold_aligned.reindex(idx.index).ffill().pct_change().fillna(0.0)
            riskoff = (nifty_close < ema).reindex(idx.index).fillna(False)

            # H: gold strong relative to NIFTY, else cash
            gold_strong = (g6 > n6).reindex(idx.index).fillna(False).astype(float)
            H_ret = base.where(~riskoff, gold_strong * gold_rets + (1 - gold_strong) * 0.0)
            # simpler: gold's own 6m return must be positive, else cash
            g6_pos = (g6 > 0).reindex(idx.index).fillna(False).astype(float)
            G_ret = base.where(~riskoff, g6_pos * gold_rets + (1 - g6_pos) * 0.0)
            # G + H combined: gold must be both (relative and absolute)
            both_strong = ((g6 > n6) & (g6 > 0)).reindex(idx.index).fillna(False).astype(float)
            R_ret = base.where(~riskoff, both_strong * gold_rets)

            # plain report-48 gold (full flight to hedge)
            r48_ret = base.where(~riskoff, gold_rets)

            for tag, ret in [("r48_standard", r48_ret), ("H_gold6m_vs_nifty", H_ret), ("G_gold6m_positive", G_ret), ("GOLD_AND_STRONG", R_ret)]:
                s = (1 + ret).cumprod() * 100
                m = metrics_only(s, s.index)
                results[f"{name}_top{top_n}_{tag}"] = m
                print(f"{name:12s} top{top_n:<3d} {tag:26s} CAGR {m['cagr_pct']:.2f}% / DD {m['max_drawdown_pct']:.1f}%")

    with open("results_find_goldguard.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nwrote results_find_goldguard.json")


if __name__ == "__main__":
    main()

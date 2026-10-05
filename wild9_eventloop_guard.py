"""Round 9: gold-strength guard, but with the REAL event-loop state
from build_index_regime_filtered_with_hedge (not the close-to-close
mask shortcut used in wild8). The standard r48 series is exactly the
built-in event loop; the guard variants only modify what the same
state machine HOLDS during its own "cash" (risk-off) days — gold
when strong, flat cash otherwise.
"""
import json

import numpy as np
import pandas as pd

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL, load_universe_closes
from backtest15 import load_smallcap250_closes
from backtest45 import select_top_n100
from backtest44 import select_top_smallcap
from backtest13 import load_midcap150_closes, fetch_gold_cleaned
from backtest33 import select_top_original
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


def with_state_panel(r48, state_log, nifty, ema, gold_aligned):
    """Returns a daily 'cash' boolean of event-loop 'cash' days and the
    original state log; alignment by mapping each state_log date to 'cash'.
    Values equal to the builtin state across days."""
    states = pd.Series([s == "cash" for _, s in state_log],
                       index=pd.DatetimeIndex([d for d, _ in state_log]))
    is_cash = states.reindex(r48.index).ffill().fillna(False)
    return is_cash


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

        g6 = gold_aligned.pct_change(126)
        n6 = nifty_close.pct_change(126)

        for top_n in (5, 10, 15):
            sel = (lambda fn, n: (lambda cf, t: fn(cf, t, top_n=n)))(select_fn, top_n)
            rb = rebalance_dates(closes.index, months=(6, 12))

            r48, _, r48_log = build_index_regime_filtered_with_hedge(closes, nifty_close, ema, rb, sel, gold_aligned)

            orig_idx = r48.index
            r48w = r48.loc[orig_idx]
            is_cash = with_state_panel(r48w, r48_log, nifty_close, ema, gold_aligned)

            # Base return series is r48's OWN realized returns -- the real
            # event loop's output, not an approximation -- so on invested
            # days `guarded` is byte-for-byte identical to report48_standard.
            # The guard only ever overrides a CASH day's return below.
            rets = r48w.pct_change().fillna(0.0)
            gold_rets = gold_aligned.reindex(r48w.index).ffill().pct_change().fillna(0.0)

            strong1 = (g6 > n6).reindex(r48w.index).fillna(False)
            strong2 = (g6 > 0).reindex(r48w.index).fillna(False)
            strong_both = strong1 & strong2

            def build_guarded(strong_mask):
                """During cash days: hold gold iff strong else flat cash
                (0%) -- report 48 itself always holds gold on a cash day,
                so the "strong" branch just reproduces rets unchanged and
                only the "weak" branch actually changes anything. During
                invested days: r48's own real returns, untouched. The
                state machine itself (when it flips cash<->invested) is
                unchanged from report 48."""
                guarded = rets.copy()
                cash_gold = is_cash & strong_mask.reindex(rets.index).fillna(False)
                cash_flat = is_cash & (~strong_mask.reindex(rets.index).fillna(False))
                guarded[cash_gold] = gold_rets[cash_gold]
                guarded[cash_flat] = 0.0
                return (1 + guarded).cumprod() * 100

            m48 = metrics_only(r48w, orig_idx)
            print(f"{name} top{top_n}: report48_std CAGR {m48['cagr_pct']:.2f}% / DD {m48['max_drawdown_pct']:.1f}%")
            results[f"{name}_top{top_n}_report48_standard"] = m48

            for tag, sm in [("GOLD_STRONG_vs_nifty", strong1), ("GOLD_6m_positive", strong2), ("GOLD_AND_BOTH", strong_both)]:
                s = build_guarded(sm)
                m = metrics_only(s, orig_idx)
                results[f"{name}_top{top_n}_{tag.lower()}"] = m
                print(f"  {tag:26s} CAGR {m['cagr_pct']:.2f}% / DD {m['max_drawdown_pct']:.1f}%")

    with open("results_find_goldguard2.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nwrote results_find_goldguard2.json")


if __name__ == "__main__":
    main()

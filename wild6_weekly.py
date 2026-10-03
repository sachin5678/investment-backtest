"""Round 6: report-48 ideas, but with the signal computed on WEEKLY
bars — when NIFTY 50 closes below its weekly 50, 100, or 200 EMA,
switch the sleeve to gold (full) or a 50/50 blend (the top
full-set winner on daily bars). Also runs the strictly-below-all-
three weekly EMAs combine and the plain daily-200 reference.
"""
import json

import numpy as np
import pandas as pd

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes, fetch_gold_cleaned
from backtest32 import metrics_only
from backtest33 import select_top_original, build_index_generic
from backtest42 import build_index_regime_filtered_with_hedge

from wild_experiment import run as run_wild


def weekly_flag(daily_close, ema_span_weeks, below=False):
    weekly = daily_close.resample("W-FRI").last().dropna()
    flag = weekly > weekly.ewm(span=ema_span_weeks, adjust=False).mean()
    # daily signal that holds constant through the week
    d = flag.reindex(daily_close.index, method="nearest").fillna(method="ffill").fillna(False)
    return d.reindex(daily_close.index).ffill().fillna(False)


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    gold = fetch_gold_cleaned()
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]
    gold_aligned = gold["Close"].reindex(common).ffill().bfill()
    rbdates = rebalance_dates(closes.index, months=(6, 12))

    rets_idx = None
    original_series, _ = build_index_generic(closes, rbdates, select_top_original)
    rets = original_series.pct_change().fillna(0.0)
    gold_rets = gold_aligned.reindex(original_series.index).ffill().pct_change().fillna(0.0)

    variants = {}
    labels = {}

    # report-48 reference (daily 200): stock when above its EMA, else gold
    emad = nifty_close.ewm(span=200, adjust=False).mean()
    riskoff_d = (nifty_close < emad).reindex(original_series.index).fillna(False)
    r48 = rets.where(~riskoff_d, gold_rets)
    variants["report48_daily200"] = (1 + r48).cumprod() * 100

    # best from round-5 sweep: full flight replaced by 50/50 half-blend,
    # daily EMA 200 — the in-table winner bucks up at span200 c1 gold half
    r48h = rets.where(~riskoff_d, 0.5 * rets + 0.5 * gold_rets)
    variants["best_daily200_gold_half"] = (1 + r48h).cumprod() * 100

    for wk in (50, 100, 200):
        flag = weekly_flag(nifty_close, wk)
        riskoff_w = (~flag).reindex(original_series.index).fillna(False)
        # full hedge when below weekly EMA
        variants[f"weeklyEMA{wk}_full_gold"] = (1 + rets.where(~riskoff_w, gold_rets)).cumprod() * 100
        # half blend version (the sweep's own most stable variant)
        variants[f"weeklyEMA{wk}_gold_half"] = (1 + rets.where(~riskoff_w, 0.5 * rets + 0.5 * gold_rets)).cumprod() * 100

    # combined: only below ALL THREE weekly EMAs triggers the same full gold; otherwise stocks.
    f50 = weekly_flag(nifty_close, 50)
    f100 = weekly_flag(nifty_close, 100)
    f200 = weekly_flag(nifty_close, 200)
    all_below = (~f50) & (~f100) & (~f200)
    all_below = all_below.reindex(original_series.index).fillna(False)
    variants["weekly_all3_below_full_gold"] = (1 + rets.where(~all_below, gold_rets)).cumprod() * 100
    variants["weekly_all3_below_gold_half"] = (1 + rets.where(~all_below, 0.5 * rets + 0.5 * gold_rets)).cumprod() * 100

    # combined: ANY below triggers gold — most conservative
    any_below = (~f50) | (~f100) | (~f200)
    any_below = any_below.reindex(original_series.index).fillna(False)
    variants["weekly_any_full_gold"] = (1 + rets.where(~any_below, gold_rets)).cumprod() * 100
    variants["weekly_any_gold_half"] = (1 + rets.where(~any_below, 0.5 * rets + 0.5 * gold_rets)).cumprod() * 100

    print(f"window {original_series.index[0].date()} -> {original_series.index[-1].date()}\n")
    for name, s in variants.items():
        m = metrics_only(s, s.index)
        print(f"{name:34s} CAGR {m['cagr_pct']:.2f}% / DD {m['max_drawdown_pct']:.1f}%")
    m = metrics_only(original_series, original_series.index)
    print(f"{'no filter':34s} CAGR {m['cagr_pct']:.2f}% / DD {m['max_drawdown_pct']:.1f}%")

    out = {}
    for name, s in variants.items():
        out[name] = metrics_only(s, s.index)
    out["original_no_filter"] = metrics_only(original_series, original_series.index)
    with open("results_find_weekly.json", "w") as f:
        json.dump(out, f, indent=2)
    print("\nwrote results_find_weekly.json")


if __name__ == "__main__":
    main()

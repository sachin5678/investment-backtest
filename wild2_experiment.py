"""Wild round 2 on report 48 (Midcap150 Momentum 10, NIFTY 200-EMA
risk-off, gold sleeve). Each variant defines a return series directly
from the momentum index / gold / cash daily returns, plus the full
regime-switch rules evaluated day by day.
"""
import json

import numpy as np
import pandas as pd

from backtest10 import rebalance_dates, fetch
from backtest13 import load_midcap150_closes, fetch_gold_cleaned
from backtest32 import metrics_only
from backtest33 import select_top_original, build_index_generic
from backtest42 import build_index_regime_filtered_with_hedge, EMA_SPAN


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    gold = fetch_gold_cleaned()
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]
    gold_aligned = gold["Close"].reindex(common).ffill().bfill()
    ema = nifty_close.ewm(span=EMA_SPAN, adjust=False).mean()
    rbdates = rebalance_dates(closes.index, months=(6, 12))

    original_series, _ = build_index_generic(closes, rbdates, select_top_original)
    gold_series, _, _ = build_index_regime_filtered_with_hedge(
        closes, nifty_close, ema, rbdates, select_top_original, gold_aligned)

    rets = original_series.pct_change().fillna(0.0)
    gold_rets = gold_aligned.reindex(original_series.index).ffill().pct_change().fillna(0.0)
    risk_off = (nifty_close < ema).reindex(original_series.index).fillna(False)

    variants = {}

    # A. Half-gold blend instead of full flight to gold during risk-off
    a_ret = rets.where(~risk_off, 0.5 * rets + 0.5 * gold_rets)
    variants["A. risk-off -> 50/50 stocks+gold"] = (1 + a_ret).cumprod() * 100.0

    # B. Three-state EMA alignment: full stocks when 50>100>200 all rising,
    #    full gold when everything inverted, 50/50 in between
    ema50 = nifty_close.ewm(span=50, adjust=False).mean()
    ema100 = nifty_close.ewm(span=100, adjust=False).mean()
    align_on = (nifty_close > ema50) & (ema50 > ema100) & (ema100 > ema)
    align_off = (nifty_close < ema50) & (ema50 < ema100) & (ema100 < ema)
    align_on = align_on.reindex(original_series.index, fill_value=False)
    align_off = align_off.reindex(original_series.index, fill_value=False)
    b_ret = rets.where(align_on, 0.5 * rets + 0.5 * gold_rets).where(~align_off, gold_rets)
    variants["B. EMA alignment 3-state"] = (1 + b_ret).cumprod() * 100.0

    # F. NIFTY 20d return hysteresis: gold when last 20d return < -5%,
    #    stocks when back above 0%
    ni_ret20 = nifty_close.pct_change(20).reindex(original_series.index).ffill()
    state = []
    off = False
    for v in ni_ret20:
        if off and v > 0:
            off = False
        elif (not off) and pd.notna(v) and v < -0.05:
            off = True
        state.append(off)
    f_mask = pd.Series(state, index=original_series.index)
    f_ret = rets.where(~f_mask, gold_rets)
    variants["F. NIFTY 20d<-5% gold, >0% back"] = (1 + f_ret).cumprod() * 100.0

    # G. Equity-curve trailing stop on the strategy's own NAV: gold when
    #    the momentum index NAV falls >12% below its own 252d high; back
    #    when NAV recovers to within 3%
    own_high = original_series.rolling(252, min_periods=1).max()
    nav_dd = original_series / own_high - 1
    off = False
    state = []
    for v in nav_dd:
        if off and v > -0.03:
            off = False
        elif (not off) and pd.notna(v) and v < -0.12:
            off = True
        state.append(off)
    g_mask = pd.Series(state, index=original_series.index)
    g_ret = rets.where(~g_mask, gold_rets)
    variants["G. own-NAV -12%->gold, -3%->back"] = (1 + g_ret).cumprod() * 100.0

    # E. TAA: at each June/December rebalance pick the sleeve (momentum,
    #    gold, cash) with the best trailing 12m return, hold it until the
    #    next rebalance
    cash_ret = pd.Series(0.0, index=original_series.index)
    m_ret12 = original_series.pct_change(252)
    g_ret12 = gold_aligned.reindex(original_series.index).ffill().pct_change(252)
    c_ret12 = cash_ret.rolling(252).sum() * 0.0
    chosen = pd.Series(index=original_series.index, dtype=object)
    last = "cash"
    for d in original_series.index:
        if d in set(rbdates):
            cands = {"momentum": m_ret12.get(d, np.nan), "gold": g_ret12.get(d, np.nan), "cash": 0.0}
            valid = {k: v for k, v in cands.items() if pd.notna(v)}
            last = max(valid, key=valid.get) if valid else "cash"
        chosen.loc[d] = last
    e_ret = pd.Series(0.0, index=original_series.index)
    e_ret[chosen == "momentum"] = rets[chosen == "momentum"]
    e_ret[chosen == "gold"] = gold_rets[chosen == "gold"]
    variants["E. TAA best-of-3 trailing 12m"] = (1 + e_ret).cumprod() * 100.0

    # C. Own-basket breadth: gold when fewer than 40% of the current
    #    momentum basket is above its own 50-EMA; stocks when it recovers
    #    above 50% (uses currently-sold basket during gold via candidate
    #    recompute-style semantics — here approximated with the
    #    fully-invested original basket constituents from the latest
    #    semi-annual selection)
    stock_ema50 = closes.ewm(span=50, adjust=False).mean()
    # rebuild current holdings cheaply: reuse the original index's
    # semi-annual selection via select_top_original at rb-dates
    breadth = pd.Series(np.nan, index=original_series.index)
    current = None
    for i, d in enumerate(closes.index):
        if d in set(rbdates):
            current = select_top_original(closes, i)
        if current:
            p = closes.iloc[i]
            e = stock_ema50.iloc[i]
            frac = ((p[current] > e[current]) & p[current].notna() & e[current].notna()).sum() / len(current)
            breadth.loc[d] = frac
    b_state = []
    off = False
    for v in breadth:
        if off and pd.notna(v) and v > 0.50:
            off = False
        elif (not off) and pd.notna(v) and v < 0.40:
            off = True
        b_state.append(off)
    c_mask = pd.Series(b_state, index=original_series.index)
    c_ret = rets.where(~c_mask, gold_rets)
    variants["C. basket breadth<40% -> gold"] = (1 + c_ret).cumprod() * 100.0

    print(f"window {original_series.index[0].date()} -> {original_series.index[-1].date()}\n")
    for name, s in variants.items():
        m = metrics_only(s, s.index)
        print(f"{name:40s} CAGR {m['cagr_pct']:.2f}% / DD {m['max_drawdown_pct']:.1f}%")
    m = metrics_only(gold_series, gold_series.index)
    print(f"{'report 48 (200EMA + gold, standard)':40s} CAGR {m['cagr_pct']:.2f}% / DD {m['max_drawdown_pct']:.1f}%")
    m = metrics_only(original_series, original_series.index)
    print(f"{'no filter':40s} CAGR {m['cagr_pct']:.2f}% / DD {m['max_drawdown_pct']:.1f}%")

    # persist for the website (results JSON convention)
    out = {}
    for name, s in variants.items():
        out[name.split(". ")[0] + "_" + name.split(". ", 1)[1].replace(" ", "_").replace("/", "_").replace("%", "pct").replace(">", "gt").replace("<", "lt").replace(",", "").replace("->", "_to_").replace("-", "_")[:40]] = metrics_only(s, s.index)
    out["report48_200ema_gold"] = metrics_only(gold_series, gold_series.index)
    out["original_no_filter"] = metrics_only(original_series, original_series.index)
    with open("results_find_wild2.json", "w") as f:
        json.dump(out, f, indent=2)
    print("\nwrote results_find_wild2.json")


if __name__ == "__main__":
    main()

"""Round 4: report-48-style Midcap150 Momentum 10 through monthly,
quarterly, semi-annual rebalance cadences, under the best regime
rules found so far (report 48 standard, B 3-state EMA alignment,
C basket-breadth gate, A 50/50 gold blend, G/H nested gold filters).
Also the same cadences for the ETF top-1 rotation + own-EMA-guard
(the one round-3 variant worth salvaging).
"""
import json

import numpy as np
import pandas as pd
import yfinance as yf

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes, fetch_gold_cleaned
from backtest32 import metrics_only
from backtest33 import select_top_original, build_index_generic
from backtest42 import build_index_regime_filtered_with_hedge, EMA_SPAN


def regime_series(closes, nifty_close, gold_aligned, rbdates, mode):
    """Returns a daily weight w ∈ {0, 0.5, 1} for the momentum sleeve
    (rest is gold). mode in {"report48", "align3", "breadth40", "half"}
    """
    ema200 = nifty_close.ewm(span=EMA_SPAN, adjust=False).mean()
    ema50 = nifty_close.ewm(span=50, adjust=False).mean()
    ema100 = nifty_close.ewm(span=100, adjust=False).mean()
    nc = nifty_close
    w = pd.Series(1.0, index=closes.index)
    if mode == "report48":
        w = (nc >= ema200).astype(float)
    elif mode == "half":
        w = pd.Series(0.5, index=closes.index)
        w[nc >= ema200] = 1.0
    elif mode == "align3":
        full = (nc > ema50) & (ema50 > ema100) & (ema100 > ema200)
        none_ = (nc < ema50) & (ema50 < ema100) & (ema100 < ema200)
        w = pd.Series(0.5, index=closes.index)
        w[full] = 1.0
        w[none_] = 0.0
    elif mode == "breadth40":
        stock_ema50 = closes.ewm(span=50, adjust=False).mean()
        state = w.copy()
        off = False
        cur = None
        for i, d in enumerate(closes.index):
            if d in set(rbdates):
                cur = select_top_original(closes, i)
            if cur:
                p = closes.iloc[i]; e = stock_ema50.iloc[i]
                frac = ((p[cur] > e[cur]) & p[cur].notna() & e[cur].notna()).sum() / len(cur)
            else:
                frac = np.nan
            if off and pd.notna(frac) and frac > 0.5:
                off = False
            elif (not off) and pd.notna(frac) and frac < 0.4:
                off = True
            # below NIFTY 200-EMA always taper to gold
            if nc.iloc[i] < ema200.iloc[i]:
                off = True
            if off:
                state.iloc[i] = 0.0
            else:
                state.iloc[i] = 1.0
        w = state
    return w


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    gold = fetch_gold_cleaned()
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]
    gold_aligned = gold["Close"].reindex(common).ffill().bfill()

    print("=== Midcap150 Momentum 10, regime weights by mode × cadence ===")
    results = {}
    for mode in ["report48", "align3", "breadth40", "half"]:
        row = []
        for months in [(3, 6, 9, 12), (4, 8, 12), (6, 12)]:
            rb = rebalance_dates(closes.index, months=months)
            w = regime_series(closes, nifty_close, gold_aligned, rb, mode)
            idx, _ = build_index_generic(closes, rb, select_top_original)
            w = w.reindex(idx.index).ffill().fillna(1.0)
            rets = idx.pct_change().fillna(0.0)
            gres = gold_aligned.reindex(idx.index).ffill().pct_change().fillna(0.0)
            blended = w.shift(1).fillna(w.iloc[0]) * rets + (1 - w.shift(1).fillna(w.iloc[0])) * gres
            s = (1 + blended).cumprod() * 100
            results[f"{mode}_m{'_'.join(map(str, months))}"] = s
            m = metrics_only(s, s.index)
            row.append(f"  m={months}: CAGR {m['cagr_pct']:.2f}% / DD {m['max_drawdown_pct']:.1f}%")
        print(f"{mode:12s}")
        print("\n".join(row))

    # ETF: top-1 12m rotation with own-200EMA gold guard, three cadences
    print("\n=== ETF top-1 12m rotation + own-200EMA guard ===")
    EQUITY_ETF = ["NIFTYBEES.NS", "JUNIORBEES.NS", "MOM100.NS", "MON100.NS"]
    frames = []
    for t in EQUITY_ETF + ["GOLDBEES.NS"]:
        df = yf.download(t, period="max", auto_adjust=False, progress=False)
        df.columns = df.columns.droplevel(1) if isinstance(df.columns, pd.MultiIndex) else df.columns
        frames.append(df["Close"].rename(t))
    px = pd.concat(frames, axis=1).sort_index()
    bad = px.index[(px.index >= "2019-12-19") & (px.index <= "2019-12-20")]
    px = px.drop(index=bad)
    rets = px.pct_change().fillna(0.0)
    gold_rets = rets["GOLDBEES.NS"]
    em_own = {t: px[t].ewm(span=200, adjust=False).mean() for t in EQUITY_ETF}
    for months in [(3, 6, 9, 12), (4, 8, 12), (6, 12)]:
        rb_m = []
        for (y, m), grp in px.index.to_series().groupby([px.index.year, px.index.month]):
            if m in months:
                rb_m.append(grp.iloc[-1])
        rot_ret = pd.Series(np.nan, index=px.index)
        holder = None
        for i, d in enumerate(px.index):
            if d in set(rb_m) and i >= 252:
                r12 = px.iloc[i] / px.iloc[i - 252] - 1.0
                pool = r12[EQUITY_ETF].dropna()
                holder = pool.idxmax() if len(pool) else None
            if holder and pd.notna(em_own[holder].iloc[i]):
                rot_ret.iloc[i] = rets[holder].iloc[i] if px[holder].iloc[i] > em_own[holder].iloc[i] else gold_rets.iloc[i]
        s = (1 + rot_ret.fillna(0)).cumprod() * 100
        results[f"etf_ownguard_m{'_'.join(map(str, months))}"] = s
        vv = s.loc[s.first_valid_index():]
        m = metrics_only(vv, vv.index)
        print(f"  m={months}: CAGR {m['cagr_pct']:.2f}% / DD {m['max_drawdown_pct']:.1f}%")

    common_idx = None
    for s in results.values():
        common_idx = s.index if common_idx is None else common_idx.intersection(s.index)
    out = {}
    for k, s in results.items():
        out[k] = metrics_only(s, common_idx)
    # add a no-filter momentum portfolio for reference at quarterly cadence
    rb_q = rebalance_dates(closes.index, months=(4, 8, 12))
    idx, _ = build_index_generic(closes, rb_q, select_top_original)
    out["momentum10_nofilter_quarterly"] = metrics_only(idx, common_idx.intersection(idx.index))
    with open("results_find_cadence.json", "w") as f:
        json.dump(out, f, indent=2)
    print("\nwrote results_find_cadence.json")


if __name__ == "__main__":
    main()

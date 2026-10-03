"""Round 3: ETFs — Nifty Next 50 (JUNIORBEES), Midcap 100 (MOM100),
Nasdaq 100 (MON100), Nifty 50 (NIFTYBEES), Gold (GOLDBEES), Silver
(SILVERBEES). A monthly top-1 trailing-12m momentum rotation on the
four equity ETFs, plus regime-filter combos (gold sleeve, 200-EMA,
50/50 blend, EMA-alignment, 20d hysteresis) and naive baselines.
"""
import json

import numpy as np
import pandas as pd
import yfinance as yf

from backtest10 import rebalance_dates, cumret_drawdown, series_to_points, CURRENCY_SYMBOL
from backtest32 import metrics_only

EQUITY_ETF = ["NIFTYBEES.NS", "JUNIORBEES.NS", "MOM100.NS", "MON100.NS"]
ALL_ETF = EQUITY_ETF + ["GOLDBEES.NS", "SILVERBEES.NS"]


def load():
    frames = []
    for t in ALL_ETF:
        df = yf.download(t, period="max", auto_adjust=False, progress=False)
        df.columns = df.columns.droplevel(1) if isinstance(df.columns, pd.MultiIndex) else df.columns
        frames.append(df["Close"].rename(t))
    px = pd.concat(frames, axis=1).sort_index()
    # gold glitch cleanup (same artifact as every other report)
    bad = px.index[(px.index >= "2019-12-19") & (px.index <= "2019-12-20")]
    px = px.drop(index=bad)
    return px


def build_rotation(px, top_k, lookback, months, ranking="top"):
    """Weekly-grade rotation: at each rebalance date in the given months,
    pick the top-K equity ETFs by trailing `lookback` trading days return,
    equal-weight them, hold to next rebalance."""
    rb = []
    for (y, m), grp in px.index.to_series().groupby([px.index.year, px.index.month]):
        if m in months:
            rb.append(grp.iloc[-1])
    series = pd.Series(np.nan, index=px.index)
    holdings = None
    for i, d in enumerate(px.index):
        if d in set(rb):
            if i >= lookback:
                r12 = px.iloc[i] / px.iloc[i - lookback] - 1.0
                pool = r12[EQUITY_ETF].dropna()
                holdings = list(pool.nlargest(top_k).index) if len(pool) >= top_k else None
        if holdings is None:
            series.iloc[i] = np.nan if i == 0 else series.iloc[i - 1]
            continue
        series.iloc[i] = px[holdings].iloc[i].mean() if i < 1 or d in set(rb) else series.iloc[i - 1] if series.iloc[i - 1] < 0 else series.iloc[i] if series.iloc[i] == series.iloc[i] else np.nan
    return series


def main():
    px = load()
    print("window:", px.index[0].date(), "->", px.index[-1].date())
    print("coverage:", {t: f"{px[t].first_valid_index().date()} -> {px[t].last_valid_index().date()}" for t in px.columns})

    rets = px.pct_change().fillna(0.0)
    gold_rets = rets["GOLDBEES.NS"]
    px_n = px.dropna(how="any")
    common = px_n.index
    rb_m = []
    for (y, m), grp in px.index.to_series().groupby([px.index.year, px.index.month]):
        rb_m.append(grp.iloc[-1])

    # --- baselines ---
    eq_w = (1 + rets[EQUITY_ETF].mean(axis=1)).cumprod() * 100
    bh_nifty = px["NIFTYBEES.NS"] / px["NIFTYBEES.NS"].dropna().iloc[0] * 100
    bh_gold = px["GOLDBEES.NS"] / px["GOLDBEES.NS"].dropna().iloc[0] * 100
    bh_silver = px["SILVERBEES.NS"] / px["SILVERBEES.NS"].dropna().iloc[0] * 100
    variants = {
        "buy-hold Niftybees": bh_nifty,
        "buy-hold Gold": bh_gold,
        "buy-hold Silver": bh_silver,
        "Equal-weight 4 equity ETFs": eq_w,
    }

    # --- monthly top-1 trailing-12m rotation on the 4 equity ETFs ---
    holder = None
    rot_ret = pd.Series(np.nan, index=px.index)
    for i, d in enumerate(px.index):
        if d in set(rb_m) and i >= 252:
            r12 = px.iloc[i] / px.iloc[i - 252] - 1.0
            pool = r12[EQUITY_ETF].dropna()
            holder = pool.idxmax() if len(pool) else None
        if holder:
            rot_ret.iloc[i] = rets[holder].iloc[i]
    rot = (1 + rot_ret.fillna(0)).cumprod() * 100
    variants["Top-1 12m rotation (monthly)"] = rot

    # --- top-1 with standard 200-EMA filter on the chosen ETF's own EMA ---
    em_own = {t: px[t].ewm(span=200, adjust=False).mean() for t in EQUITY_ETF}
    rot2_ret = rot_ret.copy()
    holder = None
    for i, d in enumerate(px.index):
        if d in set(rb_m) and i >= 252:
            r12 = px.iloc[i] / px.iloc[i - 252] - 1.0
            pool = r12[EQUITY_ETF].dropna()
            holder = pool.idxmax() if len(pool) else None
        if holder and pd.notna(em_own[holder].iloc[i]):
            rot2_ret.iloc[i] = rets[holder].iloc[i] if px[holder].iloc[i] > em_own[holder].iloc[i] else gold_rets.iloc[i]
    variants["Top-1 12m, gold when pick<its 200EMA"] = (1 + rot2_ret.fillna(0)).cumprod() * 100

    # --- top-1 with 50/50 stock+gold during NIFTY 200-EMA risk-off ---
    risk_off = px["NIFTYBEES.NS"] < px["NIFTYBEES.NS"].ewm(span=200, adjust=False).mean()
    rot3_ret = rot_ret.where(~risk_off, 0.5 * rot_ret + 0.5 * gold_rets)
    variants["Top-1, 50/50 gold in NIFTY risk-off"] = (1 + rot3_ret.fillna(0)).cumprod() * 100

    # --- top-2 relaxed (smoother) ---
    rot5_ret = pd.Series(np.nan, index=px.index)
    holder2 = []
    for i, d in enumerate(px.index):
        if d in set(rb_m) and i >= 252:
            r12 = px.iloc[i] / px.iloc[i - 252] - 1.0
            pool = r12[EQUITY_ETF].dropna()
            holder2 = list(pool.nlargest(2).index) if len(pool) >= 2 else []
        if holder2:
            rot5_ret.iloc[i] = rets[holder2].iloc[i].mean()
    variants["Top-2 12m rotation (monthly)"] = (1 + rot5_ret.fillna(0)).cumprod() * 100

    # trim to common coverage where at least the rotation baseline works;
    # silver only has history from 2022-02, keep its own index
    first = rot_ret.first_valid_index()
    variants = {}
    for k, v in {
        "buy-hold Niftybees": bh_nifty, "buy-hold Gold": bh_gold, "buy-hold Silver": bh_silver,
        "Equal-weight 4 equity ETFs": eq_w, "Top-1 12m rotation (monthly)": rot,
        "Top-1 12m, gold when pick<its 200EMA": (1 + rot2_ret.fillna(0)).cumprod() * 100,
        "Top-1, 50/50 gold in NIFTY risk-off": (1 + rot3_ret.fillna(0)).cumprod() * 100,
        "Top-2 12m rotation (monthly)": (1 + rot5_ret.fillna(0)).cumprod() * 100,
    }.items():
        variants[k] = v.loc[v.first_valid_index():] if k == "buy-hold Silver" else v.loc[first:]

    print()
    for name, s in variants.items():
        m = metrics_only(s, s.index)
        print(f"{name:48s} CAGR {m['cagr_pct']:.2f}% / DD {m['max_drawdown_pct']:.1f}%")

    out = {k.replace(" ", "_").replace("-", "_").replace("/", "_"): metrics_only(v, v.index) for k, v in variants.items()}
    with open("results_find_etf.json", "w") as f:
        json.dump(out, f, indent=2)
    print("\nwrote results_find_etf.json")


if __name__ == "__main__":
    main()

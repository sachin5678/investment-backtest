"""
Point-in-time NIFTY Quality formula scoring — usable for a REAL periodic
rebalance backtest, unlike compute_quality_scores.py's one-time,
present-day-only snapshot (report 13). Same formula, same
fundamentals_raw.pkl cache; the only change is that every metric is
computed using ONLY fiscal-year columns that closed ON OR BEFORE a given
`asof` date, so a rebalance on date D never uses a fiscal year's numbers
before that year actually existed (no look-ahead).

Formula (unchanged from compute_quality_scores.py, confirmed via NSE's
published Quality-index methodology):
  Quality Score = 0.33*Z(ROE) - 0.33*Z(D/E) - 0.33*Z(EPS growth variability)
  ROE, D/E: averaged over the trailing annual fundamentals available AS OF
  that date. EPS growth variability: std dev of year-over-year Diluted EPS
  growth, computed across the same trailing annual EPS figures.

CRITICAL DATA-AVAILABILITY FINDING (see reports 74/75 for the full
disclosure): yfinance's cached annual balance_sheet/financials history is
really only ~3 usable fiscal years deep for most tickers (FY ending
2023-03-31 through 2026-03-31) — the requested 5th year (2022-03-31) is
almost universally NaN/missing. Under the SAME eligibility rules
compute_quality_scores.py already used (>=2 ROE/D-E observations, >=3
Diluted-EPS observations so growth variability is a real std of >=2
year-over-year figures, not a single-point degenerate "variability"), a
broad (480+/500) NIFTY500-wide universe first becomes scoreable as of
FY2025-03-31 — NOT FY2022/2023/2024, which is only 0-2 tickers wide. That
leaves exactly TWO real, broad, point-in-time snapshots to rebalance
against: FY2025-03-31 and FY2026-03-31. Confirmed empirically (not
assumed) by testing every candidate fiscal year-end against this
eligibility bar across the full 500-ticker cache.
"""
import pickle

import numpy as np
import pandas as pd

with open("fundamentals_raw.pkl", "rb") as f:
    RAW = pickle.load(f)

MIN_ROE_OBS = 2
MIN_DE_OBS = 2
MIN_EPS_OBS = 3
MIN_GROWTH_OBS = 2


def extract_metrics_asof(data, asof):
    bs, fin = data.get("balance_sheet"), data.get("financials")
    if bs is None or fin is None or bs.empty or fin.empty:
        return None
    cols_bs = [c for c in bs.columns if c <= asof]
    cols_fin = [c for c in fin.columns if c <= asof]
    if not cols_bs or not cols_fin:
        return None
    bs, fin = bs[cols_bs], fin[cols_fin]
    try:
        equity = bs.loc["Stockholders Equity"].dropna()
        debt = bs.loc["Total Debt"].reindex(equity.index)
        net_income = fin.loc["Net Income"].reindex(equity.index) if "Net Income" in fin.index else None
        eps_row = "Diluted EPS" if "Diluted EPS" in fin.index else ("Basic EPS" if "Basic EPS" in fin.index else None)
        eps = fin.loc[eps_row].reindex(equity.index) if eps_row else None
    except KeyError:
        return None
    if net_income is None or eps is None:
        return None

    valid_eq = equity[equity > 0]
    if len(valid_eq) < 2:
        return None
    roe_series = (net_income / equity).replace([np.inf, -np.inf], np.nan).dropna()
    de_series = (debt / equity).replace([np.inf, -np.inf], np.nan).dropna()
    if len(roe_series) < MIN_ROE_OBS or len(de_series) < MIN_DE_OBS:
        return None

    eps_clean = eps.dropna().sort_index()
    if len(eps_clean) < MIN_EPS_OBS:
        return None
    growth = eps_clean.pct_change().replace([np.inf, -np.inf], np.nan).dropna()
    if len(growth) < MIN_GROWTH_OBS:
        return None

    return {"roe_avg": float(roe_series.mean()), "de_avg": float(de_series.mean()),
            "eps_var": float(growth.std()), "n_years": len(cols_bs)}


def rank_quality(tickers, asof, top_n):
    """Cross-sectional Z-score + rank WITHIN `tickers` only (so a
    Midcap150-only ranking isn't diluted by names outside that universe),
    as of `asof`. Returns (top_n tickers as a bare list, the full scored
    DataFrame for diagnostics — empty if nothing was eligible)."""
    rows = []
    for t in tickers:
        data = RAW.get(t)
        if data is None:
            continue
        m = extract_metrics_asof(data, asof)
        if m:
            rows.append({"ticker": t, **m})
    df = pd.DataFrame(rows)
    if df.empty:
        return [], df
    for col in ("roe_avg", "de_avg", "eps_var"):
        df[f"z_{col}"] = (df[col] - df[col].mean()) / df[col].std()
    df["quality_score"] = 0.33 * df["z_roe_avg"] - 0.33 * df["z_de_avg"] - 0.33 * df["z_eps_var"]
    df = df.sort_values("quality_score", ascending=False).reset_index(drop=True)
    return list(df.head(top_n)["ticker"]), df

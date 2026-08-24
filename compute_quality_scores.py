"""Computes the real NIFTY Quality formula's score for every NIFTY 500
stock using the ~5 years of annual fundamentals available via yfinance,
selects the top 50, and prints the result. This is a ONE-TIME, present-day
snapshot — not a time-varying, periodically-rebalanced score, because
historical fundamentals that far back don't exist in this data source (see
backtest12.py's docstring for the full disclosure).

Formula (confirmed via NSE's published methodology):
  Quality Score = 0.33*Z(ROE) - 0.33*Z(D/E) - 0.33*Z(EPS growth variability)
  ROE, D/E: averaged over the trailing ~5 annual fundamentals available.
  EPS growth variability: std dev of year-over-year Diluted EPS growth,
  computed across the same trailing annual EPS figures.
  Weight = sqrt(free-float market cap) x quality score, capped 5%/stock
  (current market cap used as the free-float proxy for this single snapshot).
"""
import json
import pickle
import numpy as np
import pandas as pd

with open("fundamentals_raw.pkl", "rb") as f:
    RAW = pickle.load(f)


def extract_metrics(ticker, data):
    bs, fin = data.get("balance_sheet"), data.get("financials")
    if bs is None or fin is None or bs.empty or fin.empty:
        return None
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
    if len(roe_series) < 2 or len(de_series) < 2:
        return None
    roe_avg = float(roe_series.mean())
    de_avg = float(de_series.mean())

    eps_clean = eps.dropna().sort_index()
    if len(eps_clean) < 3:
        return None
    growth = eps_clean.pct_change().replace([np.inf, -np.inf], np.nan).dropna()
    if len(growth) < 2:
        return None
    eps_var = float(growth.std())

    return {"ticker": ticker, "roe_avg": roe_avg, "de_avg": de_avg, "eps_var": eps_var,
            "market_cap": data.get("market_cap"), "n_years": len(equity)}


def cap_weights(weights, cap=0.05, max_iter=100):
    w = weights.copy() / weights.sum()
    for _ in range(max_iter):
        over = w > cap
        if not over.any():
            break
        excess = (w[over] - cap).sum()
        w[over] = cap
        under = ~over
        if w[under].sum() <= 0:
            break
        w[under] = w[under] + excess * (w[under] / w[under].sum())
    return w


def main():
    rows = []
    for ticker, data in RAW.items():
        m = extract_metrics(ticker, data)
        if m and m["market_cap"]:
            rows.append(m)
    df = pd.DataFrame(rows)
    print(f"{len(df)} of {len(RAW)} NIFTY 500 stocks have usable fundamentals "
          f"(ROE, D/E, >=3 years of EPS for growth variability, positive equity, known market cap).")

    for col in ("roe_avg", "de_avg", "eps_var"):
        df[f"z_{col}"] = (df[col] - df[col].mean()) / df[col].std()

    df["quality_score"] = 0.33 * df["z_roe_avg"] - 0.33 * df["z_de_avg"] - 0.33 * df["z_eps_var"]
    df = df.sort_values("quality_score", ascending=False)
    top50 = df.head(50).copy()

    raw_w = np.sqrt(top50["market_cap"]) * top50["quality_score"]
    if (raw_w <= 0).any():
        print(f"NOTE: {int((raw_w <= 0).sum())} of the top 50 have a non-positive weight basis "
              f"(quality_score <= 0 despite ranking top 50) — floored to a small positive weight.")
        raw_w = raw_w.clip(lower=raw_w[raw_w > 0].min() * 0.1)
    top50["weight"] = cap_weights(raw_w).values

    top50.to_json("quality50_selection.json", orient="records", indent=2)
    print(f"\nEligible universe stats: ROE mean={df['roe_avg'].mean():.3f} std={df['roe_avg'].std():.3f}; "
          f"D/E mean={df['de_avg'].mean():.2f} std={df['de_avg'].std():.2f}; "
          f"EPS-var mean={df['eps_var'].mean():.2f} std={df['eps_var'].std():.2f}")
    print("\nTop 50 by quality score:")
    print(top50[["ticker", "roe_avg", "de_avg", "eps_var", "quality_score", "weight"]].to_string(index=False))
    print(f"\nWeight check: sum={top50['weight'].sum():.4f}, max={top50['weight'].max():.4f}")


if __name__ == "__main__":
    main()

"""
Static "today's Quality-50 basket" backtest — NOT a reconstruction of the
real, periodically-rebalanced NIFTY500 Quality 50 index.

Real methodology (confirmed via NSE's published documentation):
  Quality Score = 0.33*Z(ROE) - 0.33*Z(Debt/Equity) - 0.33*Z(5yr EPS growth
  variability), each averaged/measured over the trailing 5 years. Top 50 by
  score selected from NIFTY 500, weighted by sqrt(free-float market cap) x
  score, capped 5%/stock, rebalanced periodically.

WHY THIS CANNOT BE RECONSTRUCTED OVER TIME THE WAY MOMENTUM WAS (reports 11-12):
  Momentum's score is computed purely from PRICE, and Yahoo Finance has
  decades of price history — so a momentum score could be computed at any
  past rebalance date. Quality's score needs ROE, Debt/Equity, and EPS —
  FUNDAMENTAL data — and yfinance only exposes ~5 years of ANNUAL
  fundamentals per company, for every company, with no way to see what the
  fundamentals looked like as of a rebalance date in, say, 2015. There is
  no historical point-in-time fundamentals data source available in this
  project. So the quality score itself can only ever be computed ONCE, as
  of today.

WHAT THIS SCRIPT ACTUALLY DOES (confirmed with you in chat):
  1. Computes today's quality score for all 500 NIFTY 500 stocks using the
     ~5 years of fundamentals yfinance has (see compute_quality_scores.py).
  2. Selects the top 50, weights them per the real formula (sqrt(market
     cap) x score, capped 5%, current market cap standing in for free-float
     since this is a single snapshot, not a time series).
  3. Buys that FIXED basket once and holds it, unrebalanced, as far back in
     time as its constituents' price histories allow — a "what if you'd
     bought today's quality winners years ago and never touched it again"
     test, not a simulation of the real index's actual history.
  4. Because several of the top 50 are very recent IPOs (some listed within
     the last year), a SECOND basket drops the stocks with under ~3.5 years
     of price history and reweights the remaining ~44 — giving a much
     longer, more useful backtest window at the cost of no longer being
     "the actual top 50."
"""
import json
import numpy as np
import pandas as pd

from backtest10 import fetch, cumret_drawdown, series_to_points
from backtest4 import CURRENCY_SYMBOL

RECENT_IPO_CUTOFF_DAYS = 1280   # ~3.5 years — drops stocks listed after ~March 2023


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


def load_prices_for(tickers):
    raw200 = pd.read_pickle("universe_raw.pkl")
    extra = pd.read_pickle("quality50_extra_raw.pkl")
    cached200 = set(c[0] for c in raw200.columns)
    cols = {}
    for t in tickers:
        src = raw200 if t in cached200 else extra
        cols[t] = src[(t, "Close")]
    df = pd.DataFrame(cols).sort_index().ffill()
    return df


def build_basket(closes, tickers, weights, label):
    sub = closes[tickers].dropna()
    start_date = sub.index[0]
    entry_prices = sub.iloc[0]
    base_value = 100.0
    shares = (weights * base_value) / entry_prices
    value = (sub * shares).sum(axis=1)
    return value, start_date


def main():
    sel = pd.read_json("quality50_selection.json")
    all_tickers = sel["ticker"].tolist()
    closes = load_prices_for(all_tickers)

    first_dates = closes[all_tickers].apply(lambda s: s.dropna().index.min())
    days_history = (pd.Timestamp("2026-08-24") - first_dates).dt.days
    sel = sel.set_index("ticker")
    sel["days_history"] = days_history
    sel = sel.reset_index()

    raw_w_all = np.sqrt(sel["market_cap"]) * sel["quality_score"]
    sel["weight_50"] = cap_weights(raw_w_all).values

    long_tickers = sel[sel["days_history"] >= RECENT_IPO_CUTOFF_DAYS]["ticker"].tolist()
    dropped = sel[sel["days_history"] < RECENT_IPO_CUTOFF_DAYS][["ticker", "days_history"]].to_dict("records")
    long_sel = sel[sel["ticker"].isin(long_tickers)].copy()
    raw_w_long = np.sqrt(long_sel["market_cap"]) * long_sel["quality_score"]
    long_sel["weight_44"] = cap_weights(raw_w_long).values

    value_50, start_50 = build_basket(closes, all_tickers, sel["weight_50"].values, "Quality-50 (all)")
    value_44, start_44 = build_basket(closes, long_tickers, long_sel["weight_44"].values, "Quality-44 (ex-recent-IPOs)")

    nifty = fetch("^NSEI")
    midcap = fetch("MID150BEES.NS")

    def bench_over(series, bench_df, col="Close"):
        common = series.index.intersection(bench_df.index)
        s = bench_df.loc[common, col]
        return s / s.iloc[0] * 100.0, common[0], common[-1]

    nifty_44, n44_start, n44_end = bench_over(value_44, nifty)
    midcap_44, m44_start, m44_end = bench_over(value_44, midcap)
    nifty_50, _, _ = bench_over(value_50, nifty)

    def metrics(series):
        mdd, peak, trough, uw = cumret_drawdown(series, pd.Series(1.0, index=series.index))
        years = (series.index[-1] - series.index[0]).days / 365.25
        cagr = float((series.iloc[-1] / series.iloc[0]) ** (1 / years) * 100 - 100) if years > 0 else None
        return {
            "net_return_pct": float((series.iloc[-1] / series.iloc[0] - 1) * 100),
            "cagr_pct": cagr, "max_drawdown_pct": mdd,
            "max_drawdown_peak_date": peak, "max_drawdown_trough_date": trough,
            "longest_underwater_days": uw,
        }

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "num_universe": int(len(pd.read_json("quality50_selection.json"))),
        "num_eligible": 482,
        "top50": sel[["ticker", "roe_avg", "de_avg", "eps_var", "quality_score", "weight_50", "days_history"]].to_dict("records"),
        "dropped_recent_ipos": dropped,
        "cutoff_days": RECENT_IPO_CUTOFF_DAYS,
        "quality50": {
            "start_date": start_50.strftime("%Y-%m-%d"), "end_date": value_50.index[-1].strftime("%Y-%m-%d"),
            "equity_curve": series_to_points(value_50 / value_50.iloc[0] * 100.0),
            "nifty_equity_curve": series_to_points(nifty_50),
            **metrics(value_50),
        },
        "quality44": {
            "start_date": start_44.strftime("%Y-%m-%d"), "end_date": value_44.index[-1].strftime("%Y-%m-%d"),
            "num_stocks": len(long_tickers),
            "equity_curve": series_to_points(value_44 / value_44.iloc[0] * 100.0),
            **metrics(value_44),
        },
        "nifty_vs_44": {
            "equity_curve": series_to_points(nifty_44),
            **metrics(nifty.loc[nifty.index.intersection(value_44.index), "Close"]),
        },
        "midcap_vs_44": {
            "equity_curve": series_to_points(midcap_44),
            "start_date": m44_start.strftime("%Y-%m-%d"),
            **metrics(midcap.loc[midcap.index.intersection(value_44.index), "Close"]),
        },
    }
    with open("results12.json", "w") as f:
        json.dump(results, f)

    print("Quality-50 (all 50):", results["quality50"]["start_date"], "to", results["quality50"]["end_date"])
    print("  ", {k: v for k, v in results["quality50"].items() if k not in ("equity_curve", "nifty_equity_curve")})
    print("Quality-44 (ex recent IPOs):", results["quality44"]["start_date"], "to", results["quality44"]["end_date"])
    print("  ", {k: v for k, v in results["quality44"].items() if k != "equity_curve"})
    print("NIFTY 50 over same window:", {k: v for k, v in results["nifty_vs_44"].items() if k != "equity_curve"})
    print("Midcap over its own overlap:", {k: v for k, v in results["midcap_vs_44"].items() if k != "equity_curve"})
    print("\nDropped as recent IPOs:", dropped)


if __name__ == "__main__":
    main()

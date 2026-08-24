"""
Gold/Silver Absolute Momentum Rotation — the same "only own it while momentum
favours it" idea used throughout this project (reports 11, 12, 14-19, 21),
applied to just two assets: gold and silver.

WHY THE FORMULA HAD TO CHANGE
Every other momentum reconstruction in this project ranks a broad universe
(30-500+ stocks) by a CROSS-SECTIONALLY Z-scored score — each stock's
risk-adjusted 6m/12m return measured against the mean and spread of every
OTHER eligible stock that same day. That statistical step needs breadth to
mean anything; with only two assets, a cross-sectional Z-score of 2 points
degenerates to nothing more than "which one is higher" and throws away the
actual magnitude of the signal.

So this report uses ABSOLUTE (time-series) momentum instead: each asset's
OWN risk-adjusted momentum score, compared to zero rather than to the other
asset. Same building blocks as every other reconstruction here — 6-month and
12-month price return, each divided by trailing 1-year daily-return
volatility, then averaged 0.5/0.5 — just judged against a fixed bar instead
of a cross-sectional ranking:
    score = 0.5 * (ret_6m / vol_1y) + 0.5 * (ret_12m / vol_1y)
  - score > 0  -> hold that asset
  - score <= 0 -> exit that asset to cash
Both can be held at once (split 50/50 of whatever's invested) if both score
positive; both can be in cash at once if neither does. This is a direct,
literal implementation of "only invest when momentum favours it, else exit."

INSTRUMENTS: GLD (SPDR Gold Shares, since 2004-11-18) and SLV (iShares
Silver Trust, since 2006-04-28) — global USD spot-tracking ETFs, not the NSE
INR-denominated gold/silver ETFs used in report 14's blend (GOLDBEES.NS).
Everything here is in USD; no currency conversion or FX-hedging assumption
is made anywhere, same disclosure as report 21 (NASDAQ).

REBALANCE: monthly (last trading day of every month) — simpler and more
responsive than the 6m/12m NIFTY200-style cadence used for the broad-universe
reconstructions, appropriate for a 2-asset rule that's meant to react to
trend changes rather than reshuffle a large book.

Benchmarks: buy-and-hold GLD, buy-and-hold SLV, and a static 50/50 GLD/SLV
blend rebalanced on the same monthly schedule (so any outperformance can be
attributed to the momentum switching itself, not to a difference in
rebalancing frequency).
"""
import json

import numpy as np
import pandas as pd

from backtest10 import cumret_drawdown, series_to_points, rebalance_dates
from backtest13 import metrics
from backtest20 import fetch_us

LOOKBACK_12M = 252
LOOKBACK_6M = 126
CURRENCY_SYMBOL = "$"
GOLD_TICKER, SILVER_TICKER = "GLD", "SLV"


def asset_score(closes, t_idx, ticker):
    """0.5*Z-building-block(6m) + 0.5*Z-building-block(12m), but WITHOUT the
    cross-sectional Z-score step (see module docstring) — just the raw
    risk-adjusted return itself, judged against zero."""
    if t_idx < LOOKBACK_12M:
        return None
    price_t = closes[ticker].iloc[t_idx]
    price_t12 = closes[ticker].iloc[t_idx - LOOKBACK_12M]
    price_t6 = closes[ticker].iloc[t_idx - LOOKBACK_6M]
    if pd.isna(price_t) or pd.isna(price_t12) or pd.isna(price_t6):
        return None
    window = closes[ticker].iloc[t_idx - LOOKBACK_12M: t_idx + 1]
    vol_1y = window.pct_change().std()
    if not vol_1y or vol_1y <= 0:
        return None
    ret_6m = price_t / price_t6 - 1.0
    ret_12m = price_t / price_t12 - 1.0
    score = 0.5 * (ret_6m / vol_1y) + 0.5 * (ret_12m / vol_1y)
    return float(score) if np.isfinite(score) else None


def build_rotation(closes):
    """Monthly rebalance: at each month-end, score gold and silver
    independently; hold (equally split among) whichever have positive
    score, sit in cash otherwise. No stop-loss/intra-month exit — the rule
    is purely "what does momentum say at the start of the month.\""""
    dates = closes.index
    rbdates = set(rebalance_dates(dates, months=range(1, 13)))
    date_pos = {d: i for i, d in enumerate(dates)}

    value = pd.Series(np.nan, index=dates)
    holdings = {}  # ticker -> shares
    cash = 100.0
    started = False
    selections = []

    for i, d in enumerate(dates):
        price_today = {t: closes[t].iloc[i] for t in (GOLD_TICKER, SILVER_TICKER)}

        if d in rbdates:
            t_idx = date_pos[d]
            scores = {t: asset_score(closes, t_idx, t) for t in (GOLD_TICKER, SILVER_TICKER)}
            if all(s is not None for s in scores.values()):
                # mark-to-market current holdings before reallocating
                port_value = cash + sum(holdings.get(t, 0.0) * price_today[t] for t in holdings)
                if not started:
                    port_value = 100.0
                    started = True
                favoured = [t for t, s in scores.items() if s is not None and s > 0]
                holdings = {}
                if favoured:
                    stake_each = port_value / len(favoured)
                    for t in favoured:
                        holdings[t] = stake_each / price_today[t]
                    cash = 0.0
                else:
                    cash = port_value
                selections.append({
                    "date": d.strftime("%Y-%m-%d"),
                    "gold_score": round(scores[GOLD_TICKER], 3),
                    "silver_score": round(scores[SILVER_TICKER], 3),
                    "holding": favoured if favoured else ["cash"],
                })

        if started:
            value.iloc[i] = cash + sum(holdings.get(t, 0.0) * price_today[t] for t in holdings)

    value = value.dropna()
    return value, selections


def build_static_5050(closes):
    """Benchmark: 50/50 GLD/SLV, rebalanced back to 50/50 on the same
    monthly schedule (isolates the value of momentum-switching itself from
    the value of just diversifying across the two metals)."""
    dates = closes.index
    rbdates = set(rebalance_dates(dates, months=range(1, 13)))
    date_pos = {d: i for i, d in enumerate(dates)}
    value = pd.Series(np.nan, index=dates)
    shares = {GOLD_TICKER: 50.0 / closes[GOLD_TICKER].iloc[0], SILVER_TICKER: 50.0 / closes[SILVER_TICKER].iloc[0]}

    for i, d in enumerate(dates):
        price_today = {t: closes[t].iloc[i] for t in (GOLD_TICKER, SILVER_TICKER)}
        if d in rbdates and i > 0:
            port_value = sum(shares[t] * price_today[t] for t in shares)
            for t in shares:
                shares[t] = (port_value / 2.0) / price_today[t]
        value.iloc[i] = sum(shares[t] * price_today[t] for t in shares)

    return value


def main():
    gld = fetch_us(GOLD_TICKER)
    slv = fetch_us(SILVER_TICKER)
    common = gld.index.intersection(slv.index)
    closes = pd.DataFrame({GOLD_TICKER: gld.loc[common, "Close"], SILVER_TICKER: slv.loc[common, "Close"]}).sort_index()

    rotation_value, selections = build_rotation(closes)
    start_date, end_date = rotation_value.index[0], rotation_value.index[-1]

    win = closes.index[(closes.index >= start_date) & (closes.index <= end_date)]
    gld_series = closes.loc[win, GOLD_TICKER]
    slv_series = closes.loc[win, SILVER_TICKER]
    static_5050 = build_static_5050(closes.loc[win])

    def norm(s):
        return s / s.iloc[0] * 100.0

    rotation_norm = norm(rotation_value)
    gld_norm = norm(gld_series)
    slv_norm = norm(slv_series)
    static_norm = norm(static_5050)

    cash_pct_of_months = sum(1 for s in selections if s["holding"] == ["cash"]) / len(selections) * 100
    both_pct_of_months = sum(1 for s in selections if len(s["holding"]) == 2) / len(selections) * 100

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": start_date.strftime("%Y-%m-%d"), "end_date": end_date.strftime("%Y-%m-%d"),
        "num_rebalances": len(selections),
        "cash_pct_of_months": round(cash_pct_of_months, 1),
        "both_pct_of_months": round(both_pct_of_months, 1),
        "selections_sample": selections[:6] + selections[-6:] if len(selections) > 12 else selections,
        "gold_silver_momentum": {"equity_curve": series_to_points(rotation_norm), **metrics(rotation_value)},
        "gld_buyhold": {"equity_curve": series_to_points(gld_norm), **metrics(gld_series)},
        "slv_buyhold": {"equity_curve": series_to_points(slv_norm), **metrics(slv_series)},
        "static_5050": {"equity_curve": series_to_points(static_norm), **metrics(static_5050)},
    }

    with open("results22.json", "w") as f:
        json.dump(results, f, indent=2)
    print("wrote results22.json")
    print(f"window: {results['start_date']} -> {results['end_date']}  rebalances: {results['num_rebalances']}")
    print(f"momentum CAGR {results['gold_silver_momentum']['cagr_pct']:.1f}% / DD {results['gold_silver_momentum']['max_drawdown_pct']:.1f}%")
    print(f"GLD b&h CAGR {results['gld_buyhold']['cagr_pct']:.1f}% / DD {results['gld_buyhold']['max_drawdown_pct']:.1f}%")
    print(f"SLV b&h CAGR {results['slv_buyhold']['cagr_pct']:.1f}% / DD {results['slv_buyhold']['max_drawdown_pct']:.1f}%")
    print(f"static 50/50 CAGR {results['static_5050']['cagr_pct']:.1f}% / DD {results['static_5050']['max_drawdown_pct']:.1f}%")
    print(f"months in cash: {cash_pct_of_months:.1f}%  months holding both: {both_pct_of_months:.1f}%")


if __name__ == "__main__":
    main()

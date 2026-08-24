"""
"Midcap150 Momentum 20" reconstruction, plus a 50% momentum / 50% gold
blend — NOTE: "Momentum 20" is NOT an official NSE index. The real one is
Nifty Midcap150 Momentum 50 (top 50 of NIFTY Midcap 150, not top 20) — same
situation as the earlier "NIFTY100 Momentum 10" case. This applies the
identical real formula to a smaller, invented top-20 selection instead.

Real Nifty Midcap150 Momentum 50 methodology (confirmed via NSE's published
documentation): same 6m/12m risk-adjusted momentum score, z-scored and
asymmetrically normalised, as the other momentum indices in this project —
but rebalanced using data ending the last trading day of MAY and NOVEMBER
(not June/December like NIFTY200 Momentum 30), and weighted by free-float
market cap x score capped at the lower of 5% or 5x the stock's Midcap 150
free-float weight (this report uses the simpler flat-5% cap used throughout
this project's other reconstructions, not the 5x-float-weight variant — one
more disclosed simplification).

Same disclosed approximations as backtest10.py/11.py apply: today's fixed
NIFTY Midcap 150 roster used retroactively (survivorship bias), equal
weighting instead of free-float-market-cap x score, no F&O-eligibility
screen, rebalance dates approximated as last trading day of May/November.

Gold proxy: GOLDBEES.NS (Nippon India ETF Gold BeES), full history since
2009 — a real, tradable, long-history instrument, no reconstruction needed.

50/50 blend: rebalanced back to an exact 50/50 split at the SAME semi-annual
dates as the momentum leg's own rebalances (a judgment call — no rebalancing
frequency was specified, so this reuses the momentum leg's existing cadence
rather than introducing a separate schedule).
"""
import json
import numpy as np
import pandas as pd

from backtest10 import load_universe_closes, build_index, rebalance_dates, cumret_drawdown, series_to_points, fetch, CURRENCY_SYMBOL
from niftymidcap150_symbols import NIFTY_MIDCAP150_SYMBOLS

TOP_N = 20
MIN_ELIGIBLE = 30
GOLD_TICKER = "GOLDBEES.NS"


def load_midcap150_closes():
    raw200 = pd.read_pickle("universe_raw.pkl")
    extra_q = pd.read_pickle("quality50_extra_raw.pkl")
    extra_m = pd.read_pickle("midcap150_extra_raw.pkl")
    tickers = [s + ".NS" for s in NIFTY_MIDCAP150_SYMBOLS]

    def get_close(t):
        for src in (raw200, extra_q, extra_m):
            if t in set(c[0] for c in src.columns):
                return src[(t, "Close")]
        raise KeyError(t)

    closes = pd.DataFrame({t: get_close(t) for t in tickers}).sort_index().ffill()
    return closes


def blend_50_50(series_a, series_b, rebalance_dts):
    """Two-asset portfolio, split 50/50 at inception and reset to exactly
    50/50 at each date in rebalance_dts; drifts freely in between."""
    common = series_a.index.intersection(series_b.index)
    a, b = series_a.loc[common], series_b.loc[common]
    rb_set = set(rebalance_dts) & set(common)

    value = pd.Series(np.nan, index=common)
    total = 100.0
    half_a_shares = (total / 2) / a.iloc[0]
    half_b_shares = (total / 2) / b.iloc[0]
    for i, d in enumerate(common):
        total = half_a_shares * a.loc[d] + half_b_shares * b.loc[d]
        value.loc[d] = total
        if d in rb_set:
            half_a_shares = (total / 2) / a.loc[d]
            half_b_shares = (total / 2) / b.loc[d]
    return value


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


def fetch_gold_cleaned():
    """GOLDBEES.NS shows a 2-day data glitch on 2019-12-19 and 2019-12-20 —
    Close drops to ~₹0.33 (a ~99% one-day fall) then jumps straight back to
    ~₹33.65 on the next trading day, while every other day before and after
    (including the days immediately surrounding this pair) sits consistently
    on the same ~₹25-146 scale. That is not a real price move — verified by
    hand against the raw Yahoo Finance data before building this report,
    the same kind of listing/adjustment artifact found in HDFCMOMENT.NS in
    an earlier report. Those 2 rows are dropped entirely (not forward-filled)
    — since every other series in this report is later intersected against
    gold's date index, this simply excludes those 2 calendar days from the
    whole analysis, an immaterial effect over an ~18-year span."""
    df = fetch(GOLD_TICKER)
    bad_dates = df.index[(df.index >= "2019-12-19") & (df.index <= "2019-12-20")]
    df = df.drop(index=bad_dates)
    return df


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    midcap = fetch("MID150BEES.NS")
    gold_df = fetch_gold_cleaned()

    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]

    index_level, selections = build_index(closes, top_n=TOP_N, min_eligible=MIN_ELIGIBLE, rebalance_months=(5, 11))
    start_date, end_date = index_level.index[0], index_level.index[-1]

    long_common = nifty.index[(nifty.index >= start_date) & (nifty.index <= end_date)]
    long_common = long_common.intersection(index_level.index).intersection(gold_df.index)
    momentum_series = index_level.loc[long_common]
    nifty_series = nifty.loc[long_common, "Close"]
    gold_series = gold_df.loc[long_common, "Close"]

    midcap_common = long_common[long_common.isin(midcap.index)]
    midcap_series = midcap.loc[midcap_common, "Close"]

    def norm(s):
        return s / s.iloc[0] * 100.0

    mom_rb_dates = [d for d in rebalance_dates(long_common, months=(5, 11))]
    blend = blend_50_50(momentum_series, gold_series, mom_rb_dates)

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "universe_size": len(closes.columns), "top_n": TOP_N,
        "start_date": start_date.strftime("%Y-%m-%d"), "end_date": end_date.strftime("%Y-%m-%d"),
        "midcap_start_date": midcap_series.index[0].strftime("%Y-%m-%d"),
        "gold_ticker": GOLD_TICKER,
        "num_rebalances": len(selections),
        "selections_sample": selections[:3] + selections[-3:] if len(selections) > 6 else selections,
        "momentum20": {"equity_curve": series_to_points(norm(momentum_series)), **metrics(momentum_series)},
        "nifty": {"equity_curve": series_to_points(norm(nifty_series)), **metrics(nifty_series)},
        "midcap": {"equity_curve": series_to_points(norm(midcap_series)), **metrics(midcap_series)},
        "gold": {"equity_curve": series_to_points(norm(gold_series)), **metrics(gold_series)},
        "blend_50_50": {"equity_curve": series_to_points(blend), **metrics(blend)},
    }
    with open("results13.json", "w") as f:
        json.dump(results, f)

    print("start", start_date.date(), "end", end_date.date(), "rebalances", len(selections))
    for k in ("momentum20", "nifty", "midcap", "gold", "blend_50_50"):
        v = results[k]
        print(f"[{k}] net_return={v['net_return_pct']:.1f}% cagr={v['cagr_pct']:.2f}% "
              f"mdd={v['max_drawdown_pct']:.1f}% uw_days={v['longest_underwater_days']}")


if __name__ == "__main__":
    main()

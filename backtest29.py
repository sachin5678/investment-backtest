"""
Smallcap250 Momentum 10 & Momentum 5 — dedicated head-to-head report.

Smallcap250 Momentum 10 already exists as one of three variants inside
report 16 (backtest15.py); this report recomputes it fresh alongside a NEW,
more-concentrated Momentum 5 variant (same universe, same exact 6m/12m
risk-adjusted momentum formula, same June/December rebalance — just top 5
instead of top 10, equal-weighted), the same concentration test as report
28's NIFTY100 Momentum 5.

NEITHER is an official NSE product — see backtest15.py's docstring: the
real smallcap momentum-family index is NIFTY Smallcap250 Momentum Quality
100, a momentum+quality HYBRID score, not pure momentum, and top 100 not
top 5/10.

Same disclosed approximations as every reconstruction in this project:
today's fixed NIFTY Smallcap 250 constituent list used retroactively
(survivorship bias — plausibly the strongest of any universe in this
project, since smallcap membership churns fastest), equal weighting
instead of free-float-market-cap x score, no F&O-eligibility screen,
June/December rebalance borrowed from the NIFTY200 Momentum convention.

Benchmarks: NIFTYSMLCAP250.NS (the real, un-reconstructed index, no
reconstruction needed), NIFTY 50, and the Midcap 150 ETF.
"""
import json
import pandas as pd

from backtest10 import build_index, cumret_drawdown, series_to_points, fetch, CURRENCY_SYMBOL
from backtest13 import metrics
from backtest15 import load_smallcap250_closes

TOP_N_10 = 10
TOP_N_5 = 5
MIN_ELIGIBLE_SMALLCAP = 40


def run_one(closes, top_n, min_eligible, common_dates):
    index_level, selections = build_index(closes, top_n=top_n, min_eligible=min_eligible, rebalance_months=(6, 12))
    start_date, end_date = index_level.index[0], index_level.index[-1]
    long_common = common_dates[(common_dates >= start_date) & (common_dates <= end_date)]
    long_common = long_common.intersection(index_level.index)
    series = index_level.loc[long_common]
    return series, selections


def main():
    smallcap_closes = load_smallcap250_closes()
    nifty = fetch("^NSEI")
    midcap_etf = fetch("MID150BEES.NS")
    smallcap_idx = fetch("NIFTYSMLCAP250.NS")

    sc_common = smallcap_closes.index.intersection(nifty.index)
    smallcap_closes = smallcap_closes.loc[sc_common]

    series_10, sel_10 = run_one(smallcap_closes, TOP_N_10, MIN_ELIGIBLE_SMALLCAP, nifty.index)
    series_5, sel_5 = run_one(smallcap_closes, TOP_N_5, MIN_ELIGIBLE_SMALLCAP, nifty.index)

    common = series_10.index.intersection(series_5.index)
    series_10, series_5 = series_10.loc[common], series_5.loc[common]

    nifty_common = common[common.isin(nifty.index)]
    nifty_series = nifty.loc[nifty_common, "Close"]

    smallcap_idx_common = common[common.isin(smallcap_idx.index)]
    smallcap_idx_series = smallcap_idx.loc[smallcap_idx_common, "Close"]

    midcap_common = common[common.isin(midcap_etf.index)]
    midcap_series = midcap_etf.loc[midcap_common, "Close"]

    def norm(s):
        return s / s.iloc[0] * 100.0

    def sample(sel):
        return sel[:3] + sel[-3:] if len(sel) > 6 else sel

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "universe_size": len(smallcap_closes.columns),
        "start_date": common[0].strftime("%Y-%m-%d"), "end_date": common[-1].strftime("%Y-%m-%d"),
        "smallcap_idx_start_date": smallcap_idx_series.index[0].strftime("%Y-%m-%d"),
        "midcap_etf_start_date": midcap_series.index[0].strftime("%Y-%m-%d"),
        "num_rebalances": len(sel_10),
        "momentum10_selections_sample": sample(sel_10),
        "momentum5_selections_sample": sample(sel_5),
        "momentum10": {"equity_curve": series_to_points(norm(series_10)), **metrics(series_10)},
        "momentum5": {"equity_curve": series_to_points(norm(series_5)), **metrics(series_5)},
        "nifty": {"equity_curve": series_to_points(norm(nifty_series)), **metrics(nifty_series)},
        "smallcap_index": {"equity_curve": series_to_points(norm(smallcap_idx_series)), **metrics(smallcap_idx_series)},
        "midcap_etf": {"equity_curve": series_to_points(norm(midcap_series)), **metrics(midcap_series)},
    }

    with open("results28.json", "w") as f:
        json.dump(results, f)

    print("start", results["start_date"], "end", results["end_date"], "rebalances", results["num_rebalances"])
    for k in ("momentum10", "momentum5", "nifty", "smallcap_index", "midcap_etf"):
        v = results[k]
        print(f"[{k}] net_return={v['net_return_pct']:.1f}% cagr={v['cagr_pct']:.2f}% "
              f"mdd={v['max_drawdown_pct']:.1f}% uw_days={v['longest_underwater_days']}")


if __name__ == "__main__":
    main()

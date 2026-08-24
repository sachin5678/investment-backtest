"""
Same "Midcap150 Momentum 20" custom reconstruction as the last report, but
rebalanced every 3 months instead of semi-annually.

The real Nifty Midcap150 Momentum 50 index rebalances in May/November only
(see backtest13.py). There's no official quarterly variant to anchor to, so
this uses February/May/August/November — the same May/November anchor
months, with February and August inserted evenly between them to get a
true 3-month cadence. This is now two steps removed from anything NSE
actually publishes (custom top-20 selection AND a custom quarterly
schedule), which is disclosed prominently in the report.
"""
import json
import pandas as pd

from backtest10 import build_index, rebalance_dates, cumret_drawdown, series_to_points, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes, fetch_gold_cleaned, blend_50_50, metrics, TOP_N, MIN_ELIGIBLE

REBALANCE_MONTHS = (2, 5, 8, 11)


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    midcap = fetch("MID150BEES.NS")

    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]

    index_level, selections = build_index(closes, top_n=TOP_N, min_eligible=MIN_ELIGIBLE, rebalance_months=REBALANCE_MONTHS)
    start_date, end_date = index_level.index[0], index_level.index[-1]

    long_common = nifty.index[(nifty.index >= start_date) & (nifty.index <= end_date)]
    long_common = long_common.intersection(index_level.index)
    momentum_series = index_level.loc[long_common]
    nifty_series = nifty.loc[long_common, "Close"]
    midcap_common = long_common[long_common.isin(midcap.index)]
    midcap_series = midcap.loc[midcap_common, "Close"]

    def norm(s):
        return s / s.iloc[0] * 100.0

    with open("results13.json") as f:
        semiannual = json.load(f)

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "universe_size": len(closes.columns), "top_n": TOP_N,
        "rebalance_months": list(REBALANCE_MONTHS),
        "start_date": start_date.strftime("%Y-%m-%d"), "end_date": end_date.strftime("%Y-%m-%d"),
        "midcap_start_date": midcap_series.index[0].strftime("%Y-%m-%d"),
        "num_rebalances": len(selections),
        "selections_sample": selections[:3] + selections[-3:] if len(selections) > 6 else selections,
        "momentum20_quarterly": {"equity_curve": series_to_points(norm(momentum_series)), **metrics(momentum_series)},
        "momentum20_semiannual": semiannual["momentum20"],
        "nifty": {"equity_curve": series_to_points(norm(nifty_series)), **metrics(nifty_series)},
        "midcap": {"equity_curve": series_to_points(norm(midcap_series)), **metrics(midcap_series)},
    }
    with open("results14.json", "w") as f:
        json.dump(results, f)

    print("start", start_date.date(), "end", end_date.date(), "rebalances", len(selections))
    for k in ("momentum20_quarterly", "momentum20_semiannual", "nifty", "midcap"):
        v = results[k]
        print(f"[{k}] net_return={v['net_return_pct']:.1f}% cagr={v['cagr_pct']:.2f}% "
              f"mdd={v['max_drawdown_pct']:.1f}% uw_days={v['longest_underwater_days']}")


if __name__ == "__main__":
    main()

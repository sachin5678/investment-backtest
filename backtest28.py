"""
"NIFTY100 Momentum 5" — a new, more concentrated variant of report 12's
"NIFTY100 Momentum 10" (itself NOT a real NSE index — see backtest11.py's
docstring). Same universe (today's NIFTY 100 constituent list), same
exact 6m/12m risk-adjusted momentum formula, same June/December rebalance
— only the portfolio size changes: top 5 instead of top 10, equal-weighted.

Same disclosed approximations as backtest11.py/backtest10.py apply here:
today's fixed NIFTY 100 roster used retroactively (survivorship bias),
equal-weighting instead of free-float-market-cap x score, no
F&O-eligibility screen, June/December rebalance dates approximated as the
last trading day of the month.

Compares against: NIFTY 50 (real index), the real midcap ETF over its own
shorter available window, AND NIFTY100 Momentum 10 (report 12) recomputed
fresh over the identical common window — concentrating a momentum
portfolio from 10 names down to 5 is a real, testable question about
whether extra concentration pays off or just adds idiosyncratic risk.
"""
import json
import pandas as pd

from backtest10 import load_universe_closes, build_index, cumret_drawdown, series_to_points, fetch, CURRENCY_SYMBOL
from nifty100_symbols import NIFTY_100_SYMBOLS

TOP_N = 5
TOP_N_PARENT = 10
MIN_ELIGIBLE = 20


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


def main():
    closes_all = load_universe_closes()
    n100_tickers = [s + ".NS" for s in NIFTY_100_SYMBOLS]
    missing = [t for t in n100_tickers if t not in closes_all.columns]
    assert not missing, f"missing tickers not in cached universe: {missing}"
    closes = closes_all[n100_tickers]

    nifty = fetch("^NSEI")
    midcap = fetch("MID150BEES.NS")

    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]

    index_level_5, selections_5 = build_index(closes, top_n=TOP_N, min_eligible=MIN_ELIGIBLE)
    index_level_10, selections_10 = build_index(closes, top_n=TOP_N_PARENT, min_eligible=MIN_ELIGIBLE)

    start_date = index_level_5.index[0]
    end_date = index_level_5.index[-1]

    long_common = nifty.index[(nifty.index >= start_date) & (nifty.index <= end_date)]
    long_common = long_common.intersection(index_level_5.index).intersection(index_level_10.index)

    mom5_series = index_level_5.loc[long_common]
    mom10_series = index_level_10.loc[long_common]
    nifty_series = nifty.loc[long_common, "Close"]

    midcap_common = long_common[long_common.isin(midcap.index)]
    midcap_series = midcap.loc[midcap_common, "Close"]

    def norm(s):
        return s / s.iloc[0] * 100.0

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "universe_size": len(closes.columns), "top_n": TOP_N,
        "start_date": start_date.strftime("%Y-%m-%d"), "end_date": long_common[-1].strftime("%Y-%m-%d"),
        "midcap_start_date": midcap_series.index[0].strftime("%Y-%m-%d"),
        "num_rebalances": len(selections_5),
        "selections_sample": selections_5[:3] + selections_5[-3:] if len(selections_5) > 6 else selections_5,
        "momentum5": {
            "equity_curve": series_to_points(norm(mom5_series)),
            **metrics(mom5_series),
        },
        "momentum10": {
            "equity_curve": series_to_points(norm(mom10_series)),
            **metrics(mom10_series),
        },
        "nifty": {
            "equity_curve": series_to_points(norm(nifty_series)),
            **metrics(nifty_series),
        },
        "midcap": {
            "equity_curve": series_to_points(norm(midcap_series)),
            **metrics(midcap_series),
        },
    }
    with open("results27.json", "w") as f:
        json.dump(results, f)

    print("start", results["start_date"], "end", results["end_date"], "rebalances", results["num_rebalances"])
    for k in ("momentum5", "momentum10", "nifty", "midcap"):
        v = results[k]
        print(f"[{k}] net_return={v['net_return_pct']:.1f}% cagr={v['cagr_pct']:.2f}% "
              f"mdd={v['max_drawdown_pct']:.1f}% uw_days={v['longest_underwater_days']}")
    print("\nfirst rebalance:", results["selections_sample"][0]["date"], results["selections_sample"][0]["tickers"])
    print("last rebalance:", results["selections_sample"][-1]["date"], results["selections_sample"][-1]["tickers"])


if __name__ == "__main__":
    main()

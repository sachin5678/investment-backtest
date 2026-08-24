"""
"NIFTY100 Momentum 10" reconstruction — NOTE: this is NOT an official NSE
index. Searched for it directly; the real NSE momentum family is NIFTY200
Momentum 30, NIFTY500 Momentum 50, and Midcap/Smallcap "Momentum Quality"
variants — no "NIFTY100 Momentum 10" (or Momentum 30) exists. This report
applies the exact same published Momentum 30 formula used in the last report
to a smaller, more concentrated setup instead: universe = NIFTY 100 (today's
list, fetched fresh from NSE's archive), top 10 selected instead of top 30 —
as a clearly-labelled custom variant, not a real product.

Same disclosed approximations as backtest10.py apply here: today's fixed
NIFTY 100 roster used retroactively (survivorship bias), equal-weighting
instead of free-float-market-cap x score, no F&O-eligibility screen,
June/December rebalance dates approximated as last trading day of the month.
All 100 of today's NIFTY 100 constituents were already present in the
NIFTY 200 universe fetched for the last report, so no new data download was
needed — same cached price history (universe_raw.pkl) is reused here.
"""
import json
import pandas as pd

from backtest10 import load_universe_closes, build_index, cumret_drawdown, series_to_points, fetch, CURRENCY_SYMBOL
from nifty100_symbols import NIFTY_100_SYMBOLS

TOP_N = 10
MIN_ELIGIBLE = 20   # scaled down proportionally from the 200-universe/40-min-eligible rule


def build():
    closes_all = load_universe_closes()
    n100_tickers = [s + ".NS" for s in NIFTY_100_SYMBOLS]
    missing = [t for t in n100_tickers if t not in closes_all.columns]
    assert not missing, f"missing tickers not in cached universe: {missing}"
    closes = closes_all[n100_tickers]

    nifty = fetch("^NSEI")
    midcap = fetch("MID150BEES.NS")

    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]

    index_level, selections = build_index(closes, top_n=TOP_N, min_eligible=MIN_ELIGIBLE)
    start_date = index_level.index[0]
    end_date = index_level.index[-1]

    long_common = nifty.index[(nifty.index >= start_date) & (nifty.index <= end_date)]
    long_common = long_common.intersection(index_level.index)
    momentum_series = index_level.loc[long_common]
    nifty_series = nifty.loc[long_common, "Close"]

    midcap_common = long_common[long_common.isin(midcap.index)]
    midcap_series = midcap.loc[midcap_common, "Close"]

    def norm(s):
        return s / s.iloc[0] * 100.0

    mdd_m, peak_m, trough_m, uw_m = cumret_drawdown(momentum_series, pd.Series(1.0, index=momentum_series.index))
    mdd_n, peak_n, trough_n, uw_n = cumret_drawdown(nifty_series, pd.Series(1.0, index=nifty_series.index))
    mdd_mc, peak_mc, trough_mc, uw_mc = cumret_drawdown(midcap_series, pd.Series(1.0, index=midcap_series.index))

    def cagr_of(s):
        years = (s.index[-1] - s.index[0]).days / 365.25
        return float((s.iloc[-1] / s.iloc[0]) ** (1 / years) * 100 - 100)

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "universe_size": len(closes.columns), "top_n": TOP_N,
        "start_date": start_date.strftime("%Y-%m-%d"), "end_date": end_date.strftime("%Y-%m-%d"),
        "midcap_start_date": midcap_series.index[0].strftime("%Y-%m-%d"),
        "num_rebalances": len(selections),
        "selections_sample": selections[:3] + selections[-3:] if len(selections) > 6 else selections,
        "reconstructed_momentum": {
            "equity_curve": series_to_points(norm(momentum_series)),
            "net_return_pct": float((momentum_series.iloc[-1] / momentum_series.iloc[0] - 1) * 100),
            "cagr_pct": cagr_of(momentum_series),
            "max_drawdown_pct": mdd_m, "max_drawdown_peak_date": peak_m, "max_drawdown_trough_date": trough_m,
            "longest_underwater_days": uw_m,
        },
        "nifty": {
            "equity_curve": series_to_points(norm(nifty_series)),
            "net_return_pct": float((nifty_series.iloc[-1] / nifty_series.iloc[0] - 1) * 100),
            "cagr_pct": cagr_of(nifty_series),
            "max_drawdown_pct": mdd_n, "max_drawdown_peak_date": peak_n, "max_drawdown_trough_date": trough_n,
            "longest_underwater_days": uw_n,
        },
        "midcap": {
            "equity_curve": series_to_points(norm(midcap_series)),
            "net_return_pct": float((midcap_series.iloc[-1] / midcap_series.iloc[0] - 1) * 100),
            "cagr_pct": cagr_of(midcap_series),
            "max_drawdown_pct": mdd_mc, "max_drawdown_peak_date": peak_mc, "max_drawdown_trough_date": trough_mc,
            "longest_underwater_days": uw_mc,
        },
    }
    return results


if __name__ == "__main__":
    r = build()
    with open("results11.json", "w") as f:
        json.dump(r, f)
    print("start", r["start_date"], "end", r["end_date"], "rebalances", r["num_rebalances"])
    for k in ("reconstructed_momentum", "nifty", "midcap"):
        v = r[k]
        print(f"[{k}] net_return={v['net_return_pct']:.1f}% cagr={v['cagr_pct']:.2f}% "
              f"mdd={v['max_drawdown_pct']:.1f}% uw_days={v['longest_underwater_days']}")
    print("\nfirst rebalance:", r["selections_sample"][0]["date"], r["selections_sample"][0]["tickers"])
    print("last rebalance:", r["selections_sample"][-1]["date"], r["selections_sample"][-1]["tickers"])

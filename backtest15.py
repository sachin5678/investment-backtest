"""
Three custom momentum reconstructions, compared side by side:
  - Smallcap250 Momentum 20
  - Smallcap250 Momentum 10
  - Midcap150 Momentum 10

NONE of these are official NSE products. The real smallcap momentum-family
index is Nifty Smallcap250 Momentum QUALITY 100 — a momentum+quality HYBRID
score (different formula, includes ROE/D-E/EPS terms), top 100, capped 3%.
There is no pure-momentum-only smallcap NSE index. The real midcap one is
Nifty Midcap150 Momentum 50 (top 50, not top 10) — same situation as the
"Momentum 20" custom variant from an earlier report. All three reconstructions
here use the same PURE momentum formula applied throughout this project (6m/
12m risk-adjusted return, z-scored, asymmetrically normalised), just with
different universes and top-N counts — an apples-to-apples comparison of
"what does a smaller/larger, smallcap/midcap momentum sleeve look like,"
not a simulation of any real index.

Same disclosed approximations as every reconstruction in this series:
today's fixed universe used retroactively (survivorship bias — plausibly
strongest here for smallcaps, whose membership churns even more than
midcaps'), equal weighting instead of free-float-market-cap x score, no
F&O-eligibility screen, rebalance dates approximated as last trading day of
June/December (smallcap has no real momentum index to anchor a rebalance
calendar to, so this reuses the NIFTY200 Momentum 30 convention rather than
inventing a third one).

2 of the 250 smallcap tickers (SONACOMS.NS, KIMS.NS) returned no price data
from Yahoo Finance at all and are excluded — a data-availability gap, not a
judgment call.

Benchmark: NIFTYSMLCAP250.NS (the real, un-reconstructed NIFTY Smallcap 250
index itself — 21 years of history, no reconstruction needed) alongside
NIFTY 50 and the Midcap 150 ETF.
"""
import json
import pandas as pd

from backtest10 import build_index, cumret_drawdown, series_to_points, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes, metrics
from niftysmallcap250_symbols import NIFTY_SMALLCAP250_SYMBOLS

MIN_ELIGIBLE_SMALLCAP = 40
MIN_ELIGIBLE_MIDCAP = 30


def load_smallcap250_closes():
    raw200 = pd.read_pickle("universe_raw.pkl")
    extra_q = pd.read_pickle("quality50_extra_raw.pkl")
    extra_m = pd.read_pickle("midcap150_extra_raw.pkl")
    extra_s = pd.read_pickle("smallcap250_extra_raw.pkl")
    sources = (raw200, extra_q, extra_m, extra_s)

    cols = {}
    for sym in NIFTY_SMALLCAP250_SYMBOLS:
        t = sym + ".NS"
        for src in sources:
            if t in set(c[0] for c in src.columns):
                s = src[(t, "Close")]
                if s.notna().any():
                    cols[t] = s
                break
    closes = pd.DataFrame(cols).sort_index().ffill()
    return closes


def run_one(closes, top_n, min_eligible, nifty, label):
    index_level, selections = build_index(closes, top_n=top_n, min_eligible=min_eligible, rebalance_months=(6, 12))
    start_date, end_date = index_level.index[0], index_level.index[-1]
    long_common = nifty.index[(nifty.index >= start_date) & (nifty.index <= end_date)]
    long_common = long_common.intersection(index_level.index)
    series = index_level.loc[long_common]
    return {
        "label": label, "start_date": start_date.strftime("%Y-%m-%d"), "end_date": end_date.strftime("%Y-%m-%d"),
        "num_rebalances": len(selections),
        "selections_sample": selections[:2] + selections[-2:] if len(selections) > 4 else selections,
        "equity_curve": series_to_points(series / series.iloc[0] * 100.0),
        **metrics(series),
    }, long_common


def bench_metrics(series_full, common_dates):
    common = series_full.index.intersection(common_dates)
    s = series_full.loc[common]
    return {"equity_curve": series_to_points(s / s.iloc[0] * 100.0), **metrics(s)}


def main():
    smallcap_closes = load_smallcap250_closes()
    midcap_closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    midcap_etf = fetch("MID150BEES.NS")
    smallcap_idx = fetch("NIFTYSMLCAP250.NS")

    sc_common = smallcap_closes.index.intersection(nifty.index)
    smallcap_closes = smallcap_closes.loc[sc_common]
    mc_common = midcap_closes.index.intersection(nifty.index)
    midcap_closes = midcap_closes.loc[mc_common]

    sc20, sc20_dates = run_one(smallcap_closes, 20, MIN_ELIGIBLE_SMALLCAP, nifty, "Smallcap250 Momentum 20")
    sc10, sc10_dates = run_one(smallcap_closes, 10, MIN_ELIGIBLE_SMALLCAP, nifty, "Smallcap250 Momentum 10")
    mc10, mc10_dates = run_one(midcap_closes, 10, MIN_ELIGIBLE_MIDCAP, nifty, "Midcap150 Momentum 10")

    # a common window across all three, for the headline comparison
    common_all = sc20_dates.intersection(sc10_dates).intersection(mc10_dates)

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "smallcap_universe_size": len(smallcap_closes.columns),
        "midcap_universe_size": len(midcap_closes.columns),
        "excluded_smallcap_tickers": ["SONACOMS.NS", "KIMS.NS"],
        "common_start": common_all[0].strftime("%Y-%m-%d"), "common_end": common_all[-1].strftime("%Y-%m-%d"),
        "midcap_etf_start": "2019-02-04",
        "smallcap20": sc20, "smallcap10": sc10, "midcap10": mc10,
        "nifty": bench_metrics(nifty["Close"], common_all),
        "smallcap_index": bench_metrics(smallcap_idx["Close"], common_all),
        "midcap_etf": bench_metrics(midcap_etf["Close"], common_all),
    }
    with open("results15.json", "w") as f:
        json.dump(results, f)

    for k in ("smallcap20", "smallcap10", "midcap10", "nifty", "smallcap_index", "midcap_etf"):
        v = results[k]
        print(f"[{k}] start={v.get('start_date','(bench)')} net_return={v['net_return_pct']:.1f}% "
              f"cagr={v['cagr_pct']:.2f}% mdd={v['max_drawdown_pct']:.1f}% uw_days={v['longest_underwater_days']}")


if __name__ == "__main__":
    main()

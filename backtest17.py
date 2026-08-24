"""
Three more custom momentum reconstructions, each at its universe's real,
normal rebalance cadence (not monthly — report 16 already covered that):

  - Midcap150 Momentum 30   (real index is Midcap150 Momentum 50 — top 50;
                              this is top 30. Cadence: May/November, the
                              real one, same as report 14's Momentum-20.)
  - NIFTY500 Momentum 10    (real index is NIFTY500 Momentum 50 — top 50;
                              this is top 10. Cadence: June/December — this
                              IS the real index's actual cadence, confirmed
                              via NSE's published methodology, unlike the
                              "borrowed convention" used for the smallcap
                              reconstructions in report 16.)
  - NIFTY500 Momentum 15    (same universe and cadence as the top-10
                              version, just top 15 instead.)

None of the three top-N counts are real NSE products (the real index always
selects 50) — only the UNIVERSE and REBALANCE MONTHS are real here. Same
disclosed approximations as every reconstruction in this series: today's
fixed universe used retroactively (survivorship bias), equal weighting
instead of free-float-market-cap x score, no F&O-eligibility screen.

All required price data was already fetched for earlier reports — NIFTY 500
is exactly the union of NIFTY 100 + Midcap 150 + Smallcap 250 (confirmed:
500 = 100 + 150 + 250, matching NSE's own segmentation), and all of it is
already cached from reports 11-16. No new downloads needed.
"""
import json
import pandas as pd

from backtest10 import build_index, cumret_drawdown, series_to_points, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes, metrics
from nifty500_symbols import NIFTY_500_SYMBOLS

MIN_ELIGIBLE_MIDCAP = 30
MIN_ELIGIBLE_NIFTY500 = 80


def load_nifty500_closes():
    raw200 = pd.read_pickle("universe_raw.pkl")
    extra_q = pd.read_pickle("quality50_extra_raw.pkl")
    extra_m = pd.read_pickle("midcap150_extra_raw.pkl")
    extra_s = pd.read_pickle("smallcap250_extra_raw.pkl")
    sources = (raw200, extra_q, extra_m, extra_s)

    cols = {}
    for sym in NIFTY_500_SYMBOLS:
        t = sym + ".NS"
        for src in sources:
            if t in set(c[0] for c in src.columns):
                s = src[(t, "Close")]
                if s.notna().any():
                    cols[t] = s
                break
    closes = pd.DataFrame(cols).sort_index().ffill()
    return closes


def run_one(closes, top_n, min_eligible, rebalance_months, nifty, label):
    index_level, selections = build_index(closes, top_n=top_n, min_eligible=min_eligible, rebalance_months=rebalance_months)
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
    midcap_closes = load_midcap150_closes()
    n500_closes = load_nifty500_closes()
    nifty = fetch("^NSEI")
    midcap_etf = fetch("MID150BEES.NS")

    midcap_closes = midcap_closes.loc[midcap_closes.index.intersection(nifty.index)]
    n500_closes = n500_closes.loc[n500_closes.index.intersection(nifty.index)]

    mc30, mc30_dates = run_one(midcap_closes, 30, MIN_ELIGIBLE_MIDCAP, (5, 11), nifty, "Midcap150 Momentum 30")
    n500_10, n10_dates = run_one(n500_closes, 10, MIN_ELIGIBLE_NIFTY500, (6, 12), nifty, "NIFTY500 Momentum 10")
    n500_15, n15_dates = run_one(n500_closes, 15, MIN_ELIGIBLE_NIFTY500, (6, 12), nifty, "NIFTY500 Momentum 15")

    common_all = mc30_dates.intersection(n10_dates).intersection(n15_dates)

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "midcap_universe_size": len(midcap_closes.columns),
        "nifty500_universe_size": len(n500_closes.columns),
        "common_start": common_all[0].strftime("%Y-%m-%d"), "common_end": common_all[-1].strftime("%Y-%m-%d"),
        "midcap_etf_start": "2019-02-04",
        "midcap30": mc30, "nifty500_10": n500_10, "nifty500_15": n500_15,
        "nifty": bench_metrics(nifty["Close"], common_all),
        "midcap_etf": bench_metrics(midcap_etf["Close"], common_all),
    }
    with open("results17.json", "w") as f:
        json.dump(results, f)

    for k in ("midcap30", "nifty500_10", "nifty500_15", "nifty", "midcap_etf"):
        v = results[k]
        print(f"[{k}] start={v.get('start_date','(bench)')} net_return={v['net_return_pct']:.1f}% "
              f"cagr={v['cagr_pct']:.2f}% mdd={v['max_drawdown_pct']:.1f}% uw_days={v['longest_underwater_days']}")


if __name__ == "__main__":
    main()

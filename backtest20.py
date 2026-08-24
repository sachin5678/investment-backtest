"""
"NASDAQ100 Momentum 10" — the same reconstruction methodology used
throughout this project (reports 11, 12, 14-19), applied to a market
outside India for the first time: the Nasdaq-100.

NOT a real, official index. Nasdaq does not publish a "Nasdaq-100 Momentum"
factor index the way NSE does for NIFTY (no Nasdaq equivalent of NIFTY200
Momentum 30 exists) — this is a custom construction, same situation as
"NIFTY100 Momentum 10" (report 12) and every other "Momentum N" variant in
this project that isn't a real NSE product.

METHODOLOGY (identical formula to every reconstruction in this project):
  - Universe: today's 102 Nasdaq-100 constituents (fetched from
    slickcharts.com, nasdaq100_symbols.py), applied retroactively as far
    back as each stock's own price history allows — the same survivorship
    bias disclosed in every reconstruction here, arguably STRONGER for a
    growth-heavy tech index than for NIFTY: several of today's constituents
    (Palantir, CoreWeave, SpaceX, Nebius, Rocket Lab, Astera Labs...) IPO'd
    very recently and would not have been "in" any Nasdaq-100 reconstruction
    a decade ago even though this backtest's eligibility screen lets the
    OTHER 90+ names carry the early years.
  - Per-stock momentum score: 6-month and 12-month price return, each
    divided by trailing-1-year daily-return volatility, Z-scored
    cross-sectionally, combined 0.5*Z(6m)+0.5*Z(12m), asymmetrically
    normalised — the exact same formula as every other reconstruction here.
  - Top 10 by score, equal-weighted (not free-float market cap x score —
    no official index to defer to for a weighting rule here either).
  - Rebalanced June/December — a borrowed convention (matching this
    project's NIFTY200 Momentum cadence), not a real Nasdaq-100 rebalance
    schedule, since none exists for this custom construction.
  - No F&O-eligibility screen (doesn't apply to US equities in this
    project's data sources anyway).

Benchmarks: QQQ (the real, tradable Invesco Nasdaq-100 ETF — full history,
no reconstruction needed) and the S&P 500 (^GSPC) as the broad US market
reference — the same "custom construction vs. the real ETF vs. the broad
market" structure used for every Indian reconstruction in this project.
Everything in this report is in USD; no currency conversion or FX-hedging
assumption is made anywhere (see build_html21.py for the one cross-market
comparison this makes, clearly caveated).

ALSO computes a LAST-5-YEARS slice of the identical strategy (same
rebalance selections, same formula — just windowed to the most recent 5
years and rebased to 100 at that window's own start) specifically because
the full-history number above is dominated by a survivorship bias that is
much weaker over a recent 5-year window: today's 102-constituent list is a
far more accurate reflection of the ACTUAL investable Nasdaq-100 5 years
ago than it is of the year 2000.

ALSO computes a direct comparison against Midcap150 Momentum 10 (report
16), both recomputed at full daily resolution and intersected onto the
SAME calendar window — which, because Midcap150 Momentum 10's own history
only starts 2008-12-31, naturally becomes "2009 to today." QQQ and NIFTY 50
are included as each market's own real benchmark over that identical
window. No currency conversion is applied anywhere: this compares each
market's own LOCAL-CURRENCY growth (USD vs INR), not a single real
investor's actual cross-border return — see build_html21.py's explicit
disclosure on this.
"""
import json

import numpy as np
import pandas as pd

from backtest10 import build_index, cumret_drawdown, series_to_points, rebalance_dates, fetch
from backtest13 import metrics, load_midcap150_closes
from nasdaq100_symbols import NASDAQ_100_SYMBOLS

MIDCAP_TOP_N = 10
MIDCAP_MIN_ELIGIBLE = 30

TOP_N = 10
MIN_ELIGIBLE = 20
CURRENCY_SYMBOL = "$"


def fetch_us(ticker):
    import yfinance as yf
    df = yf.download(ticker, period="max", auto_adjust=False, progress=False)
    df.columns = df.columns.droplevel(1)
    df = df[["Open", "High", "Low", "Close"]].dropna()
    df.index = pd.to_datetime(df.index)
    return df.sort_index()


def load_nasdaq100_closes():
    raw = pd.read_pickle("nasdaq100_raw.pkl")
    tickers = sorted(set(c[0] for c in raw.columns))
    cols = {}
    for t in tickers:
        s = raw[(t, "Close")]
        if s.notna().any():
            cols[t] = s
    closes = pd.DataFrame(cols).sort_index().ffill()
    return closes


def main():
    closes = load_nasdaq100_closes()
    qqq = fetch_us("QQQ")
    spx = fetch_us("^GSPC")

    common = closes.index.intersection(qqq.index)
    closes = closes.loc[common]

    index_level, selections = build_index(closes, top_n=TOP_N, min_eligible=MIN_ELIGIBLE, rebalance_months=(6, 12))
    start_date, end_date = index_level.index[0], index_level.index[-1]

    win = qqq.index[(qqq.index >= start_date) & (qqq.index <= end_date)]
    win = win.intersection(index_level.index).intersection(spx.index)
    mom_series = index_level.loc[win]
    qqq_series = qqq.loc[win, "Close"]
    spx_series = spx.loc[win, "Close"]

    def norm(s):
        return s / s.iloc[0] * 100.0

    # last-5-years slice: the SAME momentum selections/equity curve computed
    # above (each rebalance still uses its own full trailing 6m/12m history,
    # exactly as the real strategy would), just windowed down to the most
    # recent 5 years and rebased to 100 at that window's own start — a much
    # lower-survivorship-bias period than the full 2000-2026 span, since
    # today's 102-constituent list is a far more accurate reflection of
    # what was actually investable 5 years ago than it is of 2000.
    five_yr_start = win[-1] - pd.DateOffset(years=5)
    win_5y = win[win >= five_yr_start]
    mom_5y, qqq_5y, spx_5y = norm(mom_series.loc[win_5y]), norm(qqq_series.loc[win_5y]), norm(spx_series.loc[win_5y])
    selections_5y = [s for s in selections if s["date"] >= win_5y[0].strftime("%Y-%m-%d")]

    # vs. Midcap150 Momentum 10 (report 16), same window, both recomputed at
    # FULL daily resolution (not read back from either report's own
    # downsampled equity_curve JSON) so the common-window intersection and
    # rebasing are exact. Midcap150 Momentum 10's own history only starts
    # 2008-12-31, so the common window here naturally becomes "2009 to
    # today" once intersected against NASDAQ100 Momentum-10's much longer
    # 2000+ series. Currency is NOT converted anywhere — this compares each
    # market's own LOCAL-CURRENCY growth, not a single investor's real
    # cross-border return; see build_html21.py for the explicit disclosure.
    nifty = fetch("^NSEI")
    midcap_closes = load_midcap150_closes()
    midcap_closes = midcap_closes.loc[midcap_closes.index.intersection(nifty.index)]
    midcap_mom_level, _ = build_index(midcap_closes, top_n=MIDCAP_TOP_N, min_eligible=MIDCAP_MIN_ELIGIBLE, rebalance_months=(6, 12))

    # QQQ and NIFTY 50 both have full history well before 2009, so — unlike
    # MID150BEES.NS (the tradable midcap ETF, which only starts 2019-02-04
    # and is therefore deliberately left OUT of this specific comparison to
    # avoid forcing a series onto a rebase point it has no data at) — both
    # can share the exact same common_vs window and rebase point as the two
    # momentum reconstructions below.
    common_vs = mom_series.index.intersection(midcap_mom_level.index).intersection(nifty.index)
    nasdaq_vs, midcap_vs = norm(mom_series.loc[common_vs]), norm(midcap_mom_level.loc[common_vs])
    qqq_vs = norm(qqq_series.loc[qqq_series.index.intersection(common_vs)])
    nifty_vs = norm(nifty.loc[common_vs, "Close"])

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "universe_size": len(closes.columns),
        "start_date": win[0].strftime("%Y-%m-%d"), "end_date": win[-1].strftime("%Y-%m-%d"),
        "num_rebalances": len(selections),
        "selections_sample": selections[:3] + selections[-3:] if len(selections) > 6 else selections,
        "five_year_start_date": win_5y[0].strftime("%Y-%m-%d"), "five_year_end_date": win_5y[-1].strftime("%Y-%m-%d"),
        "five_year_num_rebalances": len(selections_5y),
        "five_year_selections": selections_5y,
        "nasdaq100_momentum10": {"equity_curve": series_to_points(norm(mom_series)), **metrics(mom_series)},
        "qqq": {"equity_curve": series_to_points(norm(qqq_series)), **metrics(qqq_series)},
        "sp500": {"equity_curve": series_to_points(norm(spx_series)), **metrics(spx_series)},
        "nasdaq100_momentum10_5y": {"equity_curve": series_to_points(mom_5y), **metrics(mom_series.loc[win_5y])},
        "qqq_5y": {"equity_curve": series_to_points(qqq_5y), **metrics(qqq_series.loc[win_5y])},
        "sp500_5y": {"equity_curve": series_to_points(spx_5y), **metrics(spx_series.loc[win_5y])},
        "vs_midcap_start_date": common_vs[0].strftime("%Y-%m-%d"), "vs_midcap_end_date": common_vs[-1].strftime("%Y-%m-%d"),
        "cmp_nasdaq_momentum10": {"equity_curve": series_to_points(nasdaq_vs), **metrics(mom_series.loc[common_vs])},
        "cmp_midcap_momentum10": {"equity_curve": series_to_points(midcap_vs), **metrics(midcap_mom_level.loc[common_vs])},
        "cmp_qqq": {"equity_curve": series_to_points(qqq_vs), **metrics(qqq_series.loc[common_vs])},
        "cmp_nifty50": {"equity_curve": series_to_points(nifty_vs), **metrics(nifty.loc[common_vs, "Close"])},
    }
    with open("results20.json", "w") as f:
        json.dump(results, f)

    print("start", win[0].date(), "end", win[-1].date(), "rebalances", len(selections))
    for k in ("nasdaq100_momentum10", "qqq", "sp500"):
        v = results[k]
        print(f"[{k}] net_return={v['net_return_pct']:.1f}% cagr={v['cagr_pct']:.2f}% "
              f"mdd={v['max_drawdown_pct']:.1f}% uw_days={v['longest_underwater_days']}")
    print("\nfirst rebalance:", selections[0]["date"], selections[0]["tickers"])
    print("last rebalance:", selections[-1]["date"], selections[-1]["tickers"])

    print(f"\n--- last 5 years: {win_5y[0].date()} to {win_5y[-1].date()} ---")
    for k in ("nasdaq100_momentum10_5y", "qqq_5y", "sp500_5y"):
        v = results[k]
        print(f"[{k}] net_return={v['net_return_pct']:.1f}% cagr={v['cagr_pct']:.2f}% "
              f"mdd={v['max_drawdown_pct']:.1f}% uw_days={v['longest_underwater_days']}")
    print("5y rebalances:", len(selections_5y))
    for s in selections_5y:
        print(" ", s["date"], s["tickers"])

    print(f"\n--- vs Midcap150 Momentum 10, common window: {common_vs[0].date()} to {common_vs[-1].date()} ---")
    for k in ("cmp_nasdaq_momentum10", "cmp_midcap_momentum10", "cmp_qqq", "cmp_nifty50"):
        v = results[k]
        print(f"[{k}] net_return={v['net_return_pct']:.1f}% cagr={v['cagr_pct']:.2f}% "
              f"mdd={v['max_drawdown_pct']:.1f}% uw_days={v['longest_underwater_days']}")


if __name__ == "__main__":
    main()

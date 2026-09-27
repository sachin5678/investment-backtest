"""
Midcap150 Quality 10 — a REAL, periodically-rebalanced backtest using the
NSE Quality methodology (see quality_pit.py), analogous to report 74's
NIFTY500 Quality 50 but on this project's flagship Midcap150 universe,
top 10 instead of top 50 (10 out of 150 is proportionally close to
50 out of 500 — roughly the same ~6-7% slice of each universe).

Same short-window disclosure as report 74 applies here UNCHANGED: only
two broad, point-in-time-correct fundamentals snapshots exist in this
project's yfinance cache (FY ending 2025-03-31 and 2026-03-31), so this
is a ~14-month, one-rebalance test — not comparable in duration or
rebalance count to the 18-year momentum reports. See quality_pit.py's
own docstring for the full data-availability finding.

Same 2-calendar-month reporting lag assumption, same equal-weighting
simplification (not free-float-market-cap x quality-score), same
today's-fixed-constituent-list survivorship bias as every other
reconstruction here. Compared against Midcap150 Momentum 10 (this
project's own flagship strategy, report 11/16's real ongoing June/
December-rebalanced series, sliced to the same window — not rebuilt)
and NIFTY 50.
"""
import json

import pandas as pd

from backtest10 import fetch, CURRENCY_SYMBOL, rebalance_dates
from backtest13 import load_midcap150_closes
from backtest32 import metrics_only
from backtest33 import build_index_generic, select_top_original
from niftymidcap150_symbols import NIFTY_MIDCAP150_SYMBOLS
from quality_pit import rank_quality

TOP_N = 10
LAG_MONTHS = 2
FISCAL_YEAR_ENDS = ["2025-03-31", "2026-03-31"]


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]

    tickers = [s + ".NS" for s in NIFTY_MIDCAP150_SYMBOLS if s + ".NS" in closes.columns]

    rb_dates, schedule, universe_sizes = [], {}, []
    for fy_end in FISCAL_YEAR_ENDS:
        asof = pd.Timestamp(fy_end)
        usable_from = asof + pd.DateOffset(months=LAG_MONTHS)
        candidates = common[common >= usable_from]
        if len(candidates) == 0:
            continue
        rb_date = candidates[0]
        price_today = closes.loc[rb_date]
        priceable = [t for t in tickers if pd.notna(price_today.get(t))]
        top_n_tickers, scored_df = rank_quality(priceable, asof, TOP_N)
        if not top_n_tickers:
            continue
        rb_dates.append(rb_date)
        schedule[rb_date] = top_n_tickers
        universe_sizes.append({"fiscal_year_end": fy_end, "rebalance_date": rb_date.strftime("%Y-%m-%d"),
                                "eligible_count": len(scored_df), "basket_size": len(top_n_tickers)})

    def select_from_schedule(c, t_idx):
        d = c.index[t_idx]
        return schedule.get(d)

    quality_series, quality_sel = build_index_generic(closes, rb_dates, select_from_schedule)

    # The momentum flagship's OWN real, independent June/Dec-rebalanced
    # series, sliced (not rebuilt) to this test's short window.
    mid_rbdates = rebalance_dates(closes.index, months=(6, 12))
    momentum_series, _ = build_index_generic(closes, mid_rbdates, select_top_original)

    window_idx = quality_series.index
    momentum_window = momentum_series.loc[momentum_series.index.intersection(window_idx)]
    nifty_window = nifty_close.loc[nifty_close.index.intersection(window_idx)]

    common_idx = quality_series.index.intersection(momentum_window.index).intersection(nifty_window.index)
    quality_metrics = metrics_only(quality_series, common_idx)
    momentum_metrics = metrics_only(momentum_window, common_idx)
    nifty_metrics = metrics_only(nifty_window, common_idx)

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "lag_months": LAG_MONTHS, "top_n": TOP_N,
        "rebalance_schedule": universe_sizes,
        "quality": {**quality_metrics, "selections_sample": quality_sel},
        "momentum_flagship": momentum_metrics,
        "nifty": nifty_metrics,
    }

    with open("results74.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}")
    for u in universe_sizes:
        print(f"  {u['fiscal_year_end']} fiscal year -> rebalance {u['rebalance_date']}, "
              f"{u['eligible_count']} eligible, basket {u['basket_size']}")
    print(f"quality-10           CAGR {quality_metrics['cagr_pct']:.2f}% / DD {quality_metrics['max_drawdown_pct']:.1f}% / net {quality_metrics['net_return_pct']:.1f}%")
    print(f"momentum-10 flagship CAGR {momentum_metrics['cagr_pct']:.2f}% / DD {momentum_metrics['max_drawdown_pct']:.1f}% / net {momentum_metrics['net_return_pct']:.1f}%")
    print(f"nifty 50             CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}% / net {nifty_metrics['net_return_pct']:.1f}%")


if __name__ == "__main__":
    main()

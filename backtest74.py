"""
NIFTY500 Quality 50 — a REAL, periodically-rebalanced backtest using the
NSE Quality methodology (see quality_pit.py), unlike report 13's one-time
present-day snapshot.

WHY THE WINDOW IS SO SHORT: yfinance's cached annual balance_sheet/
financials history only goes ~3 usable fiscal years deep for most
tickers. Under the same eligibility bar report 13 already used (>=3
Diluted-EPS observations so "growth variability" is a real std of >=2
year-over-year figures, not a degenerate single-point number), a broad
NIFTY500-wide universe first becomes scoreable as of FY ending
2025-03-31 — not 2022/2023/2024. The next (and, as of this data cache,
LAST) broad snapshot is FY ending 2026-03-31. That gives exactly ONE real
rebalance event to test, not the 18-year, dozens-of-rebalances window
every momentum report in this project uses. This is disclosed prominently
below, not smoothed over.

Mechanics: a fiscal year's fundamentals are assumed usable starting 2
calendar months after fiscal year-end (a disclosed assumption — real
result-announcement timing varies by company, but 60 days is a
commonly-cited outer bound for large/mid-cap annual results under SEBI
LODR norms). So:
  - Portfolio formed 2025-06-02 using FY2025-03-31 Quality scores.
  - Rebalanced 2026-06-01 using FY2026-03-31 Quality scores.
  - Held through the end of this project's cached price data.

Same NIFTY500 universe (today's fixed constituent list, survivorship-
biased, same disclosed simplification as every other reconstruction
here), equal-weighted (not free-float-market-cap x quality-score
weighted, same simplification report 13 used) top 50 by quality score.
Compared against: NIFTY 50 (real index) and this project's own NIFTY500
Momentum 10 flagship (report 18/39's real ongoing strategy, its own June/
December cadence unchanged) — the momentum series is NOT rebuilt for this
short window, its actual full 18-year equity curve is simply sliced to
the same start/end dates as the quality strategy, for a fair "which of
our two live strategies would you rather have held over this exact
recent stretch" comparison.
"""
import json

import pandas as pd

from backtest10 import fetch, CURRENCY_SYMBOL, rebalance_dates
from backtest17 import load_nifty500_closes
from backtest32 import metrics_only
from backtest33 import build_index_generic
from backtest39 import select_top_original_n500
from nifty500_symbols import NIFTY_500_SYMBOLS
from quality_pit import rank_quality

TOP_N = 50
LAG_MONTHS = 2
FISCAL_YEAR_ENDS = ["2025-03-31", "2026-03-31"]


def main():
    closes = load_nifty500_closes()
    nifty = fetch("^NSEI")
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]

    tickers = [s + ".NS" for s in NIFTY_500_SYMBOLS if s + ".NS" in closes.columns]

    rb_dates, schedule, universe_sizes = [], {}, []
    for fy_end in FISCAL_YEAR_ENDS:
        asof = pd.Timestamp(fy_end)
        usable_from = asof + pd.DateOffset(months=LAG_MONTHS)
        candidates = common[common >= usable_from]
        if len(candidates) == 0:
            continue
        rb_date = candidates[0]
        # A ticker can have usable FUNDAMENTALS (quality_pit.py's own
        # eligibility bar) while having no PRICE yet on this exact
        # rebalance date — e.g. a name that only started trading after
        # this rebalance (a real case found here: TRAVELFOOD.NS listed
        # 2025-07-14, after the 2025-06-02 rebalance, but already had
        # fundamentals cached). Selecting it would silently corrupt the
        # whole portfolio's valuation the moment its price later turns
        # non-NaN (build_index_generic allocates shares = dollar/NaN =
        # NaN at the rebalance itself, which then poisons every day's sum
        # once that ticker's price stops being NaN) — so, same as every
        # momentum select_fn in this project, only tickers with a real
        # price on the rebalance date itself are eligible to be picked.
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
    n500_rbdates = rebalance_dates(closes.index, months=(6, 12))
    momentum_series, _ = build_index_generic(closes, n500_rbdates, select_top_original_n500)

    start_date, end_date = quality_series.index[0], quality_series.index[-1]
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

    with open("results73.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}")
    for u in universe_sizes:
        print(f"  {u['fiscal_year_end']} fiscal year -> rebalance {u['rebalance_date']}, "
              f"{u['eligible_count']} eligible, basket {u['basket_size']}")
    print(f"quality-50           CAGR {quality_metrics['cagr_pct']:.2f}% / DD {quality_metrics['max_drawdown_pct']:.1f}% / net {quality_metrics['net_return_pct']:.1f}%")
    print(f"momentum-10 flagship CAGR {momentum_metrics['cagr_pct']:.2f}% / DD {momentum_metrics['max_drawdown_pct']:.1f}% / net {momentum_metrics['net_return_pct']:.1f}%")
    print(f"nifty 50             CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}% / net {nifty_metrics['net_return_pct']:.1f}%")


if __name__ == "__main__":
    main()

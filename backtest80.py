"""
Momentum rotation across a broad, DISTINCT universe of NSE-listed ETFs —
sectoral (banking, IT, pharma, PSU banks, consumption, auto, FMCG, metal,
private banks, healthcare), smart-beta/factor (alpha, low-volatility,
quality, value), commodity (gold, silver), and international (Nasdaq 100,
FANG+, S&P 500 top 50) — instead of individual stocks. Same momentum
formula this whole project uses elsewhere (6-month and 12-month price
return, each divided by trailing-1-year daily-return volatility, cross-
sectionally Z-scored, 0.5/0.5 combined, asymmetrically normalized), top 5
held at a time, equal-weighted.

26 candidate ETF tickers were fetched fresh via yfinance (see
fetch_etf_universe.py) — 25 resolved with real, usable data (only
REALTYIETF.NS failed, not found). Their real listing dates span 2009
(NIFTYBEES/JUNIORBEES/BANKBEES/PSUBNKBEES/GOLDBEES) to as late as 2024-25
(METALIETF/MOM30IETF/VAL30IETF), so the momentum formula's own 252-day
eligibility check naturally excludes a new ETF until it has a year of its
own history — the same mechanism every stock-universe report here already
relies on, just far more consequential given how differently-aged these
ETFs are. A universe-wide MIN_ELIGIBLE=10 (confirmed empirically, not
assumed — see the mechanism note in the report) means this backtest only
becomes meaningful once 10+ of the 25 ETFs are simultaneously scoreable,
which happens ~2021 — a real, but far shorter window than the 18-year
stock-momentum reports.

Tests three rebalance cadences at the SAME top-5, same formula: monthly,
quarterly (every 3 months), and semi-annual (June/December, this
project's usual cadence) — to see whether a faster-moving ETF universe
(sector/factor rotations can be faster-moving than individual-stock
momentum) rewards more frequent rebalancing, unlike report 77's finding
on individual stocks.
"""
import json
import pickle

import pandas as pd

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest32 import metrics_only
from backtest33 import select_top_original, build_index_generic

TOP_N = 5
MIN_ELIGIBLE = 10


def load_etf_closes():
    with open("etf_universe_raw.pkl", "rb") as f:
        raw = pickle.load(f)
    cols = {t: df["Close"] for t, df in raw.items()}
    return pd.DataFrame(cols).sort_index().ffill(), sorted(raw.keys())


def main():
    closes, universe = load_etf_closes()
    nifty = fetch("^NSEI")
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]

    select_fn = lambda c, t_idx: select_top_original(c, t_idx, top_n=TOP_N, min_eligible=MIN_ELIGIBLE)

    rb_schedules = {
        "monthly": rebalance_dates(closes.index, months=tuple(range(1, 13))),
        "quarterly": rebalance_dates(closes.index, months=(3, 6, 9, 12)),
        "semiannual": rebalance_dates(closes.index, months=(6, 12)),
    }

    series_by_cadence, selections_by_cadence = {}, {}
    for label, rbdates in rb_schedules.items():
        s, sel = build_index_generic(closes, rbdates, select_fn)
        series_by_cadence[label] = s
        selections_by_cadence[label] = sel

    # Equal-weight, buy-and-hold ALL eligible ETFs at inception (rebased
    # to the earliest date any of them are all simultaneously available)
    # — a natural "does picking matter at all" benchmark, distinct from
    # NIFTY 50 (which is itself just one of the 25 candidates).
    equalweight_series = closes.pct_change().mean(axis=1).add(1).cumprod().mul(100.0)

    common_idx = None
    for s in series_by_cadence.values():
        common_idx = s.index if common_idx is None else common_idx.intersection(s.index)

    metrics = {label: metrics_only(s, common_idx) for label, s in series_by_cadence.items()}
    nifty_metrics = metrics_only(nifty_close, common_idx)
    equalweight_metrics = metrics_only(equalweight_series, common_idx)

    def sample(sel):
        return sel[:3] + sel[-3:] if len(sel) > 6 else sel

    def pick_frequency(sel):
        counts = {}
        for s in sel:
            for t in s["tickers"]:
                counts[t] = counts.get(t, 0) + 1
        return sorted(counts.items(), key=lambda kv: -kv[1])

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "top_n": TOP_N, "min_eligible": MIN_ELIGIBLE, "universe_size": len(universe), "universe": universe,
        "num_rebalances": {k: len(v) for k, v in rb_schedules.items()},
        "monthly": {**metrics["monthly"], "selections_sample": sample(selections_by_cadence["monthly"]),
                    "pick_frequency": pick_frequency(selections_by_cadence["monthly"])[:8]},
        "quarterly": {**metrics["quarterly"], "selections_sample": sample(selections_by_cadence["quarterly"]),
                      "pick_frequency": pick_frequency(selections_by_cadence["quarterly"])[:8]},
        "semiannual": {**metrics["semiannual"], "selections_sample": sample(selections_by_cadence["semiannual"]),
                       "pick_frequency": pick_frequency(selections_by_cadence["semiannual"])[:8]},
        "nifty": nifty_metrics,
        "equal_weight_all_etfs": equalweight_metrics,
    }

    with open("results79.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}")
    for label in ("monthly", "quarterly", "semiannual"):
        m = metrics[label]
        print(f"{label:<10} CAGR {m['cagr_pct']:.2f}% / DD {m['max_drawdown_pct']:.1f}% "
              f"({results['num_rebalances'][label]} rebalances)")
    print(f"nifty 50            CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")
    print(f"equal-weight all-ETF CAGR {equalweight_metrics['cagr_pct']:.2f}% / DD {equalweight_metrics['max_drawdown_pct']:.1f}%")


if __name__ == "__main__":
    main()

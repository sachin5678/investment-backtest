"""
Re-runs every custom momentum reconstruction built so far in this project,
switching each one's rebalance calendar to MONTHLY (last trading day of
every month) instead of its original cadence, and compares monthly vs.
original for each. Same formula, same universe, same top-N, same equal
weighting, same survivorship-bias caveat as every report in this series —
only the rebalance frequency changes.

The six reconstructions carried over from earlier reports:
  A. NIFTY200 Momentum 30      (report 11) — original cadence: June/December
  B. NIFTY100 Momentum 10      (report 12) — original cadence: June/December
  C. Midcap150 Momentum 20     (report 14) — original cadence: May/November
  D. Smallcap250 Momentum 20   (report 16) — original cadence: June/December
  E. Smallcap250 Momentum 10   (report 16) — original cadence: June/December
  F. Midcap150 Momentum 10     (report 16) — original cadence: June/December

("Momentum-20 quarterly" from report 15 and the gold blend from report 14
are variants/portfolios built on top of a momentum reconstruction, not a
fresh reconstruction themselves, so they're not re-run here.)

Monthly rebalancing means 12x the reshuffles of the semi-annual originals
(or 6x the May/November original) — and, as with the quarterly report, this
comparison models ZERO transaction costs for any cadence, so it is
structurally biased in favour of whichever schedule trades most often.
"""
import json
import pandas as pd

from backtest10 import load_universe_closes, build_index, cumret_drawdown, series_to_points, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes, metrics
from backtest15 import load_smallcap250_closes
from nifty100_symbols import NIFTY_100_SYMBOLS

MONTHLY = tuple(range(1, 13))

CONFIGS = [
    {"key": "nifty200_top30", "label": "NIFTY200 Momentum 30", "top_n": 30, "min_eligible": 40,
     "universe": "nifty200", "original_file": "results10.json", "original_key": "reconstructed_momentum",
     "original_cadence": "June/December"},
    {"key": "nifty100_top10", "label": "NIFTY100 Momentum 10", "top_n": 10, "min_eligible": 20,
     "universe": "nifty100", "original_file": "results11.json", "original_key": "reconstructed_momentum",
     "original_cadence": "June/December"},
    {"key": "midcap150_top20", "label": "Midcap150 Momentum 20", "top_n": 20, "min_eligible": 30,
     "universe": "midcap150", "original_file": "results13.json", "original_key": "momentum20",
     "original_cadence": "May/November"},
    {"key": "smallcap250_top20", "label": "Smallcap250 Momentum 20", "top_n": 20, "min_eligible": 40,
     "universe": "smallcap250", "original_file": "results15.json", "original_key": "smallcap20",
     "original_cadence": "June/December"},
    {"key": "smallcap250_top10", "label": "Smallcap250 Momentum 10", "top_n": 10, "min_eligible": 40,
     "universe": "smallcap250", "original_file": "results15.json", "original_key": "smallcap10",
     "original_cadence": "June/December"},
    {"key": "midcap150_top10", "label": "Midcap150 Momentum 10", "top_n": 10, "min_eligible": 30,
     "universe": "midcap150", "original_file": "results15.json", "original_key": "midcap10",
     "original_cadence": "June/December"},
]


def load_universes(nifty):
    nifty200 = load_universe_closes()
    nifty200 = nifty200.loc[nifty200.index.intersection(nifty.index)]

    nifty100_tickers = [s + ".NS" for s in NIFTY_100_SYMBOLS]
    nifty100 = nifty200[nifty100_tickers]

    midcap150 = load_midcap150_closes()
    midcap150 = midcap150.loc[midcap150.index.intersection(nifty.index)]

    smallcap250 = load_smallcap250_closes()
    smallcap250 = smallcap250.loc[smallcap250.index.intersection(nifty.index)]

    return {"nifty200": nifty200, "nifty100": nifty100, "midcap150": midcap150, "smallcap250": smallcap250}


def run_monthly(closes, top_n, min_eligible, nifty):
    index_level, selections = build_index(closes, top_n=top_n, min_eligible=min_eligible, rebalance_months=MONTHLY)
    start_date, end_date = index_level.index[0], index_level.index[-1]
    long_common = nifty.index[(nifty.index >= start_date) & (nifty.index <= end_date)]
    long_common = long_common.intersection(index_level.index)
    series = index_level.loc[long_common]
    return {
        "start_date": start_date.strftime("%Y-%m-%d"), "end_date": end_date.strftime("%Y-%m-%d"),
        "num_rebalances": len(selections),
        "equity_curve": series_to_points(series / series.iloc[0] * 100.0),
        **metrics(series),
    }


def main():
    nifty = fetch("^NSEI")
    universes = load_universes(nifty)

    results = {"generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"), "currency_symbol": CURRENCY_SYMBOL,
               "configs": {}}

    for cfg in CONFIGS:
        closes = universes[cfg["universe"]]
        monthly = run_monthly(closes, cfg["top_n"], cfg["min_eligible"], nifty)
        with open(cfg["original_file"]) as f:
            orig_full = json.load(f)
        original = orig_full[cfg["original_key"]]
        results["configs"][cfg["key"]] = {
            "label": cfg["label"], "original_cadence": cfg["original_cadence"],
            "monthly": monthly, "original": original,
        }
        print(f"[{cfg['key']}] monthly: cagr={monthly['cagr_pct']:.2f}% mdd={monthly['max_drawdown_pct']:.1f}% "
              f"rebalances={monthly['num_rebalances']}  |  original ({cfg['original_cadence']}): "
              f"cagr={original['cagr_pct']:.2f}% mdd={original['max_drawdown_pct']:.1f}%")

    with open("results16.json", "w") as f:
        json.dump(results, f)


if __name__ == "__main__":
    main()

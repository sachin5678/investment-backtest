"""
Midcap150 Momentum 10 — every possible semi-annual rebalance OFFSET,
compared. The "normal" strategy used throughout this project (reports
11-19, 24) rebalances every June and December. But "6 months apart" can
start from any month: Jan/Jul, Feb/Aug, Mar/Sep, Apr/Oct, May/Nov, or
Jun/Dec — six equally valid ways to run the exact same rule with the
calendar just shifted. This report runs all six over the SAME full
2008-2026 history, same universe, same top-10/equal-weight/6m-12m-momentum
formula — only the rebalance month-pair changes — to see how much of the
"normal" (Jun/Dec) result is the rule itself vs. which 2 months of the
year it happens to check momentum on.

Every stock's momentum score depends on price levels exactly 6 and 12
months before the rebalance date, so a different offset genuinely samples
different trailing windows and can select a different top 10 — this is
not just a labeling change.
"""
import json

import numpy as np
import pandas as pd

from backtest10 import build_index, cumret_drawdown, series_to_points, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes, metrics

TOP_N = 10
MIN_ELIGIBLE = 30

MONTH_NAME = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
              7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}

OFFSETS = [(1, 7), (2, 8), (3, 9), (4, 10), (5, 11), (6, 12)]


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]

    configs = {}
    for m1, m2 in OFFSETS:
        key = f"{MONTH_NAME[m1].lower()}_{MONTH_NAME[m2].lower()}"
        label = f"{MONTH_NAME[m1]}/{MONTH_NAME[m2]}"
        index_level, selections = build_index(closes, top_n=TOP_N, min_eligible=MIN_ELIGIBLE, rebalance_months=(m1, m2))
        start_date, end_date = index_level.index[0], index_level.index[-1]

        def norm(s):
            return s / s.iloc[0] * 100.0

        series_norm = norm(index_level)
        configs[key] = {
            "label": label, "is_normal": (m1, m2) == (6, 12),
            "start_date": start_date.strftime("%Y-%m-%d"), "end_date": end_date.strftime("%Y-%m-%d"),
            "num_rebalances": len(selections),
            "equity_curve": series_to_points(series_norm),
            **metrics(index_level),
        }
        m = configs[key]
        print(f"[{label}] cagr={m['cagr_pct']:.2f}% mdd={m['max_drawdown_pct']:.1f}% "
              f"net={m['net_return_pct']:.1f}% rebalances={m['num_rebalances']}")

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "configs": configs,
    }
    with open("results24.json", "w") as f:
        json.dump(results, f)
    print("wrote results24.json")


if __name__ == "__main__":
    main()

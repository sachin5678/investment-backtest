"""
Midcap150 Momentum 10 — RELATIVE momentum (excess return over NIFTY 50)
vs. the original ABSOLUTE momentum formula.

The original formula ranks stocks on their own 6m/12m risk-adjusted
return, absolute — a stock scores well simply for having gone up a lot,
regardless of what the broad market did over the same stretch. This
report tests a genuinely different formula: rank on EXCESS return over
NIFTY 50 instead — `(stock's 6m/12m return) - (NIFTY 50's 6m/12m return
over the identical window)` — before the same risk-adjustment,
cross-sectional Z-scoring, 0.5/0.5 combination, and asymmetric
normalization as always. Only the return quantity being ranked changes;
every other mechanic (top-10, equal-weight, June/December rebalance,
Midcap150 universe, the stock's own volatility as the risk-adjustment
denominator) is identical to reports 11-19/24-33.

WHY THIS IS A REAL, NOT COSMETIC, CHANGE: in a strong broad bull market,
absolute momentum can rank a stock highly just for "going up with
everything else," even if it's actually a laggard relative to the market.
Relative momentum specifically isolates stocks beating the tide, not
riding it — a stock with the same absolute return in a rising market
scores LOWER here than it would under the original formula, while a stock
that fell less than the market during a downturn can score HIGHER even
with a negative absolute return.

WHY NIFTY 50, NOT THE MIDCAP ETF: MID150BEES.NS (the real, tradable
midcap ETF used as this strategy's own benchmark in reports 24/26/31-33)
only has price history from 2019-02-04 onward — computing excess return
against it would leave 11 of this backtest's 18 years with no valid
benchmark return at all. NIFTY 50 has full history back to well before
2008 and is already used as "the market" reference throughout this
project (reports 1-21), so it's the only benchmark that can be applied to
this strategy's ENTIRE window without truncating it.
"""
import json

import numpy as np
import pandas as pd

from backtest10 import rebalance_dates, cumret_drawdown, series_to_points, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes
from backtest32 import metrics_only
from backtest33 import select_top_original, build_index_generic, overlap_stats

TOP_N = 10
MIN_ELIGIBLE = 30
LOOKBACK_12M = 252
LOOKBACK_6M = 126


def make_select_relative(nifty_aligned):
    """Closure so the benchmark series doesn't need to be a module-level
    global — nifty_aligned must already share closes' exact index (see
    main(), which builds it via .loc[closes.index])."""

    def select_top_relative(closes, t_idx, top_n=TOP_N, min_eligible=MIN_ELIGIBLE):
        if t_idx < LOOKBACK_12M:
            return None
        price_t = closes.iloc[t_idx]
        price_t12 = closes.iloc[t_idx - LOOKBACK_12M]
        price_t6 = closes.iloc[t_idx - LOOKBACK_6M]
        eligible = price_t.notna() & price_t12.notna() & price_t6.notna()
        tickers = closes.columns[eligible]
        if len(tickers) < min_eligible:
            return None

        window = closes.iloc[t_idx - LOOKBACK_12M: t_idx + 1][tickers]
        daily_ret = window.pct_change().dropna(how="all")
        vol_1y = daily_ret.std()

        nifty_t = nifty_aligned.iloc[t_idx]
        nifty_t12 = nifty_aligned.iloc[t_idx - LOOKBACK_12M]
        nifty_t6 = nifty_aligned.iloc[t_idx - LOOKBACK_6M]
        bench_ret_6m = nifty_t / nifty_t6 - 1.0
        bench_ret_12m = nifty_t / nifty_t12 - 1.0

        ret_6m = price_t[tickers] / price_t6[tickers] - 1.0
        ret_12m = price_t[tickers] / price_t12[tickers] - 1.0
        excess_6m = ret_6m - bench_ret_6m
        excess_12m = ret_12m - bench_ret_12m
        ratio_6m = excess_6m / vol_1y
        ratio_12m = excess_12m / vol_1y

        valid = ratio_6m.notna() & ratio_12m.notna() & np.isfinite(ratio_6m) & np.isfinite(ratio_12m)
        ratio_6m, ratio_12m = ratio_6m[valid], ratio_12m[valid]
        if len(ratio_6m) < min_eligible:
            return None

        z6 = (ratio_6m - ratio_6m.mean()) / ratio_6m.std()
        z12 = (ratio_12m - ratio_12m.mean()) / ratio_12m.std()
        waz = 0.5 * z6 + 0.5 * z12
        norm_score = waz.apply(lambda w: 1 + w if w >= 0 else 1 / (1 - w))
        return list(norm_score.sort_values(ascending=False).head(top_n).index)

    return select_top_relative


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nifty_aligned = nifty.loc[closes.index, "Close"]

    rbdates = rebalance_dates(closes.index, months=(6, 12))
    select_top_relative = make_select_relative(nifty_aligned)

    original_series, original_sel = build_index_generic(closes, rbdates, select_top_original)
    relative_series, relative_sel = build_index_generic(closes, rbdates, select_top_relative)

    common_idx = original_series.index.intersection(relative_series.index)
    original_metrics = metrics_only(original_series, common_idx)
    relative_metrics = metrics_only(relative_series, common_idx)

    nifty_series = nifty.loc[common_idx, "Close"]
    nifty_metrics = metrics_only(nifty_series, common_idx)

    overlaps = overlap_stats(original_sel, relative_sel)
    avg_overlap = round(float(np.mean(overlaps)), 1) if overlaps else None

    def sample(sel):
        return sel[:3] + sel[-3:] if len(sel) > 6 else sel

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "num_rebalances": len(original_sel),
        "avg_overlap_pct": avg_overlap,
        "num_overlap_rebalances": len(overlaps),
        "original": {**original_metrics, "selections_sample": sample(original_sel)},
        "relative": {**relative_metrics, "selections_sample": sample(relative_sel)},
        "nifty": nifty_metrics,
    }

    with open("results33.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}  rebalances {results['num_rebalances']}")
    print(f"original (absolute) CAGR {original_metrics['cagr_pct']:.2f}% / DD {original_metrics['max_drawdown_pct']:.1f}%")
    print(f"relative (vs NIFTY)  CAGR {relative_metrics['cagr_pct']:.2f}% / DD {relative_metrics['max_drawdown_pct']:.1f}%")
    print(f"nifty 50 benchmark   CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")
    print(f"avg rebalance overlap: {avg_overlap}% ({len(overlaps)} rebalances compared)")


if __name__ == "__main__":
    main()

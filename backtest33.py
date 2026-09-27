"""
Midcap150 Momentum 10 — "12-1" skip-month momentum vs. the original formula.

The original momentum score (select_top30() in backtest10.py, reused by
every reconstruction in this project): 6-month and 12-month price return,
each divided by trailing-1-year daily-return volatility, cross-sectionally
Z-scored, combined 0.5/0.5, asymmetrically normalized — all measured AS OF
the rebalance date itself.

This report tests the single most common real-world variant of that
formula: **skip the most recent month**. Academic momentum research
(Jegadeesh & Titman 1993, and the standard Fama-French "Mom" factor
construction used industry-wide since) measures momentum over a formation
period that EXCLUDES the most recent ~1 month, because that final month is
dominated by short-term price reversal rather than the same trend-
persistence effect that drives the multi-month momentum signal. This is
often called "12-1" momentum (12-month lookback, 1-month skip).

MECHANICALLY, THE ONLY CHANGE: every price/volatility reference point that
used to be measured "as of today" (t_idx) is instead measured "as of ~1
month ago" (t_idx - 21 trading days) — both the 6-month and 12-month
return windows shift back by the same 21 days, and so does the volatility
window they're divided by (kept aligned to the same reference point, to
avoid comparing a shifted return against a non-shifted volatility
estimate). The window LENGTHS (6 months, 12 months, 1 year of vol) are
unchanged — only the "as of" date each window is anchored to moves back
by one month. Same top-10, equal-weight, June/December rebalance,
Midcap150 universe as reports 11-19/24-32 throughout.

Compared: the modified formula's own equity curve, the ORIGINAL formula
recomputed fresh over the identical window (not just re-quoting report
16/17's number, to guarantee an exact apples-to-apples date range), and
a rebalance-by-rebalance overlap metric — what fraction of each
rebalance's top-10 picks are the SAME stock under both formulas — since a
higher-level CAGR/drawdown comparison alone doesn't show whether the
1-month skip is quietly picking a near-identical portfolio or something
substantially different.
"""
import json

import numpy as np
import pandas as pd

from backtest10 import rebalance_dates, cumret_drawdown, series_to_points, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes
from backtest32 import metrics_only

TOP_N = 10
MIN_ELIGIBLE = 30
LOOKBACK_12M = 252
LOOKBACK_6M = 126
SKIP_MONTH_DAYS = 21   # ~1 trading month


def select_top_original(closes, t_idx, top_n=TOP_N, min_eligible=MIN_ELIGIBLE):
    """Identical to backtest10.select_top30 — reimplemented here (not
    imported) only so both variants sit side by side in one file for easy
    comparison; the formula itself is unchanged."""
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

    ret_6m = price_t[tickers] / price_t6[tickers] - 1.0
    ret_12m = price_t[tickers] / price_t12[tickers] - 1.0
    ratio_6m = ret_6m / vol_1y
    ratio_12m = ret_12m / vol_1y

    valid = ratio_6m.notna() & ratio_12m.notna() & np.isfinite(ratio_6m) & np.isfinite(ratio_12m)
    ratio_6m, ratio_12m = ratio_6m[valid], ratio_12m[valid]
    if len(ratio_6m) < min_eligible:
        return None

    z6 = (ratio_6m - ratio_6m.mean()) / ratio_6m.std()
    z12 = (ratio_12m - ratio_12m.mean()) / ratio_12m.std()
    waz = 0.5 * z6 + 0.5 * z12
    norm_score = waz.apply(lambda w: 1 + w if w >= 0 else 1 / (1 - w))
    return list(norm_score.sort_values(ascending=False).head(top_n).index)


def select_top_skip1(closes, t_idx, top_n=TOP_N, min_eligible=MIN_ELIGIBLE):
    """Same formula as select_top_original, except every reference point
    (both return windows AND the volatility window they're divided by) is
    anchored SKIP_MONTH_DAYS earlier — "as of 1 month ago" instead of "as
    of today" — implementing the 12-1 skip-month convention."""
    ref_idx = t_idx - SKIP_MONTH_DAYS
    if ref_idx < LOOKBACK_12M:
        return None
    price_t = closes.iloc[ref_idx]
    price_t12 = closes.iloc[ref_idx - LOOKBACK_12M]
    price_t6 = closes.iloc[ref_idx - LOOKBACK_6M]
    eligible = price_t.notna() & price_t12.notna() & price_t6.notna()
    tickers = closes.columns[eligible]
    if len(tickers) < min_eligible:
        return None

    window = closes.iloc[ref_idx - LOOKBACK_12M: ref_idx + 1][tickers]
    daily_ret = window.pct_change().dropna(how="all")
    vol_1y = daily_ret.std()

    ret_6m = price_t[tickers] / price_t6[tickers] - 1.0
    ret_12m = price_t[tickers] / price_t12[tickers] - 1.0
    ratio_6m = ret_6m / vol_1y
    ratio_12m = ret_12m / vol_1y

    valid = ratio_6m.notna() & ratio_12m.notna() & np.isfinite(ratio_6m) & np.isfinite(ratio_12m)
    ratio_6m, ratio_12m = ratio_6m[valid], ratio_12m[valid]
    if len(ratio_6m) < min_eligible:
        return None

    z6 = (ratio_6m - ratio_6m.mean()) / ratio_6m.std()
    z12 = (ratio_12m - ratio_12m.mean()) / ratio_12m.std()
    waz = 0.5 * z6 + 0.5 * z12
    norm_score = waz.apply(lambda w: 1 + w if w >= 0 else 1 / (1 - w))
    return list(norm_score.sort_values(ascending=False).head(top_n).index)


def build_index_generic(closes, rbdates, select_fn):
    dates = closes.index
    rb_set = set(rbdates)
    date_pos = {d: i for i, d in enumerate(dates)}
    index_level = pd.Series(np.nan, index=dates)
    shares = {}
    started = False
    selections = []

    for i, d in enumerate(dates):
        if d in rb_set:
            t_idx = date_pos[d]
            selected = select_fn(closes, t_idx)
            if selected is not None:
                price_today = closes.iloc[t_idx]
                if not started:
                    value_before = 100.0
                    started = True
                else:
                    value_before = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares)
                    if value_before <= 0:
                        value_before = index_level.iloc[i - 1] if i > 0 else 100.0
                dollar_each = value_before / len(selected)
                shares = {tk: dollar_each / price_today[tk] for tk in selected}
                selections.append({"date": d.strftime("%Y-%m-%d"), "tickers": [t.replace(".NS", "") for t in selected]})
        if started:
            price_today = closes.iloc[i]
            val = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares if pd.notna(price_today.get(tk)))
            index_level.iloc[i] = val
    return index_level.dropna(), selections


def build_index_generic_invvol(closes, rbdates, select_fn, vol_lookback=LOOKBACK_12M):
    """Same rebalance/portfolio-construction loop as build_index_generic,
    except each rebalance's dollar allocation is weighted INVERSELY to
    each selected stock's own trailing volatility (daily-return std over
    the same vol_lookback window the scoring formula itself uses) instead
    of splitting equally. A calmer stock in the top-10 gets a bigger
    dollar weight, a shakier one gets a smaller one — weights are
    normalized to sum to the portfolio's total value at every rebalance,
    same as equal-weighting always has been."""
    dates = closes.index
    rb_set = set(rbdates)
    date_pos = {d: i for i, d in enumerate(dates)}
    index_level = pd.Series(np.nan, index=dates)
    shares = {}
    started = False
    selections = []

    for i, d in enumerate(dates):
        if d in rb_set:
            t_idx = date_pos[d]
            selected = select_fn(closes, t_idx)
            if selected is not None:
                price_today = closes.iloc[t_idx]
                if not started:
                    value_before = 100.0
                    started = True
                else:
                    value_before = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares)
                    if value_before <= 0:
                        value_before = index_level.iloc[i - 1] if i > 0 else 100.0

                window = closes.iloc[max(t_idx - vol_lookback, 0): t_idx + 1][selected]
                vol = window.pct_change().dropna(how="all").std()
                inv_vol = 1.0 / vol
                inv_vol = inv_vol.replace([np.inf, -np.inf], np.nan).dropna()
                if len(inv_vol) < len(selected):
                    missing = [tk for tk in selected if tk not in inv_vol.index]
                    for tk in missing:
                        inv_vol[tk] = inv_vol.mean() if len(inv_vol) else 1.0
                weights = inv_vol / inv_vol.sum()

                shares = {tk: (value_before * weights[tk]) / price_today[tk] for tk in selected}
                selections.append({"date": d.strftime("%Y-%m-%d"), "tickers": [t.replace(".NS", "") for t in selected],
                                    "weights_pct": {t.replace(".NS", ""): round(float(weights[t] * 100), 2) for t in selected}})
        if started:
            price_today = closes.iloc[i]
            val = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares if pd.notna(price_today.get(tk)))
            index_level.iloc[i] = val
    return index_level.dropna(), selections


def build_index_generic_gated(closes, rbdates, select_fn, slot_count=TOP_N):
    """Same rebalance/portfolio-construction loop as build_index_generic,
    except the dollar-per-slot size is fixed at value_before/slot_count
    REGARDLESS of how many tickers select_fn actually returns — if
    select_fn returns fewer than slot_count tickers (e.g. an absolute-
    momentum gate rejected some candidates), the unfilled slots' capital
    is tracked as an explicit cash reserve (0% return) rather than being
    redistributed across the names that DID qualify, until the next
    rebalance re-evaluates everything."""
    dates = closes.index
    rb_set = set(rbdates)
    date_pos = {d: i for i, d in enumerate(dates)}
    index_level = pd.Series(np.nan, index=dates)
    shares = {}
    cash_reserve = 0.0
    started = False
    selections = []

    for i, d in enumerate(dates):
        if d in rb_set:
            t_idx = date_pos[d]
            selected = select_fn(closes, t_idx)
            if selected is not None:
                price_today = closes.iloc[t_idx]
                if not started:
                    value_before = 100.0
                    started = True
                else:
                    value_before = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares) + cash_reserve
                    if value_before <= 0:
                        value_before = index_level.iloc[i - 1] if i > 0 else 100.0
                dollar_each = value_before / slot_count
                shares = {tk: dollar_each / price_today[tk] for tk in selected}
                cash_reserve = value_before - dollar_each * len(selected)
                selections.append({"date": d.strftime("%Y-%m-%d"), "tickers": [t.replace(".NS", "") for t in selected],
                                    "num_filled": len(selected), "num_slots": slot_count})
        if started:
            price_today = closes.iloc[i]
            val = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares if pd.notna(price_today.get(tk))) + cash_reserve
            index_level.iloc[i] = val
    return index_level.dropna(), selections


def overlap_stats(sel_a, sel_b):
    """% of the top-10 in common, per matching rebalance date, across both
    selection lists (assumes both use the same rebalance calendar, which
    they do — only the reference date INSIDE each rebalance differs)."""
    by_date_a = {s["date"]: set(s["tickers"]) for s in sel_a}
    overlaps = []
    for s in sel_b:
        if s["date"] in by_date_a:
            a, b = by_date_a[s["date"]], set(s["tickers"])
            overlaps.append(len(a & b) / len(a | b) * 100 if (a | b) else 0.0)
    return overlaps


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]

    rbdates = rebalance_dates(closes.index, months=(6, 12))

    original_series, original_sel = build_index_generic(closes, rbdates, select_top_original)
    skip1_series, skip1_sel = build_index_generic(closes, rbdates, select_top_skip1)

    common_idx = original_series.index.intersection(skip1_series.index)
    original_metrics = metrics_only(original_series, common_idx)
    skip1_metrics = metrics_only(skip1_series, common_idx)

    overlaps = overlap_stats(original_sel, skip1_sel)
    avg_overlap = round(float(np.mean(overlaps)), 1) if overlaps else None

    def sample(sel):
        return sel[:3] + sel[-3:] if len(sel) > 6 else sel

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "num_rebalances": len(original_sel),
        "skip_month_days": SKIP_MONTH_DAYS,
        "avg_overlap_pct": avg_overlap,
        "num_overlap_rebalances": len(overlaps),
        "original": {**original_metrics, "selections_sample": sample(original_sel)},
        "skip1": {**skip1_metrics, "selections_sample": sample(skip1_sel)},
    }

    with open("results32.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}  rebalances {results['num_rebalances']}")
    print(f"original CAGR {original_metrics['cagr_pct']:.2f}% / DD {original_metrics['max_drawdown_pct']:.1f}%")
    print(f"12-1 skip CAGR {skip1_metrics['cagr_pct']:.2f}% / DD {skip1_metrics['max_drawdown_pct']:.1f}%")
    print(f"avg rebalance overlap: {avg_overlap}% ({len(overlaps)} rebalances compared)")


if __name__ == "__main__":
    main()

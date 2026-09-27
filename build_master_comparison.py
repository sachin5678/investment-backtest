"""
Aggregates every momentum-strategy variant tested across reports 11/12
and 33-70 into ONE master comparison table, with Sharpe and Sortino
ratios computed correctly.

WHY THIS EXISTS AS ITS OWN SCRIPT, NOT REUSING results*.json: every
report's "equity_curve" field is downsampled to at most 1500 points
(series_to_points) for compact HTML embedding, which distorts a
Sharpe/Sortino calculation (that needs true day-to-day volatility, not
volatility measured across multi-day gaps). This script instead calls
each variant's OWN already-tested build function DIRECTLY (the exact
same functions backtest33.py-backtest70.py already use), gets each
variant's full daily equity series, and computes Sharpe/Sortino from
THAT. CAGR/max-drawdown are recomputed the same way for cross-checking
against each report's already-published numbers (see the sanity-check
prints at the end) but are not treated as new results — they are
expected to match what's already published.

Assumes 0% risk-free rate throughout (same simplification as every
"cash earns 0%" convention elsewhere in this project). Sharpe/Sortino
use the standard annualization (mean daily return / std, times sqrt(252)
trading days); Sortino's downside deviation uses 0% as the minimum
acceptable return (same as calling a day "bad" only if the return is
negative, not measured against some other target).

Scope (confirmed with the user): the momentum-strategy family only,
reports 11/12 and 33-70 — the front-loaded/inverse-vol/regime-filter/
hedge/trend-filter/stop-loss/exposure-scaling combinations tested across
Midcap150, Smallcap250, NIFTY100, and NIFTY500. Earlier non-momentum
reports (breakout, SIP, dip-buying, sector rotation, RSI, gold/silver
rotation) use different metrics (XIRR, not CAGR) and aren't included.
"""
import json

import numpy as np
import pandas as pd

from backtest10 import rebalance_dates, fetch, load_universe_closes
from backtest13 import load_midcap150_closes, fetch_gold_cleaned
from backtest15 import load_smallcap250_closes
from backtest17 import load_nifty500_closes
from nifty100_symbols import NIFTY_100_SYMBOLS

from backtest33 import (select_top_original, build_index_generic, build_index_generic_invvol,
                         build_index_generic_gated)
from backtest37 import select_top_frontloaded
from backtest39 import select_top_frontloaded_n500, select_top_original_n500
from backtest40 import select_top_frontloaded_smallcap
from backtest41 import select_top_frontloaded_n100
from backtest42 import (build_index_regime_filtered, build_index_regime_filtered_with_hedge,
                         build_index_regime_filtered_asymmetric, build_smooth_exposure,
                         build_smooth_exposure_with_hedge, EMA_SPAN, REENTRY_EMA_SPAN)
from backtest44 import select_top_smallcap, MIN_ELIGIBLE_SMALLCAP
from backtest45 import select_top_n100, MIN_ELIGIBLE as MIN_ELIGIBLE_N100
from backtest58 import build_with_trailing_stop
from backtest27 import load_midcap150_field
from backtest62 import select_top_abs_gate as select_top_abs_gate_mid
from backtest63 import select_top_abs_gate as select_top_abs_gate_small
from backtest64 import select_top_abs_gate as select_top_abs_gate_n100

ASSUMED_LIQUID_YIELD = 0.06
BAND = 0.15
STOP_PCT = 0.30

rows = []


def sharpe_sortino(daily_ret):
    daily_ret = daily_ret.dropna()
    if len(daily_ret) < 30:
        return None, None
    mean = daily_ret.mean()
    std = daily_ret.std()
    sharpe = float(mean / std * np.sqrt(252)) if std and std > 0 else None
    downside = daily_ret[daily_ret < 0]
    downside_std = downside.std() if len(downside) > 1 else None
    sortino = float(mean / downside_std * np.sqrt(252)) if downside_std and downside_std > 0 else None
    return sharpe, sortino


def metrics_from_series(series):
    series = series.dropna()
    daily_ret = series.pct_change()
    sharpe, sortino = sharpe_sortino(daily_ret)
    years = (series.index[-1] - series.index[0]).days / 365.25
    cagr = float((series.iloc[-1] / series.iloc[0]) ** (1 / years) * 100 - 100) if years > 0 else None
    net_return = float((series.iloc[-1] / series.iloc[0] - 1) * 100)
    running_peak = series.cummax()
    dd = (series / running_peak - 1.0) * 100.0
    max_dd = float(dd.min())
    return {
        "cagr_pct": cagr, "max_drawdown_pct": max_dd, "net_return_pct": net_return,
        "sharpe": sharpe, "sortino": sortino,
        "start_date": series.index[0].strftime("%Y-%m-%d"), "end_date": series.index[-1].strftime("%Y-%m-%d"),
    }


def add_row(universe, category, label, report, variant_series, bench_series, common_idx):
    v = metrics_from_series(variant_series.loc[common_idx])
    b = metrics_from_series(bench_series.loc[common_idx])
    rows.append({
        "universe": universe, "category": category, "label": label, "report": report,
        "start_date": v["start_date"], "end_date": v["end_date"],
        "cagr_pct": v["cagr_pct"], "max_drawdown_pct": v["max_drawdown_pct"], "net_return_pct": v["net_return_pct"],
        "sharpe": v["sharpe"], "sortino": v["sortino"],
        "bench_cagr_pct": b["cagr_pct"], "bench_max_drawdown_pct": b["max_drawdown_pct"],
        "bench_sharpe": b["sharpe"], "bench_sortino": b["sortino"],
    })
    print(f"  [{universe}] {label}: CAGR {v['cagr_pct']:.2f}% DD {v['max_drawdown_pct']:.1f}% "
          f"Sharpe {v['sharpe']:.2f} Sortino {v['sortino']:.2f}  ({v['start_date']}->{v['end_date']})")


def liquid_series_for(index):
    days_elapsed = (index - index[0]).days
    return pd.Series((1 + ASSUMED_LIQUID_YIELD) ** (days_elapsed / 365.25) * 100.0, index=index)


def process_universe(universe_name, closes, nifty_close, select_fn, select_fn_frontloaded,
                      select_fn_abs_gate, own_signal_close, own_signal_label, min_eligible_gate,
                      report_numbers, gold_close=None):
    ema200 = nifty_close.ewm(span=EMA_SPAN, adjust=False).mean()
    rbdates = rebalance_dates(closes.index, months=(6, 12))

    original_series, _ = build_index_generic(closes, rbdates, select_fn)
    common_idx = original_series.index.intersection(nifty_close.index)

    add_row(universe_name, "Baseline", "Original (equal-weight momentum)", report_numbers["original"],
            original_series, nifty_close, common_idx)

    if select_fn_frontloaded is not None:
        fl_series, _ = build_index_generic(closes, rbdates, select_fn_frontloaded)
        idx = common_idx.intersection(fl_series.index)
        add_row(universe_name, "Weighting", "Front-loaded 3m/6m/12m (50/30/20)", report_numbers["frontloaded"],
                fl_series, nifty_close, idx)

    filt_series, _, _ = build_index_regime_filtered(closes, nifty_close, ema200, rbdates, select_fn)
    idx = common_idx.intersection(filt_series.index)
    add_row(universe_name, "Regime Filter", "200-EMA regime filter + cash", report_numbers["filter_cash"],
            filt_series, nifty_close, idx)

    if gold_close is not None:
        # NOTE: earlier reports (48-50) pre-truncated `closes` to gold's own
        # index BEFORE running the lookback-dependent selection formula,
        # which pushed the first valid rebalance ~1.5 years later than
        # necessary (the formula's 252-day lookback then measures from the
        # truncated start, not from Midcap150's actual pre-2008 history) and
        # was misattributed in those reports to "gold's data starting mid-
        # 2010" — gold (GOLDBEES.NS) actually has data from 2009-01-02. Here
        # the FULL closes/nifty window is used (matching every other row's
        # own lookback), with gold reindexed onto it (a two-day ffill/bfill
        # gap at the very start, before gold's first real price, is
        # negligible over an 18-year window).
        gold_aligned = gold_close.reindex(closes.index).ffill().bfill()
        gold_series, _, _ = build_index_regime_filtered_with_hedge(
            closes, nifty_close, ema200, rbdates, select_fn, gold_aligned)
        idx_g = gold_series.index.intersection(nifty_close.index).intersection(gold_close.index)
        add_row(universe_name, "Filter + Hedge", "200-EMA regime filter + gold", report_numbers["filter_gold"],
                gold_series, nifty_close, idx_g)

    invvol_series, _ = build_index_generic_invvol(closes, rbdates, select_fn)
    idx = common_idx.intersection(invvol_series.index)
    add_row(universe_name, "Weighting", "Inverse-volatility weighting", report_numbers["invvol"],
            invvol_series, nifty_close, idx)

    if own_signal_close is not None:
        own_idx = closes.index.intersection(nifty_close.index).intersection(own_signal_close.index)
        own_ema = own_signal_close.loc[own_idx].ewm(span=EMA_SPAN, adjust=False).mean()
        own_series, _, _ = build_index_regime_filtered(closes.loc[own_idx], own_signal_close.loc[own_idx], own_ema, rbdates, select_fn)
        idx_o = own_series.index.intersection(nifty_close.index)
        add_row(universe_name, "Trend Filter", f"Universe-specific trend filter ({own_signal_label})", report_numbers["own_signal"],
                own_series, nifty_close, idx_o)

    asym_ema50 = nifty_close.ewm(span=REENTRY_EMA_SPAN, adjust=False).mean()
    asym_series, _, _ = build_index_regime_filtered_asymmetric(closes, nifty_close, ema200, asym_ema50, rbdates, select_fn)
    idx = common_idx.intersection(asym_series.index)
    add_row(universe_name, "Regime Filter", "Asymmetric EMA (fast 50d re-entry)", report_numbers["asymmetric"],
            asym_series, nifty_close, idx)

    gated_series, _ = build_index_generic_gated(closes, rbdates, select_fn_abs_gate, slot_count=10)
    idx = common_idx.intersection(gated_series.index)
    add_row(universe_name, "Momentum Formula", "Absolute momentum gate", report_numbers["abs_gate"],
            gated_series, nifty_close, idx)

    smooth_cash, _ = build_smooth_exposure(original_series, nifty_close, ema200, band_pct=BAND)
    idx = common_idx.intersection(smooth_cash.index)
    add_row(universe_name, "Exposure Scaling", "Smooth exposure 15% band + cash", report_numbers["smooth"],
            smooth_cash, nifty_close, idx)

    if gold_close is not None:
        idx_g2 = original_series.index.intersection(gold_close.index).intersection(nifty_close.index)
        smooth_gold, _ = build_smooth_exposure_with_hedge(original_series, nifty_close, ema200, gold_close, band_pct=BAND)
        add_row(universe_name, "Exposure Scaling", "Smooth exposure 15% band + gold", report_numbers["smooth_hedge"],
                smooth_gold, nifty_close, idx_g2)

        liquid_close = liquid_series_for(original_series.index)
        smooth_liquid, _ = build_smooth_exposure_with_hedge(original_series, nifty_close, ema200, liquid_close, band_pct=BAND)
        add_row(universe_name, "Exposure Scaling", "Smooth exposure 15% band + liquid fund (assumed 6%)", report_numbers["smooth_hedge"],
                smooth_liquid, nifty_close, idx_g2)

    if STOP_PCT is not None and report_numbers.get("trailing_stop"):
        tickers = list(closes.columns)
        lows = load_midcap150_field("Low", tickers).loc[closes.index, tickers]
        highs = load_midcap150_field("High", tickers).loc[closes.index, tickers]
        opens = load_midcap150_field("Open", tickers).loc[closes.index, tickers]
        trail_series, _ = build_with_trailing_stop(closes, lows, highs, opens, rbdates, STOP_PCT)
        idx = common_idx.intersection(trail_series.index)
        add_row(universe_name, "Stop-Loss", "Trailing stop 30% off peak", report_numbers["trailing_stop"],
                trail_series, nifty_close, idx)


def main():
    nifty = fetch("^NSEI")
    nifty_close_full = nifty["Close"]
    gold = fetch_gold_cleaned()
    gold_close_full = gold["Close"]

    print("=== Midcap150 ===")
    mid_closes = load_midcap150_closes()
    mid_common = mid_closes.index.intersection(nifty_close_full.index)
    midcapietf = fetch("MIDCAPIETF.NS")["Close"]
    process_universe(
        "Midcap150", mid_closes.loc[mid_common], nifty_close_full.loc[mid_common],
        select_top_original, select_top_frontloaded, select_top_abs_gate_mid,
        midcapietf, "MIDCAPIETF.NS", 30,
        {"original": 11, "frontloaded": 37, "filter_cash": 42, "filter_gold": 48, "invvol": 51,
         "own_signal": 54, "asymmetric": 59, "abs_gate": 62, "smooth": 65, "smooth_hedge": 68,
         "trailing_stop": 58},
        gold_close=gold_close_full,
    )

    print("=== Smallcap250 ===")
    small_closes = load_smallcap250_closes()
    small_common = small_closes.index.intersection(nifty_close_full.index)
    smallcap_idx = fetch("NIFTYSMLCAP250.NS")["Close"]
    process_universe(
        "Smallcap250", small_closes.loc[small_common], nifty_close_full.loc[small_common],
        select_top_smallcap, select_top_frontloaded_smallcap, select_top_abs_gate_small,
        smallcap_idx, "NIFTYSMLCAP250.NS", MIN_ELIGIBLE_SMALLCAP,
        {"original": 16, "frontloaded": 40, "filter_cash": 44, "filter_gold": 49, "invvol": 52,
         "own_signal": 55, "asymmetric": 60, "abs_gate": 63, "smooth": 66, "smooth_hedge": 69},
        gold_close=gold_close_full,
    )

    print("=== NIFTY100 ===")
    universe_all = load_universe_closes()
    n100_tickers = [s + ".NS" for s in NIFTY_100_SYMBOLS]
    n100_closes = universe_all[[t for t in n100_tickers if t in universe_all.columns]]
    n100_common = n100_closes.index.intersection(nifty_close_full.index)
    cnx100 = fetch("^CNX100")["Close"]
    process_universe(
        "NIFTY100", n100_closes.loc[n100_common], nifty_close_full.loc[n100_common],
        select_top_n100, select_top_frontloaded_n100, select_top_abs_gate_n100,
        cnx100, "^CNX100", MIN_ELIGIBLE_N100,
        {"original": 12, "frontloaded": 41, "filter_cash": 45, "filter_gold": 50, "invvol": 53,
         "own_signal": 56, "asymmetric": 61, "abs_gate": 64, "smooth": 67, "smooth_hedge": 70},
        gold_close=gold_close_full,
    )

    print("=== NIFTY500 (limited: original, front-loaded, filter only) ===")
    n500_closes = load_nifty500_closes()
    n500_common = n500_closes.index.intersection(nifty_close_full.index)
    n500_closes = n500_closes.loc[n500_common]
    n500_nifty = nifty_close_full.loc[n500_common]
    n500_ema = n500_nifty.ewm(span=EMA_SPAN, adjust=False).mean()
    n500_rbdates = rebalance_dates(n500_closes.index, months=(6, 12))
    n500_orig, _ = build_index_generic(n500_closes, n500_rbdates, select_top_original_n500)
    idx = n500_orig.index.intersection(n500_nifty.index)
    add_row("NIFTY500", "Baseline", "Original (equal-weight momentum)", 18, n500_orig, n500_nifty, idx)
    n500_fl, _ = build_index_generic(n500_closes, n500_rbdates, select_top_frontloaded_n500)
    idx = n500_orig.index.intersection(n500_fl.index)
    add_row("NIFTY500", "Weighting", "Front-loaded 3m/6m/12m (50/30/20)", 39, n500_fl, n500_nifty, idx)
    n500_filt, _, _ = build_index_regime_filtered(n500_closes, n500_nifty, n500_ema, n500_rbdates, select_top_original_n500)
    idx = n500_orig.index.intersection(n500_filt.index)
    add_row("NIFTY500", "Regime Filter", "200-EMA regime filter + cash", 43, n500_filt, n500_nifty, idx)

    with open("master_comparison.json", "w") as f:
        json.dump({"generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"), "rows": rows}, f, indent=2)
    print(f"\nWrote master_comparison.json with {len(rows)} rows")


if __name__ == "__main__":
    main()

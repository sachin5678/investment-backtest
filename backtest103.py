"""
Microcap 250 Momentum 10 — gold instead of cash during the 200-day EMA regime
filter's risk-off periods.

This is report 48's EXACT design (Midcap150 Momentum 10 + 200-EMA regime
filter + gold swap), ported to the NIFTY Microcap 250 universe — the first
universe in this series that required a NEW price cache (microcap250_raw.pkl,
fetched by fetch_microcap250_prices.py on 2026-10-18) because microcap names
are not part of any cached NIFTY 500-family universe.

The only two changes vs. report 48 are:

  1. UNIVERSE: NIFTY Microcap 250 (249 Series=EQ names from NSE's official
     constituent CSV, microcap250_symbols.py, fetched 2026-10-18) instead of
     Midcap150.
  2. ELIGIBILITY FLOOR: min_eligible=40 — the Smallcap250 convention
     (40/250), applied unchanged to this 249-name universe. On microcaps the
     floor is expected to BIND for several early years: today's microcap
     constituents skew recently-listed, so fewer than 40 names have a full
     12m+6m price history in the early part of the cache. Where it binds,
     build_index_generic simply does not select that rebalance and the
     backtest starts later — no silent fill-in.

Everything else — the momentum formula (imported as report 44/49's
select_top_smallcap, byte-identical to the formula every other universe
uses), the June/December rebalance cadence, the NIFTY-50-driven 200-day EMA
signal, the gold sleeve (GOLDBEES.NS), and the engine functions
build_index_generic / build_index_regime_filtered /
build_index_regime_filtered_with_hedge — comes unchanged from the same
modules reports 42-49 use. Nothing here is a re-implementation, so these
numbers are directly comparable to reports 42-50's published figures.

DISCLOSURES — heavier here than anywhere else in this series, read before
quoting any number below:
  - SURVIVORSHIP BIAS IS SEVERE: today's Microcap 250 membership applied
    retroactively. Microcap failures/delistings are concentrated in exactly
    the names this list can no longer contain. This biases returns UP.
  - THE INDEX LAUNCHED ONLY IN DEC 2024: "Microcap 250 history" before then
    is a backfilled construct of today's constituents, not a live index.
  - THIN LIQUIDITY: microcap daily closes are noisier (multi-day halts,
    wide spreads), which interacts with equal-rupee sizing conventions.
  - Equal weighting instead of free-float-market-cap weighting (same as
    every other reconstruction here).
  - The 200-EMA signal is still driven by NIFTY 50 (report 42 convention) —
    unrelated to the holdings universe, exactly as in reports 44/48/49/50.
"""
import json

import pandas as pd

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest13 import fetch_gold_cleaned
from backtest32 import metrics_only
from backtest33 import build_index_generic
from backtest42 import (build_index_regime_filtered, build_index_regime_filtered_with_hedge,
                        cash_blocks_from_log, EMA_SPAN)
from backtest44 import select_top_smallcap
from microcap250_symbols import MICROCAP_250_SYMBOLS

TOP_N = 10
MIN_ELIGIBLE_MICROCAP = 40  # Smallcap250's floor (40/250), same fraction here


def load_microcap250_closes():
    """NIFTY Microcap 250 closes from the fresh microcap250_raw.pkl snapshot
    (all 249 EQ names fetched 2026-10-18 in one uniform download). Loader
    mirrors load_smallcap250_closes: keep any name with real prices, let the
    selector's per-rebalance eligibility gate (12m+6m non-NaN) do the rest —
    no silent fill-in of missing history."""
    raw = pd.read_pickle("microcap250_raw.pkl")
    present = set(c[0] for c in raw.columns)
    cols = {}
    for sym in MICROCAP_250_SYMBOLS:
        t = sym + ".NS"
        if t in present:
            s = raw[(t, "Close")]
            if s.notna().any():
                cols[t] = s
    return pd.DataFrame(cols).sort_index().ffill()


def main():
    closes = load_microcap250_closes()
    nifty = fetch("^NSEI")
    gold = fetch_gold_cleaned()
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]
    gold_close_aligned = gold["Close"].reindex(common).ffill().bfill()
    ema = nifty_close.ewm(span=EMA_SPAN, adjust=False).mean()

    rbdates = rebalance_dates(closes.index, months=(6, 12))

    # report 44's published selector, defaults top_n=10 / min_eligible=40
    sel = select_top_smallcap
    original_series, original_sel = build_index_generic(closes, rbdates, sel)
    cash_series, cash_sel, cash_log = build_index_regime_filtered(closes, nifty_close, ema, rbdates, sel)
    gold_series, gold_sel, gold_log = build_index_regime_filtered_with_hedge(
        closes, nifty_close, ema, rbdates, sel, gold_close_aligned)

    common_idx = original_series.index.intersection(cash_series.index).intersection(gold_series.index)
    original_metrics = metrics_only(original_series, common_idx)
    cash_metrics = metrics_only(cash_series, common_idx)
    gold_metrics = metrics_only(gold_series, common_idx)
    nifty_metrics = metrics_only(nifty_close.loc[common_idx], common_idx)

    real_gold_idx = common_idx.intersection(gold["Close"].index)
    gold_bench_metrics = metrics_only(gold["Close"], real_gold_idx)

    cash_blocks, pct_cash = cash_blocks_from_log(cash_log)
    num_reentries = sum(1 for s in cash_sel if s["trigger"] == "regime_reentry")

    def sample(sel_list):
        return sel_list[:3] + sel_list[-3:] if len(sel_list) > 6 else sel_list

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "universe": "NIFTY Microcap 250 (official NSE list, 249 EQ names, fetched 2026-10-18)",
        "top_n": TOP_N,
        "min_eligible": MIN_ELIGIBLE_MICROCAP,
        "rebalance_months": [6, 12],
        "start_date": common_idx[0].strftime("%Y-%m-%d"),
        "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "ema_span": EMA_SPAN,
        "pct_time_in_cash": round(pct_cash, 1),
        "num_regime_reentries": num_reentries,
        "disclosures": [
            "survivorship bias: today's Microcap 250 membership applied retroactively",
            "index launched Dec 2024; pre-2025 history is a backfilled construct",
            "thin liquidity: microcap closes are noisier than any other universe here",
            "equal weighting, not free-float-market-cap weighting",
        ],
        "original": {**original_metrics, "selections_sample": sample(original_sel)},
        "cash_filtered": {**cash_metrics, "selections_sample": sample(cash_sel)},
        "gold_filtered": {**gold_metrics, "selections_sample": sample(gold_sel)},
        "nifty": nifty_metrics,
        "gold_benchmark": gold_bench_metrics,
    }

    with open("results102.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"universe: Microcap 250 ({closes.shape[1]} names with prices), "
          f"window {results['start_date']} -> {results['end_date']}")
    print(f"pct time in cash: {results['pct_time_in_cash']}%   regime re-entries: {num_reentries}")
    print(f"no filter                CAGR {original_metrics['cagr_pct']:.2f}% / DD {original_metrics['max_drawdown_pct']:.1f}%")
    print(f"200-EMA + cash           CAGR {cash_metrics['cagr_pct']:.2f}% / DD {cash_metrics['max_drawdown_pct']:.1f}%")
    print(f"200-EMA + gold           CAGR {gold_metrics['cagr_pct']:.2f}% / DD {gold_metrics['max_drawdown_pct']:.1f}%")
    print(f"nifty 50 benchmark       CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")
    print(f"gold (GOLDBEES.NS) alone CAGR {gold_bench_metrics['cagr_pct']:.2f}% / DD {gold_bench_metrics['max_drawdown_pct']:.1f}%")


if __name__ == "__main__":
    main()

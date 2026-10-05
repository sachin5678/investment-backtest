"""
Midcap150 Momentum 10 — report 48's exact design, but with a
GOLD-STRENGTH GUARD on the regime filter's hedge leg: during a risk-off
period (NIFTY below its 200-day EMA), hold gold ONLY while gold itself
passes BOTH of two trend checks — gold's own 6-month return beats
NIFTY's 6-month return, AND gold's own 6-month return is positive.
Whenever either check fails, sit in flat 0%-return cash instead of gold
for that day.

WHY: report 48 treats gold as an unconditional hedge — any time the
regime flips off, 100% of the hedge sleeve goes into gold, no questions
asked. But gold has its own bear markets (2013's taper-tantrum selloff,
2021-22's correction) that can and do coincide with equity weakness, so
"gold always protects you when stocks don't" is itself an unverified
assumption. This guard only ever REPLACES gold with flat cash — it never
adds leverage or a third asset — so any improvement has to come from
avoiding gold's own bad stretches, not from gold earning something
better.

CORRECTNESS NOTE (why this file exists as a clean numbered report rather
than just trusting the earlier exploratory sweep): an earlier
"Opencode"-contributed version of this same idea (wild8_goldguard_
universe.py) computed the "invested" leg from build_index_generic's
plain buy-and-hold index rather than from report 48's own real event
loop — those two diverge after any regime re-entry, since report 48
freshly reselects its top-10 on re-entry while the plain index just
keeps holding whatever it picked at the last scheduled rebalance. A
follow-up fix (wild9_eventloop_guard.py) corrected the CASH-day timing
but was still found, on review, to source invested-day returns from the
same wrong series. This file is the properly audited version: every
single invested day's return comes directly from report 48's own
build_index_regime_filtered_with_hedge() output — nothing is
reimplemented or approximated.
"""
import json

import pandas as pd

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes, fetch_gold_cleaned
from backtest32 import metrics_only
from backtest33 import select_top_original, build_index_generic
from backtest42 import build_index_regime_filtered_with_hedge, cash_blocks_from_log, EMA_SPAN

GOLD_LOOKBACK_DAYS = 126  # ~6 trading months, matching wild9's own convention


def is_cash_panel(state_log, index):
    states = pd.Series([s == "cash" for _, s in state_log],
                        index=pd.DatetimeIndex([d for d, _ in state_log]))
    return states.reindex(index).ffill().fillna(False)


def build_gold_strength_guard(closes, nifty_close, ema, rbdates, select_fn, gold_aligned, lookback_days=GOLD_LOOKBACK_DAYS):
    """The properly-audited gold-strength guard on top of report 48's own
    event loop: r48 and its state_log come directly from
    build_index_regime_filtered_with_hedge, every invested day's return is
    r48's own realized return (never approximated), and the guard only
    ever overrides a CASH day -- hold gold if gold's own `lookback_days`
    return beats NIFTY's AND is positive, else flat 0% cash. Returns
    (guarded_series, r48_series, r48_log, is_cash, cash_and_fail) so
    callers (this file's own report, and the master comparison table)
    can share one implementation instead of two."""
    r48, _, r48_log = build_index_regime_filtered_with_hedge(closes, nifty_close, ema, rbdates, select_fn, gold_aligned)
    is_cash = is_cash_panel(r48_log, r48.index)

    gold6 = gold_aligned.pct_change(lookback_days)
    nifty6 = nifty_close.pct_change(lookback_days)
    guard_passes = (gold6 > nifty6).reindex(r48.index).fillna(False) & (gold6 > 0).reindex(r48.index).fillna(False)

    rets = r48.pct_change().fillna(0.0)
    gold_rets = gold_aligned.reindex(r48.index).ffill().pct_change().fillna(0.0)

    cash_and_pass = is_cash & guard_passes
    cash_and_fail = is_cash & (~guard_passes)
    guarded_rets = rets.copy()
    guarded_rets[cash_and_pass] = gold_rets[cash_and_pass]
    guarded_rets[cash_and_fail] = 0.0
    guarded_series = (1 + guarded_rets).cumprod() * 100

    return guarded_series, r48, r48_log, is_cash, cash_and_fail


def guard_block_breakdown(cash_blocks, guard_is_gold):
    """For each cash (regime-off) block, what fraction of its days the
    guard actually held gold vs. sat in flat cash -- the single clearest
    way to see whether this guard's benefit is concentrated in a small
    number of historical episodes or spread broadly across many."""
    out = []
    for b in cash_blocks:
        block_idx = guard_is_gold.loc[b["start"]:b["end"]]
        if len(block_idx) == 0:
            continue
        gold_days = int(block_idx.sum())
        out.append({**b, "gold_days": gold_days, "flat_days": len(block_idx) - gold_days,
                    "mostly": "gold" if gold_days >= len(block_idx) / 2 else "flat"})
    return out


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    gold = fetch_gold_cleaned()
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]
    gold_aligned = gold["Close"].reindex(common).ffill().bfill()
    real_gold_idx = common.intersection(gold["Close"].index)

    ema200 = nifty_close.ewm(span=EMA_SPAN, adjust=False).mean()
    rbdates = rebalance_dates(closes.index, months=(6, 12))

    original_series, _ = build_index_generic(closes, rbdates, select_top_original)
    guarded_series, r48, r48_log, is_cash, cash_and_fail = build_gold_strength_guard(
        closes, nifty_close, ema200, rbdates, select_top_original, gold_aligned)

    common_idx = original_series.index.intersection(r48.index).intersection(real_gold_idx)

    guard_is_gold_on_cash_days = is_cash & (~cash_and_fail)

    original_metrics = metrics_only(original_series, common_idx)
    r48_metrics = metrics_only(r48, common_idx)
    guarded_metrics = metrics_only(guarded_series, common_idx)
    nifty_metrics = metrics_only(nifty_close, common_idx)
    gold_bench_metrics = metrics_only(gold["Close"], common_idx.intersection(real_gold_idx))

    cash_blocks, pct_cash = cash_blocks_from_log(r48_log)
    block_breakdown = guard_block_breakdown(cash_blocks, guard_is_gold_on_cash_days)
    num_blocks_mostly_flat = sum(1 for b in block_breakdown if b["mostly"] == "flat")
    days_saved_to_flat = int(cash_and_fail.sum())
    total_cash_days = int(is_cash.sum())
    days_in_short_blips = days_saved_to_flat - sum(b["flat_days"] for b in block_breakdown)

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "ema_span": EMA_SPAN, "gold_lookback_days": GOLD_LOOKBACK_DAYS,
        "pct_time_in_cash_regime": round(pct_cash, 1), "total_cash_regime_days": total_cash_days,
        "days_guard_moved_to_flat": days_saved_to_flat, "days_in_short_blips": days_in_short_blips,
        "num_cash_blocks": len(block_breakdown), "num_cash_blocks_mostly_flat": num_blocks_mostly_flat,
        "cash_block_breakdown": block_breakdown,
        "original": original_metrics,
        "report48_standard": r48_metrics,
        "gold_strength_guard": guarded_metrics,
        "nifty": nifty_metrics,
        "gold_benchmark": gold_bench_metrics,
    }

    with open("results90.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}")
    print(f"no filter                  CAGR {original_metrics['cagr_pct']:.2f}% / DD {original_metrics['max_drawdown_pct']:.1f}%")
    print(f"report 48 (gold, no guard) CAGR {r48_metrics['cagr_pct']:.2f}% / DD {r48_metrics['max_drawdown_pct']:.1f}%")
    print(f"gold-strength guard        CAGR {guarded_metrics['cagr_pct']:.2f}% / DD {guarded_metrics['max_drawdown_pct']:.1f}%")
    print(f"nifty 50                   CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")
    print(f"gold alone                 CAGR {gold_bench_metrics['cagr_pct']:.2f}% / DD {gold_bench_metrics['max_drawdown_pct']:.1f}%")
    print(f"\n{days_saved_to_flat} of {int(is_cash.sum())} cash-regime days moved from gold to flat cash "
          f"({len(block_breakdown)} distinct cash blocks, {num_blocks_mostly_flat} mostly-flat)")
    for b in block_breakdown[:6]:
        print(f"  {b['start']} -> {b['end']} ({b['days']}d): {b['gold_days']}d gold / {b['flat_days']}d flat -> mostly {b['mostly']}")


if __name__ == "__main__":
    main()

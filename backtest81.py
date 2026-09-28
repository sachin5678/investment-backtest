"""
Midcap150 Momentum 10 — averaging down WITHIN each 6-month holding period,
instead of just buying once at rebalance and holding untouched until the
next one.

Mechanics (confirmed with the user before building — two genuine design
choices that would otherwise be ambiguous):
  - Same picks as the flagship strategy: select_top_original(), top-10,
    equal-weight, June/December rebalance.
  - Track each stock's PEAK price since it was bought this holding period
    (starts at the entry price, updates daily).
  - 1st averaging buy: the FIRST time the stock's close falls to 15% below
    that peak-since-entry, invest an extra amount EQUAL to the original
    per-stock allocation (so a stock that averages once has 2x its
    starting capital committed).
  - 2nd averaging buy: the FIRST time it falls to 30% below peak-since-
    entry (after already averaging once), invest ANOTHER equal amount
    (3x starting capital committed if both trigger).
  - Both averaging buys use NEW, EXTERNAL capital — not money taken from
    the other 9 positions — same convention this project already used for
    report 4/20's dip-buying overlays.
  - At the next rebalance, the ENTIRE position (original + any averaged-in
    shares) is sold and a fresh ₹10-per-stock allocation is called for the
    new top-10 picks. This is a periodic-capital-call model (like a fund
    calling and returning capital each cycle), not a compounding "let
    profits ride forever" model — deliberately, so the averaging overlay's
    effect can be isolated with XIRR (money-weighted return, the same
    metric report 4/20 already use for capital-injection strategies)
    without conflating it with "does letting gains compound help" (already
    answered by every CAGR-based report in this project).

Compared against an otherwise-IDENTICAL baseline with the averaging logic
turned off — same picks, same periodic ₹10/stock capital calls, same
XIRR measurement — so the ONLY difference between the two is whether
mid-period drawdowns get bought into or not.
"""
import json
import sys

import numpy as np
import pandas as pd

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from backtest4 import xirr, series_to_points
from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes
from backtest32 import metrics_only
from backtest33 import select_top_original, build_index_generic

BASE_ALLOC = 10.0
DROP_1 = 0.15
DROP_2 = 0.30


def simulate(closes, rbdates, select_fn, use_averaging):
    dates = closes.index
    cashflows = []
    value_curve = pd.Series(np.nan, index=dates)
    invested_curve = pd.Series(np.nan, index=dates)
    cumulative_invested = 0.0
    total_realized = 0.0
    positions = {}
    trigger_once, trigger_twice, total_positions = 0, 0, 0
    cycle_capital_called = 0.0
    cycle_returns = []

    for i, rb in enumerate(rbdates):
        price_at_rb = closes.loc[rb]

        if positions:
            proceeds = sum(pos["shares"] * price_at_rb.get(tk, np.nan) for tk, pos in positions.items()
                            if pd.notna(price_at_rb.get(tk, np.nan)))
            cashflows.append((rb, float(proceeds)))
            total_realized += float(proceeds)
            if cycle_capital_called > 0:
                cycle_returns.append((proceeds / cycle_capital_called - 1.0) * 100.0)
            positions = {}
            cycle_capital_called = 0.0

        t_idx = dates.get_loc(rb)
        selected = select_fn(closes, t_idx)
        if selected is not None:
            for tk in selected:
                entry_price = price_at_rb.get(tk)
                if pd.isna(entry_price) or entry_price <= 0:
                    continue
                cashflows.append((rb, -BASE_ALLOC))
                cumulative_invested += BASE_ALLOC
                cycle_capital_called += BASE_ALLOC
                total_positions += 1
                positions[tk] = {"shares": BASE_ALLOC / entry_price, "peak": entry_price,
                                  "averaged1": False, "averaged2": False}

        value_curve.loc[rb] = sum(pos["shares"] * price_at_rb.get(tk, np.nan) for tk, pos in positions.items())
        invested_curve.loc[rb] = cumulative_invested

        next_rb = rbdates[i + 1] if i + 1 < len(rbdates) else None
        day_range = dates[(dates > rb) & (dates < next_rb)] if next_rb is not None else dates[dates > rb]

        for d in day_range:
            price_today = closes.loc[d]
            day_value = 0.0
            for tk, pos in positions.items():
                price = price_today.get(tk)
                if pd.isna(price):
                    day_value += pos["shares"] * pos["peak"]
                    continue
                if price > pos["peak"]:
                    pos["peak"] = price
                if use_averaging:
                    if not pos["averaged1"] and price <= pos["peak"] * (1 - DROP_1):
                        pos["shares"] += BASE_ALLOC / price
                        cashflows.append((d, -BASE_ALLOC))
                        cumulative_invested += BASE_ALLOC
                        cycle_capital_called += BASE_ALLOC
                        pos["averaged1"] = True
                        trigger_once += 1
                    elif pos["averaged1"] and not pos["averaged2"] and price <= pos["peak"] * (1 - DROP_2):
                        pos["shares"] += BASE_ALLOC / price
                        cashflows.append((d, -BASE_ALLOC))
                        cumulative_invested += BASE_ALLOC
                        cycle_capital_called += BASE_ALLOC
                        pos["averaged2"] = True
                        trigger_twice += 1
                day_value += pos["shares"] * price
            value_curve.loc[d] = day_value
            invested_curve.loc[d] = cumulative_invested

    final_open_value = 0.0
    if positions:
        last_date = dates[-1]
        price_last = closes.loc[last_date]
        final_open_value = sum(pos["shares"] * price_last.get(tk, np.nan) for tk, pos in positions.items()
                                if pd.notna(price_last.get(tk, np.nan)))
        cashflows.append((last_date, float(final_open_value)))

    cashflows = sorted(cashflows, key=lambda cf: cf[0])
    rate = xirr(cashflows)
    total_invested = float(invested_curve.dropna().iloc[-1])
    total_returned = total_realized + final_open_value
    money_multiple = total_returned / total_invested if total_invested else None

    # NOTE: max-drawdown-on-(value/invested) is deliberately NOT reported
    # here. That ratio is meaningful for a strategy that stays invested
    # continuously (report 4's SIP+dip model) where both curves only ever
    # grow. Here, capital is CALLED, then RETURNED (realized) every single
    # rebalance, so "value" resets to a small number every 6 months while
    # "invested" keeps climbing cumulatively forever — the ratio would show
    # a ~100% "drawdown" at every rebalance by pure accounting construction,
    # not because anything went wrong. worst/best single-CYCLE return (each
    # cycle's own proceeds against its own called capital) is the honest
    # substitute — it answers "how bad did the worst 6-month cycle get" on
    # a like-for-like, capital-relative basis instead.
    return {
        "value_curve": series_to_points(value_curve.dropna()),
        "invested_curve": series_to_points(invested_curve.dropna()),
        "total_invested": total_invested, "total_realized": total_realized, "final_open_value": final_open_value,
        "total_returned": total_returned, "money_multiple": money_multiple,
        "xirr_pct": rate,
        "worst_cycle_return_pct": min(cycle_returns) if cycle_returns else None,
        "best_cycle_return_pct": max(cycle_returns) if cycle_returns else None,
        "num_cycles_completed": len(cycle_returns),
        "total_positions": total_positions, "trigger_once": trigger_once, "trigger_twice": trigger_twice,
    }


def simulate_compounding_with_averaging(closes, rbdates, select_fn, drop1=DROP_1, drop2=DROP_2):
    """The SAME averaging idea (top up on -15%/-30% from peak-since-entry,
    same size as the original per-stock allocation), but as ONE continuous
    compounding portfolio like every other flagship report — no new
    external capital ever enters. Each averaging buy is funded by trimming
    the OTHER currently-held positions proportionally (a same-day internal
    reallocation, not a cash injection), so total portfolio value is
    unchanged at the instant of the trim and the whole thing compounds
    forward through every rebalance exactly like build_index_generic.
    Returns a single equity_curve/selections, directly CAGR-comparable to
    the plain (no-averaging) flagship series."""
    dates = closes.index
    index_level = pd.Series(np.nan, index=dates)
    shares = {}
    started = False
    selections = []

    for i, rb in enumerate(rbdates):
        t_idx = dates.get_loc(rb)
        price_at_rb = closes.loc[rb]
        selected = select_fn(closes, t_idx)
        if selected is not None:
            if not started:
                value_before = 100.0
                started = True
            else:
                value_before = sum(shares.get(tk, 0.0) * price_at_rb.get(tk, 0.0) for tk in shares)
                if value_before <= 0:
                    value_before = index_level.iloc[dates.get_loc(rb) - 1]
            dollar_each = value_before / len(selected)
            shares = {tk: dollar_each / price_at_rb[tk] for tk in selected}
            original_alloc = {tk: dollar_each for tk in selected}
            peak = {tk: price_at_rb[tk] for tk in selected}
            averaged1 = {tk: False for tk in selected}
            averaged2 = {tk: False for tk in selected}
            selections.append({"date": rb.strftime("%Y-%m-%d"), "tickers": [t.replace(".NS", "") for t in selected]})

        if not started:
            continue

        index_level.loc[rb] = sum(shares.get(tk, 0.0) * price_at_rb.get(tk, 0.0) for tk in shares)

        next_rb = rbdates[i + 1] if i + 1 < len(rbdates) else None
        day_range = dates[(dates > rb) & (dates < next_rb)] if next_rb is not None else dates[dates > rb]

        for d in day_range:
            price_today = closes.loc[d]
            for tk in list(shares.keys()):
                price = price_today.get(tk)
                if pd.isna(price):
                    continue
                if price > peak[tk]:
                    peak[tk] = price
                trigger = None
                if not averaged1[tk] and price <= peak[tk] * (1 - drop1):
                    trigger = "averaged1"
                elif averaged1[tk] and not averaged2[tk] and price <= peak[tk] * (1 - drop2):
                    trigger = "averaged2"
                if trigger:
                    need_cash = original_alloc[tk]
                    others = [t for t in shares if t != tk]
                    other_value = sum(shares[t] * price_today.get(t, 0.0) for t in others
                                       if pd.notna(price_today.get(t)))
                    if other_value > 0:
                        actual_cash = min(need_cash, other_value)
                        for t in others:
                            p_t = price_today.get(t)
                            if pd.isna(p_t) or p_t <= 0:
                                continue
                            t_value = shares[t] * p_t
                            reduction_value = t_value * (actual_cash / other_value)
                            shares[t] -= reduction_value / p_t
                        shares[tk] += actual_cash / price
                    if trigger == "averaged1":
                        averaged1[tk] = True
                    else:
                        averaged2[tk] = True
            index_level.loc[d] = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares
                                      if pd.notna(price_today.get(tk)))

    return index_level.dropna(), selections


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]

    rbdates = rebalance_dates(closes.index, months=(6, 12))
    # Drop rebalance dates before the formula has 252 days of lookback.
    rbdates = [d for d in rbdates if closes.index.get_loc(d) >= 252]

    baseline = simulate(closes, rbdates, select_top_original, use_averaging=False)
    averaged = simulate(closes, rbdates, select_top_original, use_averaging=True)

    # Reconciliation row: the REAL flagship money-management rule (report
    # 16/33's own engine) — every cycle's ending value becomes the entire
    # bet for the next cycle, fully compounding, no averaging. This is the
    # SAME picks/prices as "baseline" above, just with the opposite
    # capital-management rule, specifically to show WHY its CAGR doesn't
    # match "baseline"'s XIRR even though both are "no averaging" — the
    # two structures amount to different bets, not different arithmetic.
    plain_series, _ = build_index_generic(closes, rbdates, select_top_original)
    common_idx = closes.index[closes.index >= rbdates[0]]
    plain_compounding = metrics_only(plain_series, common_idx.intersection(plain_series.index))
    nifty_metrics = metrics_only(nifty_close.loc[common_idx.intersection(nifty_close.index)], common_idx)

    # THE MAIN QUESTION: one continuous compounding portfolio, no new
    # external capital ever, averaging buys funded by trimming the other
    # 9 holdings instead — directly CAGR-comparable to plain_compounding.
    compound_avg_series, compound_avg_sel = simulate_compounding_with_averaging(closes, rbdates, select_top_original)
    compounding_with_averaging = metrics_only(compound_avg_series, common_idx.intersection(compound_avg_series.index))
    compounding_with_averaging["selections_sample"] = (
        compound_avg_sel[:3] + compound_avg_sel[-3:] if len(compound_avg_sel) > 6 else compound_avg_sel)

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": rbdates[0].strftime("%Y-%m-%d"), "end_date": closes.index[-1].strftime("%Y-%m-%d"),
        "base_alloc": BASE_ALLOC, "drop_1_pct": DROP_1 * 100, "drop_2_pct": DROP_2 * 100,
        "num_rebalances": len(rbdates),
        "plain_compounding": plain_compounding,
        "compounding_with_averaging": compounding_with_averaging,
        "baseline": baseline, "averaged": averaged,
        "nifty": nifty_metrics,
    }

    with open("results80.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}, {len(rbdates)} rebalances")
    print(f"MAIN COMPARISON (one compounding portfolio, no external capital):")
    print(f"  plain, no averaging      CAGR {plain_compounding['cagr_pct']:.2f}% / DD {plain_compounding['max_drawdown_pct']:.1f}%")
    print(f"  with averaging (15/30%)  CAGR {compounding_with_averaging['cagr_pct']:.2f}% / DD {compounding_with_averaging['max_drawdown_pct']:.1f}%")
    print(f"\n(secondary, periodic-capital-call framing, XIRR-based — see report text for why this is a different question)")
    for label, r in (("baseline (no averaging)", baseline), ("with averaging", averaged)):
        print(f"{label:<26} XIRR {r['xirr_pct']:.2f}% | called {CURRENCY_SYMBOL}{r['total_invested']:,.0f} "
              f"-> returned {CURRENCY_SYMBOL}{r['total_returned']:,.0f} ({r['money_multiple']:.2f}x) | "
              f"worst cycle {r['worst_cycle_return_pct']:.1f}% / best cycle {r['best_cycle_return_pct']:.1f}%")
    print(f"\ntotal stock-positions: {averaged['total_positions']}")
    print(f"triggered 1st averaging buy: {averaged['trigger_once']} times "
          f"({averaged['trigger_once']/averaged['total_positions']*100:.1f}% of positions)")
    print(f"triggered 2nd averaging buy: {averaged['trigger_twice']} times "
          f"({averaged['trigger_twice']/averaged['total_positions']*100:.1f}% of positions)")


if __name__ == "__main__":
    main()

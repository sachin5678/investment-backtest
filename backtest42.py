"""
Midcap150 Momentum 10 — with a 200-day EMA regime filter on NIFTY 50.

The user's idea: only ever HOLD the momentum portfolio while the broad
market (NIFTY 50, "the main index") is above its own 200-day EMA. The
moment NIFTY 50 closes below its 200-EMA, sell everything and sit in
100% cash (0% return, no interest modeled — same convention as report
03's "Wait for the Dip") until NIFTY 50 closes back above its 200-EMA,
at which point re-enter with a FRESH top-10 selection (not the old one —
prices have moved, so the selection is recomputed at the moment of
re-entry) rather than waiting for the next scheduled June/December
rebalance.

This means regime switches can happen on ANY trading day, not just
scheduled rebalance dates — the filter takes priority over the normal
semi-annual schedule. A scheduled rebalance that falls while NIFTY 50 is
already below its 200-EMA is simply skipped (still in cash); the next
real action is either the next scheduled rebalance (if still above the
EMA) or the day NIFTY 50 crosses back above it (whichever comes first).

Same top-10, equal-weight, June/December schedule, Midcap150 universe,
original 6m/12m risk-adjusted momentum formula (backtest33.select_top_original,
identical to backtest10.select_top30) as every other Midcap150 Momentum
10 report — the ONLY change is this cash/invested regime switch layered
on top.
"""
import json

import numpy as np
import pandas as pd

from backtest10 import rebalance_dates, cumret_drawdown, series_to_points, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes
from backtest32 import metrics_only
from backtest33 import select_top_original, build_index_generic

EMA_SPAN = 200
MIN_CASH_BLOCK_DAYS = 10   # ignore single-digit-day noise when listing "cash periods" for the report


def build_index_regime_filtered(closes, nifty_close, ema, rbdates, select_fn, confirm_days=1):
    """confirm_days=1 (default) flips state the first day the signal
    disagrees with it — the original report 42 behavior, unchanged. A
    higher confirm_days requires the OPPOSITE signal to hold for that many
    CONSECUTIVE trading days before the state actually flips (a whipsaw
    dampener); a day that agrees with the current state resets the streak
    to zero, same as most practical "N-day confirmation" trend filters."""
    dates = closes.index
    rb_set = set(rbdates)
    index_level = pd.Series(np.nan, index=dates)
    shares = {}
    started = False
    state = "cash"
    selections = []
    state_log = []   # (date, state) once started
    opposite_streak = 0

    def do_select(t_idx):
        return select_fn(closes, t_idx)

    def buy(selected, value_before, price_today):
        dollar_each = value_before / len(selected)
        return {tk: dollar_each / price_today[tk] for tk in selected}

    for i, d in enumerate(dates):
        is_rebalance_day = d in rb_set
        ema_today = ema.iloc[i]
        raw_invested = bool(nifty_close.iloc[i] > ema_today) if pd.notna(ema_today) else False
        price_today = closes.iloc[i]

        if not started:
            regime_invested = raw_invested
            if is_rebalance_day:
                selected = do_select(i)
                if selected is not None:
                    started = True
                    if regime_invested:
                        state = "invested"
                        shares = buy(selected, 100.0, price_today)
                        selections.append({"date": d.strftime("%Y-%m-%d"),
                                            "tickers": [t.replace(".NS", "") for t in selected],
                                            "trigger": "initial_entry"})
                    else:
                        state = "cash"
                        shares = {}
            if started:
                val = 100.0 if state == "cash" else sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares)
                index_level.iloc[i] = val
                state_log.append((d, state))
            continue

        if raw_invested == (state == "invested"):
            opposite_streak = 0
            regime_invested = (state == "invested")
        else:
            opposite_streak += 1
            if opposite_streak >= confirm_days:
                regime_invested = raw_invested
                opposite_streak = 0
            else:
                regime_invested = (state == "invested")

        if state == "invested":
            value_before = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares if pd.notna(price_today.get(tk)))
            if value_before <= 0:
                value_before = index_level.iloc[i - 1]
        else:
            value_before = index_level.iloc[i - 1]

        if state == "invested" and not regime_invested:
            state = "cash"
            shares = {}
            val = value_before
        elif state == "cash" and regime_invested:
            selected = do_select(i)
            if selected is not None:
                shares = buy(selected, value_before, price_today)
                state = "invested"
                selections.append({"date": d.strftime("%Y-%m-%d"),
                                    "tickers": [t.replace(".NS", "") for t in selected],
                                    "trigger": "regime_reentry"})
            val = value_before
        elif state == "invested" and regime_invested and is_rebalance_day:
            selected = do_select(i)
            if selected is not None:
                shares = buy(selected, value_before, price_today)
                selections.append({"date": d.strftime("%Y-%m-%d"),
                                    "tickers": [t.replace(".NS", "") for t in selected],
                                    "trigger": "scheduled_rebalance"})
            val = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares if pd.notna(price_today.get(tk)))
        else:
            if state == "invested":
                val = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares if pd.notna(price_today.get(tk)))
                if val <= 0:
                    val = value_before
            else:
                val = value_before

        index_level.iloc[i] = val
        state_log.append((d, state))

    return index_level.dropna(), selections, state_log


def build_index_regime_filtered_with_hedge(closes, signal_close, signal_ma, rbdates, select_fn, hedge_close, confirm_days=1):
    """Same mechanics as build_index_regime_filtered, except the "cash"
    period holds HEDGE_CLOSE (e.g. gold) instead of literal 0%-return
    cash — marked to market against hedge_close every day, exactly like
    the stock portfolio is marked to market while invested. A separate
    function (not a parameter added to build_index_regime_filtered)
    specifically so report 42-47's already-published cash-based numbers
    can never be affected by this change."""
    dates = closes.index
    rb_set = set(rbdates)
    index_level = pd.Series(np.nan, index=dates)
    shares = {}
    hedge_units = 0.0
    started = False
    state = "cash"
    selections = []
    state_log = []
    opposite_streak = 0

    def do_select(t_idx):
        return select_fn(closes, t_idx)

    def buy(selected, value_before, price_today):
        dollar_each = value_before / len(selected)
        return {tk: dollar_each / price_today[tk] for tk in selected}

    for i, d in enumerate(dates):
        is_rebalance_day = d in rb_set
        ma_today = signal_ma.iloc[i]
        raw_invested = bool(signal_close.iloc[i] > ma_today) if pd.notna(ma_today) else False
        price_today = closes.iloc[i]
        hedge_price_today = hedge_close.iloc[i]

        if not started:
            regime_invested = raw_invested
            if is_rebalance_day:
                selected = do_select(i)
                if selected is not None:
                    started = True
                    if regime_invested:
                        state = "invested"
                        shares = buy(selected, 100.0, price_today)
                        selections.append({"date": d.strftime("%Y-%m-%d"),
                                            "tickers": [t.replace(".NS", "") for t in selected],
                                            "trigger": "initial_entry"})
                    else:
                        state = "cash"
                        hedge_units = 100.0 / hedge_price_today
            if started:
                val = hedge_units * hedge_price_today if state == "cash" else sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares)
                index_level.iloc[i] = val
                state_log.append((d, state))
            continue

        if raw_invested == (state == "invested"):
            opposite_streak = 0
            regime_invested = (state == "invested")
        else:
            opposite_streak += 1
            if opposite_streak >= confirm_days:
                regime_invested = raw_invested
                opposite_streak = 0
            else:
                regime_invested = (state == "invested")

        if state == "invested":
            value_before = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares if pd.notna(price_today.get(tk)))
            if value_before <= 0:
                value_before = index_level.iloc[i - 1]
        else:
            value_before = hedge_units * hedge_price_today

        if state == "invested" and not regime_invested:
            state = "cash"
            shares = {}
            hedge_units = value_before / hedge_price_today
            val = value_before
        elif state == "cash" and regime_invested:
            selected = do_select(i)
            if selected is not None:
                shares = buy(selected, value_before, price_today)
                state = "invested"
                hedge_units = 0.0
                selections.append({"date": d.strftime("%Y-%m-%d"),
                                    "tickers": [t.replace(".NS", "") for t in selected],
                                    "trigger": "regime_reentry"})
            val = value_before
        elif state == "invested" and regime_invested and is_rebalance_day:
            selected = do_select(i)
            if selected is not None:
                shares = buy(selected, value_before, price_today)
                selections.append({"date": d.strftime("%Y-%m-%d"),
                                    "tickers": [t.replace(".NS", "") for t in selected],
                                    "trigger": "scheduled_rebalance"})
            val = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares if pd.notna(price_today.get(tk)))
        else:
            if state == "invested":
                val = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares if pd.notna(price_today.get(tk)))
                if val <= 0:
                    val = value_before
            else:
                val = hedge_units * hedge_price_today

        index_level.iloc[i] = val
        state_log.append((d, state))

    return index_level.dropna(), selections, state_log


def cash_blocks_from_log(state_log, min_days=MIN_CASH_BLOCK_DAYS):
    if not state_log:
        return [], 0.0
    idx = pd.DatetimeIndex([d for d, _ in state_log])
    states = pd.Series([s for _, s in state_log], index=idx)
    pct_cash = float((states == "cash").mean() * 100)

    block_id = (states != states.shift()).cumsum()
    blocks = []
    for _, grp in states.groupby(block_id):
        if grp.iloc[0] != "cash":
            continue
        blocks.append({"start": grp.index[0].strftime("%Y-%m-%d"),
                        "end": grp.index[-1].strftime("%Y-%m-%d"),
                        "days": int(len(grp))})
    blocks = [b for b in blocks if b["days"] >= min_days]
    blocks.sort(key=lambda b: b["days"], reverse=True)
    return blocks, pct_cash


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]
    ema = nifty_close.ewm(span=EMA_SPAN, adjust=False).mean()

    rbdates = rebalance_dates(closes.index, months=(6, 12))

    original_series, original_sel = build_index_generic(closes, rbdates, select_top_original)
    filtered_series, filtered_sel, state_log = build_index_regime_filtered(closes, nifty_close, ema, rbdates, select_top_original)

    common_idx = original_series.index.intersection(filtered_series.index)
    original_metrics = metrics_only(original_series, common_idx)
    filtered_metrics = metrics_only(filtered_series, common_idx)

    nifty_series = nifty_close.loc[common_idx]
    nifty_metrics = metrics_only(nifty_series, common_idx)

    cash_blocks, pct_cash = cash_blocks_from_log(state_log)

    num_scheduled_hit = sum(1 for s in filtered_sel if s["trigger"] == "scheduled_rebalance")
    num_reentries = sum(1 for s in filtered_sel if s["trigger"] == "regime_reentry")
    rb_in_window = [d for d in rbdates if d in common_idx]
    num_scheduled_total = len(rb_in_window)
    num_scheduled_skipped = num_scheduled_total - num_scheduled_hit - (1 if filtered_sel and filtered_sel[0]["trigger"] == "initial_entry" and filtered_sel[0]["date"] in [d.strftime("%Y-%m-%d") for d in rb_in_window] else 0)
    num_scheduled_skipped = max(num_scheduled_skipped, 0)

    def sample(sel):
        return sel[:3] + sel[-3:] if len(sel) > 6 else sel

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "ema_span": EMA_SPAN,
        "pct_time_in_cash": round(pct_cash, 1),
        "num_cash_periods_10d_plus": len(cash_blocks),
        "num_regime_reentries": num_reentries,
        "num_scheduled_rebalances_total": num_scheduled_total,
        "num_scheduled_rebalances_skipped_in_cash": num_scheduled_skipped,
        "cash_periods": cash_blocks[:8],
        "original": {**original_metrics, "selections_sample": sample(original_sel)},
        "filtered": {**filtered_metrics, "selections_sample": sample(filtered_sel)},
        "nifty": nifty_metrics,
    }

    with open("results41.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}")
    print(f"Midcap150 Momentum 10 (no filter)          CAGR {original_metrics['cagr_pct']:.2f}% / DD {original_metrics['max_drawdown_pct']:.1f}%")
    print(f"Midcap150 Momentum 10 (200-EMA regime)      CAGR {filtered_metrics['cagr_pct']:.2f}% / DD {filtered_metrics['max_drawdown_pct']:.1f}%")
    print(f"nifty 50 benchmark                          CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")
    print(f"time spent in cash: {pct_cash:.1f}%  |  cash periods (10d+): {len(cash_blocks)}  |  regime re-entries: {num_reentries}")
    print(f"scheduled rebalances: {num_scheduled_total}, of which skipped (in cash at the time): {num_scheduled_skipped}")
    if cash_blocks:
        print("longest cash periods:")
        for b in cash_blocks[:5]:
            print(f"  {b['start']} -> {b['end']}  ({b['days']}d)")


if __name__ == "__main__":
    main()

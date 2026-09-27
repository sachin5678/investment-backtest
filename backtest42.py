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


def build_index_regime_filtered_breadth(closes, nifty_close, ema, rbdates, select_fn, breadth_threshold=0.5, breadth_ema_span=EMA_SPAN):
    """Same 200-day EMA regime filter as build_index_regime_filtered, PLUS
    a second condition: NIFTY 50 must be above its own 200-EMA AND at
    least breadth_threshold (e.g. 0.5 = 50%) of the relevant top-10
    candidates must ALSO be above their own 200-day EMA (same span,
    computed per-stock). While invested, "the relevant top-10" is
    whatever is CURRENTLY HELD (cheap to check, no recomputation). While
    in cash and NIFTY's condition is met, today's candidate top-10 is
    recomputed via select_fn specifically to check its breadth before
    deciding whether to actually buy — if breadth fails, the strategy
    stays in cash and re-checks the next day, exactly like a real
    "wait for confirmation before entering" rule would."""
    stock_ema = closes.ewm(span=breadth_ema_span, adjust=False).mean()
    dates = closes.index
    rb_set = set(rbdates)
    index_level = pd.Series(np.nan, index=dates)
    shares = {}
    started = False
    state = "cash"
    selections = []
    state_log = []

    def do_select(t_idx):
        return select_fn(closes, t_idx)

    def buy(selected, value_before, price_today):
        dollar_each = value_before / len(selected)
        return {tk: dollar_each / price_today[tk] for tk in selected}

    def breadth_ok(tickers, i):
        if not tickers:
            return False
        price_today = closes.iloc[i]
        ema_today = stock_ema.iloc[i]
        cnt = sum(1 for tk in tickers
                   if pd.notna(price_today.get(tk)) and pd.notna(ema_today.get(tk)) and price_today[tk] > ema_today[tk])
        return (cnt / len(tickers)) >= breadth_threshold

    for i, d in enumerate(dates):
        is_rebalance_day = d in rb_set
        ema_today = ema.iloc[i]
        nifty_ok = bool(nifty_close.iloc[i] > ema_today) if pd.notna(ema_today) else False
        price_today = closes.iloc[i]

        if not started:
            if is_rebalance_day and nifty_ok:
                selected = do_select(i)
                if selected is not None and breadth_ok(selected, i):
                    started = True
                    state = "invested"
                    shares = buy(selected, 100.0, price_today)
                    selections.append({"date": d.strftime("%Y-%m-%d"),
                                        "tickers": [t.replace(".NS", "") for t in selected],
                                        "trigger": "initial_entry"})
            if started:
                val = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares)
                index_level.iloc[i] = val
                state_log.append((d, state))
            continue

        if state == "invested":
            value_before = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares if pd.notna(price_today.get(tk)))
            if value_before <= 0:
                value_before = index_level.iloc[i - 1]
            still_ok = nifty_ok and breadth_ok(list(shares.keys()), i)
            if not still_ok:
                state = "cash"
                shares = {}
                val = value_before
            elif is_rebalance_day:
                selected = do_select(i)
                if selected is not None:
                    shares = buy(selected, value_before, price_today)
                    selections.append({"date": d.strftime("%Y-%m-%d"),
                                        "tickers": [t.replace(".NS", "") for t in selected],
                                        "trigger": "scheduled_rebalance"})
                val = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares if pd.notna(price_today.get(tk)))
            else:
                val = value_before
        else:
            value_before = index_level.iloc[i - 1]
            val = value_before
            if nifty_ok:
                selected = do_select(i)
                if selected is not None and breadth_ok(selected, i):
                    shares = buy(selected, value_before, price_today)
                    state = "invested"
                    selections.append({"date": d.strftime("%Y-%m-%d"),
                                        "tickers": [t.replace(".NS", "") for t in selected],
                                        "trigger": "regime_reentry"})
                    val = value_before

        index_level.iloc[i] = val
        state_log.append((d, state))

    return index_level.dropna(), selections, state_log


REENTRY_EMA_SPAN = 50


def build_index_regime_filtered_asymmetric(closes, signal_close, exit_ema, reentry_ema, rbdates, select_fn, confirm_days=1):
    """Same regime-filter mechanics as build_index_regime_filtered, except
    the signal used to decide EXIT (while invested) and the signal used
    to decide RE-ENTRY (while in cash) are DIFFERENT EMAs of the same
    price series — a slow one (e.g. 200-day) for exits, so the filter
    doesn't whipsaw out on every minor dip, and a fast one (e.g. 50-day)
    for re-entries, so the filter doesn't sit out the early part of a
    recovery waiting for the slow average to catch up. confirm_days
    behaves exactly as in build_index_regime_filtered, applied
    separately to whichever condition is currently in force."""
    dates = closes.index
    rb_set = set(rbdates)
    index_level = pd.Series(np.nan, index=dates)
    shares = {}
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

    def raw_signal(i, currently_invested):
        ma = (exit_ema if currently_invested else reentry_ema).iloc[i]
        return bool(signal_close.iloc[i] > ma) if pd.notna(ma) else False

    for i, d in enumerate(dates):
        is_rebalance_day = d in rb_set
        price_today = closes.iloc[i]

        if not started:
            regime_invested = raw_signal(i, currently_invested=False)
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

        raw_invested = raw_signal(i, currently_invested=(state == "invested"))
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


def build_smooth_exposure(fully_invested_series, signal_close, ema, band_pct=0.15):
    """A continuous alternative to the binary cash/invested switch: scale
    equity exposure smoothly between 100% (signal_close at or above its
    EMA) and 0% (signal_close at or below (1-band_pct) times its EMA),
    linear in between, instead of a hard on/off flip. There is no
    discrete "state" here at all, so there is nothing to whipsaw between
    — the exposure fraction just moves a little day to day as the ratio
    moves.

    Mechanically this reuses the ALREADY-COMPUTED fully-invested equity
    curve's own daily returns (fully_invested_series, e.g. from
    build_index_generic) and scales each day's return by that day's
    exposure fraction — cash contributes a flat 0% for the unexposed
    portion, same convention as every other cash-holding report here.
    Today's exposure fraction is derived from YESTERDAY's close-to-EMA
    ratio (shifted by one day) so that today's return isn't scaled using
    information only available at today's own close — the same
    same-day-signal-next-day-effect ordering implied throughout reports
    42-64, just made explicit here since a continuous fraction makes the
    ordering easy to get backwards by accident."""
    ratio = (signal_close / ema - (1 - band_pct)) / band_pct
    exposure = ratio.clip(lower=0.0, upper=1.0)
    exposure = exposure.reindex(fully_invested_series.index).ffill().fillna(0.0)
    exposure_used = exposure.shift(1).fillna(0.0)
    rets = fully_invested_series.pct_change().fillna(0.0)
    blended_ret = exposure_used * rets
    blended = (1 + blended_ret).cumprod() * float(fully_invested_series.iloc[0])
    return blended, exposure


def build_smooth_exposure_with_hedge(fully_invested_series, signal_close, ema, hedge_close, band_pct=0.15):
    """Same mechanics as build_smooth_exposure, except the UNEXPOSED
    portion of the portfolio earns hedge_close's own daily return instead
    of a flat 0% — e.g. gold (GOLDBEES.NS) or a liquid-fund proxy —
    exactly mirroring how build_index_regime_filtered_with_hedge extends
    the binary filter's cash sleeve to hold something other than cash.
    Same look-ahead-safe ordering: today's blended return uses
    YESTERDAY's exposure fraction."""
    ratio = (signal_close / ema - (1 - band_pct)) / band_pct
    exposure = ratio.clip(lower=0.0, upper=1.0)
    exposure = exposure.reindex(fully_invested_series.index).ffill().fillna(0.0)
    exposure_used = exposure.shift(1).fillna(0.0)
    rets = fully_invested_series.pct_change().fillna(0.0)
    hedge_rets = hedge_close.reindex(fully_invested_series.index).ffill().pct_change().fillna(0.0)
    blended_ret = exposure_used * rets + (1 - exposure_used) * hedge_rets
    blended = (1 + blended_ret).cumprod() * float(fully_invested_series.iloc[0])
    return blended, exposure


def build_index_core_satellite(closes, signal_close, ema, rbdates, select_fn, hedge_close,
                                on_momentum_weight=0.7, on_hedge_weight=0.3, confirm_days=1):
    """A permanent core-satellite split, not a cash/invested switch: while
    signal_close is above its EMA, hold on_momentum_weight (e.g. 70%) in
    the top-10 momentum portfolio and on_hedge_weight (e.g. 30%) in
    hedge_close (gold) AT ALL TIMES — even in an otherwise-healthy market,
    30% always sits in gold. The moment signal_close closes below its
    EMA, sell the ENTIRE portfolio into 100% hedge_close (a full flight to
    gold, not just topping up the existing 30% sleeve) until signal_close
    closes back above its EMA, at which point re-enter at the SAME
    70/30 split with a freshly recomputed top-10 (not the old one).

    The 70/30 split itself is only re-targeted exactly at scheduled
    rebalance dates (rbdates) while already in the "on" regime, or at the
    moment of a regime transition — between those events, the momentum
    and gold sleeves are each left to drift with their own returns, same
    convention as every other rebalance-based report here."""
    dates = closes.index
    rb_set = set(rbdates)
    index_level = pd.Series(np.nan, index=dates)
    shares = {}
    hedge_units = 0.0
    started = False
    full_hedge = True
    selections = []
    state_log = []
    opposite_streak = 0

    def do_select(t_idx):
        return select_fn(closes, t_idx)

    def split_into(selected, total_value, price_today, hedge_price_today):
        mom_target = total_value * on_momentum_weight
        hedge_target = total_value * on_hedge_weight
        new_shares = {tk: mom_target / len(selected) / price_today[tk] for tk in selected}
        new_hedge_units = hedge_target / hedge_price_today
        return new_shares, new_hedge_units

    for i, d in enumerate(dates):
        is_rebalance_day = d in rb_set
        ema_today = ema.iloc[i]
        raw_on = bool(signal_close.iloc[i] > ema_today) if pd.notna(ema_today) else False
        price_today = closes.iloc[i]
        hedge_price_today = hedge_close.iloc[i]

        if not started:
            if is_rebalance_day:
                if raw_on:
                    selected = do_select(i)
                    if selected is not None:
                        started = True
                        full_hedge = False
                        shares, hedge_units = split_into(selected, 100.0, price_today, hedge_price_today)
                        selections.append({"date": d.strftime("%Y-%m-%d"),
                                            "tickers": [t.replace(".NS", "") for t in selected],
                                            "trigger": "initial_entry"})
                else:
                    started = True
                    full_hedge = True
                    hedge_units = 100.0 / hedge_price_today
            if started:
                val = (0.0 if full_hedge else sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares)) + hedge_units * hedge_price_today
                index_level.iloc[i] = val
                state_log.append((d, "full_gold" if full_hedge else "70_30"))
            continue

        currently_on = not full_hedge
        if raw_on == currently_on:
            opposite_streak = 0
            confirmed_on = currently_on
        else:
            opposite_streak += 1
            if opposite_streak >= confirm_days:
                confirmed_on = raw_on
                opposite_streak = 0
            else:
                confirmed_on = currently_on

        mom_value_before = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares if pd.notna(price_today.get(tk))) if shares else 0.0
        hedge_value_before = hedge_units * hedge_price_today
        value_before = mom_value_before + hedge_value_before
        if value_before <= 0:
            value_before = index_level.iloc[i - 1]

        if confirmed_on and full_hedge:
            selected = do_select(i)
            if selected is not None:
                shares, hedge_units = split_into(selected, value_before, price_today, hedge_price_today)
                full_hedge = False
                selections.append({"date": d.strftime("%Y-%m-%d"),
                                    "tickers": [t.replace(".NS", "") for t in selected],
                                    "trigger": "regime_reentry"})
            val = value_before
        elif (not confirmed_on) and (not full_hedge):
            shares = {}
            hedge_units = value_before / hedge_price_today
            full_hedge = True
            val = value_before
        elif confirmed_on and is_rebalance_day:
            selected = do_select(i)
            if selected is not None:
                shares, hedge_units = split_into(selected, value_before, price_today, hedge_price_today)
                selections.append({"date": d.strftime("%Y-%m-%d"),
                                    "tickers": [t.replace(".NS", "") for t in selected],
                                    "trigger": "scheduled_rebalance"})
            val = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares if pd.notna(price_today.get(tk))) + hedge_units * hedge_price_today
        else:
            val = (0.0 if full_hedge else sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares if pd.notna(price_today.get(tk)))) + hedge_units * hedge_price_today
            if val <= 0:
                val = value_before

        index_level.iloc[i] = val
        state_log.append((d, "full_gold" if full_hedge else "70_30"))

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

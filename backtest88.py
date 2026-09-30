"""
Midcap150 Momentum 10 — report 48's exact design, testing execution
TIMING on the scheduled semi-annual rebalance.

TWO THINGS WERE ASKED; ONLY ONE IS ACTUALLY TESTABLE WITH THIS PROJECT'S
DATA:
  - "Rebalance at 3:00 PM instead of 3:30 PM (close)" — NOT TESTABLE.
    This project's entire price history, for every report, comes from
    yfinance's DAILY OHLC bars (Open/High/Low/Close) — there is no
    intraday tick or minute-level data anywhere in this project, and
    18 years of historical intraday data for ~150 stocks isn't available
    from any free source this project uses. There is no honest way to
    compute "the price at 3:00 PM" from a daily bar; the Close price IS
    the 3:30 PM (NSE's actual close) print, and nothing in the cache
    represents any other specific time of day. This variant is skipped
    entirely rather than faked with a made-up proxy.
  - "Rebalance next-day morning instead of same day" — TESTABLE. Real
    per-ticker OPEN prices ARE cached for the whole Midcap150 universe
    (confirmed directly from the source pkl files before writing this).
    This tests filling the SCHEDULED semi-annual reselection at the
    FIRST TRADING DAY AFTER the rebalance month's last day, at THAT
    day's OPEN price, instead of the last day's own CLOSE — a genuinely
    different execution assumption from every other report here, which
    treats scheduled events as fillable at their own day's close (see
    backtest4.py's docstring for that convention, and why REACTIVE
    signals use next-day open instead).

Only the SCHEDULED stock-selection refresh is delayed this way — the
200-EMA regime filter's own entries/exits into and out of gold are left
completely unchanged (still same-day close, exactly like report 48),
so this isolates ONE specific timing question rather than changing two
things at once.
"""
import json
import sys

import numpy as np
import pandas as pd

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes, fetch_gold_cleaned
from backtest32 import metrics_only
from backtest33 import select_top_original
from backtest42 import build_index_regime_filtered_with_hedge, EMA_SPAN
from niftymidcap150_symbols import NIFTY_MIDCAP150_SYMBOLS


def load_midcap150_opens():
    raw200 = pd.read_pickle("universe_raw.pkl")
    extra_q = pd.read_pickle("quality50_extra_raw.pkl")
    extra_m = pd.read_pickle("midcap150_extra_raw.pkl")
    tickers = [s + ".NS" for s in NIFTY_MIDCAP150_SYMBOLS]

    def get_open(t):
        for src in (raw200, extra_q, extra_m):
            if t in set(c[0] for c in src.columns):
                return src[(t, "Open")]
        raise KeyError(t)

    opens = pd.DataFrame({t: get_open(t) for t in tickers}).sort_index().ffill()
    return opens


def build_index_regime_filtered_with_hedge_delayed_rebalance(closes, opens, signal_close, signal_ma, rbdates,
                                                               select_fn, hedge_close, confirm_days=1):
    """Identical mechanics to backtest42.build_index_regime_filtered_with_hedge
    EXCEPT the scheduled semi-annual reselection (state stays "invested",
    is_rebalance_day) is deferred: the new top-10 is computed using data
    AS OF the scheduled day (same signal timing as always), but the
    actual trade executes at the NEXT TRADING DAY'S OPEN price instead of
    the scheduled day's own close. Regime entries/exits (into/out of
    gold) are UNCHANGED — still same-day close, exactly like report 48."""
    dates = closes.index
    rb_set = set(rbdates)
    index_level = pd.Series(np.nan, index=dates)
    shares = {}
    hedge_units = 0.0
    started = False
    state = "cash"
    selections = []
    opposite_streak = 0
    pending = None  # tickers awaiting execution at TODAY's open

    def buy(selected, value_before, price_today):
        dollar_each = value_before / len(selected)
        return {tk: dollar_each / price_today[tk] for tk in selected}

    for i, d in enumerate(dates):
        is_rebalance_day = d in rb_set
        ma_today = signal_ma.iloc[i]
        raw_invested = bool(signal_close.iloc[i] > ma_today) if pd.notna(ma_today) else False
        price_today = closes.iloc[i]
        open_today = opens.iloc[i]
        hedge_price_today = hedge_close.iloc[i]

        # Execute yesterday's scheduled selection at TODAY's open, if pending.
        if pending is not None and state == "invested":
            value_now = sum(shares.get(tk, 0.0) * open_today.get(tk, np.nan) for tk in shares
                             if pd.notna(open_today.get(tk)))
            if value_now <= 0:
                value_now = index_level.iloc[i - 1] if i > 0 else 100.0
            valid_opens = {tk: open_today.get(tk) for tk in pending if pd.notna(open_today.get(tk)) and open_today.get(tk, 0) > 0}
            if valid_opens:
                dollar_each = value_now / len(valid_opens)
                shares = {tk: dollar_each / p for tk, p in valid_opens.items()}
                selections.append({"date": d.strftime("%Y-%m-%d"),
                                    "tickers": [t.replace(".NS", "") for t in valid_opens],
                                    "trigger": "scheduled_rebalance_next_open"})
            pending = None

        if not started:
            regime_invested = raw_invested
            if is_rebalance_day:
                selected = select_fn(closes, i)
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
                val = hedge_units * hedge_price_today if state == "cash" else sum(
                    shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares)
                index_level.iloc[i] = val
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
            pending = None  # a regime exit cancels any pending scheduled re-entry
            val = value_before
        elif state == "cash" and regime_invested:
            selected = select_fn(closes, i)
            if selected is not None:
                shares = buy(selected, value_before, price_today)
                state = "invested"
                hedge_units = 0.0
                selections.append({"date": d.strftime("%Y-%m-%d"),
                                    "tickers": [t.replace(".NS", "") for t in selected],
                                    "trigger": "regime_reentry"})
            val = value_before
        elif state == "invested" and regime_invested and is_rebalance_day:
            # DEFERRED: mark today at the OLD shares' close value; schedule
            # the new selection to execute at TOMORROW's open instead.
            selected = select_fn(closes, i)
            if selected is not None:
                pending = selected
            val = value_before
        else:
            if state == "invested":
                val = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares if pd.notna(price_today.get(tk)))
                if val <= 0:
                    val = value_before
            else:
                val = hedge_units * hedge_price_today

        index_level.iloc[i] = val

    return index_level.dropna(), selections


def main():
    closes = load_midcap150_closes()
    opens = load_midcap150_opens()
    nifty = fetch("^NSEI")
    gold = fetch_gold_cleaned()
    common = closes.index.intersection(nifty.index).intersection(opens.index)
    closes = closes.loc[common]
    opens = opens.loc[common]
    nifty_close = nifty.loc[common, "Close"]
    gold_aligned = gold["Close"].reindex(common).ffill().bfill()
    real_gold_idx = common.intersection(gold["Close"].index)

    ema200 = nifty_close.ewm(span=EMA_SPAN, adjust=False).mean()
    rbdates = rebalance_dates(closes.index, months=(6, 12))

    same_day_close, _, _ = build_index_regime_filtered_with_hedge(
        closes, nifty_close, ema200, rbdates, select_top_original, gold_aligned)
    next_day_open, sel_ndo = build_index_regime_filtered_with_hedge_delayed_rebalance(
        closes, opens, nifty_close, ema200, rbdates, select_top_original, gold_aligned)

    common_idx = same_day_close.index.intersection(next_day_open.index).intersection(real_gold_idx)
    same_day_metrics = metrics_only(same_day_close, common_idx)
    next_day_metrics = metrics_only(next_day_open, common_idx)
    next_day_metrics["selections_sample"] = sel_ndo[:3] + sel_ndo[-3:] if len(sel_ndo) > 6 else sel_ndo
    nifty_metrics = metrics_only(nifty_close, common_idx)
    gold_bench_metrics = metrics_only(gold["Close"], common_idx.intersection(real_gold_idx))

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "ema_span": EMA_SPAN, "num_rebalances": len(rbdates),
        "same_day_close": same_day_metrics, "next_day_open": next_day_metrics,
        "nifty": nifty_metrics, "gold_benchmark": gold_bench_metrics,
    }

    with open("results87.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}")
    print(f"same-day close (report 48)  CAGR {same_day_metrics['cagr_pct']:.2f}% / DD {same_day_metrics['max_drawdown_pct']:.1f}%")
    print(f"next-day open               CAGR {next_day_metrics['cagr_pct']:.2f}% / DD {next_day_metrics['max_drawdown_pct']:.1f}%")
    print(f"nifty 50                    CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")
    print(f"gold alone                  CAGR {gold_bench_metrics['cagr_pct']:.2f}% / DD {gold_bench_metrics['max_drawdown_pct']:.1f}%")


if __name__ == "__main__":
    main()

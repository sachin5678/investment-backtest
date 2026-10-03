"""Quick experiment (not a numbered report): report 48's 200-EMA gold
regime filter, with a dip-buy override on the gold sleeve — when the
index has fallen >=15% below its own 200-EMA, switch back into stocks
(contrarian re-entry) rather than waiting for the EMA cross back
above. Standard case (gap < 15% while below EMA) still holds gold.

Daily-evaluated: if the gap then shrinks below the threshold before
the index recovers above its EMA, the strategy flips back to gold
(whipsaw possible — this measures it, intentionally not suppressed).

Variants tested: standard report-48 gold, and the dip-buy override at
gap thresholds of 10% / 15% / 20% / 25%.
"""
import pandas as pd
import numpy as np

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes, fetch_gold_cleaned
from backtest32 import metrics_only
from backtest33 import select_top_original, build_index_generic
from backtest42 import build_index_regime_filtered_with_hedge, EMA_SPAN


def build_with_dipbuy(closes, nifty_close, ema, rbdates, select_fn, hedge_close, gap_thresh):
    """build_index_regime_filtered_with_hedge(confirm_days=1) with
    raw_invested = (price > EMA) OR ((EMA - price)/EMA >= gap_thresh)."""
    dates = closes.index
    rb_set = set(rbdates)
    index_level = pd.Series(np.nan, index=dates)
    shares, hedge_units = {}, 0.0
    started, state = False, "cash"
    selections, state_log = [], []

    def buy(selected, value_before, price_today):
        return {tk: (value_before / len(selected)) / price_today[tk] for tk in selected}

    for i, d in enumerate(dates):
        is_rb = d in rb_set
        ma_today = ema.iloc[i]
        price_t = nifty_close.iloc[i]
        if pd.notna(ma_today):
            gap = (ma_today - price_t) / ma_today
            raw_invested = bool(price_t > ma_today) or bool(gap >= gap_thresh)
        else:
            raw_invested = False
        price_today = closes.iloc[i]
        hedge_price_today = hedge_close.iloc[i]

        if not started:
            regime_invested = raw_invested
            if is_rb:
                selected = select_fn(closes, i)
                if selected is not None:
                    started = True
                    if regime_invested:
                        state = "invested"
                        shares = buy(selected, 100.0, price_today)
                        selections.append({"date": d.strftime("%Y-%m-%d"), "trigger": "initial_entry"})
                    else:
                        state = "cash"
                        hedge_units = 100.0 / hedge_price_today
            if started:
                val = hedge_units * hedge_price_today if state == "cash" else sum(s * price_today.get(t, 0.0) for t, s in shares.items())
                index_level.iloc[i] = val
                state_log.append((d, state))
            continue

        regime_invested = raw_invested

        if state == "invested":
            value_before = sum(s * price_today.get(t, 0.0) for t, s in shares.items() if pd.notna(price_today.get(t)))
            if value_before <= 0:
                value_before = index_level.iloc[i - 1]
        else:
            value_before = hedge_units * hedge_price_today

        if state == "invested" and not regime_invested:
            state = "cash"; shares = {}
            hedge_units = value_before / hedge_price_today
            val = value_before
        elif state == "cash" and regime_invested:
            selected = select_fn(closes, i)
            if selected is not None:
                shares = buy(selected, value_before, price_today)
                state = "invested"; hedge_units = 0.0
                selections.append({"date": d.strftime("%Y-%m-%d"), "trigger": "dipbuy_or_regime_reentry"})
            val = value_before
        elif state == "invested" and regime_invested and is_rb:
            selected = select_fn(closes, i)
            if selected is not None:
                shares = buy(selected, value_before, price_today)
                selections.append({"date": d.strftime("%Y-%m-%d"), "trigger": "scheduled_rebalance"})
            val = sum(s * price_today.get(t, 0.0) for t, s in shares.items() if pd.notna(price_today.get(t)))
        else:
            if state == "invested":
                val = sum(s * price_today.get(t, 0.0) for t, s in shares.items() if pd.notna(price_today.get(t)))
                if val <= 0:
                    val = value_before
            else:
                val = hedge_units * hedge_price_today

        index_level.iloc[i] = val
        state_log.append((d, state))

    return index_level.dropna(), selections, state_log


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    gold = fetch_gold_cleaned()
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]
    gold_aligned = gold["Close"].reindex(common).ffill().bfill()
    ema = nifty_close.ewm(span=EMA_SPAN, adjust=False).mean()
    rbdates = rebalance_dates(closes.index, months=(6, 12))

    original_series, _ = build_index_generic(closes, rbdates, select_top_original)
    gold_series, _, _ = build_index_regime_filtered_with_hedge(
        closes, nifty_close, ema, rbdates, select_top_original, gold_aligned)

    common_idx = original_series.index.intersection(gold_series.index)
    series = {"report48 (no override)": gold_series}
    for thr in (0.10, 0.15, 0.20, 0.25):
        s, sel, log = build_with_dipbuy(closes, nifty_close, ema, rbdates, select_top_original, gold_aligned, thr)
        series[f"dip-buy override @ {int(thr*100)}%"] = s
        common_idx = common_idx.intersection(s.index)
        reentries = sum(1 for x in sel if x["trigger"] == "dipbuy_or_regime_reentry")
        pct_gold = sum(1 for _, st in log if st == "cash") / len(log) * 100
        print(f"{thr:.0%} threshold: {reentries} stock re-entries, {pct_gold:.1f}% of days in gold sleeve")

    print(f"\nwindow {common_idx[0].date()} -> {common_idx[-1].date()}")
    for name, s in series.items():
        m = metrics_only(s, common_idx)
        print(f"{name:32s} CAGR {m['cagr_pct']:.2f}% / DD {m['max_drawdown_pct']:.1f}% / underwater {m['longest_underwater_days']}d")
    m = metrics_only(original_series, common_idx)
    print(f"{'no filter':32s} CAGR {m['cagr_pct']:.2f}% / DD {m['max_drawdown_pct']:.1f}% / underwater {m['longest_underwater_days']}d")


if __name__ == "__main__":
    main()

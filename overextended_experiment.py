"""Quick experiment (not a numbered report): report 48's 200-EMA gold
regime filter, with an OVERHEATED-EXIT override on the stock sleeve —
when NIFTY 50 is above its 200-EMA but trading >=15% ABOVE it, treat
that as extended and move everything to gold. Stay in gold until the
gap compresses back below 5%. Standard below-EMA risk-off still holds
gold; re-entry from that state happens on the usual EMA cross (gap is
~0 then, always < 5%).

Tests overextension thresholds of 10/15/20% with re-entry thresholds
of 3/5/7%.
"""
import pandas as pd
import numpy as np

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes, fetch_gold_cleaned
from backtest32 import metrics_only
from backtest33 import select_top_original, build_index_generic
from backtest42 import build_index_regime_filtered_with_hedge, EMA_SPAN


def build(closes, nifty_close, ema, rbdates, select_fn, hedge_close, over_pct, exit_pct):
    dates = closes.index
    rb_set = set(rbdates)
    index_level = pd.Series(np.nan, index=dates)
    shares, hedge_units = {}, 0.0
    started, state = False, "cash"
    selections, state_log = [], []
    gold_reason = None   # "risk_off" | "overextended"

    def buy(selected, value_before, price_today):
        return {tk: (value_before / len(selected)) / price_today[tk] for tk in selected}

    for i, d in enumerate(dates):
        is_rb = d in rb_set
        ma_today = ema.iloc[i]
        price_t = nifty_close.iloc[i]
        price_today = closes.iloc[i]
        hedge_price_today = hedge_close.iloc[i]

        # regime signal with the overextended latch
        if pd.isna(ma_today):
            desired = "cash"
        elif state == "invested":
            if price_t < ma_today:
                desired = "cash"
            elif (price_t - ma_today) / ma_today >= over_pct:
                desired = "cash"
            else:
                desired = "invested"
        else:  # in gold sleeve
            if gold_reason == "overextended":
                if price_t > ma_today and (price_t - ma_today) / ma_today < exit_pct:
                    desired = "invested"
                else:
                    desired = "cash"
            else:  # risk_off: plain EMA cross back
                desired = "invested" if price_t > ma_today else "cash"

        if not started:
            if pd.notna(ma_today) and is_rb:
                selected = select_fn(closes, i)
                if selected is not None:
                    started = True
                    if price_t > ma_today:
                        state = "invested"
                        shares = buy(selected, 100.0, price_today)
                        selections.append({"date": d.strftime("%Y-%m-%d"), "trigger": "initial_entry"})
                    else:
                        state = "cash"
                        gold_reason = "risk_off"
                        hedge_units = 100.0 / hedge_price_today
            if started:
                val = hedge_units * hedge_price_today if state == "cash" else sum(s * price_today.get(t, 0.0) for t, s in shares.items())
                index_level.iloc[i] = val
                state_log.append((d, state))
            continue

        if state == "invested":
            value_before = sum(s * price_today.get(t, 0.0) for t, s in shares.items() if pd.notna(price_today.get(t)))
            if value_before <= 0:
                value_before = index_level.iloc[i - 1]
        else:
            value_before = hedge_units * hedge_price_today

        if state == "invested" and desired == "cash":
            gold_reason = "overextended" if (pd.notna(ma_today) and price_t >= ma_today) else "risk_off"
            state = "cash"; shares = {}
            hedge_units = value_before / hedge_price_today
            val = value_before
        elif state == "cash" and desired == "invested":
            selected = select_fn(closes, i)
            if selected is not None:
                shares = buy(selected, value_before, price_today)
                state = "invested"; hedge_units = 0.0; gold_reason = None
                selections.append({"date": d.strftime("%Y-%m-%d"), "trigger": "regime_or_gap_reentry"})
            val = value_before
        elif state == "invested" and desired == "invested" and is_rb:
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
    for over in (0.10, 0.15, 0.20):
        for exit_ in (0.03, 0.05, 0.07):
            s, sel, log = build(closes, nifty_close, ema, rbdates, select_top_original, gold_aligned, over, exit_)
            common_idx = common_idx.intersection(s.index)
            series[f"over>{int(over*100)}% / re-enter<{int(exit_*100)}%"] = s

    print(f"window {common_idx[0].date()} -> {common_idx[-1].date()}")
    for name, s in series.items():
        m = metrics_only(s, common_idx)
        print(f"{name:32s} CAGR {m['cagr_pct']:.2f}% / DD {m['max_drawdown_pct']:.1f}% / underwater {m['longest_underwater_days']}d")
    m = metrics_only(original_series, common_idx)
    print(f"{'no filter':32s} CAGR {m['cagr_pct']:.2f}% / DD {m['max_drawdown_pct']:.1f}% / underwater {m['longest_underwater_days']}d")


if __name__ == "__main__":
    main()

"""
Midcap150 Momentum 10 — report 48's exact design, with 0.1% slippage on
EVERY trade: every buy fills 0.1% ABOVE the modeled price, every sell
fills 0.1% BELOW it. Zero transaction costs has been a disclosed
simplification in every report in this project so far (including report
48 itself) — this tests exactly how much of the reported edge survives
once a specific, real-feeling cost is actually charged.

Every transition in report 48's design is really a TWO-LEG trade (sell
whatever you're currently holding, buy whatever you're moving into), so
slippage is charged on both legs every time capital changes what it's
invested in:
  - Regime EXIT (stocks -> gold): sell all 10 stocks 0.1% below price,
    then buy gold 0.1% above its price.
  - Regime RE-ENTRY (gold -> stocks): sell gold 0.1% below its price,
    then buy the new top-10 0.1% above price.
  - Scheduled semi-annual REFRESH (stocks -> new stocks, regime stays
    "on"): sell the old top-10 0.1% below price, buy the new top-10
    0.1% above price — a full round-trip, same as any other rebalance.
  - The very FIRST entry only pays the buy-side markup (there's no prior
    real asset being liquidated to sell).

Mark-to-market on days with NO trade is unaffected — slippage only ever
hits at the moment of an actual buy or sell, exactly as a real brokerage
fill would work.
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

SLIPPAGE = 0.001  # 0.1%


def build_index_regime_filtered_with_hedge_slippage(closes, signal_close, signal_ma, rbdates, select_fn,
                                                      hedge_close, slippage=SLIPPAGE, confirm_days=1):
    """Identical mechanics to backtest42.build_index_regime_filtered_with_hedge
    except every buy fills at price*(1+slippage) and every sell fills at
    price*(1-slippage) — see this file's own docstring for exactly which
    transitions count as a two-leg (sell+buy) trade vs. a buy-only one."""
    dates = closes.index
    rb_set = set(rbdates)
    index_level = pd.Series(np.nan, index=dates)
    shares = {}
    hedge_units = 0.0
    started = False
    state = "cash"
    selections = []
    opposite_streak = 0
    buy_mult = 1 + slippage
    sell_mult = 1 - slippage

    def do_select(t_idx):
        return select_fn(closes, t_idx)

    def buy_stocks(selected, value_before, price_today):
        dollar_each = value_before / len(selected)
        return {tk: dollar_each / (price_today[tk] * buy_mult) for tk in selected}

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
                        shares = buy_stocks(selected, 100.0, price_today)
                        selections.append({"date": d.strftime("%Y-%m-%d"),
                                            "tickers": [t.replace(".NS", "") for t in selected],
                                            "trigger": "initial_entry"})
                    else:
                        state = "cash"
                        hedge_units = 100.0 / (hedge_price_today * buy_mult)
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
            mtm_value = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares if pd.notna(price_today.get(tk)))
            if mtm_value <= 0:
                mtm_value = index_level.iloc[i - 1]
        else:
            mtm_value = hedge_units * hedge_price_today

        if state == "invested" and not regime_invested:
            # SELL all stocks (0.1% below price), BUY gold (0.1% above).
            sell_value = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) * sell_mult for tk in shares
                              if pd.notna(price_today.get(tk)))
            if sell_value <= 0:
                sell_value = mtm_value * sell_mult
            state = "cash"
            shares = {}
            hedge_units = sell_value / (hedge_price_today * buy_mult)
            val = sell_value
        elif state == "cash" and regime_invested:
            selected = do_select(i)
            if selected is not None:
                sell_value = hedge_units * hedge_price_today * sell_mult
                shares = buy_stocks(selected, sell_value, price_today)
                state = "invested"
                hedge_units = 0.0
                selections.append({"date": d.strftime("%Y-%m-%d"),
                                    "tickers": [t.replace(".NS", "") for t in selected],
                                    "trigger": "regime_reentry"})
                val = sell_value
            else:
                val = mtm_value
        elif state == "invested" and regime_invested and is_rebalance_day:
            selected = do_select(i)
            if selected is not None:
                sell_value = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) * sell_mult for tk in shares
                                  if pd.notna(price_today.get(tk)))
                if sell_value <= 0:
                    sell_value = mtm_value * sell_mult
                shares = buy_stocks(selected, sell_value, price_today)
                selections.append({"date": d.strftime("%Y-%m-%d"),
                                    "tickers": [t.replace(".NS", "") for t in selected],
                                    "trigger": "scheduled_rebalance"})
                val = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares if pd.notna(price_today.get(tk)))
            else:
                val = mtm_value
        else:
            val = mtm_value

        index_level.iloc[i] = val

    return index_level.dropna(), selections


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

    frictionless, _, _ = build_index_regime_filtered_with_hedge(
        closes, nifty_close, ema200, rbdates, select_top_original, gold_aligned)
    cost_loaded, sel_cost = build_index_regime_filtered_with_hedge_slippage(
        closes, nifty_close, ema200, rbdates, select_top_original, gold_aligned, slippage=SLIPPAGE)

    common_idx = frictionless.index.intersection(cost_loaded.index).intersection(real_gold_idx)
    frictionless_metrics = metrics_only(frictionless, common_idx)
    cost_loaded_metrics = metrics_only(cost_loaded, common_idx)
    cost_loaded_metrics["selections_sample"] = sel_cost[:3] + sel_cost[-3:] if len(sel_cost) > 6 else sel_cost
    nifty_metrics = metrics_only(nifty_close, common_idx)
    gold_bench_metrics = metrics_only(gold["Close"], common_idx.intersection(real_gold_idx))

    num_stock_trades = sum(1 for s in sel_cost) * 10  # 10 stocks bought at every listed selection event
    num_gold_transitions = sum(1 for s in sel_cost if s["trigger"] == "regime_reentry")

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "ema_span": EMA_SPAN, "slippage_pct": SLIPPAGE * 100, "num_rebalances": len(rbdates),
        "num_selection_events": len(sel_cost), "num_stock_buy_legs": num_stock_trades,
        "frictionless": frictionless_metrics, "cost_loaded": cost_loaded_metrics,
        "nifty": nifty_metrics, "gold_benchmark": gold_bench_metrics,
    }

    with open("results88.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}")
    print(f"frictionless (report 48)   CAGR {frictionless_metrics['cagr_pct']:.2f}% / DD {frictionless_metrics['max_drawdown_pct']:.1f}%")
    print(f"0.1% slippage both sides   CAGR {cost_loaded_metrics['cagr_pct']:.2f}% / DD {cost_loaded_metrics['max_drawdown_pct']:.1f}%")
    print(f"nifty 50                  CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")
    print(f"gold alone                 CAGR {gold_bench_metrics['cagr_pct']:.2f}% / DD {gold_bench_metrics['max_drawdown_pct']:.1f}%")
    print(f"\ntotal selection/switch events: {len(sel_cost)} ({num_gold_transitions} regime re-entries)")


if __name__ == "__main__":
    main()

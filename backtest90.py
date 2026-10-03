"""
Midcap150 Momentum 10 — report 48's exact design (NIFTY-50-driven
regime filter, GOLDBEES.NS instead of cash during risk-off periods)
but with a 400-day EMA instead of 200. Report 46 found that widening
the EMA span past 200 (up to 250, the widest tested there) made the
cash version's CAGR/drawdown worse; report 76 later tested a 400-day
EMA alongside rebalance-cadence variants. This report isolates the
400-day EMA change on report 48's exact semi-annual design: the
same NIFTY-driven regime signal, same Midcap150 Momentum 10 formula,
same gold-instead-of-cash hedge — only the EMA span differs.
Same full-window/gold-reindex convention as reports 48/68/71/76.
"""
import json

import pandas as pd

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes, fetch_gold_cleaned
from backtest32 import metrics_only
from backtest33 import select_top_original, build_index_generic
from backtest42 import build_index_regime_filtered, build_index_regime_filtered_with_hedge, cash_blocks_from_log, EMA_SPAN

EMA_SPAN_400 = 400


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    gold = fetch_gold_cleaned()
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]
    gold_close_aligned = gold["Close"].reindex(common).ffill().bfill()
    ema = nifty_close.ewm(span=EMA_SPAN_400, adjust=False).mean()

    rbdates = rebalance_dates(closes.index, months=(6, 12))

    original_series, _ = build_index_generic(closes, rbdates, select_top_original)
    cash_series, cash_sel, cash_log = build_index_regime_filtered(closes, nifty_close, ema, rbdates, select_top_original)
    gold_series, gold_sel, gold_log = build_index_regime_filtered_with_hedge(closes, nifty_close, ema, rbdates, select_top_original, gold_close_aligned)

    common_idx = original_series.index.intersection(cash_series.index).intersection(gold_series.index)
    original_metrics = metrics_only(original_series, common_idx)
    cash_metrics = metrics_only(cash_series, common_idx)
    gold_metrics = metrics_only(gold_series, common_idx)
    nifty_metrics = metrics_only(nifty_close.loc[common_idx], common_idx)
    # gold buy-and-hold benchmark uses gold's OWN real prices (not the
    # ffill/bfill-aligned series used just to feed the hedge sleeve above),
    # restricted to the small overlap where it actually has data
    real_gold_idx = common_idx.intersection(gold["Close"].index)
    gold_bench_metrics = metrics_only(gold["Close"], real_gold_idx)

    cash_blocks, pct_cash = cash_blocks_from_log(cash_log)
    num_reentries = sum(1 for s in cash_sel if s["trigger"] == "regime_reentry")

    def sample(sel):
        return sel[:3] + sel[-3:] if len(sel) > 6 else sel

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "ema_span": EMA_SPAN_400,
        "pct_time_in_cash": round(pct_cash, 1),
        "num_regime_reentries": num_reentries,
        "original": original_metrics,
        "cash_filtered": {**cash_metrics, "selections_sample": sample(cash_sel)},
        "gold_filtered": {**gold_metrics, "selections_sample": sample(gold_sel)},
        "nifty": nifty_metrics,
        "gold_benchmark": gold_bench_metrics,
    }

    with open("results89.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}")
    print(f"no filter                CAGR {original_metrics['cagr_pct']:.2f}% / DD {original_metrics['max_drawdown_pct']:.1f}%")
    print(f"400-EMA + cash           CAGR {cash_metrics['cagr_pct']:.2f}% / DD {cash_metrics['max_drawdown_pct']:.1f}%")
    print(f"400-EMA + gold           CAGR {gold_metrics['cagr_pct']:.2f}% / DD {gold_metrics['max_drawdown_pct']:.1f}%")
    print(f"nifty 50 benchmark       CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")
    print(f"gold (GOLDBEES.NS) alone CAGR {gold_bench_metrics['cagr_pct']:.2f}% / DD {gold_bench_metrics['max_drawdown_pct']:.1f}%")


if __name__ == "__main__":
    main()

"""
NIFTY100 Momentum 10 — gold instead of cash during the 200-day EMA
regime filter's risk-off periods. Same mechanics as reports 48-49,
applied to report 12's NIFTY100 Momentum 10 config. GOLDBEES.NS only has
price history from mid-2010, so the CASH comparison here is recomputed
fresh on this identical, shorter window (not re-quoted from report 45).
"""
import json

import pandas as pd

from backtest10 import load_universe_closes, rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest13 import fetch_gold_cleaned
from nifty100_symbols import NIFTY_100_SYMBOLS
from backtest32 import metrics_only
from backtest33 import build_index_generic
from backtest42 import build_index_regime_filtered, build_index_regime_filtered_with_hedge, cash_blocks_from_log, EMA_SPAN
from backtest45 import select_top_n100


def main():
    closes_all = load_universe_closes()
    n100_tickers = [s + ".NS" for s in NIFTY_100_SYMBOLS]
    closes = closes_all[[t for t in n100_tickers if t in closes_all.columns]]

    nifty = fetch("^NSEI")
    gold = fetch_gold_cleaned()
    common = closes.index.intersection(nifty.index).intersection(gold.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]
    gold_close = gold.loc[common, "Close"]
    ema = nifty_close.ewm(span=EMA_SPAN, adjust=False).mean()

    rbdates = rebalance_dates(closes.index, months=(6, 12))

    original_series, _ = build_index_generic(closes, rbdates, select_top_n100)
    cash_series, cash_sel, cash_log = build_index_regime_filtered(closes, nifty_close, ema, rbdates, select_top_n100)
    gold_series, gold_sel, gold_log = build_index_regime_filtered_with_hedge(closes, nifty_close, ema, rbdates, select_top_n100, gold_close)

    common_idx = original_series.index.intersection(cash_series.index).intersection(gold_series.index)
    original_metrics = metrics_only(original_series, common_idx)
    cash_metrics = metrics_only(cash_series, common_idx)
    gold_metrics = metrics_only(gold_series, common_idx)
    nifty_metrics = metrics_only(nifty_close.loc[common_idx], common_idx)
    gold_bench_metrics = metrics_only(gold_close.loc[common_idx], common_idx)

    cash_blocks, pct_cash = cash_blocks_from_log(cash_log)
    num_reentries = sum(1 for s in cash_sel if s["trigger"] == "regime_reentry")

    def sample(sel):
        return sel[:3] + sel[-3:] if len(sel) > 6 else sel

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "ema_span": EMA_SPAN,
        "pct_time_in_cash": round(pct_cash, 1),
        "num_regime_reentries": num_reentries,
        "original": original_metrics,
        "cash_filtered": {**cash_metrics, "selections_sample": sample(cash_sel)},
        "gold_filtered": {**gold_metrics, "selections_sample": sample(gold_sel)},
        "nifty": nifty_metrics,
        "gold_benchmark": gold_bench_metrics,
    }

    with open("results49.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}")
    print(f"no filter                CAGR {original_metrics['cagr_pct']:.2f}% / DD {original_metrics['max_drawdown_pct']:.1f}%")
    print(f"200-EMA + cash           CAGR {cash_metrics['cagr_pct']:.2f}% / DD {cash_metrics['max_drawdown_pct']:.1f}%")
    print(f"200-EMA + gold           CAGR {gold_metrics['cagr_pct']:.2f}% / DD {gold_metrics['max_drawdown_pct']:.1f}%")
    print(f"nifty 50 benchmark       CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")
    print(f"gold (GOLDBEES.NS) alone CAGR {gold_bench_metrics['cagr_pct']:.2f}% / DD {gold_bench_metrics['max_drawdown_pct']:.1f}%")


if __name__ == "__main__":
    main()

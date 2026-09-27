"""
Smallcap250 Momentum 10 — universe-specific trend filter, using the REAL
NIFTY Smallcap 250 index itself (NIFTYSMLCAP250.NS — no reconstruction
needed, same ticker report 16/29 already benchmarks against) as the
200-day-EMA regime signal, instead of NIFTY 50. Same mechanics as
report 54, applied to the Smallcap250 Momentum 10 config.
"""
import json

import pandas as pd

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest15 import load_smallcap250_closes
from backtest32 import metrics_only
from backtest33 import build_index_generic
from backtest42 import build_index_regime_filtered, cash_blocks_from_log, EMA_SPAN
from backtest44 import select_top_smallcap

UNIVERSE_TICKER = "NIFTYSMLCAP250.NS"


def main():
    closes = load_smallcap250_closes()
    nifty = fetch("^NSEI")
    universe_idx = fetch(UNIVERSE_TICKER)
    common = closes.index.intersection(nifty.index).intersection(universe_idx.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]
    universe_close = universe_idx.loc[common, "Close"]

    nifty_ema = nifty_close.ewm(span=EMA_SPAN, adjust=False).mean()
    universe_ema = universe_close.ewm(span=EMA_SPAN, adjust=False).mean()

    rbdates = rebalance_dates(closes.index, months=(6, 12))

    original_series, _ = build_index_generic(closes, rbdates, select_top_smallcap)
    nifty_signal_series, nifty_signal_sel, nifty_signal_log = build_index_regime_filtered(closes, nifty_close, nifty_ema, rbdates, select_top_smallcap)
    own_signal_series, own_signal_sel, own_signal_log = build_index_regime_filtered(closes, universe_close, universe_ema, rbdates, select_top_smallcap)

    common_idx = original_series.index.intersection(nifty_signal_series.index).intersection(own_signal_series.index)
    original_metrics = metrics_only(original_series, common_idx)
    nifty_signal_metrics = metrics_only(nifty_signal_series, common_idx)
    own_signal_metrics = metrics_only(own_signal_series, common_idx)
    nifty_metrics = metrics_only(nifty_close.loc[common_idx], common_idx)

    nifty_blocks, nifty_pct_cash = cash_blocks_from_log(nifty_signal_log)
    own_blocks, own_pct_cash = cash_blocks_from_log(own_signal_log)
    nifty_reentries = sum(1 for s in nifty_signal_sel if s["trigger"] == "regime_reentry")
    own_reentries = sum(1 for s in own_signal_sel if s["trigger"] == "regime_reentry")

    def sample(sel):
        return sel[:3] + sel[-3:] if len(sel) > 6 else sel

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "ema_span": EMA_SPAN,
        "universe_ticker": UNIVERSE_TICKER,
        "original": original_metrics,
        "nifty_signal": {**nifty_signal_metrics, "pct_time_in_cash": round(nifty_pct_cash, 1),
                         "num_regime_reentries": nifty_reentries, "num_cash_periods_10d_plus": len(nifty_blocks),
                         "cash_periods": nifty_blocks[:6], "selections_sample": sample(nifty_signal_sel)},
        "own_signal": {**own_signal_metrics, "pct_time_in_cash": round(own_pct_cash, 1),
                       "num_regime_reentries": own_reentries, "num_cash_periods_10d_plus": len(own_blocks),
                       "cash_periods": own_blocks[:6], "selections_sample": sample(own_signal_sel)},
        "nifty": nifty_metrics,
    }

    with open("results54.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}")
    print(f"no filter              CAGR {original_metrics['cagr_pct']:.2f}% / DD {original_metrics['max_drawdown_pct']:.1f}%")
    print(f"NIFTY50-signal filter  CAGR {nifty_signal_metrics['cagr_pct']:.2f}% / DD {nifty_signal_metrics['max_drawdown_pct']:.1f}%  |  cash {nifty_pct_cash:.1f}%  |  re-entries {nifty_reentries}")
    print(f"own-index-signal filter CAGR {own_signal_metrics['cagr_pct']:.2f}% / DD {own_signal_metrics['max_drawdown_pct']:.1f}%  |  cash {own_pct_cash:.1f}%  |  re-entries {own_reentries}")
    print(f"nifty 50 benchmark     CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")


if __name__ == "__main__":
    main()

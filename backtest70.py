"""
NIFTY100 Momentum 10 — smooth exposure combined with gold and a
liquid-fund yield assumption, same mechanics as reports 68-69, applied
to report 12's NIFTY100 Momentum 10 config.

Same LIQUIDBEES.NS data caveat as reports 68-69: its Yahoo Finance price
is flat for its whole history, so the liquid-fund sleeve here is modeled
as a flat ASSUMED 6% p.a. yield, not real market data.

CORRECTION: an earlier version of this report (and reports 68-69) stated
GOLDBEES.NS's history "starts mid-2010" and used a window starting
2010-06-30 on that basis. That claim was WRONG — GOLDBEES.NS actually
has price history from 2009-01-02. The truncation was caused by
restricting `closes` to the gold-intersected window BEFORE the momentum
formula's own lookback ran. This version computes the original series
(and the cash/liquid smooth-exposure variants) on the SAME full window
as report 67.
"""
import json

import pandas as pd

from backtest10 import load_universe_closes, rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest13 import fetch_gold_cleaned
from nifty100_symbols import NIFTY_100_SYMBOLS
from backtest32 import metrics_only
from backtest33 import build_index_generic
from backtest42 import build_smooth_exposure, build_smooth_exposure_with_hedge, EMA_SPAN
from backtest45 import select_top_n100

BANDS = [0.10, 0.15, 0.20]
ASSUMED_LIQUID_YIELD = 0.06


def main():
    closes_all = load_universe_closes()
    n100_tickers = [s + ".NS" for s in NIFTY_100_SYMBOLS]
    closes = closes_all[[t for t in n100_tickers if t in closes_all.columns]]

    nifty = fetch("^NSEI")
    gold = fetch_gold_cleaned()
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]
    gold_close = gold["Close"]
    ema = nifty_close.ewm(span=EMA_SPAN, adjust=False).mean()

    days_elapsed = (common - common[0]).days
    liquid_close = pd.Series((1 + ASSUMED_LIQUID_YIELD) ** (days_elapsed / 365.25) * 100.0, index=common)

    rbdates = rebalance_dates(closes.index, months=(6, 12))

    original_series, _ = build_index_generic(closes, rbdates, select_top_n100)
    common_idx = original_series.index

    variants = {}
    for band in BANDS:
        cash_series, _ = build_smooth_exposure(original_series, nifty_close, ema, band_pct=band)
        gold_series, _ = build_smooth_exposure_with_hedge(original_series, nifty_close, ema, gold_close, band_pct=band)
        liquid_series, _ = build_smooth_exposure_with_hedge(original_series, nifty_close, ema, liquid_close, band_pct=band)
        common_idx = common_idx.intersection(cash_series.index).intersection(liquid_series.index)
        variants[band] = {"cash": cash_series, "gold": gold_series, "liquid": liquid_series}

    original_metrics = metrics_only(original_series, common_idx)
    nifty_metrics = metrics_only(nifty_close.loc[common_idx], common_idx)
    real_gold_idx = common_idx.intersection(gold_close.index)
    gold_bench_metrics = metrics_only(gold_close, real_gold_idx)

    bands_out = []
    for band in BANDS:
        m_cash = metrics_only(variants[band]["cash"], common_idx)
        m_gold = metrics_only(variants[band]["gold"], common_idx)
        m_liquid = metrics_only(variants[band]["liquid"], common_idx)
        bands_out.append({
            "band_pct": band * 100,
            "cash": {"cagr_pct": m_cash["cagr_pct"], "max_drawdown_pct": m_cash["max_drawdown_pct"],
                     "net_return_pct": m_cash["net_return_pct"], "equity_curve": m_cash["equity_curve"]},
            "gold": {"cagr_pct": m_gold["cagr_pct"], "max_drawdown_pct": m_gold["max_drawdown_pct"],
                     "net_return_pct": m_gold["net_return_pct"], "equity_curve": m_gold["equity_curve"]},
            "liquid": {"cagr_pct": m_liquid["cagr_pct"], "max_drawdown_pct": m_liquid["max_drawdown_pct"],
                       "net_return_pct": m_liquid["net_return_pct"], "equity_curve": m_liquid["equity_curve"]},
        })

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "ema_span": EMA_SPAN,
        "assumed_liquid_yield_pct": ASSUMED_LIQUID_YIELD * 100,
        "original": original_metrics,
        "nifty": nifty_metrics,
        "gold_benchmark": gold_bench_metrics,
        "bands": bands_out,
    }

    with open("results69.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}")
    print(f"no filter (100% always)  CAGR {original_metrics['cagr_pct']:.2f}% / DD {original_metrics['max_drawdown_pct']:.1f}%")
    for b in bands_out:
        print(f"band {b['band_pct']:.0f}%  CASH CAGR {b['cash']['cagr_pct']:.2f}% DD {b['cash']['max_drawdown_pct']:.1f}%  |  "
              f"GOLD CAGR {b['gold']['cagr_pct']:.2f}% DD {b['gold']['max_drawdown_pct']:.1f}%  |  "
              f"LIQUID CAGR {b['liquid']['cagr_pct']:.2f}% DD {b['liquid']['max_drawdown_pct']:.1f}%")
    print(f"nifty 50 benchmark       CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")


if __name__ == "__main__":
    main()

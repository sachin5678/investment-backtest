"""
Midcap150 Momentum 10 — combining the smooth (volatility-scaled) exposure
ramp from reports 65-67 with a better home for the de-risked capital than
plain 0%-return cash: GOLD (GOLDBEES.NS, the same real ETF used in
reports 48-50's binary-filter hedge) and a LIQUID-FUND proxy for the
"safe overnight yield" a real portfolio manager would actually earn on
idle capital, instead of nothing.

DATA CAVEAT, discovered while building this report: LIQUIDBEES.NS's
Yahoo Finance "Close" price is effectively FLAT for its entire 2009-2026
history (it sits at ~1000.00 every single day, moving by fractions of a
rupee at most) — real liquid-fund yield is distributed to unit-holders
as additional bonus units, NOT reflected in the per-unit price this feed
reports. Using that raw price directly would silently model "liquid
fund" as earning exactly 0%, indistinguishable from plain cash, which
would be a misleading result to present as a finding. Instead, this
report models the liquid-fund sleeve as a flat ASSUMED annual yield
(6% p.a., a round-number approximation of India's long-run overnight/
liquid-fund yield — actual yields ranged roughly 3%-9% across this
18-year window, well above and below 6% at different points) compounding
daily — clearly a modeled assumption, NOT real market data, unlike
gold's real ETF price series.

CORRECTION: an earlier version of this report stated GOLDBEES.NS's
history "starts mid-2010" and used a window starting 2010-06-30 on that
basis. That claim was WRONG — GOLDBEES.NS actually has price history
from 2009-01-02. The truncation was actually caused by restricting
`closes` to the gold-intersected window BEFORE the momentum formula's
own lookback ran. This version computes the ORIGINAL series (and the
cash/liquid smooth-exposure variants) on the SAME full window as reports
65-67; only the GOLD variant's own reported window is limited to gold's
real ~2009-01-02 start (a two-day difference, not "mid-2010").

Same 200-day EMA signal, same three band widths (10%/15%/20%) as reports
65-67; the ONLY change under test here is what the de-risked portion of
the portfolio holds while less than 100% exposed.
"""
import json

import pandas as pd

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes, fetch_gold_cleaned
from backtest32 import metrics_only
from backtest33 import select_top_original, build_index_generic
from backtest42 import build_smooth_exposure, build_smooth_exposure_with_hedge, EMA_SPAN

BANDS = [0.10, 0.15, 0.20]
ASSUMED_LIQUID_YIELD = 0.06


def main():
    closes = load_midcap150_closes()
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

    original_series, _ = build_index_generic(closes, rbdates, select_top_original)
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

    with open("results67.json", "w") as f:
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

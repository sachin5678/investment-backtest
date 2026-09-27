"""
Midcap150 Momentum 10 — volatility-scaled (smooth) exposure instead of
the binary cash/invested regime filter (reports 42-64). Instead of
flipping 100%/0% the moment NIFTY 50 crosses its 200-day EMA, exposure
ramps linearly from 100% (at or above the EMA) down to 0% (a band_pct
below the EMA), removing the whipsaw problem at its root — there is no
discrete state to flip back and forth, so there is nothing to "re-enter"
or "confirm." Three band widths tested (10%/15%/20%) against the
original (always 100% exposure) and report 42's binary 200-EMA filter,
all recomputed fresh on the identical window.
"""
import json

import numpy as np
import pandas as pd

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes
from backtest32 import metrics_only
from backtest33 import select_top_original, build_index_generic
from backtest42 import build_index_regime_filtered, build_smooth_exposure, EMA_SPAN

BANDS = [0.10, 0.15, 0.20]


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]
    ema = nifty_close.ewm(span=EMA_SPAN, adjust=False).mean()

    rbdates = rebalance_dates(closes.index, months=(6, 12))

    original_series, _ = build_index_generic(closes, rbdates, select_top_original)
    binary_series, binary_sel, binary_log = build_index_regime_filtered(closes, nifty_close, ema, rbdates, select_top_original)

    band_results = {}
    common_idx = original_series.index.intersection(binary_series.index)
    for band in BANDS:
        blended, exposure = build_smooth_exposure(original_series, nifty_close, ema, band_pct=band)
        common_idx = common_idx.intersection(blended.index)
        band_results[band] = {"series": blended, "exposure": exposure}

    original_metrics = metrics_only(original_series, common_idx)
    binary_metrics = metrics_only(binary_series, common_idx)
    binary_metrics["num_regime_reentries"] = sum(1 for s in binary_sel if s["trigger"] == "regime_reentry")
    nifty_metrics = metrics_only(nifty_close.loc[common_idx], common_idx)

    bands_out = []
    for band in BANDS:
        m = metrics_only(band_results[band]["series"], common_idx)
        exposure_aligned = band_results[band]["exposure"].reindex(common_idx)
        bands_out.append({
            "band_pct": band * 100,
            "cagr_pct": m["cagr_pct"], "max_drawdown_pct": m["max_drawdown_pct"],
            "net_return_pct": m["net_return_pct"], "longest_underwater_days": m["longest_underwater_days"],
            "equity_curve": m["equity_curve"],
            "avg_exposure_pct": round(float(exposure_aligned.mean() * 100), 1),
            "pct_days_full_exposure": round(float((exposure_aligned >= 0.999).mean() * 100), 1),
            "pct_days_zero_exposure": round(float((exposure_aligned <= 0.001).mean() * 100), 1),
        })

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "ema_span": EMA_SPAN,
        "original": original_metrics,
        "binary_filter": binary_metrics,
        "nifty": nifty_metrics,
        "bands": bands_out,
    }

    with open("results64.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}")
    print(f"no filter (100% always)  CAGR {original_metrics['cagr_pct']:.2f}% / DD {original_metrics['max_drawdown_pct']:.1f}%")
    print(f"binary 200-EMA (rpt 42)  CAGR {binary_metrics['cagr_pct']:.2f}% / DD {binary_metrics['max_drawdown_pct']:.1f}%")
    for b in bands_out:
        print(f"smooth band {b['band_pct']:.0f}%      CAGR {b['cagr_pct']:.2f}% / DD {b['max_drawdown_pct']:.1f}%  |  avg exposure {b['avg_exposure_pct']:.1f}%")
    print(f"nifty 50 benchmark       CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")


if __name__ == "__main__":
    main()

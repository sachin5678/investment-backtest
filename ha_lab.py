"""HA x hero pilot — does report 104's smoothed Heikin-Ashi indicator
improve the repo's hero (report 98 Max stack A / report 93)?

This is an exploratory lab, not a report. Every variant runs through the
same ms_builder accounting as reports 93-98 (0.05% cost + 0.05% slippage
per side, whole units off, midcap150, Jun/Dec reviews, gold park).

Axes tested:
  * HA regime  — replace the NIFTY 200-EMA risk-off signal with the
                 index's smoothed HA (green = risk-on; optional strict
                 close-above-HA-open confirmation).
  * HA buy     — at a review, only buy names that are HA-green (and,
                 optionally, close above the HA open, and ATR contracting).
  * HA keep    — at a review, sell a holder that has turned HA-red.

Run:  py -3 ha_lab.py
"""
import json

import numpy as np
import pandas as pd

import ms_builder
from backtest32 import metrics_only

KEEP_RISING = {"when": "keep", "indicator": "ret_6m", "op": "above", "value": 0}
BASE98 = {"conditions": [KEEP_RISING], "exit_rank": 30}

HA_GREEN = {"when": "buy", "indicator": "ha_green"}
HA_ABOVE = {"when": "buy", "indicator": "ha_above"}
ATR_TIGHT = {"when": "buy", "indicator": "atr_ratio", "op": "below", "value": 0.8}
KEEP_HA = {"when": "keep", "indicator": "ha_green"}


def variant_cfg(base_overrides=None, regime_signal=None, conditions=None):
    cfg = ms_builder.default_config(**(base_overrides or {}))
    if regime_signal:
        cfg["regime"]["signal"] = regime_signal
    if conditions is not None:
        cfg["conditions"] = conditions
    return cfg


def sharpe_of(series):
    r = series.pct_change().dropna()
    if len(r) < 10 or r.std() == 0:
        return None
    return float(r.mean() / r.std() * np.sqrt(252.0))


def main():
    print("loading market data ...")
    market = ms_builder.load_market()
    closes = market["closes"]
    dates = closes.index
    print(f"window {dates[0].date()} -> {dates[-1].date()} ({len(dates)} days), "
          f"{len(closes.columns)} symbols")

    print("building ranks + features (this now includes smoothed HA) ...")
    rank_df, fit_df, _score = ms_builder.build_ranks(closes)
    feats = ms_builder.build_features(market)
    common = market["common"]

    variants = [
        # --- baseline ---
        ("98 baseline (stack A)", variant_cfg(BASE98)),
        # --- HA as the market regime, replacing the 200-EMA ---
        ("98 + HA regime (green)", variant_cfg(BASE98, "ha")),
        ("98 + HA regime (green & close>HA open)", variant_cfg(BASE98, "ha_close")),
        # --- HA as an entry filter at the review ---
        ("98 + HA buy (green)", variant_cfg(BASE98, conditions=[KEEP_RISING, HA_GREEN])),
        ("98 + HA buy (green & close>HA open)",
         variant_cfg(BASE98, conditions=[KEEP_RISING, HA_GREEN, HA_ABOVE])),
        ("98 + HA buy (green & close>HA open & ATR<0.8)",
         variant_cfg(BASE98, conditions=[KEEP_RISING, HA_GREEN, HA_ABOVE, ATR_TIGHT])),
        # --- HA as a keep/exit filter at the review ---
        ("98 + HA keep (green) on top of 6m>0",
         variant_cfg(BASE98, conditions=[KEEP_RISING, KEEP_HA])),
        ("98 + HA keep (green only, replaces 6m>0)",
         variant_cfg(BASE98, conditions=[KEEP_HA])),
        # --- regime + entry ---
        ("98 + HA regime + HA buy",
         variant_cfg(BASE98, "ha", conditions=[KEEP_RISING, HA_GREEN, HA_ABOVE])),
        # --- the base hero, for context ---
        ("93 hero baseline", variant_cfg(None)),
        ("93 hero + HA regime (green)", variant_cfg(None, "ha")),
        ("93 hero + HA buy (green & close>HA open)",
         variant_cfg(None, conditions=[HA_GREEN, HA_ABOVE])),
    ]

    rows = []
    for label, cfg in variants:
        print(f"  running {label} ...", flush=True)
        rbdates = ms_builder.rebalance_dates_for(cfg, dates)
        run = ms_builder.run_variant(cfg, market, feats, rank_df, fit_df, rbdates)
        m = metrics_only(run["series"], common)
        closed = [t for t in run["trades"] if t["status"] == "closed"]
        win = [t for t in closed if t["pct_return"] > 0]
        regime_exits = sum(1 for e in run["events"] if e["trigger"] == "regime_exit")
        rows.append({
            "label": label,
            "cagr_pct": round(m["cagr_pct"], 2),
            "max_dd_pct": round(m["max_drawdown_pct"], 2),
            "sharpe": round(sharpe_of(run["series"]), 2) if sharpe_of(run["series"]) else None,
            "calmar": round(m["cagr_pct"] / abs(m["max_drawdown_pct"]), 2) if m["max_drawdown_pct"] else None,
            "final_x": round(float(run["series"].iloc[-1] / run["series"].iloc[0]), 2),
            "trades": len(closed),
            "win_pct": round(len(win) / len(closed) * 100, 1) if closed else None,
            "regime_exits": regime_exits,
        })

    base = rows[0]
    print()
    header = (f"{'variant':52s} {'CAGR':>7s} {'DD':>8s} {'Sharpe':>7s} "
              f"{'Calmar':>7s} {'final x':>8s} {'trades':>6s} {'win%':>6s} {'regime exits':>12s}")
    print(header)
    print("-" * len(header))
    for r in rows:
        delta = "" if r is base else f"  ({r['cagr_pct'] - base['cagr_pct']:+.2f}pp)"
        print(f"{r['label']:52s} {r['cagr_pct']:7.2f} {r['max_dd_pct']:8.2f} "
              f"{(r['sharpe'] if r['sharpe'] is not None else float('nan')):7.2f} "
              f"{(r['calmar'] if r['calmar'] is not None else float('nan')):7.2f} "
              f"{r['final_x']:8.2f} {r['trades']:6d} "
              f"{(r['win_pct'] if r['win_pct'] is not None else float('nan')):6.1f} "
              f"{r['regime_exits']:12d}{delta}")

    with open("ha_lab.json", "w", encoding="utf-8") as f:
        json.dump({"window": [dates[0].strftime("%Y-%m-%d"), dates[-1].strftime("%Y-%m-%d")],
                   "variants": rows}, f, indent=1)
    print("\nwrote ha_lab.json")


if __name__ == "__main__":
    main()

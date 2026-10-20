"""Report 105 — Smoothed Heikin-Ashi x the hero (report 98 Max stack A).

A deliberately negative lab: every way of bolting report 104's HA indicator
onto the repo's hero is measured against the untouched hero, on the same
data, window and cost model.

Run:  py -3 backtest105.py    (writes results104.json)
"""
import json
from datetime import datetime

import numpy as np
import pandas as pd

import ms_builder
from backtest32 import metrics_only

KEEP_RISING = {"when": "keep", "indicator": "ret_6m", "op": "above", "value": 0}
BASE98 = {"conditions": [KEEP_RISING], "exit_rank": 30}
BASE93 = {}

HA_GREEN = {"when": "buy", "indicator": "ha_green"}
HA_ABOVE = {"when": "buy", "indicator": "ha_above"}
ATR_TIGHT = {"when": "buy", "indicator": "atr_ratio", "op": "below", "value": 0.8}
KEEP_HA = {"when": "keep", "indicator": "ha_green"}


def cfg98(conditions=None, extra_exit=None, reentry_gate=None, action=None, regime_signal=None):
    cfg = ms_builder.default_config(**BASE98)
    if conditions is not None:
        cfg["conditions"] = conditions
    if regime_signal:
        cfg["regime"]["signal"] = regime_signal
    cfg["regime"]["extra_exit"] = extra_exit
    cfg["regime"]["reentry_gate"] = reentry_gate
    if action:
        cfg["regime"]["action"] = action
    return cfg


def cfg93(conditions=None, regime_signal=None):
    cfg = ms_builder.default_config()
    if conditions is not None:
        cfg["conditions"] = conditions
    if regime_signal:
        cfg["regime"]["signal"] = regime_signal
    return cfg


def sharpe_of(series):
    r = series.pct_change().dropna()
    if len(r) < 10 or r.std() == 0:
        return None
    return float(r.mean() / r.std() * np.sqrt(252.0))


def underwater_of(curve):
    out, peak = [], -np.inf
    for d, v in curve:
        peak = max(peak, v)
        out.append([d, round((v / peak - 1.0) * 100.0, 2)])
    return out


def yearly_of(curve):
    last = {}
    for d, v in curve:
        last[d[:4]] = v
    out, prev = {}, curve[0][1]
    for y in sorted(last):
        out[y] = round((last[y] / prev - 1.0) * 100.0, 2)
        prev = last[y]
    return out


def main():
    print("loading market data ...")
    market = ms_builder.load_market()
    closes = market["closes"]
    dates = closes.index
    common = market["common"]
    print(f"window {dates[0].date()} -> {dates[-1].date()} ({len(dates)} days), "
          f"{len(closes.columns)} symbols")

    print("building ranks + features ...")
    rank_df, fit_df, _score = ms_builder.build_ranks(closes)
    feats = ms_builder.build_features(market)

    variants = [
        # key, label, group, cfg
        ("hero98", "Hero — report 98 Max stack A", "The hero", cfg98()),

        ("ha_regime", "HA regime green replaces the 200-EMA", "HA replaces the regime",
         cfg98(regime_signal="ha")),
        ("ha_regime_strict", "HA regime green + index close > HA open", "HA replaces the regime",
         cfg98(regime_signal="ha_close")),

        ("ha_buy", "HA buy filter — green only", "HA gates the stock picks",
         cfg98(conditions=[KEEP_RISING, HA_GREEN])),
        ("ha_buy_above", "HA buy filter — green + close > HA open", "HA gates the stock picks",
         cfg98(conditions=[KEEP_RISING, HA_GREEN, HA_ABOVE])),
        ("ha_buy_atr", "HA buy filter + ATR(14)/ATR(50) < 0.8", "HA gates the stock picks",
         cfg98(conditions=[KEEP_RISING, HA_GREEN, HA_ABOVE, ATR_TIGHT])),
        ("ha_keep", "HA keep filter — review exit on HA red (on top of 6m > 0)", "HA gates the stock picks",
         cfg98(conditions=[KEEP_RISING, KEEP_HA])),
        ("ha_keep_only", "HA keep filter — replaces the 6m > 0 keep rule", "HA gates the stock picks",
         cfg98(conditions=[KEEP_HA])),
        ("ha_regime_buy", "HA regime + HA buy filter", "HA gates the stock picks",
         cfg98(conditions=[KEEP_RISING, HA_GREEN, HA_ABOVE], regime_signal="ha")),

        ("ha_reentry", "200-EMA exits, HA-green re-entry gate", "HA as an asymmetric overlay",
         cfg98(reentry_gate="ha")),
        ("ha_early", "200-EMA exits + HA-red early exit", "HA as an asymmetric overlay",
         cfg98(extra_exit="ha")),
        ("ha_early_gate", "200-EMA exits + HA-red early exit + HA re-entry", "HA as an asymmetric overlay",
         cfg98(extra_exit="ha", reentry_gate="ha")),
        ("ha_half", "HA-red half de-risk, 200-EMA full exit", "HA as an asymmetric overlay",
         cfg98(extra_exit="ha", action="half")),

        ("hero93", "Base hero — report 93 exactly", "Base hero context", cfg93()),
        ("hero93_regime", "Base hero + HA regime", "Base hero context",
         cfg93(regime_signal="ha")),
        ("hero93_buy", "Base hero + HA buy filter", "Base hero context",
         cfg93(conditions=[HA_GREEN, HA_ABOVE])),
    ]

    out = []
    for key, label, group, cfg in variants:
        print(f"  running {label} ...", flush=True)
        rbdates = ms_builder.rebalance_dates_for(cfg, dates)
        run = ms_builder.run_variant(cfg, market, feats, rank_df, fit_df, rbdates)
        m = metrics_only(run["series"], common)
        closed = [t for t in run["trades"] if t["status"] == "closed"]
        wins = [t for t in closed if t["pct_return"] > 0]
        curve = m["equity_curve"]
        out.append({
            "key": key,
            "label": label,
            "group": group,
            "cagr_pct": round(m["cagr_pct"], 3),
            "net_return_pct": round(m["net_return_pct"], 3),
            "max_drawdown_pct": round(m["max_drawdown_pct"], 3),
            "max_drawdown_peak_date": m["max_drawdown_peak_date"],
            "max_drawdown_trough_date": m["max_drawdown_trough_date"],
            "longest_underwater_days": m["longest_underwater_days"],
            "sharpe": round(sharpe_of(run["series"]), 3),
            "calmar": round(m["cagr_pct"] / abs(m["max_drawdown_pct"]), 3),
            "final_x": round(float(run["series"].iloc[-1] / run["series"].iloc[0]), 3),
            "trades": len(closed),
            "win_pct": round(len(wins) / len(closed) * 100.0, 1) if closed else None,
            "regime_exits": sum(1 for e in run["events"] if e["trigger"] == "regime_exit"),
            "config": ms_builder.describe_config(cfg),
            "equity_curve": curve,
            "underwater": underwater_of(curve),
            "yearly": yearly_of(curve),
        })

    result = {
        "report": 105,
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "start_date": dates[0].strftime("%Y-%m-%d"),
        "end_date": dates[-1].strftime("%Y-%m-%d"),
        "hero": "Report 98 Max stack A — keep-if 6m > 0, exit rank 30, NIFTY 200-EMA + gold",
        "ha_definition": ("Smoothed Heikin-Ashi (EMA 10 applied twice, report 104); green = HA close > HA open; "
                          "strict = also price > HA open; ATR contraction = ATR(14)/ATR(50) < 0.8"),
        "cost_note": "0.1% cost per side, 0% slippage, fractional units; tax is not modelled in this lab.",
        # keyed by label so the webapp's generic extractSeries finds one
        # series object per variant (it does not descend into arrays).
        "variants": {v["label"]: v for v in out},
    }
    with open("results104.json", "w", encoding="utf-8") as f:
        json.dump(ms_builder._json_safe(result), f, indent=1, ensure_ascii=False)
    print(f"\nwrote results104.json ({len(out)} variants)")

    hero = out[0]
    print(f"\nhero: {hero['cagr_pct']:.2f}% CAGR / {hero['max_drawdown_pct']:.2f}% DD / "
          f"Sharpe {hero['sharpe']:.2f} / {hero['trades']} trades")
    for v in out[1:]:
        print(f"  {v['label']:62s} {v['cagr_pct']:6.2f}%  "
              f"{v['cagr_pct'] - hero['cagr_pct']:+6.2f}pp  DD {v['max_drawdown_pct']:6.2f}%  "
              f"Sharpe {v['sharpe']:.2f}")


if __name__ == "__main__":
    main()

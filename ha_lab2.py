"""HA x hero pilot, part 2 — asymmetric overlays on the 200-EMA regime.

Part 1 replaced the regime and used HA as a review-level entry/keep filter;
every variant lost. This part keeps the hero's proven 200-EMA exits and asks
whether HA adds value at the edges:

  * re-entry gate   — after a 200-EMA risk-off, wait for index HA green
  * early exit      — also exit when index HA turns red (slow regime still on)
  * half de-risk    — the early exit sells half instead of everything
  * both            — early exit + HA-confirmed re-entry

Run:  py -3 ha_lab2.py
"""
import json

import ms_builder
from backtest32 import metrics_only

from ha_lab import BASE98, sharpe_of


def cfg_with(extra_exit=None, reentry_gate=None, action=None, base=None):
    cfg = ms_builder.default_config(**(BASE98 if base is None else base))
    cfg["regime"]["extra_exit"] = extra_exit
    cfg["regime"]["reentry_gate"] = reentry_gate
    if action:
        cfg["regime"]["action"] = action
    return cfg


def main():
    print("loading market data ...")
    market = ms_builder.load_market()
    closes = market["closes"]
    dates = closes.index
    print(f"window {dates[0].date()} -> {dates[-1].date()} ({len(dates)} days)")

    print("building ranks + features ...")
    rank_df, fit_df, _score = ms_builder.build_ranks(closes)
    feats = ms_builder.build_features(market)
    common = market["common"]

    variants = [
        ("98 baseline (stack A)", cfg_with()),
        ("98 + 200EMA exit, HA-green re-entry", cfg_with(reentry_gate="ha")),
        ("98 + 200EMA exit + HA-red early exit", cfg_with(extra_exit="ha")),
        ("98 + 200EMA exit + HA-red early exit + HA re-entry",
         cfg_with(extra_exit="ha", reentry_gate="ha")),
        ("98 + HA-red half de-risk, 200EMA exit", cfg_with(extra_exit="ha", action="half")),
        ("93 baseline + HA-green re-entry", cfg_with(reentry_gate="ha", base={})),
        ("93 baseline + HA-red early exit", cfg_with(extra_exit="ha", base={})),
    ]

    rows = []
    for label, cfg in variants:
        print(f"  running {label} ...", flush=True)
        rbdates = ms_builder.rebalance_dates_for(cfg, dates)
        run = ms_builder.run_variant(cfg, market, feats, rank_df, fit_df, rbdates)
        m = metrics_only(run["series"], common)
        closed = [t for t in run["trades"] if t["status"] == "closed"]
        win = [t for t in closed if t["pct_return"] > 0]
        rows.append({
            "label": label,
            "cagr_pct": round(m["cagr_pct"], 2),
            "max_dd_pct": round(m["max_drawdown_pct"], 2),
            "sharpe": round(sharpe_of(run["series"]), 2),
            "calmar": round(m["cagr_pct"] / abs(m["max_drawdown_pct"]), 2),
            "final_x": round(float(run["series"].iloc[-1] / run["series"].iloc[0]), 2),
            "trades": len(closed),
            "win_pct": round(len(win) / len(closed) * 100, 1) if closed else None,
            "regime_exits": sum(1 for e in run["events"] if e["trigger"] == "regime_exit"),
        })

    base = rows[0]
    print()
    header = (f"{'variant':60s} {'CAGR':>7s} {'DD':>8s} {'Sharpe':>7s} "
              f"{'Calmar':>7s} {'final x':>8s} {'trades':>6s} {'win%':>6s} {'exits':>6s}")
    print(header)
    print("-" * len(header))
    for r in rows:
        delta = "" if r is base else f"  ({r['cagr_pct'] - base['cagr_pct']:+.2f}pp)"
        print(f"{r['label']:60s} {r['cagr_pct']:7.2f} {r['max_dd_pct']:8.2f} "
              f"{r['sharpe']:7.2f} {r['calmar']:7.2f} {r['final_x']:8.2f} "
              f"{r['trades']:6d} {r['win_pct']:6.1f} {r['regime_exits']:6d}{delta}")

    with open("ha_lab2.json", "w", encoding="utf-8") as f:
        json.dump({"window": [dates[0].strftime("%Y-%m-%d"), dates[-1].strftime("%Y-%m-%d")],
                   "variants": rows}, f, indent=1)
    print("\nwrote ha_lab2.json")


if __name__ == "__main__":
    main()

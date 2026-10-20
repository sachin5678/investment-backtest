"""ATR contraction x hero pilot — isolate report 104's ATR(14)/ATR(50)
filter from the Heikin-Ashi signal that was tested with it in report 105.

The question: if the hero keeps its own 200-EMA regime and its own exits,
does gating new entries on ATR contraction (or expansion) help?

Axes:
  * buy  ATR14/ATR50 < threshold   (contraction)
  * buy  ATR14/ATR50 > threshold   (expansion)
  * keep ATR14/ATR50 < threshold   (review exit when volatility expands)
  * hero 93 versions, for context

Run:  py -3 atr_lab.py
"""
import json

import numpy as np

import ms_builder
from backtest32 import metrics_only
from backtest105 import cfg98, cfg93, sharpe_of, KEEP_RISING


def buy_atr(op, value):
    return {"when": "buy", "indicator": "atr_ratio", "op": op, "value": value}


def keep_atr(op, value):
    return {"when": "keep", "indicator": "atr_ratio", "op": op, "value": value}


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

    # --- diagnostic: how often do the top-10 momentum names pass ATR gates?
    rbdates = ms_builder.rebalance_dates_for(cfg98(), dates)
    print(f"review dates: {len(rbdates)}")
    for label, op, thresh in [("contraction < 0.8", "below", 0.8),
                              ("contraction < 1.0", "below", 1.0),
                              ("expansion > 1.0", "above", 1.0),
                              ("expansion > 1.2", "above", 1.2)]:
        top_rates, all_rates = [], []
        for d in rbdates:
            row = rank_df.loc[d].dropna().sort_values()
            if len(row) < 10:
                continue
            top = row.index[:10]
            a_top = feats["atr_ratio"].loc[d, top].dropna()
            a_all = feats["atr_ratio"].loc[d, row.index].dropna()
            if len(a_top):
                top_rates.append(((a_top < thresh) if op == "below" else (a_top > thresh)).mean())
            if len(a_all):
                all_rates.append(((a_all < thresh) if op == "below" else (a_all > thresh)).mean())
        print(f"  {label:22s} top-10 pass {np.mean(top_rates)*100:5.1f}%   "
              f"all-ranked pass {np.mean(all_rates)*100:5.1f}%   ({len(top_rates)} reviews)")

    variants = [
        ("98 baseline (stack A)", cfg98()),
        # --- entry gate: buy only when the stock's ATR is contracting
        ("98 + buy ATR<0.5", cfg98(conditions=[KEEP_RISING, buy_atr("below", 0.5)])),
        ("98 + buy ATR<0.6", cfg98(conditions=[KEEP_RISING, buy_atr("below", 0.6)])),
        ("98 + buy ATR<0.7", cfg98(conditions=[KEEP_RISING, buy_atr("below", 0.7)])),
        ("98 + buy ATR<0.8", cfg98(conditions=[KEEP_RISING, buy_atr("below", 0.8)])),
        ("98 + buy ATR<0.9", cfg98(conditions=[KEEP_RISING, buy_atr("below", 0.9)])),
        ("98 + buy ATR<1.0", cfg98(conditions=[KEEP_RISING, buy_atr("below", 1.0)])),
        ("98 + buy ATR<1.1", cfg98(conditions=[KEEP_RISING, buy_atr("below", 1.1)])),
        # --- the opposite: buy only when volatility is expanding
        ("98 + buy ATR>1.0", cfg98(conditions=[KEEP_RISING, buy_atr("above", 1.0)])),
        ("98 + buy ATR>1.2", cfg98(conditions=[KEEP_RISING, buy_atr("above", 1.2)])),
        # --- review exit: keep a holder only while ATR is contracting
        ("98 + keep ATR<0.8", cfg98(conditions=[KEEP_RISING, keep_atr("below", 0.8)])),
        ("98 + keep ATR<1.0", cfg98(conditions=[KEEP_RISING, keep_atr("below", 1.0)])),
        ("98 + keep ATR<1.2", cfg98(conditions=[KEEP_RISING, keep_atr("below", 1.2)])),
        # --- both
        ("98 + buy ATR<0.8 + keep ATR<0.8",
         cfg98(conditions=[KEEP_RISING, buy_atr("below", 0.8), keep_atr("below", 0.8)])),
        ("98 + buy ATR<1.0 + keep ATR<1.0",
         cfg98(conditions=[KEEP_RISING, buy_atr("below", 1.0), keep_atr("below", 1.0)])),
        # --- base hero context
        ("93 baseline", cfg93()),
        ("93 + buy ATR<0.8", cfg93(conditions=[buy_atr("below", 0.8)])),
        ("93 + buy ATR<1.0", cfg93(conditions=[buy_atr("below", 1.0)])),
        ("93 + keep ATR<1.0", cfg93(conditions=[keep_atr("below", 1.0)])),
    ]

    rows = []
    for label, cfg in variants:
        print(f"  running {label} ...", flush=True)
        rbd = ms_builder.rebalance_dates_for(cfg, dates)
        run = ms_builder.run_variant(cfg, market, feats, rank_df, fit_df, rbd)
        m = metrics_only(run["series"], common)
        closed = [t for t in run["trades"] if t["status"] == "closed"]
        wins = [t for t in closed if t["pct_return"] > 0]
        rows.append({
            "label": label,
            "cagr_pct": round(m["cagr_pct"], 2),
            "max_dd_pct": round(m["max_drawdown_pct"], 2),
            "sharpe": round(sharpe_of(run["series"]), 2),
            "calmar": round(m["cagr_pct"] / abs(m["max_drawdown_pct"]), 2),
            "final_x": round(float(run["series"].iloc[-1] / run["series"].iloc[0]), 1),
            "trades": len(closed),
            "win_pct": round(len(wins) / len(closed) * 100, 1) if closed else None,
        })

    base = rows[0]
    print()
    header = (f"{'variant':46s} {'CAGR':>7s} {'DD':>8s} {'Sharpe':>7s} "
              f"{'Calmar':>7s} {'final x':>8s} {'trades':>6s} {'win%':>6s}")
    print(header)
    print("-" * len(header))
    for r in rows:
        delta = "" if r is base else f"  ({r['cagr_pct'] - base['cagr_pct']:+.2f}pp)"
        print(f"{r['label']:46s} {r['cagr_pct']:7.2f} {r['max_dd_pct']:8.2f} "
              f"{r['sharpe']:7.2f} {r['calmar']:7.2f} {r['final_x']:8.1f} "
              f"{r['trades']:6d} {r['win_pct']:6.1f}{delta}")

    with open("atr_lab.json", "w", encoding="utf-8") as f:
        json.dump({"window": [dates[0].strftime("%Y-%m-%d"), dates[-1].strftime("%Y-%m-%d")],
                   "variants": rows}, f, indent=1)
    print("\nwrote atr_lab.json")


if __name__ == "__main__":
    main()

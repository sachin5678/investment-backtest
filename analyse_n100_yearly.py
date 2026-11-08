"""NIFTY100 Momentum 5/10/20, yearly rebalance, with vs without the
200-EMA gold regime switch. Reuses report 12/45/48's builders as-is."""
import json, sys
import pandas as pd
from backtest10 import load_universe_closes, rebalance_dates, fetch
from backtest13 import fetch_gold_cleaned
from nifty100_symbols import NIFTY_100_SYMBOLS
from backtest32 import metrics_only
from backtest33 import build_index_generic
from backtest42 import build_index_regime_filtered_with_hedge, EMA_SPAN
from backtest45 import select_top_n100

closes_all = load_universe_closes()
closes = closes_all[[s + ".NS" for s in NIFTY_100_SYMBOLS if s + ".NS" in closes_all.columns]]
nifty = fetch("^NSEI"); gold = fetch_gold_cleaned()
common = closes.index.intersection(nifty.index)
closes = closes.loc[common]; nc = nifty.loc[common, "Close"]
gold_al = gold["Close"].reindex(common).ffill().bfill()
ema = nc.ewm(span=EMA_SPAN, adjust=False).mean()

def sel(n):
    return lambda c, t: select_top_n100(c, t, top_n=n)

res = {}
for m in range(1, 13):
    rb = rebalance_dates(closes.index, months=(m,))
    for n in (5, 10, 20):
        plain, _ = build_index_generic(closes, rb, sel(n))
        reg, _, log = build_index_regime_filtered_with_hedge(closes, nc, ema, rb, sel(n), gold_al)
        res[(m, n)] = (plain, reg)
idx = None
for p, r in res.values():
    idx = p.index.intersection(r.index) if idx is None else idx.intersection(p.index).intersection(r.index)
nm = metrics_only(nc, idx)
print("window", idx[0].date(), idx[-1].date(), "| NIFTY50 CAGR %.2f DD %.1f" % (nm["cagr_pct"], nm["max_drawdown_pct"]))
print(list(nm.keys()))
out = {"window": [str(idx[0].date()), str(idx[-1].date())], "nifty": {k: nm[k] for k in nm if k != "equity_curve"}, "rows": []}
for n in (5, 10, 20):
    for m in range(1, 13):
        p, r = res[(m, n)]
        a, b = metrics_only(p, idx), metrics_only(r, idx)
        out["rows"].append({"n": n, "month": m, "plain": {k: a[k] for k in a if k != "equity_curve"}, "gold": {k: b[k] for k in b if k != "equity_curve"}})
json.dump(out, open("n100_yearly_analysis.json", "w"), indent=1)
import statistics as st
for n in (5, 10, 20):
    rows = [r for r in out["rows"] if r["n"] == n]
    for key in ("plain", "gold"):
        c = [r[key]["cagr_pct"] for r in rows]; d = [r[key]["max_drawdown_pct"] for r in rows]
        sh = [r[key].get("sharpe") for r in rows]
        print(f"N={n:2d} {key:5s} CAGR med {st.median(c):5.1f} range {min(c):5.1f}..{max(c):5.1f} | DD med {st.median(d):6.1f} worst {min(d):6.1f}")
    jun = next(r for r in rows if r["month"] == 6); dec = next(r for r in rows if r["month"] == 12)
    for lab, r in (("June", jun), ("Dec", dec)):
        print(f"      {lab}: plain {r['plain']['cagr_pct']:.1f}%/{r['plain']['max_drawdown_pct']:.1f}%  gold {r['gold']['cagr_pct']:.1f}%/{r['gold']['max_drawdown_pct']:.1f}%")

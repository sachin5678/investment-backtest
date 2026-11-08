"""NIFTY100 Momentum 5/10/20, yearly rebalance, with vs without the gold
regime switch — NEXT-OPEN execution (CLAUDE.md rule 3), compared with the
legacy same-close numbers from analyse_n100_yearly.py."""
import json, statistics as st
import pandas as pd
from backtest10 import load_universe_closes, rebalance_dates, fetch
from backtest13 import fetch_gold_cleaned
from nifty100_symbols import NIFTY_100_SYMBOLS
from backtest32 import metrics_only
from backtest33 import build_index_generic
from backtest42 import build_index_regime_filtered_with_hedge, EMA_SPAN
from backtest45 import select_top_n100
from backtest_nextopen import build_next_open, load_opens, clean_open

ca = load_universe_closes()
closes = ca[[s + ".NS" for s in NIFTY_100_SYMBOLS if s + ".NS" in ca.columns]]
nifty = fetch("^NSEI"); gold = fetch_gold_cleaned()
common = closes.index.intersection(nifty.index)
closes = closes.loc[common]; nc = nifty.loc[common, "Close"]
opens = load_opens(closes)
g_close = gold["Close"].reindex(common).ffill().bfill()
g_open = clean_open(gold["Open"].reindex(common), gold["Close"].reindex(common)).ffill().bfill()
ema = nc.ewm(span=EMA_SPAN, adjust=False).mean()
sel = lambda n: (lambda c, t: select_top_n100(c, t, top_n=n))

res = {}
for m in range(1, 13):
    rb = rebalance_dates(closes.index, months=(m,))
    for n in (5, 10, 20):
        res[(m, n)] = {
            "close_plain": build_index_generic(closes, rb, sel(n))[0],
            "close_gold": build_index_regime_filtered_with_hedge(closes, nc, ema, rb, sel(n), g_close)[0],
            "open_plain": build_next_open(closes, opens, nc, ema, rb, sel(n), g_close, g_open, use_regime=False)[0],
            "open_gold": build_next_open(closes, opens, nc, ema, rb, sel(n), g_close, g_open, use_regime=True)[0],
        }
idx = None
for d in res.values():
    for s in d.values():
        idx = s.index if idx is None else idx.intersection(s.index)
nm = metrics_only(nc, idx)
print("window", idx[0].date(), idx[-1].date(), "| NIFTY50 CAGR %.2f DD %.1f" % (nm["cagr_pct"], nm["max_drawdown_pct"]))
out = {"window": [str(idx[0].date()), str(idx[-1].date())], "rows": []}
for n in (5, 10, 20):
    for m in range(1, 13):
        row = {"n": n, "month": m}
        for k, s in res[(m, n)].items():
            x = metrics_only(s, idx); row[k] = {a: x[a] for a in x if a != "equity_curve"}
        out["rows"].append(row)
json.dump(out, open("n100_yearly_nextopen.json", "w"), indent=1)
for n in (5, 10, 20):
    rows = [r for r in out["rows"] if r["n"] == n]
    for k in ("close_plain", "open_plain", "close_gold", "open_gold"):
        c = [r[k]["cagr_pct"] for r in rows]; d = [r[k]["max_drawdown_pct"] for r in rows]
        print(f"N={n:2d} {k:11s} CAGR med {st.median(c):5.1f} ({min(c):5.1f}..{max(c):5.1f}) | DD med {st.median(d):6.1f} worst {min(d):6.1f}")
    for lab, mo in (("June", 6), ("Dec", 12)):
        r = next(r for r in rows if r["month"] == mo)
        print("      %-4s " % lab + "  ".join(f"{k} {r[k]['cagr_pct']:.1f}%/{r[k]['max_drawdown_pct']:.1f}%" for k in ("open_plain", "open_gold")))

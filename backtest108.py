"""Report 108 — NIFTY100 Momentum 10 / 20, SIX-MONTHLY (semi-annual) rebalance,
with and without the 200-EMA gold regime switch, under both execution
conventions (the report-107 analysis re-run on a twice-a-year cadence):

  * next-open (CLAUDE.md rule 3, the headline): a signal at day T's close
    fills at T+1's open — backtest_nextopen.build_next_open
  * same-close (legacy, reports 42-99's convention): a signal fills at the
    close that produced it — backtest42/33 builders, shown for comparison

Universe: today's NIFTY 100 constituents applied backwards (the same
survivorship caveat as reports 12/45). Scoring: report 45's risk-adjusted
6m/12m momentum (select_top_n100). Gold switch: NIFTY 50 vs its 200-EMA,
risk-off parks 100% in GOLDBEES (confirm_days=1). No costs/taxes.

Charts: the Jun/Dec and Jan/Jul calendars (full curves). Calendar table: all
six semi-annual calendars. Writes results107.json (webapp report id 108).
"""
import json
import sys

import pandas as pd

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from backtest10 import load_universe_closes, rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest13 import fetch_gold_cleaned
from backtest32 import metrics_only
from backtest33 import build_index_generic
from backtest42 import build_index_regime_filtered_with_hedge, EMA_SPAN
from backtest45 import select_top_n100
from backtest_nextopen import build_next_open, load_opens, clean_open
from nifty100_symbols import NIFTY_100_SYMBOLS

NS = (10, 20)
# a semi-annual calendar is the pair (m, m+6); keyed by its first month m
MONTH = {1: "Jan/Jul", 2: "Feb/Aug", 3: "Mar/Sep", 4: "Apr/Oct", 5: "May/Nov", 6: "Jun/Dec"}
CHART_CALENDARS = {6: "Jun/Dec", 1: "Jan/Jul"}


def slim(m):
    return {k: v for k, v in m.items() if k != "equity_curve"}


def main():
    ca = load_universe_closes()
    closes = ca[[s + ".NS" for s in NIFTY_100_SYMBOLS if s + ".NS" in ca.columns]]
    nifty = fetch("^NSEI")
    gold = fetch_gold_cleaned()
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nc = nifty.loc[common, "Close"]
    opens = load_opens(closes)
    g_close = gold["Close"].reindex(common).ffill().bfill()
    g_open = clean_open(gold["Open"].reindex(common), gold["Close"].reindex(common)).ffill().bfill()
    ema = nc.ewm(span=EMA_SPAN, adjust=False).mean()

    def sel(n):
        return lambda c, t: select_top_n100(c, t, top_n=n)

    built = {}
    for m in range(1, 7):
        rb = rebalance_dates(closes.index, months=(m, m + 6))
        for n in NS:
            built[(m, n, "open", False)] = build_next_open(closes, opens, nc, ema, rb, sel(n), g_close, g_open, use_regime=False)[0]
            built[(m, n, "open", True)] = build_next_open(closes, opens, nc, ema, rb, sel(n), g_close, g_open, use_regime=True)[0]
            built[(m, n, "close", False)] = build_index_generic(closes, rb, sel(n))[0]
            built[(m, n, "close", True)] = build_index_regime_filtered_with_hedge(closes, nc, ema, rb, sel(n), g_close)[0]
        print(f"built calendar {MONTH[m]}")

    idx = None
    for s in built.values():
        idx = s.index if idx is None else idx.intersection(s.index)
    nifty_m = metrics_only(nc, idx)
    real_gold_idx = idx.intersection(gold["Close"].index)
    gold_m = metrics_only(gold["Close"], real_gold_idx)

    variants = {}
    for m, cal in CHART_CALENDARS.items():
        for n in NS:
            for ex in ("open", "close"):
                for g in (False, True):
                    key = f"top{n}_{'gold' if g else 'plain'}_{ex}_{m}"
                    met = metrics_only(built[(m, n, ex, g)], idx)
                    met["display_label"] = (f"Top {n} · {'gold switch' if g else 'no switch'} · "
                                            f"{'next-open' if ex == 'open' else 'same-close'} · {cal}")
                    met["tags"] = {"n": n, "gold": g, "exec": ex, "cal": cal}
                    variants[key] = met
    nifty_m["display_label"] = "NIFTY 50 (buy & hold)"
    nifty_m["tags"] = {"benchmark": True}
    variants["nifty50"] = nifty_m

    table = []
    for m in range(1, 7):
        for n in NS:
            row = {"month": m, "calendar": MONTH[m], "n": n}
            for ex in ("open", "close"):
                for g in (False, True):
                    mm = metrics_only(built[(m, n, ex, g)], idx)
                    row[f"{ex}_{'gold' if g else 'plain'}"] = {
                        "cagr_pct": mm["cagr_pct"], "max_drawdown_pct": mm["max_drawdown_pct"],
                        "net_return_pct": mm["net_return_pct"]}
            table.append(row)

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": idx[0].strftime("%Y-%m-%d"), "end_date": idx[-1].strftime("%Y-%m-%d"),
        "ema_span": EMA_SPAN,
        "variants": variants,
        "gold_benchmark": slim(gold_m),
        "calendar_table": table,
        "calendar_title": "Every semi-annual rebalance calendar — CAGR / max drawdown",
        "calendar_blurb": "A twice-a-year rebalance still depends on WHICH two months it uses. Each row is one calendar (first month + six months later); the shaded row closing each block is the median of the six. Follows the filter boxes above.",
    }
    with open("results107.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=1, ensure_ascii=False, allow_nan=False)

    print(f"window {results['start_date']} -> {results['end_date']}; NIFTY50 CAGR {nifty_m['cagr_pct']:.2f}% DD {nifty_m['max_drawdown_pct']:.1f}%")
    for n in NS:
        for ex in ("open", "close"):
            for g in (False, True):
                v = variants[f"top{n}_{'gold' if g else 'plain'}_{ex}_6"]
                print(f"  top{n:2d} {ex:5s} {'gold ' if g else 'plain'} Jun/Dec CAGR {v['cagr_pct']:5.1f}%  DD {v['max_drawdown_pct']:6.1f}%")


if __name__ == "__main__":
    main()

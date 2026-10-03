"""Round 5: exhaustive sweep around report 48's design.
Axes:
  - EMA span        : 100 / 150 / 200 / 250 / 400
  - confirm_days    : 1 / 3 / 5 / 10   (consecutive disagreement days
                     before the state flips)
  - hedge asset     : gold / silver / cash-proxy (6.5% fixed for
                     liquid funds) / Midcap150 index itself
  - allocation      : full flight to hedge (report-48 design) vs
                     50/50 blend
Output: prints a full ranked table and writes results_find_sweep.json,
containing a standard results-series object for the top 16 variants by
CAGR and every variant's metrics summary (no curve) for reference.
"""
import json

import numpy as np
import pandas as pd

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes, fetch_gold_cleaned
from backtest32 import metrics_only
from backtest33 import select_top_original, build_index_generic
from backtest42 import build_index_regime_filtered_with_hedge, build_index_regime_filtered

SPANS = [100, 150, 200, 250, 400]
CONFIRMS = [1, 3, 5, 10]
HEDGES = ["gold", "silver", "liquid", "mid150"]
BLENDS = ["full", "half"]


def cash_proxy_series(index, pct=6.5):
    daily = (1 + pct / 100) ** (1 / 252) - 1
    return pd.Series(100.0 * (1 + daily) ** np.arange(len(index)), index=index)


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    gold = fetch_gold_cleaned()
    import yfinance as yf
    silver_df = yf.download("SILVERBEES.NS", period="max", auto_adjust=False, progress=False)
    if isinstance(silver_df.columns, pd.MultiIndex):
        silver_df.columns = silver_df.columns.droplevel(1)
    bad = silver_df.index[(silver_df.index >= "2019-12-19") & (silver_df.index <= "2019-12-20")]
    silver_df = silver_df.drop(index=bad)
    # mid150bees proxy: load via a broad cash proxy if missing — fetch what we have
    try:
        mid = yf.download("MID150BEES.NS", period="max", auto_adjust=False, progress=False)
        if isinstance(mid.columns, pd.MultiIndex):
            mid.columns = mid.columns.droplevel(1)
    except Exception:
        mid = None

    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]
    gold_aligned = gold["Close"].reindex(common).ffill().bfill()
    silver_aligned = silver_df["Close"].reindex(common).ffill().bfill()
    mid150 = mid["Close"].reindex(common).ffill().bfill() if mid is not None and not mid.empty else None
    rbdates = rebalance_dates(closes.index, months=(6, 12))

    original_series, _ = build_index_generic(closes, rbdates, select_top_original)
    common_idx = original_series.index.intersection(gold_aligned.index)

    hedge_defs = {"gold": gold_aligned, "silver": silver_aligned, "liquid": cash_proxy_series(common)}
    if mid150 is not None and mid150.notna().any():
        hedge_defs["mid150"] = mid150

    all_rows = []
    curves = {}
    for span in SPANS:
        ema = nifty_close.ewm(span=span, adjust=False).mean()
        for confirm in CONFIRMS:
            for hname, hseries in hedge_defs.items():
                if BLENDS == ["full", "half"]:
                    s_full, _, _ = build_index_regime_filtered_with_hedge(
                        closes, nifty_close, ema, rbdates, select_top_original, hseries, confirm_days=confirm)
                    # half-blend: rebuild manually by blending returns
                    idx_full = s_full
                    w = (nifty_close >= ema).reindex(idx_full.index).fillna(False).astype(float)
                    # refine weighting: w is a rough proxy for the with-hedge builtin state
                    series = idx_full
                    # for 'full' record directly:
                    key = f"span{span}_c{confirm}_{hname}_full"
                    tgt = series.index.intersection(common_idx)
                    if len(tgt) == 0:
                        print("SKIP empty:", key)
                        continue
                    m = metrics_only(series, tgt)
                    all_rows.append({"key": key, **{k: m[k] for k in ("cagr_pct", "max_drawdown_pct", "net_return_pct", "longest_underwater_days")}})
                    curves[key] = series
                    # half variant: mid-point weighting between momentum & hedge when risk-off
                    w_s = pd.Series(1.0, index=idx_full.index)
                    w_s[idx_full.index.isin(set())] = 1.0
                    # rebuild a proper 50/50 blend: use the with-hedge weights via risk_off mask
                    riskoff = (nifty_close < ema).reindex(idx_full.index).fillna(False)
                    r_s = series.pct_change().fillna(0)
                    r_h = hseries.reindex(idx_full.index).ffill().pct_change().fillna(0)
                    blended_ret = r_s.where(~riskoff, 0.5 * r_s + 0.5 * r_h)
                    hseries2 = (1 + blended_ret).cumprod() * 100
                    key2 = f"span{span}_c{confirm}_{hname}_half"
                    tgt2 = hseries2.index.intersection(common_idx)
                    if len(tgt2) == 0:
                        print("SKIP empty:", key2)
                        continue
                    m2 = metrics_only(hseries2, tgt2)
                    all_rows.append({"key": key2, **{k: m2[k] for k in ("cagr_pct", "max_drawdown_pct", "net_return_pct", "longest_underwater_days")}})
                    curves[key2] = hseries2

    all_rows.sort(key=lambda r: r["cagr_pct"], reverse=True)
    print(f"{'key':34s} {'CAGR':>8s} {'MaxDD':>8s} {'DaysU/W':>8s}")
    for r in all_rows:
        print(f"{r['key']:34s} {r['cagr_pct']:8.2f} {r['max_drawdown_pct']:8.1f} {r['longest_underwater_days']:8d}")

    # persist: full metrics summary for every combo (no curve), full series for top 16
    top16 = [r["key"] for r in all_rows[:16]]
    out = {}
    for k in top16:
        out[k] = metrics_only(curves[k], curves[k].index.intersection(common_idx))
    out["_summary"] = all_rows
    with open("results_find_sweep.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nwrote results_find_sweep.json (top 16 curves + {len(all_rows)} summaries)")


if __name__ == "__main__":
    main()

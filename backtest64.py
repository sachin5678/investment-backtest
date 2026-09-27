"""
NIFTY100 Momentum 10 — absolute momentum gate, same mechanics as reports
62-63, applied to report 12's NIFTY100 Momentum 10 config.
"""
import json

import numpy as np
import pandas as pd

from backtest10 import load_universe_closes, rebalance_dates, fetch, CURRENCY_SYMBOL
from nifty100_symbols import NIFTY_100_SYMBOLS
from backtest32 import metrics_only
from backtest33 import build_index_generic, build_index_generic_gated, TOP_N, LOOKBACK_12M, LOOKBACK_6M
from backtest45 import select_top_n100, MIN_ELIGIBLE


def select_top_abs_gate(closes, t_idx, top_n=TOP_N, min_eligible=MIN_ELIGIBLE):
    if t_idx < LOOKBACK_12M:
        return None
    price_t = closes.iloc[t_idx]
    price_t12 = closes.iloc[t_idx - LOOKBACK_12M]
    price_t6 = closes.iloc[t_idx - LOOKBACK_6M]
    eligible = price_t.notna() & price_t12.notna() & price_t6.notna()
    tickers = closes.columns[eligible]
    if len(tickers) < min_eligible:
        return None

    window = closes.iloc[t_idx - LOOKBACK_12M: t_idx + 1][tickers]
    daily_ret = window.pct_change().dropna(how="all")
    vol_1y = daily_ret.std()

    ret_6m = price_t[tickers] / price_t6[tickers] - 1.0
    ret_12m = price_t[tickers] / price_t12[tickers] - 1.0
    ratio_6m = ret_6m / vol_1y
    ratio_12m = ret_12m / vol_1y

    valid = ratio_6m.notna() & ratio_12m.notna() & np.isfinite(ratio_6m) & np.isfinite(ratio_12m)
    ratio_6m, ratio_12m = ratio_6m[valid], ratio_12m[valid]
    if len(ratio_6m) < min_eligible:
        return None

    z6 = (ratio_6m - ratio_6m.mean()) / ratio_6m.std()
    z12 = (ratio_12m - ratio_12m.mean()) / ratio_12m.std()
    waz = 0.5 * z6 + 0.5 * z12
    norm_score = waz.apply(lambda w: 1 + w if w >= 0 else 1 / (1 - w))

    abs_ok = ret_12m.reindex(norm_score.index) > 0
    gated_score = norm_score[abs_ok]
    ranked = gated_score.sort_values(ascending=False).head(top_n)
    return list(ranked.index)


def main():
    closes_all = load_universe_closes()
    n100_tickers = [s + ".NS" for s in NIFTY_100_SYMBOLS]
    closes = closes_all[[t for t in n100_tickers if t in closes_all.columns]]

    nifty = fetch("^NSEI")
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]

    rbdates = rebalance_dates(closes.index, months=(6, 12))

    original_series, original_sel = build_index_generic(closes, rbdates, select_top_n100)
    gated_series, gated_sel = build_index_generic_gated(closes, rbdates, select_top_abs_gate, slot_count=TOP_N)

    common_idx = original_series.index.intersection(gated_series.index)
    original_metrics = metrics_only(original_series, common_idx)
    gated_metrics = metrics_only(gated_series, common_idx)
    nifty_metrics = metrics_only(nifty.loc[common_idx, "Close"], common_idx)

    fills = [s["num_filled"] for s in gated_sel]
    num_partial = sum(1 for f in fills if f < TOP_N)
    avg_filled = round(float(np.mean(fills)), 2) if fills else None

    def sample(sel):
        return sel[:3] + sel[-3:] if len(sel) > 6 else sel

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "num_rebalances": len(gated_sel),
        "num_partial_fill_rebalances": num_partial,
        "avg_slots_filled": avg_filled,
        "original": {**original_metrics, "selections_sample": sample(original_sel)},
        "gated": {**gated_metrics, "selections_sample": sample(gated_sel)},
        "nifty": nifty_metrics,
    }

    with open("results63.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}  rebalances {results['num_rebalances']}")
    print(f"Original (no gate)      CAGR {original_metrics['cagr_pct']:.2f}% / DD {original_metrics['max_drawdown_pct']:.1f}%")
    print(f"Absolute momentum gate  CAGR {gated_metrics['cagr_pct']:.2f}% / DD {gated_metrics['max_drawdown_pct']:.1f}%")
    print(f"nifty 50                CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")
    print(f"partial-fill rebalances: {num_partial}/{len(gated_sel)}  |  avg slots filled: {avg_filled}/{TOP_N}")


if __name__ == "__main__":
    main()

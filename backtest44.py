"""
Smallcap250 Momentum 10 — the same 200-day EMA regime filter from report
42, tested on a third universe. Filter mechanics identical to reports 42-43.
Report 16/29's Smallcap250 Momentum 10 config: top 10, equal-weight,
June/December, min_eligible=40.
"""
import json

import numpy as np
import pandas as pd

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest15 import load_smallcap250_closes
from backtest32 import metrics_only
from backtest33 import build_index_generic
from backtest42 import build_index_regime_filtered, cash_blocks_from_log, EMA_SPAN

TOP_N = 10
MIN_ELIGIBLE_SMALLCAP = 40
LOOKBACK_12M = 252
LOOKBACK_6M = 126


def select_top_smallcap(closes, t_idx, top_n=TOP_N, min_eligible=MIN_ELIGIBLE_SMALLCAP):
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
    return list(norm_score.sort_values(ascending=False).head(top_n).index)


def main():
    closes = load_smallcap250_closes()
    nifty = fetch("^NSEI")
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]
    ema = nifty_close.ewm(span=EMA_SPAN, adjust=False).mean()

    rbdates = rebalance_dates(closes.index, months=(6, 12))

    original_series, original_sel = build_index_generic(closes, rbdates, select_top_smallcap)
    filtered_series, filtered_sel, state_log = build_index_regime_filtered(closes, nifty_close, ema, rbdates, select_top_smallcap)

    common_idx = original_series.index.intersection(filtered_series.index)
    original_metrics = metrics_only(original_series, common_idx)
    filtered_metrics = metrics_only(filtered_series, common_idx)
    nifty_metrics = metrics_only(nifty_close.loc[common_idx], common_idx)

    cash_blocks, pct_cash = cash_blocks_from_log(state_log)
    num_reentries = sum(1 for s in filtered_sel if s["trigger"] == "regime_reentry")
    rb_in_window = [d for d in rbdates if d in common_idx]
    num_scheduled_total = len(rb_in_window)
    num_scheduled_hit = sum(1 for s in filtered_sel if s["trigger"] == "scheduled_rebalance")
    num_scheduled_skipped = max(num_scheduled_total - num_scheduled_hit, 0)

    def sample(sel):
        return sel[:3] + sel[-3:] if len(sel) > 6 else sel

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "ema_span": EMA_SPAN,
        "pct_time_in_cash": round(pct_cash, 1),
        "num_cash_periods_10d_plus": len(cash_blocks),
        "num_regime_reentries": num_reentries,
        "num_scheduled_rebalances_total": num_scheduled_total,
        "num_scheduled_rebalances_skipped_in_cash": num_scheduled_skipped,
        "cash_periods": cash_blocks[:8],
        "original": {**original_metrics, "selections_sample": sample(original_sel)},
        "filtered": {**filtered_metrics, "selections_sample": sample(filtered_sel)},
        "nifty": nifty_metrics,
    }

    with open("results43.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}")
    print(f"Smallcap250 Momentum 10 (no filter)       CAGR {original_metrics['cagr_pct']:.2f}% / DD {original_metrics['max_drawdown_pct']:.1f}%")
    print(f"Smallcap250 Momentum 10 (200-EMA regime)  CAGR {filtered_metrics['cagr_pct']:.2f}% / DD {filtered_metrics['max_drawdown_pct']:.1f}%")
    print(f"nifty 50 benchmark                        CAGR {nifty_metrics['cagr_pct']:.2f}% / DD {nifty_metrics['max_drawdown_pct']:.1f}%")
    print(f"time in cash: {pct_cash:.1f}%  |  re-entries: {num_reentries}  |  scheduled skipped: {num_scheduled_skipped}/{num_scheduled_total}")


if __name__ == "__main__":
    main()

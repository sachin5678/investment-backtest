"""
Report 99 — Timing audit of the gold-strength guard (reports 91/92).

The guard's first release claimed +11.5pp of CAGR over report 48 with a
shallower drawdown. This report recomputes the published logic exactly as
it shipped and the corrected logic (backtest91.build_gold_strength_guard,
now prior-close timed), side by side on one window, and quantifies where
the difference came from:

  1. FLIP-OFF-DAY SUBSTITUTION — report 48's event loop flips state at a
     day's close, so the flip-off day's realized return is still STOCKS.
     The published guard treated that day as 'cash' and retroactively
     charged it gold (or 0%), dodging equity crash days like 2015-08-24
     (-11.3%) and 2022-02-24 (-6.2%) it never could have dodged live.
  2. SAME-DAY EXIT CHECKS — the published guard idled flat cash on any
     day whose own close tripped the gold checks (e.g. gold's -7.6% day
     2013-04-15), again using information from the day being replaced.

Both are same-day information. Fixed, ~all of the claimed gain vanishes:
the guard's honest value is a small drawdown improvement at ~identical
CAGR. Nothing here reimplements the invested leg — every non-guard day's
return comes from report 48's own event loop, same as reports 91/92.

This script supersedes the temporary audit_gold_guard_timing.py used
during the review (removed once this report landed) and also backed the
same fix applied to the findings-round f10 page (wild9_eventloop_guard.py).
"""
import json
import math
import sys

import pandas as pd

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes, fetch_gold_cleaned
from backtest32 import metrics_only
from backtest33 import select_top_original
from backtest42 import build_index_regime_filtered_with_hedge, EMA_SPAN
from backtest91 import build_gold_strength_guard, is_cash_panel, GOLD_LOOKBACK_DAYS


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    gold = fetch_gold_cleaned()
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]
    gold_aligned = gold["Close"].reindex(common).ffill().bfill()
    real_gold_idx = common.intersection(gold["Close"].index)

    ema200 = nifty_close.ewm(span=EMA_SPAN, adjust=False).mean()
    rbdates = rebalance_dates(closes.index, months=(6, 12))

    # --- report 48's own event loop (the baseline, never modified) ---
    r48, _, r48_log = build_index_regime_filtered_with_hedge(
        closes, nifty_close, ema200, rbdates, select_top_original, gold_aligned)
    is_cash = is_cash_panel(r48_log, r48.index)

    gold6 = gold_aligned.pct_change(GOLD_LOOKBACK_DAYS)
    nifty6 = nifty_close.pct_change(GOLD_LOOKBACK_DAYS)
    passes = (gold6 > nifty6).reindex(r48.index).fillna(False) & (gold6 > 0).reindex(r48.index).fillna(False)

    rets = r48.pct_change().fillna(0.0)
    gold_rets = gold_aligned.reindex(r48.index).ffill().pct_change().fillna(0.0)

    # --- the published (first-release) logic, exactly as it shipped ---
    cash_and_pass = is_cash & passes
    cash_and_fail = is_cash & (~passes)
    pub_rets = rets.copy()
    pub_rets[cash_and_pass] = gold_rets[cash_and_pass]
    pub_rets[cash_and_fail] = 0.0
    published = (1 + pub_rets).cumprod() * 100

    # --- the corrected logic (backtest91, prior-close timed) ---
    corrected, _, _, _, cash_and_fail_fixed = build_gold_strength_guard(
        closes, nifty_close, ema200, rbdates, select_top_original, gold_aligned)

    common_idx = r48.index.intersection(real_gold_idx)

    # --- attribution diagnostics ---
    cash_prev = is_cash.shift(1).fillna(False).astype(bool)
    fail_prev = cash_prev & (~passes.shift(1).fillna(False).astype(bool))

    boundary = is_cash & (~cash_prev)            # flip-off days: realized return is stocks
    fail_entry = cash_and_fail & (~fail_prev)    # days the published same-day rule zeroed with no prior-close warning
    boundary_pass = int((boundary & cash_and_pass).sum())
    boundary_fail = int((boundary & cash_and_fail).sum())

    boundary_rows = []
    for d in r48.index[boundary]:
        r48_r = rets[d] * 100.0
        gold_r = gold_rets[d] * 100.0
        if cash_and_pass[d]:
            charged = gold_r
        elif cash_and_fail[d]:
            charged = 0.0
        else:
            charged = r48_r
        boundary_rows.append({
            "date": d.strftime("%Y-%m-%d"),
            "r48_pct": round(r48_r, 3),
            "gold_pct": round(gold_r, 3),
            "published_charged_pct": round(charged, 3),
        })
    boundary_rows.sort(key=lambda b: b["r48_pct"])

    fail_entry_rows = []
    for d in r48.index[fail_entry]:
        fail_entry_rows.append({
            "date": d.strftime("%Y-%m-%d"),
            "r48_pct": round(rets[d] * 100.0, 3),
        })
    fail_entry_rows.sort(key=lambda b: b["r48_pct"])

    pub_mult = float(published.iloc[-1] / r48.iloc[-1])
    fix_mult = float(corrected.iloc[-1] / r48.iloc[-1])

    # Terminal-multiple decomposition: the published series differs from
    # r48 on two disjoint day-sets, so the multiples multiply.
    fail_side = float((1.0 + rets[cash_and_fail]).prod())          # published zeroed these (gold-day bleed removed)
    sub_side = float(((1.0 + gold_rets[cash_and_pass]) / (1.0 + rets[cash_and_pass])).prod())  # boundary/pass substitution

    m_r48 = metrics_only(r48, common_idx)
    m_pub = metrics_only(published, common_idx)
    m_fix = metrics_only(corrected, common_idx)
    m_nif = metrics_only(nifty_close, common_idx)
    m_gold = metrics_only(gold["Close"], common_idx.intersection(real_gold_idx))

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "ema_span": EMA_SPAN, "gold_lookback_days": GOLD_LOOKBACK_DAYS,
        "report48": m_r48,
        "guard_as_published": m_pub,
        "guard_corrected": m_fix,
        "nifty": m_nif,
        "gold_benchmark": m_gold,
        "audit": {
            "published_cagr_gain_pp": round(m_pub["cagr_pct"] - m_r48["cagr_pct"], 2),
            "corrected_cagr_gain_pp": round(m_fix["cagr_pct"] - m_r48["cagr_pct"], 2),
            "published_dd_gain_pp": round(m_pub["max_drawdown_pct"] - m_r48["max_drawdown_pct"], 2),
            "corrected_dd_gain_pp": round(m_fix["max_drawdown_pct"] - m_r48["max_drawdown_pct"], 2),
            "published_terminal_multiple": round(pub_mult, 3),
            "corrected_terminal_multiple": round(fix_mult, 3),
            "fail_side_multiple": round(1.0 / fail_side, 3),
            "substitution_multiple": round(sub_side, 3),
            "days_zeroed_published": int(cash_and_fail.sum()),
            "days_zeroed_corrected": int(cash_and_fail_fixed.sum()),
            "flipoff_boundary_days": int(boundary.sum()),
            "flipoff_pass_days": boundary_pass,
            "flipoff_fail_days": boundary_fail,
            "fail_entry_lookahead_days": int(fail_entry.sum()),
            "worst_boundary_days": boundary_rows[:12],
            "worst_fail_entry_days": fail_entry_rows[:10],
        },
    }

    with open("results98.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    a = results["audit"]
    print(f"window {results['start_date']} -> {results['end_date']}")
    print(f"report 48 (gold, no guard)   CAGR {m_r48['cagr_pct']:6.2f}% / DD {m_r48['max_drawdown_pct']:6.1f}%")
    print(f"guard AS PUBLISHED (buggy)   CAGR {m_pub['cagr_pct']:6.2f}% / DD {m_pub['max_drawdown_pct']:6.1f}%  ({a['published_cagr_gain_pp']:+.2f}pp, terminal multiple {pub_mult:.2f}x)")
    print(f"guard CORRECTED              CAGR {m_fix['cagr_pct']:6.2f}% / DD {m_fix['max_drawdown_pct']:6.1f}%  ({a['corrected_cagr_gain_pp']:+.2f}pp, terminal multiple {fix_mult:.2f}x)")
    print()
    print(f"flip-off boundary days (realized return = stocks): {a['flipoff_boundary_days']}")
    print(f"same-day fail entries with no prior-close warning : {a['fail_entry_lookahead_days']}")
    print(f"days zeroed: published {a['days_zeroed_published']} vs corrected {a['days_zeroed_corrected']}")
    print()
    print("worst flip-off boundary days (published retro-charge vs reality):")
    for b in a["worst_boundary_days"][:6]:
        print(f"  {b['date']}  r48 {b['r48_pct']:+8.3f}%   gold {b['gold_pct']:+8.3f}%   published charged {b['published_charged_pct']:+8.3f}%")


if __name__ == "__main__":
    main()

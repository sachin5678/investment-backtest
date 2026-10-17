"""
Shared live signal for the four-report alert suite (reports 71, 91, 92 and
98) — used by BOTH notify_reports.py (Telegram) and notify_reports_email.py
(email), the same one-place-for-the-math split rebalance_signal.py has for
reports 48/91.

All four reports share report 48's skeleton: Midcap150 universe, top-10
risk-adjusted 6m/12m momentum (backtest33.select_top_original), and the
daily NIFTY-50-vs-200-EMA regime check (backtest42.EMA_SPAN). What each
report's live action adds on top:

  * report 91 (results90.json) — report 48's own picks; when the regime is
    OFF, the hedge leg holds gold ONLY while gold passes both of its own
    6-month strength checks (gold's 6m return beats NIFTY's AND is
    positive); otherwise flat cash. This is the same guard computation as
    rebalance_signal.compute_current_picks() — the reference live
    implementation used by report 48's alerts — kept numerically
    identical on purpose (same GOLD_LOOKBACK_DAYS constant and the same
    prior-close convention report 99's timing correction settled on).

  * report 92 (results91.json) — the same guard re-tested on all six
    rebalance calendars; the live action is calendar-independent, so
    report 92's state is identical to report 91's.

  * report 71 (results70.json) — always-on 70/30 core-satellite: 70% in
    the top-10 and 30% in gold at all times; a regime flip moves the WHOLE
    book to 100% gold until NIFTY closes back above its 200-EMA.

  * report 98 (results97.json, the "max stack") — the report-93 review
    layer upgraded by labs 94-97: at a scheduled review a held name is
    kept only while it still ranks inside the top 30 (exit rank) AND its
    own 6-month return is positive (keep-if 6m > 0); stack B additionally
    requires new buys to pass the same 6m > 0 check. The fresh-review
    target (what a trader starting from cash buys at this review) is the
    top-10 by rank for stack A and the top-10 among 6m > 0 for stack B.
    Regime OFF parks 100% in gold — lab 94 found nothing beat report 93's
    own daily 200-EMA protect layer.

DATA FRESHNESS: fetches everything LIVE via yfinance (through
rebalance_signal.fetch_midcap150_closes_live) rather than the local cache —
a same-day alert needs the same-day close.
"""
import pandas as pd

from backtest10 import fetch
from backtest33 import select_top_original, MIN_ELIGIBLE, LOOKBACK_12M, LOOKBACK_6M
from backtest42 import EMA_SPAN
from backtest91 import GOLD_LOOKBACK_DAYS
from rebalance_signal import fetch_midcap150_closes_live, TOP_N, GOLD_TICKER

REPORTS = {
    71: "Report 71 (Core-Satellite + Gold)",
    91: "Report 91 (Gold-Strength Guard)",
    92: "Report 92 (Guard vs. Rebalance Calendar)",
    98: "Report 98 (Max Strategy)",
}


def compute_state(report):
    """One live snapshot for `report` — regime, picks, guard check and (for
    report 98) the two fresh-review targets. Fetches live prices for the
    whole Midcap150 universe, so call it once per run and render from the
    returned dict."""
    if report not in REPORTS:
        raise ValueError(f"unknown report {report!r} — expected one of {sorted(REPORTS)}")

    closes = fetch_midcap150_closes_live()
    nifty = fetch("^NSEI")
    gold = fetch(GOLD_TICKER)

    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]

    if len(common) < LOOKBACK_12M + 1:
        raise RuntimeError(f"Not enough live history yet ({len(common)} days) to compute momentum — need {LOOKBACK_12M}+.")

    ema = nifty_close.ewm(span=EMA_SPAN, adjust=False).mean()
    t_idx = len(common) - 1
    as_of = common[-1]

    state = {
        "report": report,
        "as_of": as_of,
        "regime_on": bool(nifty_close.iloc[-1] > ema.iloc[-1]),
        "nifty_close": float(nifty_close.iloc[-1]),
        "nifty_ema": float(ema.iloc[-1]),
        "gold_price": float(gold["Close"].iloc[-1]) if not gold.empty else None,
        "picks": None,
        "ret_6m_pct": {},
        "stack_a": None,
        "stack_b": None,
        "guard_passes": None,
        "guard_gold_6m_pct": None,
        "guard_nifty_6m_pct": None,
    }

    if state["regime_on"]:
        # the full ranked list (not just the top 10) — report 98 needs the
        # 6-month returns of every ranked candidate for its 6m > 0 filters,
        # and they double as the rank-order evidence for the other reports.
        ranking = select_top_original(closes, t_idx, top_n=len(closes.columns), min_eligible=MIN_ELIGIBLE)
        if not ranking:
            raise RuntimeError("ranked universe too small to compute picks")
        base = closes.iloc[t_idx - LOOKBACK_6M]
        last = closes.iloc[t_idx]
        for t in ranking:
            b = base[t]
            state["ret_6m_pct"][t.replace(".NS", "")] = (
                float(last[t] / b - 1.0) * 100.0 if pd.notna(b) and b else None
            )
        ranked = [t.replace(".NS", "") for t in ranking]
        state["picks"] = ranked[:TOP_N]
        if report == 98:
            state["stack_a"] = ranked[:TOP_N]
            state["stack_b"] = [t for t in ranked if (state["ret_6m_pct"].get(t) or 0) > 0][:TOP_N]
    else:
        # reports 91/92's gold-strength guard — mirrors
        # rebalance_signal.compute_current_picks()'s computation exactly
        # (prior-close convention per report 99's timing correction).
        if len(gold) > GOLD_LOOKBACK_DAYS and len(common) > GOLD_LOOKBACK_DAYS:
            g6 = float(gold["Close"].iloc[-1] / gold["Close"].iloc[-1 - GOLD_LOOKBACK_DAYS] - 1.0)
            n6 = float(nifty_close.iloc[-1] / nifty_close.iloc[-1 - GOLD_LOOKBACK_DAYS] - 1.0)
            state["guard_gold_6m_pct"] = g6 * 100
            state["guard_nifty_6m_pct"] = n6 * 100
            state["guard_passes"] = bool(g6 > n6 and g6 > 0)

    return state


def build_report_csv(state):
    """CSV for one report's current action — the report-48-style
    ticker/weight_pct columns (report 98 gets both stack candidates side by
    side, since its two published stacks are the same design up to the buy
    filter)."""
    report = state["report"]
    gold = GOLD_TICKER.replace(".NS", "")
    rows = []

    if report in (91, 92):
        if state["regime_on"]:
            rows = [{"ticker": t, "weight_pct": f"{100 / TOP_N:.1f}"} for t in state["picks"]]
        elif state["guard_passes"]:
            rows = [{"ticker": gold, "weight_pct": "100.0"}]
        else:
            rows = [{"ticker": "CASH", "weight_pct": "100.0"}]
    elif report == 71:
        if state["regime_on"]:
            rows = [{"ticker": t, "weight_pct": "7.0"} for t in state["picks"]]
            rows.append({"ticker": gold, "weight_pct": "30.0"})
        else:
            rows = [{"ticker": gold, "weight_pct": "100.0"}]
    elif report == 98:
        if state["regime_on"]:
            a, b = state["stack_a"], state["stack_b"]
            for i in range(TOP_N):
                rows.append({
                    "stack_a_ticker": a[i] if i < len(a) else "",
                    "stack_a_pct": "10.0" if i < len(a) else "",
                    "stack_b_ticker": b[i] if i < len(b) else "",
                    "stack_b_pct": "10.0" if i < len(b) else "",
                })
        else:
            rows = [{"stack_a_ticker": gold, "stack_a_pct": "100.0",
                     "stack_b_ticker": gold, "stack_b_pct": "100.0"}]

    return pd.DataFrame(rows).to_csv(index=False)

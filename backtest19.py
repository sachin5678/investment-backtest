"""
50/50 blend of Midcap150 Momentum 10 (this project's best-performing
momentum reconstruction so far — CAGR 40.6%, see report 18's 10-vs-20-vs-30
spectrum) and gold, with the mechanical rule you described:

  - Start 50% momentum / 50% gold, then LEAVE IT ALONE — no periodic
    recalibration at all. (A calendar-rebalanced 50/50 blend already exists
    as a separate idea — report 14's Momentum-20+Gold blend — so a matching
    "periodic 50/50, same momentum leg" line is included below purely as
    context, not as this report's main strategy.)
  - THE CATCH: the instant the momentum leg's OWN cumulative value falls 20%
    below its OWN running peak (measured on the momentum series alone — the
    same convention as every ATH-drawdown trigger already used in this
    project: reports 3, 4, 5, 6, 7, 8), sell 100% of the gold position and
    move the ENTIRE proceeds into the momentum position. A lump sum funded
    by liquidating the diversification cushion, not new cash.
  - HOLD 100% momentum (0% gold) until the momentum leg makes a brand-new
    all-time high — fully round-tripping the drawdown that triggered the
    move. This is the exact "confirmed recovery" condition from report 6,
    used here as an EXIT from a temporary all-in state instead of an ENTRY
    into one.
  - On recovery: reset to EXACTLY 50/50 again, and repeat for as long as
    the backtest runs — any number of full trigger -> recovery -> reset
    cycles.

Midcap150 Momentum 10's index level is RECOMPUTED here from the underlying
stock prices (identical build_index() call as report 16 / backtest15.py:
top 10, June/December, min_eligible=30) rather than read back from that
report's already-downsampled equity_curve JSON (capped at 1500 points over
an ~18-year DAILY series) — the -20%/new-high triggers need full daily
resolution to fire on the correct date, not an interpolated approximation.
Gold is the same cleaned GOLDBEES.NS series used in report 14
(backtest13.fetch_gold_cleaned()).

Same disclosed approximations carried over from reports 15/16: today's
fixed Midcap 150 constituent list applied retroactively (survivorship
bias), equal weighting, no F&O screen, June/December cadence borrowed from
the NIFTY200 Momentum convention rather than the real Midcap150 Momentum
index's own May/November cadence (this reuses report 16's exact
construction on purpose, since you named "midcap 10" as the specific,
already-computed asset to build on).
"""
import json

import numpy as np
import pandas as pd

from backtest10 import build_index, fetch, series_to_points, CURRENCY_SYMBOL, rebalance_dates
from backtest13 import load_midcap150_closes, metrics, blend_50_50, fetch_gold_cleaned

TOP_N = 10
MIN_ELIGIBLE = 30
DRAWDOWN_TRIGGER_PCT = -20.0


def build_catch_blend(mom, gold):
    """Event-driven 2-asset simulation of the drawdown-triggered all-in /
    confirmed-recovery-reset rule described above. Executes at the SAME
    day's close as the trigger/recovery condition is detected — the same
    fill convention used for every other threshold-based (not breakout-
    signal-based) strategy in this project."""
    common = mom.index.intersection(gold.index)
    m, g = mom.loc[common], gold.loc[common]

    value = pd.Series(np.nan, index=common)
    state = "normal"
    shares_m = 50.0 / m.iloc[0]
    shares_g = 50.0 / g.iloc[0]
    peak_m = m.iloc[0]
    events = []
    trigger_date = None

    for d in common:
        mv, gv = m.loc[d], g.loc[d]
        peak_m = max(peak_m, mv)
        dd_pct = (mv / peak_m - 1.0) * 100

        if state == "normal" and dd_pct <= DRAWDOWN_TRIGGER_PCT:
            port_val = shares_m * mv + shares_g * gv
            shares_m = port_val / mv
            shares_g = 0.0
            state = "concentrated"
            trigger_date = d
            events.append({"date": d.strftime("%Y-%m-%d"), "event": "trigger_all_in",
                            "momentum_drawdown_pct": round(dd_pct, 2), "portfolio_value": float(port_val)})
        elif state == "concentrated" and mv >= peak_m:
            port_val = shares_m * mv
            shares_m = (port_val * 0.5) / mv
            shares_g = (port_val * 0.5) / gv
            state = "normal"
            days_in_state = (d - trigger_date).days
            events.append({"date": d.strftime("%Y-%m-%d"), "event": "recovery_reset_50_50",
                            "days_since_trigger": days_in_state, "portfolio_value": float(port_val)})

        value.loc[d] = shares_m * mv + shares_g * gv

    return value, events, state


def build_static_no_rebalance(mom, gold):
    """Clean control: identical 50/50 starting split, then genuinely never
    touched again — isolates exactly what the catch adds on top of doing
    nothing at all."""
    common = mom.index.intersection(gold.index)
    m, g = mom.loc[common], gold.loc[common]
    shares_m = 50.0 / m.iloc[0]
    shares_g = 50.0 / g.iloc[0]
    return shares_m * m + shares_g * g


def main():
    midcap_closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    gold_df = fetch_gold_cleaned()
    midcap_closes = midcap_closes.loc[midcap_closes.index.intersection(nifty.index)]

    mom_level, _ = build_index(midcap_closes, top_n=TOP_N, min_eligible=MIN_ELIGIBLE, rebalance_months=(6, 12))
    mom_start, mom_end = mom_level.index[0], mom_level.index[-1]

    common = mom_level.index[(mom_level.index >= mom_start) & (mom_level.index <= mom_end)]
    common = common.intersection(gold_df.index).intersection(nifty.index)
    mom = mom_level.loc[common]
    gold = gold_df.loc[common, "Close"]
    nifty_s = nifty.loc[common, "Close"]

    catch_value, events, final_state = build_catch_blend(mom, gold)
    static_value = build_static_no_rebalance(mom, gold)
    rb_dates = rebalance_dates(common, months=(6, 12))
    periodic_value = blend_50_50(mom, gold, rb_dates)

    def norm(s):
        return s / s.iloc[0] * 100.0

    num_triggers = sum(1 for e in events if e["event"] == "trigger_all_in")
    num_recoveries = sum(1 for e in events if e["event"] == "recovery_reset_50_50")
    recovered_events = [e for e in events if e["event"] == "recovery_reset_50_50"]
    avg_days_to_recover = float(np.mean([e["days_since_trigger"] for e in recovered_events])) if recovered_events else None

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common[0].strftime("%Y-%m-%d"), "end_date": common[-1].strftime("%Y-%m-%d"),
        "drawdown_trigger_pct": DRAWDOWN_TRIGGER_PCT,
        "num_triggers": num_triggers, "num_recoveries": num_recoveries,
        "currently_in_concentrated_state": final_state == "concentrated",
        "avg_days_to_recover": avg_days_to_recover,
        "events": events,
        "catch_blend": {"equity_curve": series_to_points(catch_value), **metrics(catch_value)},
        "static_50_50_no_rebalance": {"equity_curve": series_to_points(static_value), **metrics(static_value)},
        "periodic_50_50_rebalance": {"equity_curve": series_to_points(periodic_value), **metrics(periodic_value)},
        "midcap_momentum10": {"equity_curve": series_to_points(norm(mom)), **metrics(mom)},
        "gold": {"equity_curve": series_to_points(norm(gold)), **metrics(gold)},
        "nifty": {"equity_curve": series_to_points(norm(nifty_s)), **metrics(nifty_s)},
    }
    with open("results19.json", "w") as f:
        json.dump(results, f)

    print("start", common[0].date(), "end", common[-1].date())
    for k in ("catch_blend", "static_50_50_no_rebalance", "periodic_50_50_rebalance", "midcap_momentum10", "gold", "nifty"):
        v = results[k]
        print(f"[{k}] net_return={v['net_return_pct']:.1f}% cagr={v['cagr_pct']:.2f}% "
              f"mdd={v['max_drawdown_pct']:.1f}% uw_days={v['longest_underwater_days']}")
    print(f"\ntriggers={num_triggers} recoveries={num_recoveries} "
          f"currently_in_concentrated_state={final_state == 'concentrated'} avg_days_to_recover={avg_days_to_recover}")
    print("\nfirst events:")
    for e in events[:6]:
        print(" ", e)
    print("...\nlast events:")
    for e in events[-6:]:
        print(" ", e)


if __name__ == "__main__":
    main()

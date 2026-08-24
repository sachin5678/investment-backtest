"""
Strategy 6: SIP that DOUBLES during a drawdown, NIFTY Midcap 150.

Rule, as specified in chat:
  - Base: ₹1,000/month into midcap, first trading day of the month, filled
    at that day's close (same scheduled-contribution convention as the last
    two reports).
  - Overlay: for every month whose SIP date falls while midcap is currently
    more than 15% below its all-time-high-to-date, the contribution for that
    month DOUBLES to ₹2,000 — not a one-off lump sum, but the recurring SIP
    itself, for as long as the drawdown persists ("all months").
  - Once midcap fully recovers — closes back at/above that same previous
    all-time high — the SIP reverts to the normal ₹1,000 for subsequent
    months. This uses the same hysteresis as the last two reports: once a
    ≥15% drawdown arms the "elevated" state, it stays armed through any
    partial bounce, and only clears on a genuine new all-time high.
  - Because the amount only changes on an already-scheduled monthly date,
    there is no separate reactive signal/next-open fill here — the SIP date
    itself is the only event, and its size depends on the state as of that
    same day's close.
  - Same two vanilla-SIP benchmarks (₹1,000/month, no overlay, in midcap and
    in NIFTY 50) and the same money-weighted XIRR / value-over-invested
    drawdown methodology as the last two reports. Also compared, in the
    text, against the last two reports' overlay strategies (buy-the-dip
    lump sums, buy-the-confirmed-recovery lump sum).
"""
import json
import numpy as np
import pandas as pd

from backtest4 import (
    fetch, xirr, cumret_drawdown, series_to_points,
    COMMISSION_RATE, MONTHLY_AMOUNT, NIFTY_TICKER, MIDCAP_TICKER, NIFTY_TICK, MIDCAP_TICK, CURRENCY_SYMBOL,
)

DRAWDOWN_TRIGGER_PCT = 15.0
DOUBLED_AMOUNT = 2000.0


def run_double_sip(dates, opens, closes, normal_amount, doubled_amount, drawdown_pct, tick, cost_loaded):
    n = len(dates)
    ath = pd.Series(closes).cummax().to_numpy()
    months = np.array([(d.year, d.month) for d in dates])

    units = 0.0
    total_invested = 0.0
    contributions = []
    episodes = []          # each elevated-SIP period: start/end dates, months doubled
    elevated = False
    episode_start = None
    episode_months = 0
    current_month = None

    value_curve = np.empty(n)
    invested_curve = np.empty(n)

    def buy(amount, price):
        fill_price = price + (tick if cost_loaded else 0.0)
        commission = COMMISSION_RATE * amount if cost_loaded else 0.0
        return (amount - commission) / fill_price

    for i in range(n):
        dd_today = closes[i] / ath[i] - 1.0
        if not elevated and dd_today <= -drawdown_pct / 100.0:
            elevated = True
            episode_start = dates[i]
            episode_months = 0
        if elevated and closes[i] >= ath[i]:
            episodes.append({"start": episode_start, "end": dates[i], "months_doubled": episode_months})
            elevated = False
            episode_start = None

        if current_month != tuple(months[i]):
            current_month = tuple(months[i])
            amount = doubled_amount if elevated else normal_amount
            u = buy(amount, closes[i])
            units += u
            total_invested += amount
            contributions.append((dates[i], amount, "SIP (doubled)" if elevated else "SIP"))
            if elevated:
                episode_months += 1

        value_curve[i] = units * closes[i]
        invested_curve[i] = total_invested

    if elevated:
        episodes.append({"start": episode_start, "end": None, "months_doubled": episode_months})

    value_series = pd.Series(value_curve, index=dates)
    invested_series = pd.Series(invested_curve, index=dates)
    return value_series, invested_series, contributions, episodes, units


def portfolio_result(dates, opens, closes, normal_amount, doubled_amount, drawdown_pct, tick, cost_loaded, label):
    value, invested, contributions, episodes, units = run_double_sip(
        dates, opens, closes, normal_amount, doubled_amount, drawdown_pct, tick, cost_loaded)
    mdd, peak_d, trough_d, uw_days = cumret_drawdown(value, invested)

    cashflows = [(d, -amt) for d, amt, _ in contributions]
    cashflows.append((dates[-1], float(value.iloc[-1])))
    rate = xirr(cashflows)

    total_invested = float(invested.iloc[-1])
    final_value = float(value.iloc[-1])
    num_doubled = sum(1 for _, _, k in contributions if k == "SIP (doubled)")
    return {
        "label": label,
        "value_curve": series_to_points(value),
        "invested_curve": series_to_points(invested),
        "total_invested": total_invested,
        "final_value": final_value,
        "net_gain": final_value - total_invested,
        "net_gain_pct": (final_value / total_invested - 1.0) * 100.0 if total_invested else None,
        "xirr_pct": rate,
        "num_contributions": len(contributions),
        "num_doubled_months": num_doubled,
        "episodes": [
            {"start": e["start"].strftime("%Y-%m-%d"), "end": e["end"].strftime("%Y-%m-%d") if e["end"] else None,
             "months_doubled": e["months_doubled"]}
            for e in episodes
        ],
        "max_drawdown_pct": mdd, "max_drawdown_peak_date": peak_d, "max_drawdown_trough_date": trough_d,
        "longest_underwater_days": uw_days,
    }


def build():
    nifty = fetch(NIFTY_TICKER)
    midcap = fetch(MIDCAP_TICKER)

    start_date = midcap.index[0]
    common_dates = nifty.index[(nifty.index >= start_date) & (nifty.index.isin(midcap.index))]
    nifty_a = nifty.loc[common_dates]
    midcap_a = midcap.loc[common_dates]

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "nifty_ticker": NIFTY_TICKER, "midcap_ticker": MIDCAP_TICKER, "currency_symbol": CURRENCY_SYMBOL,
        "monthly_amount": MONTHLY_AMOUNT, "doubled_amount": DOUBLED_AMOUNT, "drawdown_trigger_pct": DRAWDOWN_TRIGGER_PCT,
        "start_date": common_dates[0].strftime("%Y-%m-%d"), "end_date": common_dates[-1].strftime("%Y-%m-%d"),
        "portfolios": {},
    }

    mo, mc = midcap_a["Open"].to_numpy(), midcap_a["Close"].to_numpy()
    no, nc = nifty_a["Open"].to_numpy(), nifty_a["Close"].to_numpy()

    for cost_loaded, vk in [(False, "frictionless"), (True, "cost_loaded")]:
        results["portfolios"].setdefault("strategy", {})[vk] = portfolio_result(
            common_dates, mo, mc, MONTHLY_AMOUNT, DOUBLED_AMOUNT, DRAWDOWN_TRIGGER_PCT, MIDCAP_TICK, cost_loaded,
            "Strategy (SIP doubles during ≥15% drawdown, midcap)")
        results["portfolios"].setdefault("vanilla_midcap", {})[vk] = portfolio_result(
            common_dates, mo, mc, MONTHLY_AMOUNT, MONTHLY_AMOUNT, 999.0, MIDCAP_TICK, cost_loaded, "Vanilla SIP, midcap")

    results["portfolios"]["vanilla_nifty"] = {"frictionless": portfolio_result(
        common_dates, no, nc, MONTHLY_AMOUNT, MONTHLY_AMOUNT, 999.0, NIFTY_TICK, False, "Vanilla SIP, NIFTY 50")}

    return results


if __name__ == "__main__":
    r = build()
    with open("results6.json", "w") as f:
        json.dump(r, f)
    for pk, variants in r["portfolios"].items():
        for vk, p in variants.items():
            print(f"[{pk}/{vk}] invested={p['total_invested']:.0f} value={p['final_value']:.0f} "
                  f"gain%={p['net_gain_pct']:.1f} xirr={p['xirr_pct']:.2f} mdd={p['max_drawdown_pct']:.1f} "
                  f"uw_days={p['longest_underwater_days']} n_contrib={p['num_contributions']} "
                  f"n_doubled={p.get('num_doubled_months')}")
    print("\nelevated episodes (strategy/frictionless):")
    for e in r["portfolios"]["strategy"]["frictionless"]["episodes"]:
        print(" ", e)

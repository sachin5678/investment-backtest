"""
Strategy 5: SIP + "buy the confirmed recovery" lump-sum, NIFTY Midcap 150.

Rule, as specified in chat:
  - Base: ₹1,000/month into midcap, same convention as the last report — the
    first trading day of each calendar month, filled at that day's own close.
  - Overlay: invest an extra ₹5,000 lump sum every time midcap (a) has fallen
    at least 15% below its all-time high at some point, AND (b) then
    recovers to close above THAT SAME previous all-time high (i.e. it sets a
    fresh record close). This is the mirror image of the last report's dip
    overlay — it buys confirmed strength after a real correction, not the
    dip itself. It's a reactive signal (the breakout close), so it fills at
    the NEXT day's open, same convention as every other reactive signal in
    this project.
  - After firing, the trigger disarms — a FRESH ≥15% drawdown from the new
    all-time high must occur before it can fire again. Without this, a
    choppy sideways market near a high could fire repeatedly; this keeps it
    to one lump sum per genuine correction-then-recovery cycle, mirroring the
    "requires a new ATH since last trigger" rule from the last report.
  - Compared against the same two vanilla-SIP benchmarks as before (₹1,000/
    month only, no overlay, in midcap and in NIFTY 50 respectively), AND
    against the last report's dip-buying overlay strategy, to see which
    timing idea — buying the dip vs. buying the confirmed recovery — did
    more with the same ₹1,000/month base.
  - Same two cost variants (frictionless / 0.05% commission + 1 tick
    slippage per contribution) for the midcap portfolios; same money-weighted
    XIRR and value-over-invested drawdown methodology as the last report.
"""
import json
import numpy as np
import pandas as pd

from backtest4 import (
    fetch, xirr, cumret_drawdown, series_to_points,
    COMMISSION_RATE, MONTHLY_AMOUNT, NIFTY_TICKER, MIDCAP_TICKER, NIFTY_TICK, MIDCAP_TICK, CURRENCY_SYMBOL,
)

RECOVERY_DRAWDOWN_PCT = 15.0
RECOVERY_LUMP_SUM = 5000.0


def run_breakout_recovery_sip(dates, opens, closes, monthly_amount, drawdown_pct, lump_sum, tick, cost_loaded):
    n = len(dates)
    ath = pd.Series(closes).cummax().to_numpy()
    months = np.array([(d.year, d.month) for d in dates])

    units = 0.0
    total_invested = 0.0
    contributions = []
    events = []
    confirmed_drawdown = False
    pending_fill = None   # signal_date, or None
    current_month = None

    value_curve = np.empty(n)
    invested_curve = np.empty(n)

    def buy(amount, price):
        fill_price = price + (tick if cost_loaded else 0.0)
        commission = COMMISSION_RATE * amount if cost_loaded else 0.0
        return (amount - commission) / fill_price

    for i in range(n):
        # 1) execute a pending breakout-recovery lump sum (signalled yesterday), at today's OPEN
        if pending_fill is not None:
            u = buy(lump_sum, opens[i])
            units += u
            total_invested += lump_sum
            contributions.append((dates[i], lump_sum, "recovery lump sum"))
            events.append({
                "signal_date": pending_fill, "fill_date": dates[i],
                "fill_price": float(opens[i] + (tick if cost_loaded else 0.0)),
            })
            pending_fill = None

        # 2) monthly SIP, first trading day of the month, AT today's close
        if current_month != tuple(months[i]):
            current_month = tuple(months[i])
            u = buy(monthly_amount, closes[i])
            units += u
            total_invested += monthly_amount
            contributions.append((dates[i], monthly_amount, "SIP"))

        value_curve[i] = units * closes[i]
        invested_curve[i] = total_invested

        # 3) state machine: arm on a >=15% drawdown, fire on the close that breaks back above that ATH
        dd_today = closes[i] / ath[i] - 1.0
        if not confirmed_drawdown and dd_today <= -drawdown_pct / 100.0:
            confirmed_drawdown = True
        if confirmed_drawdown and closes[i] >= ath[i] and pending_fill is None:
            pending_fill = dates[i]
            confirmed_drawdown = False

    value_series = pd.Series(value_curve, index=dates)
    invested_series = pd.Series(invested_curve, index=dates)
    return value_series, invested_series, contributions, events, units


def portfolio_result(dates, opens, closes, monthly_amount, drawdown_pct, lump_sum, tick, cost_loaded, label):
    value, invested, contributions, events, units = run_breakout_recovery_sip(
        dates, opens, closes, monthly_amount, drawdown_pct, lump_sum, tick, cost_loaded)
    mdd, peak_d, trough_d, uw_days = cumret_drawdown(value, invested)

    cashflows = [(d, -amt) for d, amt, _ in contributions]
    cashflows.append((dates[-1], float(value.iloc[-1])))
    rate = xirr(cashflows)

    total_invested = float(invested.iloc[-1])
    final_value = float(value.iloc[-1])
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
        "events": [
            {**e, "signal_date": e["signal_date"].strftime("%Y-%m-%d"), "fill_date": e["fill_date"].strftime("%Y-%m-%d")}
            for e in events
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
        "monthly_amount": MONTHLY_AMOUNT, "recovery_drawdown_pct": RECOVERY_DRAWDOWN_PCT, "recovery_lump_sum": RECOVERY_LUMP_SUM,
        "start_date": common_dates[0].strftime("%Y-%m-%d"), "end_date": common_dates[-1].strftime("%Y-%m-%d"),
        "portfolios": {},
    }

    mo, mc = midcap_a["Open"].to_numpy(), midcap_a["Close"].to_numpy()
    no, nc = nifty_a["Open"].to_numpy(), nifty_a["Close"].to_numpy()

    for cost_loaded, vk in [(False, "frictionless"), (True, "cost_loaded")]:
        results["portfolios"].setdefault("strategy", {})[vk] = portfolio_result(
            common_dates, mo, mc, MONTHLY_AMOUNT, RECOVERY_DRAWDOWN_PCT, RECOVERY_LUMP_SUM, MIDCAP_TICK, cost_loaded,
            "Strategy (SIP + confirmed-recovery lump sum, midcap)")
        results["portfolios"].setdefault("vanilla_midcap", {})[vk] = portfolio_result(
            common_dates, mo, mc, MONTHLY_AMOUNT, 999.0, 0.0, MIDCAP_TICK, cost_loaded, "Vanilla SIP, midcap")

    results["portfolios"]["vanilla_nifty"] = {"frictionless": portfolio_result(
        common_dates, no, nc, MONTHLY_AMOUNT, 999.0, 0.0, NIFTY_TICK, False, "Vanilla SIP, NIFTY 50")}

    return results


if __name__ == "__main__":
    r = build()
    with open("results5.json", "w") as f:
        json.dump(r, f)
    for pk, variants in r["portfolios"].items():
        for vk, p in variants.items():
            print(f"[{pk}/{vk}] invested={p['total_invested']:.0f} value={p['final_value']:.0f} "
                  f"gain%={p['net_gain_pct']:.1f} xirr={p['xirr_pct']:.2f} mdd={p['max_drawdown_pct']:.1f} "
                  f"uw_days={p['longest_underwater_days']} n_contrib={p['num_contributions']}")
    print("\nrecovery events (strategy/frictionless):")
    for e in r["portfolios"]["strategy"]["frictionless"]["events"]:
        print(" ", e)

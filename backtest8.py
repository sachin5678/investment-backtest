"""
SIP timing comparison: plain vanilla ₹1,000/month into midcap (no dip
overlay at all — this isolates the effect of WHICH calendar day the SIP
runs on, nothing else), executed on the 1st, 10th, 20th, and last day of
each month. Same instrument, same amount, same span, same cost variants and
XIRR/drawdown methodology as every other report in this series.

Day-of-month resolution (a real SIP can't run on a non-trading day):
  - "1st"  -> the FIRST trading day of the calendar month
  - "10th" -> the first trading day ON OR AFTER the 10th
  - "20th" -> the first trading day ON OR AFTER the 20th
  - "last" -> the LAST trading day of the calendar month
  Each contribution fills at that day's own close (a scheduled event, same
  convention as every other SIP date in this project).
"""
import json
import numpy as np
import pandas as pd

from backtest4 import fetch, xirr, cumret_drawdown, series_to_points, COMMISSION_RATE, MONTHLY_AMOUNT, \
    NIFTY_TICKER, MIDCAP_TICKER, MIDCAP_TICK, CURRENCY_SYMBOL

DAY_TARGETS = {"1st": 1, "10th": 10, "20th": 20, "last": None}   # None = last trading day of month


def pick_sip_dates(dates, target_day):
    """dates: DatetimeIndex of trading days. target_day: int day-of-month, or
    None for 'last trading day of month'. Returns the list of chosen dates,
    one per calendar month present."""
    df = pd.DataFrame({"date": dates})
    df["ym"] = [(d.year, d.month) for d in dates]
    chosen = []
    for ym, grp in df.groupby("ym", sort=False):
        days = grp["date"].tolist()
        if target_day is None:
            chosen.append(days[-1])
        else:
            candidates = [d for d in days if d.day >= target_day]
            chosen.append(candidates[0] if candidates else days[-1])
    return chosen


def run_vanilla_sip_on_dates(dates, closes, sip_dates, monthly_amount, tick, cost_loaded):
    sip_set = set(sip_dates)
    units = 0.0
    total_invested = 0.0
    contributions = []
    value_curve = np.empty(len(dates))
    invested_curve = np.empty(len(dates))

    for i, d in enumerate(dates):
        if d in sip_set:
            fill_price = closes[i] + (tick if cost_loaded else 0.0)
            commission = COMMISSION_RATE * monthly_amount if cost_loaded else 0.0
            units += (monthly_amount - commission) / fill_price
            total_invested += monthly_amount
            contributions.append((d, monthly_amount))
        value_curve[i] = units * closes[i]
        invested_curve[i] = total_invested

    return (pd.Series(value_curve, index=dates), pd.Series(invested_curve, index=dates), contributions, units)


def portfolio_result(dates, closes, target_day, monthly_amount, tick, cost_loaded, label):
    sip_dates = pick_sip_dates(dates, target_day)
    value, invested, contributions, units = run_vanilla_sip_on_dates(
        dates, closes, sip_dates, monthly_amount, tick, cost_loaded)
    mdd, peak_d, trough_d, uw_days = cumret_drawdown(value, invested)

    cashflows = [(d, -amt) for d, amt in contributions]
    cashflows.append((dates[-1], float(value.iloc[-1])))
    rate = xirr(cashflows)

    total_invested = float(invested.iloc[-1])
    final_value = float(value.iloc[-1])
    return {
        "label": label,
        "value_curve": series_to_points(value),
        "invested_curve": series_to_points(invested),
        "sip_dates": [d.strftime("%Y-%m-%d") for d in sip_dates],
        "total_invested": total_invested,
        "final_value": final_value,
        "net_gain": final_value - total_invested,
        "net_gain_pct": (final_value / total_invested - 1.0) * 100.0 if total_invested else None,
        "xirr_pct": rate,
        "num_contributions": len(contributions),
        "max_drawdown_pct": mdd, "max_drawdown_peak_date": peak_d, "max_drawdown_trough_date": trough_d,
        "longest_underwater_days": uw_days,
    }


def build():
    midcap = fetch(MIDCAP_TICKER)
    dates = midcap.index
    closes = midcap["Close"].to_numpy()

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "midcap_ticker": MIDCAP_TICKER, "currency_symbol": CURRENCY_SYMBOL, "monthly_amount": MONTHLY_AMOUNT,
        "start_date": dates[0].strftime("%Y-%m-%d"), "end_date": dates[-1].strftime("%Y-%m-%d"),
        "day_variants": {},
    }

    for label, target_day in DAY_TARGETS.items():
        results["day_variants"][label] = {}
        for cost_loaded, vk in [(False, "frictionless"), (True, "cost_loaded")]:
            results["day_variants"][label][vk] = portfolio_result(
                dates, closes, target_day, MONTHLY_AMOUNT, MIDCAP_TICK, cost_loaded,
                f"SIP on the {label} of the month")

    return results


if __name__ == "__main__":
    r = build()
    with open("results8.json", "w") as f:
        json.dump(r, f)
    for label, variants in r["day_variants"].items():
        p = variants["frictionless"]
        print(f"[{label}] invested={p['total_invested']:.0f} value={p['final_value']:.0f} "
              f"gain%={p['net_gain_pct']:.2f} xirr={p['xirr_pct']:.3f} mdd={p['max_drawdown_pct']:.2f} "
              f"n_contrib={p['num_contributions']}")
    ranked = sorted(r["day_variants"].items(), key=lambda kv: kv[1]["frictionless"]["xirr_pct"], reverse=True)
    print("\nRanked by XIRR (frictionless):")
    for label, variants in ranked:
        print(f"  {label}: XIRR {variants['frictionless']['xirr_pct']:.4f}%")

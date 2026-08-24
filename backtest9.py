"""
Vanilla SIP comparison: momentum ETF vs. midcap vs. NIFTY 50 — no dip overlay
of any kind, ₹1,000/month, first trading day of the month, filled at that
day's close. Same money-weighted XIRR / value-over-invested drawdown
methodology as the rest of this series.

Momentum proxy (confirmed in chat): HDFC Nifty200 Momentum 30 ETF
(HDFCMOMENT.NS) — the longest-history momentum-factor ETF available on
Yahoo Finance for the Indian market, but its history only starts 2023-10-17.
To keep the three-way comparison genuinely apples-to-apples, ALL THREE SIPs
(momentum, midcap, NIFTY) are run over that same, shorter common window —
not midcap's or NIFTY's full available history.
"""
import json
import numpy as np
import pandas as pd

from backtest4 import fetch, xirr, cumret_drawdown, series_to_points, COMMISSION_RATE, MONTHLY_AMOUNT, \
    NIFTY_TICKER, MIDCAP_TICKER, NIFTY_TICK, MIDCAP_TICK, CURRENCY_SYMBOL

MOMENTUM_TICKER = "HDFCMOMENT.NS"
MOMENTUM_TICK = 0.01


def run_vanilla_sip(dates, closes, monthly_amount, tick, cost_loaded):
    n = len(dates)
    months = np.array([(d.year, d.month) for d in dates])
    units = 0.0
    total_invested = 0.0
    contributions = []
    current_month = None
    value_curve = np.empty(n)
    invested_curve = np.empty(n)

    for i in range(n):
        if current_month != tuple(months[i]):
            current_month = tuple(months[i])
            fill_price = closes[i] + (tick if cost_loaded else 0.0)
            commission = COMMISSION_RATE * monthly_amount if cost_loaded else 0.0
            units += (monthly_amount - commission) / fill_price
            total_invested += monthly_amount
            contributions.append((dates[i], monthly_amount))
        value_curve[i] = units * closes[i]
        invested_curve[i] = total_invested

    return pd.Series(value_curve, index=dates), pd.Series(invested_curve, index=dates), contributions


def portfolio_result(dates, closes, monthly_amount, tick, cost_loaded, label):
    value, invested, contributions = run_vanilla_sip(dates, closes, monthly_amount, tick, cost_loaded)
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
        "total_invested": total_invested,
        "final_value": final_value,
        "net_gain": final_value - total_invested,
        "net_gain_pct": (final_value / total_invested - 1.0) * 100.0 if total_invested else None,
        "xirr_pct": rate,
        "num_contributions": len(contributions),
        "max_drawdown_pct": mdd, "max_drawdown_peak_date": peak_d, "max_drawdown_trough_date": trough_d,
        "longest_underwater_days": uw_days,
    }


def fetch_momentum_cleaned():
    """HDFCMOMENT.NS's first 3 listed days (2023-10-17 to 10-19) print prices
    around ~₹230-238 on volumes of ~1,500-1,900 shares. On 2023-10-20 the price
    drops ~90% to ~₹23-27 on ~79,000 shares and stays in that range ever after
    (mean ≈ ₹32, std ≈ ₹13 over the full history). That is a listing-day
    pricing artifact, not a real 90% crash — verified by hand against the raw
    Yahoo Finance data before building this report. Those 3 rows are dropped
    so the backtest reflects the ETF's actual traded history from 2023-10-20."""
    df = fetch(MOMENTUM_TICKER)
    cleaned = df.loc[df.index >= "2023-10-20"]
    assert len(df) - len(cleaned) == 3, "expected exactly 3 anomalous listing-day rows to be dropped"
    return cleaned


def build():
    nifty = fetch(NIFTY_TICKER)
    midcap = fetch(MIDCAP_TICKER)
    momentum = fetch_momentum_cleaned()

    start_date = momentum.index[0]   # the shortest-history instrument sets the common window
    common_dates = nifty.index[
        (nifty.index >= start_date) & (nifty.index.isin(midcap.index)) & (nifty.index.isin(momentum.index))
    ]

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "nifty_ticker": NIFTY_TICKER, "midcap_ticker": MIDCAP_TICKER, "momentum_ticker": MOMENTUM_TICKER,
        "currency_symbol": CURRENCY_SYMBOL, "monthly_amount": MONTHLY_AMOUNT,
        "start_date": common_dates[0].strftime("%Y-%m-%d"), "end_date": common_dates[-1].strftime("%Y-%m-%d"),
        "momentum_full_history_start": momentum.index[0].strftime("%Y-%m-%d"),
        "momentum_data_note": (
            "HDFCMOMENT.NS's first 3 listed trading days (2023-10-17 to 2023-10-19) print prices "
            "around ₹230-238 on very thin volume (~1,500-1,900 shares) — a listing-day pricing "
            "artifact, not a real price level. On 2023-10-20 the price drops to its real ~₹22-27 "
            "trading range on ~79,000 shares and stays there for the rest of its history. Those 3 "
            "rows were dropped before running this backtest; the analysis starts 2023-10-20."
        ),
        "portfolios": {},
    }

    series_map = {
        "momentum": (momentum.loc[common_dates, "Close"].to_numpy(), MOMENTUM_TICK),
        "midcap": (midcap.loc[common_dates, "Close"].to_numpy(), MIDCAP_TICK),
        "nifty": (nifty.loc[common_dates, "Close"].to_numpy(), NIFTY_TICK),
    }

    for key, (closes, tick) in series_map.items():
        results["portfolios"][key] = {}
        for cost_loaded, vk in [(False, "frictionless"), (True, "cost_loaded")]:
            results["portfolios"][key][vk] = portfolio_result(
                common_dates, closes, MONTHLY_AMOUNT, tick, cost_loaded, f"Vanilla SIP, {key}")

    return results


if __name__ == "__main__":
    r = build()
    with open("results9.json", "w") as f:
        json.dump(r, f)
    for pk, variants in r["portfolios"].items():
        p = variants["frictionless"]
        print(f"[{pk}] invested={p['total_invested']:.0f} value={p['final_value']:.0f} "
              f"gain%={p['net_gain_pct']:.2f} xirr={p['xirr_pct']:.3f} mdd={p['max_drawdown_pct']:.2f} "
              f"n_contrib={p['num_contributions']}")

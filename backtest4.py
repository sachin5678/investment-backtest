"""
Strategy 4: SIP + tiered dip lump-sums, NIFTY Midcap 150.

Rule, as specified in chat:
  - Base: invest ₹1,000 every month into midcap (the same MID150BEES.NS ETF
    used in the last report), on the FIRST trading day of each calendar
    month. This is a scheduled, known-in-advance contribution, so — same
    convention as the earlier reports' scheduled events — it is modelled as
    filling AT that day's own close, not the next open.
  - Overlay: whenever midcap's own close falls to 10% below its OWN
    all-time-high, invest an extra ₹5,000 lump sum; whenever it falls to 20%
    below its ATH, invest an extra ₹10,000 lump sum (in addition to the 10%
    tier, if that also fired on the way down). Both are reactive signals —
    observed at a day's close, filled at the NEXT day's open — same
    convention as every earlier report's reactive dip triggers.
  - ASSUMPTION (flagged prominently — not specified in chat): a tier only
    fires again after midcap has set a genuinely NEW all-time high since its
    last firing. Without this, testing the raw data showed midcap wobbling
    back and forth across the -10% line 23 separate times in two months in
    2019 alone — each would otherwise fire another ₹5,000, which is very
    unlikely to be the intent behind "when it's down 10%, invest a lump sum."
  - The account is always 100% invested — every contribution buys midcap
    units immediately; there is no idle cash pool (unlike reports 1-2).
  - Two benchmarks, contributing on the SAME monthly dates for a fair
    comparison:
      (a) Vanilla SIP: ₹1,000/month into midcap, no dip overlay at all —
          isolates whether the tactical lump-sum overlay adds value.
      (b) Vanilla SIP: ₹1,000/month into NIFTY 50 (raw index) instead of
          midcap — isolates the effect of the asset class.
  - Two cost variants for the strategy and the midcap vanilla SIP:
    frictionless, and cost-loaded (0.05% commission + 1 tick slippage on
    every single contribution — midcap tick ₹0.01, an ETF; NIFTY tick 0.05
    index points, a raw index). The NIFTY benchmark is frictionless only, to
    keep scope reasonable.
  - Because contributions arrive on different dates in different amounts,
    "return %" is not one clean number. This report reports: total invested,
    final value, net gain (both ₹ and simple %), and XIRR — the standard,
    money-weighted annualised return used for SIPs/cash-flow streams — so the
    strategy and both benchmarks are genuinely comparable despite investing
    different total amounts.
  - Max drawdown / longest-underwater are computed on portfolio VALUE divided
    by CUMULATIVE INVESTED (not raw ₹ value) — raw value drifts up simply
    because more money keeps being added, which would make "drawdown" on raw
    value meaningless for a growing contribution account. This ratio-based
    approach is disclosed as a deliberate methodology choice.
"""
import json
import numpy as np
import pandas as pd
import yfinance as yf

COMMISSION_RATE = 0.0005
MONTHLY_AMOUNT = 1000.0
DIP_TIERS = [(10.0, 5000.0), (20.0, 10000.0)]   # (drawdown-from-ATH %, lump sum ₹)
NIFTY_TICKER = "^NSEI"
MIDCAP_TICKER = "MID150BEES.NS"
NIFTY_TICK = 0.05
MIDCAP_TICK = 0.01
CURRENCY_SYMBOL = "₹"


def fetch(ticker):
    df = yf.download(ticker, period="max", auto_adjust=False, progress=False)
    df.columns = df.columns.droplevel(1)
    df = df[["Open", "High", "Low", "Close"]].dropna()
    df.index = pd.to_datetime(df.index)
    return df.sort_index()


def run_sip(dates, opens, closes, monthly_amount, dip_tiers, tick, cost_loaded):
    n = len(dates)
    ath = pd.Series(closes).cummax().to_numpy()
    months = np.array([(d.year, d.month) for d in dates])

    units = 0.0
    total_invested = 0.0
    contributions = []            # (date, amount, kind)
    tier_events = []              # (date_signal, date_fill, tier_pct, amount)
    last_ath_at_trigger = {pct: None for pct, _ in dip_tiers}
    pending_fills = []            # list of (tier_pct, amount, signal_date)
    current_month = None

    value_curve = np.empty(n)
    invested_curve = np.empty(n)

    def buy(amount, price):
        fill_price = price + (tick if cost_loaded else 0.0)
        commission = COMMISSION_RATE * amount if cost_loaded else 0.0
        return (amount - commission) / fill_price

    for i in range(n):
        # 1) execute any dip lump-sum signalled yesterday, at today's OPEN
        still_pending = []
        for tier_pct, amount, signal_date in pending_fills:
            u = buy(amount, opens[i])
            units += u
            total_invested += amount
            contributions.append((dates[i], amount, f"dip -{tier_pct:.0f}%"))
            tier_events.append({
                "signal_date": signal_date, "fill_date": dates[i], "tier_pct": tier_pct,
                "amount": amount, "fill_price": float(opens[i] + (tick if cost_loaded else 0.0)),
            })
        pending_fills = []

        # 2) the monthly SIP, on the first trading day of a new calendar month, AT today's close
        if current_month != tuple(months[i]):
            current_month = tuple(months[i])
            u = buy(monthly_amount, closes[i])
            units += u
            total_invested += monthly_amount
            contributions.append((dates[i], monthly_amount, "SIP"))

        value_curve[i] = units * closes[i]
        invested_curve[i] = total_invested

        # 3) check today's close against each dip tier (fills tomorrow's open)
        for tier_pct, amount in dip_tiers:
            threshold_price = ath[i] * (1 - tier_pct / 100.0)
            if closes[i] <= threshold_price and (last_ath_at_trigger[tier_pct] is None or ath[i] > last_ath_at_trigger[tier_pct]):
                pending_fills.append((tier_pct, amount, dates[i]))
                last_ath_at_trigger[tier_pct] = ath[i]

    value_series = pd.Series(value_curve, index=dates)
    invested_series = pd.Series(invested_curve, index=dates)
    return value_series, invested_series, contributions, tier_events, units


def xirr(cashflows):
    """cashflows: list of (date, amount) — investments negative, final value positive.
    Solve NPV(rate)=0 by bisection. Returns annualised rate as %, or None."""
    t0 = cashflows[0][0]

    def npv(rate):
        return sum(cf / (1 + rate) ** ((d - t0).days / 365.0) for d, cf in cashflows)

    lo, hi = -0.999, 20.0
    f_lo, f_hi = npv(lo), npv(hi)
    if f_lo * f_hi > 0:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        f_mid = npv(mid)
        if abs(f_mid) < 1e-6:
            return mid * 100.0
        if f_lo * f_mid < 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return ((lo + hi) / 2) * 100.0


def cumret_drawdown(value, invested):
    ratio = (value / invested).replace([np.inf, -np.inf], np.nan).dropna()
    running_max = ratio.cummax()
    dd = (ratio - running_max) / running_max
    trough_idx = dd.idxmin()
    mdd = float(dd.min() * 100.0)
    peak_idx = ratio.loc[:trough_idx].idxmax()

    underwater = ratio < running_max
    longest = 0
    start = None
    dts = ratio.index
    for i, uw in enumerate(underwater):
        if uw and start is None:
            start = dts[i - 1] if i > 0 else dts[i]
        if not uw and start is not None:
            span = (dts[i] - start).days
            longest = max(longest, span)
            start = None
    if start is not None:
        longest = max(longest, (dts[-1] - start).days)
    return mdd, peak_idx.strftime("%Y-%m-%d"), trough_idx.strftime("%Y-%m-%d"), int(longest)


def series_to_points(s, max_points=1500):
    if len(s) > max_points:
        idx = np.linspace(0, len(s) - 1, max_points).round().astype(int)
        idx = np.unique(idx)
        s = s.iloc[idx]
    return [[d.strftime("%Y-%m-%d"), float(v)] for d, v in s.items()]


def portfolio_result(dates, opens, closes, monthly_amount, dip_tiers, tick, cost_loaded, label):
    value, invested, contributions, tier_events, units = run_sip(
        dates, opens, closes, monthly_amount, dip_tiers, tick, cost_loaded)
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
        "num_sip_contributions": sum(1 for _, _, k in contributions if k == "SIP"),
        "tier_events": [
            {**e, "signal_date": e["signal_date"].strftime("%Y-%m-%d"), "fill_date": e["fill_date"].strftime("%Y-%m-%d")}
            for e in tier_events
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
        "monthly_amount": MONTHLY_AMOUNT, "dip_tiers": DIP_TIERS,
        "start_date": common_dates[0].strftime("%Y-%m-%d"), "end_date": common_dates[-1].strftime("%Y-%m-%d"),
        "portfolios": {},
    }

    mo, mc = midcap_a["Open"].to_numpy(), midcap_a["Close"].to_numpy()
    no, nc = nifty_a["Open"].to_numpy(), nifty_a["Close"].to_numpy()

    for cost_loaded, vk in [(False, "frictionless"), (True, "cost_loaded")]:
        results["portfolios"].setdefault("strategy", {})[vk] = portfolio_result(
            common_dates, mo, mc, MONTHLY_AMOUNT, DIP_TIERS, MIDCAP_TICK, cost_loaded, "Strategy (SIP + dip lump-sums, midcap)")
        results["portfolios"].setdefault("vanilla_midcap", {})[vk] = portfolio_result(
            common_dates, mo, mc, MONTHLY_AMOUNT, [], MIDCAP_TICK, cost_loaded, "Vanilla SIP, midcap")

    results["portfolios"]["vanilla_nifty"] = {"frictionless": portfolio_result(
        common_dates, no, nc, MONTHLY_AMOUNT, [], NIFTY_TICK, False, "Vanilla SIP, NIFTY 50")}

    return results


if __name__ == "__main__":
    r = build()
    with open("results4.json", "w") as f:
        json.dump(r, f)
    for pk, variants in r["portfolios"].items():
        for vk, p in variants.items():
            print(f"[{pk}/{vk}] invested={p['total_invested']:.0f} value={p['final_value']:.0f} "
                  f"gain%={p['net_gain_pct']:.1f} xirr={p['xirr_pct']:.2f} mdd={p['max_drawdown_pct']:.1f} "
                  f"uw_days={p['longest_underwater_days']} n_contrib={p['num_contributions']}")
    print("\ntier events (strategy/frictionless):")
    for e in r["portfolios"]["strategy"]["frictionless"]["tier_events"]:
        print(" ", e)

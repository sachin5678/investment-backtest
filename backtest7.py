"""
Strategy 6b: same as strategy 6 (SIP doubles during a drawdown), but with the
arming threshold lowered from 15% to 10% — everything else identical (same
₹1,000/₹2,000 amounts, same disarm-on-new-ATH hysteresis, same benchmarks,
same methodology). See backtest6.py for the full rule description.
"""
import json
import pandas as pd

from backtest4 import fetch, NIFTY_TICKER, MIDCAP_TICKER, NIFTY_TICK, MIDCAP_TICK, CURRENCY_SYMBOL, MONTHLY_AMOUNT
from backtest6 import portfolio_result, DOUBLED_AMOUNT

DRAWDOWN_TRIGGER_PCT = 10.0


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
            "Strategy (SIP doubles during >=10% drawdown, midcap)")
        results["portfolios"].setdefault("vanilla_midcap", {})[vk] = portfolio_result(
            common_dates, mo, mc, MONTHLY_AMOUNT, MONTHLY_AMOUNT, 999.0, MIDCAP_TICK, cost_loaded, "Vanilla SIP, midcap")

    results["portfolios"]["vanilla_nifty"] = {"frictionless": portfolio_result(
        common_dates, no, nc, MONTHLY_AMOUNT, MONTHLY_AMOUNT, 999.0, NIFTY_TICK, False, "Vanilla SIP, NIFTY 50")}

    return results


if __name__ == "__main__":
    r = build()
    with open("results7.json", "w") as f:
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

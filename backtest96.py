"""Report 96 — the Money Lab.

The "Money" tab of momentumscore.in's builder: how the money goes in and
how positions are sized.

  1. hero — reinvest everything (compounding on)
  2. no compounding — a fixed ₹10,000 per position (₹1L / 10 slots); profits
     accumulate as cash instead of sizing up new positions
  3. SIP ₹25,000/month — added on the first trading day of each month into
     the current holdings (proportional top-up, like MomentumScore's)
  4. SIP ₹25,000/month + 10%/yr step-up
  5. buy the dip — ₹25,000 extra when NIFTY RSI(14) < 30, at most once a
     month, into the holdings that day
  6. only buy what is going up + sell when it turns negative (the Money
     tab's momentum-discipline pair, as buy/sell-when conditions)
  7. SIP + step-up + dip — the full money stack

SIP/dip contributions are tracked per variant (contributed_total) and the
curve's final value (final_value) is the number to compare them against —
CAGR on a SIP curve mixes contribution timing with returns by construction.

Writes results95.json (webapp report id 96).
"""
import ms_builder

LAB_KEY = "money"
LAB_TITLE = "Money Lab — compounding, SIP, dip top-ups, momentum discipline"
OUT = "results95.json"

CONFIGS = [
    ("hero — reinvest everything", {}),
    ("no compounding — fixed ₹10,000 per position", {"compounding": "fixed_per_position"}),
    ("SIP ₹25,000/month", {"sip": {"monthly": 25_000, "step_up_pct": 0}}),
    ("SIP ₹25,000/month + 10%/yr step-up", {"sip": {"monthly": 25_000, "step_up_pct": 10}}),
    ("buy the dip — ₹25,000 when NIFTY RSI(14) < 30",
     {"dip": {"amount": 25_000, "rsi_period": 14, "rsi_below": 30}}),
    ("only buy what is going up + sell when it turns negative",
     {"conditions": [{"when": "buy", "indicator": "ret_6m", "op": "above", "value": 0},
                     {"when": "sell", "indicator": "ret_6m", "op": "below", "value": 0}]}),
    ("SIP + step-up + dip — the full money stack",
     {"sip": {"monthly": 25_000, "step_up_pct": 10},
      "dip": {"amount": 25_000, "rsi_period": 14, "rsi_below": 30}}),
]

NOTES = [
    "All variants share report 48/93's skeleton: Midcap150 universe, top-10 risk-adjusted 6m/12m momentum, exit rank 52 with hysteresis, carried stocks keep their original shares, 0.1%/side costs, gold hedge on the NIFTY 200-EMA regime.",
    "Fixed mode: every new position gets exactly ₹10,000 (₹1,00,000 / 10); sale proceeds accumulate as cash and only park in gold during bear markets — profits never size up new positions.",
    "SIP: on the first trading day of each month the amount is added into the current holdings proportionally to their value (or into the park asset when the regime is off); the step-up compounds yearly from the window's first year.",
    "Buy the dip: checked at every close; when NIFTY 50 RSI(14) is below 30 the amount is added into the holdings that day, at most once per calendar month — MomentumScore's own rule.",
    "For SIP/dip variants compare final_value against contributed_total (both in the variant data); the equity curve and CAGR include the contribution timing by construction.",
    "Health, halves and the tax layer are computed per variant with the same ms_port code report 93 uses; after-tax curves follow report 93's conventions (indicative, not advice).",
]


def main():
    ms_builder.run_lab(LAB_KEY, LAB_TITLE, CONFIGS, OUT, NOTES)


if __name__ == "__main__":
    main()

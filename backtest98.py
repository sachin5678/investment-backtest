"""Report 98 — the Max Strategy.

Every winning knob from labs 94–97 stacked into one strategy, then put
through the full honesty battery: both-halves + tax + health (automatic per
variant), whole-units realism, two heavier cost assumptions, the money
plan on top, and — for the two candidate stacks — the same six rebalance
calendars report 92 used, to rule out date luck.

What won in each lab:
  * 94 Protect    — nothing beat the hero's own layer (daily 200-EMA on
                    NIFTY 50, 100% gold park). Left untouched.
  * 95 Conditions — keep-if 6m return > 0: +0.1pp CAGR and a shallower
                    drawdown; every heavier gate ranged from no-op to
                    destructive.
  * 96 Money      — compounding stays ON (fixed sizing: 15.6% CAGR);
                    SIP/dip are deployment plans, not alpha (judged on
                    money-multiple, shipped as the full-plan row here).
  * 97 Pick       — exit rank 30: +0.4pp CAGR at the same drawdown;
                    entry-rank gates and sector caps were destructive,
                    daily-breach was worse than the review check.

The two candidate stacks:
  A = keep-if 6m > 0 + exit rank 30
  B = A + buy-only-if 6m > 0 (the full momentum-discipline stack)

Writes results97.json (webapp report id 98).
"""
import ms_builder

LAB_KEY = "max"
LAB_TITLE = "Max Strategy — every winning knob stacked, stress-tested, date-luck checked"
OUT = "results97.json"

KEEP_RISING = {"when": "keep", "indicator": "ret_6m", "op": "above", "value": 0}
BUY_RISING = {"when": "buy", "indicator": "ret_6m", "op": "above", "value": 0}

STACK_A = {"conditions": [KEEP_RISING], "exit_rank": 30}
STACK_B = {"conditions": [BUY_RISING, KEEP_RISING], "exit_rank": 30}

CALENDARS = [
    ("Jul/Jan", (7, 1)),
    ("Aug/Feb", (8, 2)),
    ("Sep/Mar", (9, 3)),
    ("Oct/Apr", (10, 4)),
    ("Nov/May", (11, 5)),
]

CONFIGS = [
    # --- the stack candidates, one knob at a time, then combined ---
    ("hero — report 93 exactly", {}),
    ("hero + keep-if 6m > 0", {"conditions": [KEEP_RISING]}),
    ("hero + exit rank 30", {"exit_rank": 30}),
    ("max stack A — keep-if 6m > 0 + exit rank 30 (Jun/Dec)", STACK_A),
    ("max stack B — A + buy-only-if 6m > 0 (Jun/Dec)", STACK_B),
    # --- honesty battery on stack A ---
    ("stack A — whole units only", dict(STACK_A, whole_units=True)),
    ("stack A — friction 0.3%/side", dict(STACK_A, cost_pct_per_side=0.002, slippage_pct_per_side=0.001)),
    ("stack A — friction 0.5%/side", dict(STACK_A, cost_pct_per_side=0.003, slippage_pct_per_side=0.002)),
    ("stack A + SIP ₹25k/mo · 10% step-up · dip ₹25k", dict(
        STACK_A, sip={"monthly": 25_000, "step_up_pct": 10},
        dip={"amount": 25_000, "rsi_period": 14, "rsi_below": 30})),
]

# --- date-luck: both stacks on the same six calendars report 92 used ---
for label, months in CALENDARS:
    CONFIGS.append((f"stack A — calendar {label}", dict(STACK_A, rebalance_months=months)))
for label, months in CALENDARS:
    CONFIGS.append((f"stack B — calendar {label}", dict(STACK_B, rebalance_months=months)))

NOTES = [
    "Stack A = keep-if 6m return > 0 (a holder is sold at the review that finds its 6-month return negative) + exit rank 30 (a holder is also sold when its fit rank falls below 30 of the ~150 eligible names). Stack B adds buy-only-if 6m > 0 — new buys must be rising.",
    "The protect layer is report 48/93's untouched winner: daily NIFTY-50 200-EMA check, 100% GOLDBEES park, 0.1%/side on every leg. Lab 94 found nothing that beat it.",
    "The Jun/Dec rows of stack A and stack B are the same configuration as their headline rows — they are repeated inside the date-luck grids so each stack's six-calendar spread reads on its own.",
    "Date-luck calendars are month-offset pairs (Jul/Jan, Aug/Feb, Sep/Mar, Oct/Apr, Nov/May) at month-end, the same six report 92 tested on the gold-strength guard.",
    "Friction rows add slippage on top of the base cost — 0.3% and 0.5% per side total. Whole-units floors every buy to integer shares (leftover rupees stay in cash), the honest real-broker version.",
    "The SIP + dip row deploys the winning strategy on the winning money plan (₹25,000/month with a 10%/yr step-up, plus ₹25,000 on every close where NIFTY 50 RSI(14) < 30, at most once a month) — judge it by final value vs money contributed, both in its variant data.",
    "Health, halves and the tax layer are computed per variant with the same ms_port code report 93 uses; after-tax curves follow report 93's conventions (indicative, not advice).",
]


def main():
    ms_builder.run_lab(LAB_KEY, LAB_TITLE, CONFIGS, OUT, NOTES)


if __name__ == "__main__":
    main()

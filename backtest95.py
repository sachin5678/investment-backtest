"""Report 95 — the Conditions Lab.

The "Conditions" tab of momentumscore.in's builder: keep-if / buy-only-if /
sell-when rules over per-stock indicators, each tested alone on top of the
report 48/93 hero, then stacked.

  1. hero — no conditions
  2. buy only what is rising (6m return > 0)
  3. skip the wildest (6m swings < 45%)
  4. easy to trade (6m avg turnover ≥ ₹5 Cr/day)
  5. no penny stocks (price ≥ ₹50)
  6. above the 200-day EMA
  7. Supertrend (10, 3) green
  8. RSI above 50
  9. golden cross (50-EMA > 200-EMA)
 10. near all-time high (within 10%)
 11. calm market (India VIX < 20)
 12. quality gate — rising + not wild + tradable + above 200-EMA + ≥ ₹50
 13. keep-if: 6m return > 0 (a holder is sold at the review that finds it
     negative — MomentumScore's "keep if" semantics)
 14. sell-when: 6m return turns negative (sold THAT day, slot waits in cash)
 15. quality gate + sell-when Supertrend red

Semantics (MomentumScore's own): buy-only-if gates new buys — an open slot
whose best candidate fails waits in CASH, it is not given to the next name;
keep-if is checked at the Jun/Dec reviews; sell-when is checked every day
and the slot waits in cash until the next review. A condition that cannot
be evaluated (no data) never passes and never triggers.

Writes results94.json (webapp report id 95).
"""
import ms_builder

LAB_KEY = "conditions"
LAB_TITLE = "Conditions Lab — keep-if / buy-only-if / sell-when rules, one at a time"
OUT = "results94.json"

QUALITY_GATE = [
    {"when": "buy", "indicator": "ret_6m", "op": "above", "value": 0},
    {"when": "buy", "indicator": "swings_6m", "op": "below", "value": 45},
    {"when": "buy", "indicator": "turnover", "op": "above", "value": 50_000_000},
    {"when": "buy", "indicator": "above_ema200"},
    {"when": "buy", "indicator": "price", "op": "above", "value": 50},
]

CONFIGS = [
    ("hero — no conditions", {}),
    ("buy only what is rising (6m return > 0)",
     {"conditions": [{"when": "buy", "indicator": "ret_6m", "op": "above", "value": 0}]}),
    ("skip the wildest (6m swings < 45%)",
     {"conditions": [{"when": "buy", "indicator": "swings_6m", "op": "below", "value": 45}]}),
    ("easy to trade (turnover ≥ ₹5 Cr/day)",
     {"conditions": [{"when": "buy", "indicator": "turnover", "op": "above", "value": 50_000_000}]}),
    ("no penny stocks (price ≥ ₹50)",
     {"conditions": [{"when": "buy", "indicator": "price", "op": "above", "value": 50}]}),
    ("above the 200-day EMA",
     {"conditions": [{"when": "buy", "indicator": "above_ema200"}]}),
    ("Supertrend (10, 3) green",
     {"conditions": [{"when": "buy", "indicator": "supertrend_green"}]}),
    ("RSI above 50",
     {"conditions": [{"when": "buy", "indicator": "rsi", "op": "above", "value": 50}]}),
    ("golden cross (50-EMA > 200-EMA)",
     {"conditions": [{"when": "buy", "indicator": "golden_cross"}]}),
    ("near all-time high (within 10%)",
     {"conditions": [{"when": "buy", "indicator": "from_ath", "op": "above", "value": -10}]}),
    ("calm market (India VIX < 20)",
     {"conditions": [{"when": "buy", "indicator": "vix", "op": "below", "value": 20}]}),
    ("quality gate — rising + not wild + tradable + above 200-EMA + ≥ ₹50",
     {"conditions": QUALITY_GATE}),
    ("keep-if: 6m return > 0 (sold at the review that finds it negative)",
     {"conditions": [{"when": "keep", "indicator": "ret_6m", "op": "above", "value": 0}]}),
    ("sell-when: 6m return turns negative (sold that day)",
     {"conditions": [{"when": "sell", "indicator": "ret_6m", "op": "below", "value": 0}]}),
    ("quality gate + sell-when Supertrend red",
     {"conditions": QUALITY_GATE + [{"when": "sell", "indicator": "supertrend_red"}]}),
]

NOTES = [
    "All variants share report 48/93's skeleton: Midcap150 universe, top-10 risk-adjusted 6m/12m momentum, exit rank 52 with hysteresis, carried stocks keep their original shares, 0.1%/side costs, gold hedge on the NIFTY 200-EMA regime.",
    "Slot semantics are MomentumScore's: money is divided over the open slots; a slot whose best candidate fails the buy conditions waits in cash until a name passes — it is never redistributed to other slots.",
    "swings_6m = annualized standard deviation of daily returns over the last 126 trading days (the documented proxy for MomentumScore's '6-month swings' — its exact definition is unpublished).",
    "turnover = average daily Close × Volume over 126 trading days; ₹5 Cr = 50,000,000.",
    "sell-when rules are evaluated at every close: the holding is sold that day at the close (0.1% cost) and the slot waits in cash until the next Jun/Dec review.",
    "keep-if rules are evaluated at the Jun/Dec reviews, alongside the exit rank: a holder that fails either is sold at that review.",
    "India VIX on Yahoo starts in 2008 (MomentumScore shows it from ~2014); the VIX < 20 gate is simply not triggered on dates without data.",
    "Health, halves and the tax layer are computed per variant with the same ms_port code report 93 uses; after-tax curves follow report 93's conventions (indicative, not advice).",
]


def main():
    ms_builder.run_lab(LAB_KEY, LAB_TITLE, CONFIGS, OUT, NOTES)


if __name__ == "__main__":
    main()

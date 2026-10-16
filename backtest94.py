"""Report 94 — the Protect Lab.

Report 48/93's market-timing layer (NIFTY 200-EMA regime → GOLDBEES hedge),
varied one knob at a time — the "Protect" tab of momentumscore.in's builder:

  1. hero                    — report 93 exactly (daily checks, gold 100%)
  2. trend checked only on review days
  3. bear action: cash (no gold park)
  4. bear action: sell half, re-top-up on re-entry
  5. park: 50% gold + 25% silver + 25% cash
  6. VIX above 20 also means risk-off
  7. trend index: NIFTY 500
  8. signal: Supertrend (10, 3) on NIFTY 50
  9. 2-of-3 ensemble: EMA + Supertrend + VIX
 10. VIX-only regime (no EMA)
 11. signal: Supertrend (10, 3) on NIFTY 500

Everything else is identical to the hero in every row — same universe, same
ranking, same exit rank 52, same 0.1%/side costs — so each row answers one
question: which piece of the market-timing layer is actually earning its keep?

Writes results93.json (webapp report id 94).
"""
import ms_builder

LAB_KEY = "protect"
LAB_TITLE = "Protect Lab — report 48's market-timing layer, varied"
OUT = "results93.json"

CONFIGS = [
    ("hero — daily checks · gold 100%", {}),
    ("trend checked only on review days", {"regime": {"check": "at_review"}}),
    ("bear action: cash (no gold park)", {"regime": {"park": []}}),
    ("bear action: sell half · re-top-up on re-entry", {"regime": {"action": "half"}}),
    ("park: 50% gold + 25% silver + 25% cash",
     {"regime": {"park": [{"symbol": "GOLDBEES", "pct": 50}, {"symbol": "SILVERBEES", "pct": 25}]}}),
    ("VIX above 20 also means risk-off", {"regime": {"vix_filter": {"above": 20}}}),
    ("trend index: NIFTY 500", {"regime": {"index": "nifty500"}}),
    ("signal: Supertrend (10, 3) on NIFTY 50", {"regime": {"signal": "supertrend"}}),
    ("2-of-3 ensemble: EMA + Supertrend + VIX", {"regime": {"signal": "ensemble_2of3"}}),
    ("VIX-only regime (no EMA)", {"regime": {"signal": "none", "vix_filter": {"above": 20}}}),
    ("signal: Supertrend (10, 3) on NIFTY 500",
     {"regime": {"signal": "supertrend", "index": "nifty500"}}),
]

NOTES = [
    "All variants share report 48/93's skeleton: Midcap150 universe, top-10 risk-adjusted 6m/12m momentum, exit rank 52 with hysteresis, carried stocks keep their original shares, 0.1%/side costs on every leg including the hedge, rupee figures scaled from a Rs 1,00,000 start.",
    "Every variant is report 93's engine with ONE knob changed; the hero row reproduces report 93 exactly (verified by check_builder_regression.py).",
    "'trend checked only on review days' evaluates the same daily signal but acts on it only at the Jun/Dec reviews — the whipsaw question.",
    "'sell half' de-risks 50% of every position in a bear market and tops the positions back up on re-entry; freed cash still parks per the park rule.",
    "Park baskets: freed cash is split by the given percentages; a symbol without a price that day (SILVERBEES before Feb 2022) leaves its share in cash until it trades — MomentumScore's own rule.",
    "India VIX history on Yahoo starts in 2008 (MomentumScore shows it from ~2014); the 2-of-3 ensemble treats VIX > 20 as its risk-off vote.",
    "Health, halves and the tax layer are computed per variant with the same ms_port code report 93 uses; the after-tax curve follows report 93's conventions (indicative, not advice).",
]


def main():
    ms_builder.run_lab(LAB_KEY, LAB_TITLE, CONFIGS, OUT, NOTES)


if __name__ == "__main__":
    main()

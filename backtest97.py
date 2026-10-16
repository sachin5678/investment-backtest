"""Report 97 — the Pick & Rebalance Lab.

The "Pick & Rebalance" tab of momentumscore.in's builder: how many names,
when a holder is sold, when a new one may be bought, sector caps, share
granularity and friction.

  1. hero — exit rank 52, checked at reviews, 0.1%/side
  2. exit rank 20 — much tighter leash
  3. exit rank 30
  4. exit rank 100 — loose leash
  5. exit rank 10 — sell as soon as a holder slips out of the top 10
  6. exit rank 52 checked DAILY — sold the day the rank breaches, slot waits
     in cash until the next review (MomentumScore's "sell when it reaches
     this rank" checkbox)
  7. entry rank — buy only from the top 5 (hold 10); an open slot waits in
     cash until something new reaches the top 5
  8. max 3 stocks per sector
  9. max 5 stocks per sector
 10. whole units only — shares floored to integers, leftover stays cash
 11. friction 0.3%/side (0.2% cost + 0.1% slippage)
 12. friction 0.5%/side (0.3% cost + 0.2% slippage)

Sectors are Yahoo Finance's present-day classification for the NIFTY 500
(sectors_raw.json, the same file report 18 used) applied to the full
history — a documented survivorship caveat, not a claim about sector
membership in 2011.

Writes results96.json (webapp report id 97).
"""
import ms_builder

LAB_KEY = "pick"
LAB_TITLE = "Pick & Rebalance Lab — exit rank, entry rank, sectors, units, friction"
OUT = "results96.json"

CONFIGS = [
    ("hero — exit rank 52 · 0.1%/side", {}),
    ("exit rank 20", {"exit_rank": 20}),
    ("exit rank 30", {"exit_rank": 30}),
    ("exit rank 100", {"exit_rank": 100}),
    ("exit rank 10 — out as soon as it leaves the top 10", {"exit_rank": 10}),
    ("exit rank 52 checked daily (sell on breach)", {"exit_mode": "on_breach"}),
    ("entry rank — buy only from the top 5", {"entry_rank": 5}),
    ("max 3 stocks per sector", {"max_per_sector": 3}),
    ("max 5 stocks per sector", {"max_per_sector": 5}),
    ("whole units only", {"whole_units": True}),
    ("friction 0.3%/side", {"cost_pct_per_side": 0.002, "slippage_pct_per_side": 0.001}),
    ("friction 0.5%/side", {"cost_pct_per_side": 0.003, "slippage_pct_per_side": 0.002}),
]

NOTES = [
    "All variants share report 48/93's skeleton: Midcap150 universe, top-10 risk-adjusted 6m/12m momentum, carried stocks keep their original shares, gold hedge on the NIFTY 200-EMA regime, ₹1,00,000 start.",
    "Exit rank N: a holder is sold at a review only when its fit rank falls below N of the ~150 eligible names; the freed slot is refilled with the best-ranked non-held name.",
    "Daily-breach mode: the same rank check runs at every close — a holder is sold THAT day (0.1% cost) and the slot waits in cash until the next Jun/Dec review.",
    "Entry rank K: new buys may only come from the top K ranks; an open slot waits in cash until a name reaches the top K — never redistributed to other slots.",
    "Sector caps use Yahoo Finance's present-day sector for each NIFTY 500 name (sectors_raw.json, fetched once for report 18) applied backwards; a name without a sector is uncapped.",
    "Whole units: share quantities are floored to integers on every buy and the leftover rupee amount stays in cash.",
    "Friction variants add slippage on top of the base 0.1% cost — 0.3% and 0.5% per side total, the honest stress test for a 2-rebalance-a-year system.",
    "Health, halves and the tax layer are computed per variant with the same ms_port code report 93 uses; after-tax curves follow report 93's conventions (indicative, not advice).",
]


def main():
    ms_builder.run_lab(LAB_KEY, LAB_TITLE, CONFIGS, OUT, NOTES)


if __name__ == "__main__":
    main()

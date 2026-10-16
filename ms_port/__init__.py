"""ms_port — a port of MomentumScore-style review features onto this
project's own backtest artifacts.

Every module here works on the plain JSON shapes this repo already
produces (equity_curve points as [[date, value], ...], trade logs with
entry/exit dates and prices) — no pandas, no external services, fully
unit-tested under ms_port/tests.

Feature map (see PORTED_FEATURES.md at the repo root for the full
MomentumScore ↔ this-repo mapping):

  health.py       — the 10-check "Health score" card (score / 100 as the
                    share of target ranges met; trade-based checks only
                    when a trade log is available)
  robustness.py   — "Is this the rules, or luck?" — both-halves vs
                    benchmark, plus an N-variants "date luck" spread
  tax.py          — capital-gains estimate: 15%/10% → 20%/12.5% régime
                    switch on 23 Jul 2024, ₹1.25L LTCG exemption, 4%
                    cess, loss set-off/carry-forward, s.112A
                    grandfathering via a 31-Jan-2025 FMV map, and an
                    after-tax growth curve
  fit.py          — "fit" 0–100 percentile ranks + Δ vs the previous
                    review (MomentumScore's fit-in → fit-out columns)
  formula.py      — the ret(6m)/vol(6m) style formula mini-language,
                    compiled to a callable over a close-price series
"""

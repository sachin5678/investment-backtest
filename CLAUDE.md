# Project rules

## 1. Every new strategy variant gets added to the master comparison table

`master_comparison.json`/`master_comparison.html` (built by
`build_master_comparison.py` + `build_master_comparison_html.py`) and the
webapp's `/compare` route (`webapp/src/pages/Comparison.jsx`) are meant to
be a complete, always-current leaderboard of every momentum-strategy
variant tested in this project — not a one-time snapshot.

**Whenever a new numbered report is added to the momentum-strategy family**
(anything comparable to reports 11/12, 33-72: front-loaded/inverse-vol
weighting, regime filters, hedges, trend filters, stop-losses, exposure
scaling, core-satellite splits, or any future idea in that same family):

1. Add a row for it in `build_master_comparison.py` — call the same
   already-tested `build_*` function the report itself uses (never
   re-derive the math), via `add_row(universe, category, label, report_id,
   variant_series, bench_series, common_idx)`. If it's a genuinely new
   *kind* of idea (not a variant of an existing category), add a new
   `category` string and give it an entry in both `CAT_COLOR`
   (`build_master_comparison_html.py`) and `CATEGORY_COLOR`
   (`Comparison.jsx`) — both files' category list must stay in sync.
2. Regenerate `master_comparison.json` (`py -3 build_master_comparison.py`)
   and `master_comparison.html` (`py -3 build_master_comparison_html.py`),
   then copy the JSON into `webapp/public/data/master_comparison.json`.
3. Cross-check the new row's CAGR/max-drawdown against the report's own
   already-published numbers before trusting it (the aggregator recomputes
   from full daily series for correct Sharpe/Sortino — see the docstring at
   the top of `build_master_comparison.py` for why — so a mismatch means a
   bug, not a rounding difference).

Non-momentum reports (breakout, SIP, dip-buying, sector rotation, RSI,
gold/silver rotation — reports outside the 11/12/33-72 family) use
different metrics (XIRR, not CAGR) and are intentionally excluded from
this table.

## 2. The master comparison table is locked behind login

Both `/compare` (`Comparison.jsx`) and, by convention, any future
comparison/leaderboard-style page must be gated behind
`useAuth().isLoggedIn`, the same soft client-side gate used for premium
reports (`ReportPage.jsx` + `LockedReportGate.jsx` + `LoginModal.jsx`,
credentials in `webapp/src/context/AuthContext.jsx`). When logged out, show
`<LockedReportGate />` and skip the data fetch entirely (don't even fetch
`master_comparison.json` until `isLoggedIn` is true) — mirroring how a
premium report's own JSON is never fetched while locked.

This is the same *soft* gate as everywhere else in this project — it does
not hide the underlying static JSON/HTML files from anyone who looks
directly, it only controls what the app's UI shows. The static
`master_comparison.html` / `dashboard.html` files are NOT gated (consistent
with every other static report in this project being open by design); only
the webapp route is.

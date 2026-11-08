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

## 3. Backtest execution timing: signal day close, trade next morning's open

For every NEW backtest (and any rebuilt one), a signal is never executed at
the same close that produced it. Whenever the signal fires on day T —
a scheduled rebalance day, or a regime/gold/cash switch day (NIFTY 50
crossing its 200-EMA, the gold-strength guard changing state, any exit or
re-entry) — the trades are filled at the **next trading day's OPEN** (T+1
morning), at that day's open price, for the stock legs and the gold/cash
leg alike. The sell of the old holdings and the buy of the new ones happen
together at that same T+1 open; the book is valued at T+1's close onward
with the new holdings, and T's close-to-T+1-open gap is earned by the OLD
position.

- Signal inputs (momentum ranks, EMA, gold 6m checks) use data only up to
  T's close — same as what a live trader sees in the evening alert.
- This matches how the alerts are actually used (alert after close / the
  morning-after safety net, order placed at the next open).
- Existing numbered reports (48/71/91/92/98 etc.) were built with
  same-day-close execution (report 99 only fixed the guard's prior-close
  timing); do not silently change them. If a legacy report is re-run or
  compared with a new one, say which execution convention each uses, and
  never mix the two in one comparison row without flagging it.
- New backtests need Open prices alongside Close (fetch() already returns
  the full OHLC frame; the closes-only builders in backtest42 need an
  open-aware variant rather than a modified original, so published numbers
  stay reproducible).

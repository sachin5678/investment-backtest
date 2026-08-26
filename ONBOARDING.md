# Onboarding: NIFTY/Midcap Backtest Lab ("Signal Lab")

This is a continuation brief for another Claude session picking up this
project. It captures the conventions, methodology, and non-obvious
decisions that aren't visible from just reading the code — read this
before making changes, so new work stays consistent with everything
already built.

The user (Sachin) is a domain-fluent, non-coder-detail-oriented owner who
cares about **honest results over impressive ones**. He will explicitly
ask you to extend/compare/stress-test existing strategies rather than
inventing new ones from scratch — follow his lead on scope, and when a
request is ambiguous about which reports/strategies it applies to, ask
before building the wrong thing (he has corrected scope misunderstandings
before, e.g. "any stock in NSE with market cap >2000cr" not a curated
list, and "no minimum pool" when a script had invented one).

## What this project is

32 hand-rolled Python backtests (no backtesting library — plain pandas
event loops) of trading/SIP/factor strategies on Indian markets (NIFTY 50,
Midcap 150, Smallcap 250, NIFTY 500) plus two non-Indian ones (NASDAQ-100,
global gold/silver). Each backtest produces a **self-contained static HTML
report** (dark theme, inline hand-rolled SVG charts, zero build step) and
also feeds a **React/Vite/Tailwind webapp** ("Signal Lab") that browses all
reports through one UI, now with a **Supabase-backed login gate** for
premium content.

Public GitHub repo: **https://github.com/sachin5678/investment-backtest**
(public repo — see "Security posture" below, this matters).

## The file-naming convention (memorize this, it has one quirk)

For report **N**: `backtestN.py` (the engine) writes `results(N-1).json`,
and `build_htmlN.py` reads that json and writes `N_description.html`.
Example: report 24 → `backtest24.py` → `results23.json` → `build_html24.py`
→ `24_midcap_momentum10_last2yr_tradelog.html`.

**The one exception**: report 21 (NASDAQ100 Momentum 10) has no
`backtest21.py` — it reuses `backtest20.py` (writes `results20.json`) and
only `build_html21.py` is report-21-specific. Always check with `grep -l
"results20.json" backtest*.py` style searches rather than assuming the
pattern holds before editing.

Shared library modules (not report-specific, imported by many
`backtestN.py` files): `backtest10.py` (`select_top30`, `build_index`,
`rebalance_dates`, `cumret_drawdown`, `series_to_points`, `fetch`),
`backtest13.py` (`load_midcap150_closes`, `metrics`, `blend_50_50`),
`backtest27.py` (`load_midcap150_field` for Low/Open/High,
`build_original`, `summarize`), `svg_charts.py` (`line_chart`,
`area_underwater_chart`, `COL` palette, Catmull-Rom smoothing — every
chart in every report uses this, never a charting library).

After adding/changing a report, always re-run in this order:
```bash
py -3 backtestNN.py          # writes resultsNN-1.json
py -3 build_htmlNN.py        # writes NN_description.html
py -3 build_dashboard.py     # regenerates dashboard.html with the new nav entry
py -3 extract_report_content.py   # regenerates root-level report_content.json (prose, for Supabase seeding)
```
Then wire the new report into **both** `build_dashboard.py`'s `GROUPS`
list and `webapp/src/data/reportsIndex.js`'s `GROUPS` — they're
independent, hand-maintained mirrors and both need updating. If the report
id is ≥ 11, also reseed Supabase (see below) since its data doesn't live
in a public file.

## Core methodology, used identically across almost every report

- **Momentum score**: 6-month and 12-month price return, each divided by
  trailing-1-year daily-return volatility, cross-sectionally Z-scored
  across the eligible universe that day, combined `0.5*Z(6m)+0.5*Z(12m)`,
  then asymmetrically normalized (`1+w` if `w≥0` else `1/(1-w)`). This is
  `select_top30()` in `backtest10.py` — reused, not reimplemented, by
  every momentum reconstruction (reports 11, 12, 14-19, 21, 24-31).
- **Rebalancing**: most momentum reports use June/December (borrowed from
  the real NIFTY200 Momentum index's cadence, even for universes that have
  no real index at all) — report 25 found this specific choice sits
  mid-pack, not luckily best/worst, across all 6 possible semi-annual
  offsets.
- **Equal weighting**, not free-float-market-cap × score (the real
  indices' actual weighting) — disclosed every time as a simplification.
- **Today's fixed universe applied retroactively** — every reconstruction
  carries survivorship bias, disclosed every time, strongest for smallcap
  (report 29 found concentrating a smallcap universe HURTS both return and
  drawdown, the opposite of what the same concentration test found for
  NIFTY100 in report 28 — large-cap trends persist, smallcap "momentum" is
  more often a one-off news spike).
- **Realistic stop-loss/margin-call fills**: whenever a rule triggers on
  an intraday price level (stop-loss, margin call, breakeven-lock), it's
  checked via that day's **Low**, and filled at `min(Open, trigger_price)`
  — never assume you got filled exactly at the trigger price if the stock
  gapped through it overnight. This exact pattern is in reports 22, 27,
  30, 32 — reuse it, don't reinvent it.
- **Honesty ethos, non-negotiable**: every report leads with a disclosure
  panel stating the result plainly (including when the strategy
  underperforms a naive alternative — several do, on purpose), has a
  "Limitations" panel listing every simplification, and an "honesty note"
  explaining the MECHANISM behind a surprising result, not just the
  number. Never dress up a weak or risky result. When you find a bug that
  changed a number, disclose it in the commit message rather than quietly
  fixing it (see report 32's commit for the template — a double-counting
  bug that had inflated apparent CAGR ~4-8x was caught and disclosed, not
  hidden).

## House style (visual), also non-negotiable — see project memory

Always smooth charts (Catmull-Rom, `svg_charts.py`) + the unified
`dashboard.html` hub with per-strategy sidebar nav + the same dark palette
across every single report and the webapp. Colors: `#08171E` ground,
`#0F2630` panel, `#1E3A45` border, `#37F083` positive/green, `#F2643C`
negative/red, `#F2B03C` amber/assumption, `#6AE4FF` accent/cyan,
`#E6EDF0` text, `#7E97A0` muted. Pills: green=positive, red=negative,
amber triangle=assumption, grey=neutral. Every panel gets a
`WHAT THIS SHOWS` italic caption before its content.

## The webapp ("Signal Lab") — React + Vite + Tailwind v4

`webapp/src/pages/Overview.jsx` = landing page (hero, joke card, strategy
card grid, "THE NUMBERS" stat strip). `webapp/src/pages/ReportPage.jsx` =
generic per-report viewer: auto-detects every "series" object in a
report's JSON (`lib/viewmodel.js`'s `extractSeries`, walks the tree
looking for `{equity_curve, max_drawdown_pct, longest_underwater_days}`
shapes) and renders a KPI table + growth chart + drawdown chart with zero
per-report-specific code. `components/TradeLog.jsx` auto-detects whether a
report's `trades` array is per-rebalance-leg (reports 24/26, grouped by
period) or merged continuous holdings (report 31, has
`num_rebalances_held` field → flat table with New/Carried/Exited tags) and
renders the right shape automatically.

**HashRouter** is deliberate (not BrowserRouter) — makes deep links work
on static hosting with zero server config. Plain in-page anchors
(`<a href="#foo">`) break under HashRouter (rewrites the whole route) —
always use `lib/scrollTo.js`'s `scrollToSection` instead, which
`preventDefault()`s and scrolls manually.

**Modal gotcha, already fixed once, don't reintroduce it**: any modal
that's a plain child of a flex/grid container (like `AuthButton` inside
`TopNav`'s nav row) and uses `position: fixed` can get mis-sized by that
row in some browsers instead of the true viewport. `LoginModal.jsx` now
renders via `createPortal(..., document.body)` — do this for any future
modal, don't just nest it inline.

## Premium gating (Supabase) — the most recent, most complex addition

**Design**: reports 1-10 (breakout/cash-timing/basic SIP) are free —
their `resultsN.json` live in `webapp/public/data/` as before. Reports 11+
(every momentum/rotation/RSI/gold/trade-log report) are premium — their
full results JSON lives ONLY in a Supabase Postgres table
(`premium_reports`, RLS: authenticated-only). **Every** report's
disclosure/analysis prose (1-32, no exceptions) is ALSO gated — it lives
in `report_prose` (RLS: authenticated-only) and is never in a public
static file. `PREMIUM_MIN_ID = 11` in `webapp/src/data/reportsIndex.js`
is the single cutoff constant.

**Login**: username `sachin`, password `121101` (mapped internally to a
fixed Supabase auth email `sachin@signal-lab.local` since Supabase Auth
needs an email shape — no real email involved, account is pre-confirmed
via the admin API).

**One deliberately-public table**: `landing_stats` — three aggregate
marketing numbers (best CAGR found, markets covered, longest backtest)
computed across ALL 32 reports, readable by `anon` too, with NO
per-strategy detail attached. This exists because the homepage's "best
CAGR found" stat used to be computed client-side from whatever the
current visitor could fetch, so it silently shrank for logged-out users —
now it's always true regardless of login state.

**Files**: `supabase/schema.sql` (run once in the Supabase SQL editor —
idempotent, safe to re-run after adding a table). `scripts/seed_supabase.py`
(idempotent — creates/re-syncs the login user, upserts every report's
prose from the root-level `report_content.json`, upserts every id≥11
report's results, recomputes+upserts `landing_stats`). Run it with:
```powershell
$env:SUPABASE_URL="https://cvqhyjvcszkscnnfzika.supabase.co"; $env:SUPABASE_SERVICE_ROLE_KEY="<ask the user — never in git>"; py -3 scripts/seed_supabase.py
```
`webapp/.env` (gitignored) holds `VITE_SUPABASE_URL` +
`VITE_SUPABASE_ANON_KEY` (the anon/publishable key is safe to ship — RLS
does the real enforcement). The service_role/secret key is NEVER
committed and NEVER goes in the frontend — ask the user for it fresh each
time you need to reseed, or ask them to rotate it if it's ever been pasted
in plaintext chat before.

**After adding any new report ≥ 11**: you MUST re-run
`extract_report_content.py` then `scripts/seed_supabase.py` or its data
silently won't appear for logged-in users (the webapp never falls back to
a public file for premium reports).

**Security posture — tell the user this if they ever ask "is this really
private"**: the GitHub repo itself is PUBLIC and contains every report's
full HTML/data in git history, predating the gating work. The Supabase
gate only controls the deployed webapp's UI/API going forward — it does
NOT hide anything from someone who clones the repo directly. This was
explicitly disclosed to the user already; don't let a future session
imply otherwise.

## Known gotchas already debugged once — don't rediscover these

- **pandas 3.0.5**: use `resample("ME")` not `"M"` (deprecated).
  `NaN > threshold` evaluates `False` — check `.notna()` first in any
  "if no losses, RSI=100"-style fallback logic, or NaN silently becomes a
  fabricated result.
- **Double-counting in leveraged/margin backtests**: if you compute
  `own_each = cash / n` to size new positions, you MUST also do
  `cash -= own_each` (draining it), not just subtract the transaction
  fee — otherwise the capital is counted once as leftover cash and again
  as the new position's equity. This exact bug inflated report 32's
  apparent CAGR by ~4-8x before being caught; verify any new leveraged/
  cash-tracking simulation against a hand-computed single-period example
  before trusting its output.
- **Yahoo Finance / yfinance rate limits**: aggressive concurrent
  fetching (20+ workers) gets the whole account blocked (even single-
  ticker requests start failing). Batch gently: 3-8 workers, jittered
  delays, pauses between batches of ~100.
- **"Yahoo Finance" must never appear anywhere user-facing** — scrubbed
  from every report and the webapp already (so nobody can reverse-engineer
  the data source and clone the tool); if you add a new data-source
  mention, write "our data source" or similar instead.
- **Vite dev server / browser-tool quirks** (not real bugs, don't chase
  them): a stale tab can keep serving deleted files — always verify with
  `curl` directly or a brand-new tab, not a reused one. The
  screenshot/`computer` tool fails with "Browser pane is not displayed" in
  this environment — use `read_page`, `get_page_text`, and
  `javascript_tool` for verification instead of visual screenshots.

## Full report inventory (id — title — group)

| Group | Reports |
|---|---|
| NIFTY 50 Breakout System | 01 20d-high/10d-low breakout · 02 vs buy-and-hold |
| Cash Timing (NIFTY 50) | 03 Wait for the Dip |
| Midcap Rotation | 04 Flight to Midcap |
| SIP + Tactical Overlays (Midcap) | 05-09 dip lump-sums, confirmed-recovery, doubling SIPs, SIP-date-matters |
| Momentum Factor | 10 SIP in a momentum ETF · 11 Momentum formula 18yr · 12/28 NIFTY100 Momentum 10/5 |
| Quality Factor | 13 Quality-50 static basket |
| Midcap Momentum + Gold | 14 Momentum-20+gold · 15 quarterly rebalance · 16/29 Smallcap vs Midcap / Smallcap 10 vs 5 · 17 monthly-rebalance-all-6 · 18 Midcap-30 & NIFTY500 10/15 |
| Sector Rotation | 19 Sector-first momentum |
| Momentum + Gold, Drawdown-Triggered | 20 catch-blend |
| Beyond India | 21 NASDAQ100 Momentum 10 |
| Technical Signals | 22 Monthly RSI-70 crossover |
| Commodities | 23 Gold/Silver absolute momentum |
| Trade-Level Detail | 24 last-2yr trade log · 25 rebalance offsets · 26 2020-2023 trade log · 27 stop-loss 15%/30% · 30 breakeven profit-lock · 31 carried-position trade log · 32 2x Kotak Neo MTF leverage |

The "Trade-Level Detail" group is entirely about **Midcap150 Momentum
10** specifically (the project's flagship strategy) — every report there
tests a different real-world overlay (trade log granularity, exit rules,
leverage/costs) on the exact same base strategy, always compared back to
the frictionless original.

## Deployment

Repo pushed directly to `main` after every deliverable (no PR workflow
used so far — confirm with the user if that should change). Vercel
deployment was discussed but requires the user's own OAuth login, so it
was never executed by Claude — only instructions were given. If asked to
deploy, remind the user this needs their own account action, or offer to
walk them through it interactively.

## Style/workflow feedback already given by the user (apply without re-asking)

- Push to GitHub after each completed deliverable, unprompted (this is
  the established pattern, not something to ask permission for each time).
  Write substantial, structured commit messages explaining what changed
  and why, matching the style already in `git log`.
  - Multi-strategy/multi-report requests in one message are common —
  parse them into separate deliverables and build each with its own
  numbered report rather than cramming into one.
- When a user's instruction corrects a prior misunderstanding (e.g. "I
  don't want any minimum pool", "market cap > 2000cr means ANY stock, not
  a curated list"), that correction is durable — don't drift back to the
  old (wrong) interpretation in later reports on the same strategy.
- Verify webapp changes in-browser (read_page/get_page_text/console,
  since screenshots don't render in this tool environment) before
  declaring something fixed — several "fixes" needed a second pass after
  actually testing.

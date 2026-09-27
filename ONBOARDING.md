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
reports through one UI, with a lightweight **client-side login gate** for
premium content (see "Premium gating" below — it's UI-only by design, no
backend).

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
py -3 extract_report_content.py   # regenerates webapp/public/data/report_content.json (prose)
```
Then wire the new report into **both** `build_dashboard.py`'s `GROUPS`
list and `webapp/src/data/reportsIndex.js`'s `GROUPS` — they're
independent, hand-maintained mirrors and both need updating. If the
report's own `resultsN.json` isn't already in `webapp/public/data/`,
copy it there too — every report's data is a plain public static file
(see "Premium gating" below), there's no separate backend step.

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

## Premium gating — pure client-side, no backend (deliberately, twice-decided)

**History, so you don't re-litigate it**: this was first built as a
client-side-only gate, then rebuilt on Supabase (Postgres + RLS) for
genuine access control, then reverted BACK to client-side after the
Supabase version caused real deployment friction — the free-tier database
pauses after inactivity, and the two hosting platforms in use (GitHub
Pages via Actions, Vercel) each needed the same two env vars configured
separately, which kept breaking in practice. Don't propose "let's add a
real backend" again without the user asking first; if they do ask, budget
time for exactly this kind of platform-config friction and mention it
up front.

**Design**: `AuthContext.jsx` does a plain hardcoded check — username
`sachin`, password `121101` — and persists a flag to `localStorage`. No
network call, no server, nothing to keep alive. `PREMIUM_MIN_ID = 11` in
`webapp/src/data/reportsIndex.js` is the single cutoff: reports 1-10 are
free, 11+ are "premium." **Every report's data (results JSON AND the
shared `report_content.json` prose file) is a plain public static file**
in `webapp/public/data/` — login only controls what the React UI
chooses to render, not what's fetchable. `LockedReportGate` and
`StrategyCard`'s locked-teaser branch both check `isPremiumReport(id) &&
!isLoggedIn` directly (not "did the fetch fail") — if you ever change
the data-loading strategy again, keep that check independent of fetch
success/failure, or the teaser silently stops working once fetches
succeed for everyone.

**Security posture — tell the user this if they ever ask "is this really
private"**: this is a soft UI gate for casual browsing, not real access
control. Anyone can open dev tools and read `USERNAME`/`PASSWORD` in
`AuthContext.jsx`, or just fetch `webapp/public/data/resultsN.json`
directly, or clone the repo (which is PUBLIC on GitHub and contains
every report's full HTML/data anyway). This has been explicitly
disclosed to and accepted by the user twice now (once before building
this feature at all, once again on reverting from Supabase) — don't
imply otherwise to a future session or the user.

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
used so far — confirm with the user if that should change). **Two
separate live deployments exist from the same repo**: GitHub Pages (via
`.github/workflows/deploy.yml`, runs `npm run build` in `webapp/` on
every push to `main`) and Vercel (connected directly to the GitHub repo,
builds independently of the Actions workflow). If the webapp ever needs
a build-time env var again, both need it configured separately — that
exact gap (env vars only added to the GitHub Actions workflow, Vercel
silently left unconfigured) is what caused a real support issue when
the Supabase-backed version was live. The current client-side-only auth
needs no env vars on either platform, which is one of the reasons it
was kept simple.

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

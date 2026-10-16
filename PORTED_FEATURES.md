# MomentumScore → investment-backtest: feature port map

Source of truth for the target feature set: `momentumscore-feature-inventory.md`
(16 Oct 2026, read-only walkthrough of momentumscore.in). This document maps
every feature from that inventory to what now exists in this repo — ported,
partially ported, or deliberately skipped — and where to find it.

Everything below is implemented in this repo as of 16 Oct 2026 (uncommitted).
Nothing on the live MomentumScore site was written to during recon or after.

---

## 1. What was added

### A · `ms_port/` — the analytics core (pure stdlib, no pandas)

| Module | What it implements |
|---|---|
| `health.py` | The 10-check health scorecard. Score = share of MomentumScore's published target ranges met (win% ≥ 50, avg win ≥ 30%, avg loss ≤ 15%, gain/loss ≥ 2, worst daily fall ≤ 20%, CAGR ≥ 40%, tail-risk monthly −2..+2, tail-risk trade −2..+2, monthly swing ≤ 15, growth-per-fall ≥ 2.5). Trade-based checks are excluded (not failed) when a series has no trade log. |
| `robustness.py` | "Rules or luck?" — both-halves check (split at the midpoint of the benchmark's own history) and date-luck check (same engine, different review calendar). Emits PASS / MIXED / FAIL per check plus an overall verdict. |
| `tax.py` | Indian capital-gains estimator: 15%/10% with ₹1,00,000 LTCG exemption before 23 Jul 2024 → 20%/12.5% with ₹1,25,000 after; 4% cess; short-term losses offset STCG then LTCG, long-term losses offset LTCG only; 8-year carry-forward; s.112A grandfathering via the 31-Jan-2025 FMV map; per-FY table + `after_tax_curve()` to compound the tax out of the equity curve. |
| `fit.py` | MomentumScore's "fit" — a 0–100 percentile standing vs the eligible universe that day, plus ranked rows with Δ vs the previous ranking and held flags. |
| `formula.py` | The ranking formula mini-language (`ret(1m) / vol(6m)` style): tokenizer + validator + evaluator. Core only — no UI editor. |
| `tests/` | 29 tests, all passing (`py -3 -m pytest ms_port/tests`). |

### B · Report 93 — the review-layer engine (`backtest93.py` → `results92.json`)

Report 48's skeleton (Midcap150 momentum 10, NIFTY-50 200-EMA regime filter,
GOLDBEES hedge) re-run with MomentumScore's review layer on top:

- **Exit-rank-52 hysteresis** — a held stock is sold only when it falls below
  rank 52 of the eligible universe at a scheduled review; carried names keep
  their original shares (report 31 convention, no re-equalisation).
- **Fresh top-10 on regime re-entry** (no hysteresis across a regime flip).
- **0.1%/side costs on every leg** including the gold hedge →
  `before_costs` / `after_costs` / `after_tax` curves side by side.
- **Real-rupee trade log** (₹1,00,000 window start via the engine's own unit
  accounting), 686 closed trades with `rank_in → rank_out` and
  `fit_in → fit_out` and reason strings.
- **Rebalance log** — 153 events (65 regime exits, 64 re-entries, 23 scheduled
  reviews, 1 initial entry), each with sells/buys/carried and rank+fit.
- **Embedded review blocks** — `health_check`, `robustness` (halves + date-luck
  mid-month variant), `tax_report` (17 FYs, after-tax curve), `ranks` (latest
  close, regime-aware preview).

### C · Webapp surfaces (`webapp/`)

| Route / piece | What it is |
|---|---|
| `/health` | Strategy-health leaderboard across all 591 archived series (102 files), searchable/sortable, with the full 10-check card + robustness for any row. |
| `/tax` | The capital-gains estimator over every report that carries a trade log (5 reports), per-FY table, totals, notes. |
| `/mix` | Multi-system mixer — blend up to 8 strategy series into one constant-weight curve (daily step-blend on a union date axis), NIFTY 50 overlay, per-component stats, CSV. |
| `/track` | Paper portfolios — "what if I had started then": pick any report + series + start date + capital, stored in localStorage, marked against the strategy's latest data point. |
| `/ranks` | Ranking preview from report 93: full table with Δ rank / Δ fit / held / action, regime state, and the "if you rebalanced today: SELL x, BUY y" preview. |
| Report 93 page | All of the above as panels: health + robustness, tax FY table, rebalance log, ranks preview — plus rank/fit columns in the trade log. |
| Every report page | `⇩ CSV` exports (KPI table, trade log) and review panels that appear automatically when a report's data carries the blocks (report 93 does; older reports get health + robustness from the lab). |
| Sidebar | New "Tools" section: Strategy health, Capital-gains tax, Multi-system mixer, My portfolios, Ranking preview. |

### D · Static report (`build_html93.py` → `93_midcap150_momentumscore_style_review.html`)

Self-contained HTML in the established house style: headline disclosures, KPI
cards, growth-of-100 and drawdown SVG charts, series table, health scorecard,
robustness tables, full FY tax table, rebalance log (last 8 of 153), trade
statistics, limitations.

### E · Cross-report lab (`build_ms_lab.py` → `webapp/public/data/ms_lab.json`)

Scores **every** archived series in **every** `results*.json` (591 series across
102 files): health card + both-halves robustness + tax report where a trade log
exists. This is what powers `/health` and `/tax` for older reports, and what the
report page's review panels fall back to when a report has no embedded block.

---

## 2. Feature-by-feature map

Status legend: **Ported** · **Partial** · **Pre-existing** (repo already had it;
listed for completeness) · **Skipped** (with reason).

| MomentumScore feature | Status | Where | Notes / caveats |
|---|---|---|---|
| Health score /100 (10 target checks) | Ported | `ms_port/health.py`, report 93 `health_check`, `/health`, HTML panel | Tail-risk checks use return skewness as a documented proxy (MomentumScore's exact definition unpublished). |
| Robustness verdict (date-luck + halves, "Holds up / Mixed / Fragile") | Ported | `ms_port/robustness.py`, report 93 `robustness`, `/health`, HTML panel | Verdicts map to PASS / MIXED / FAIL. The quota-cost idea is irrelevant locally (runs are free). Date-luck = 1 variant (mid-month day ~15), not the full days 15–25 sweep. |
| Tax tab (after-tax CAGR, tax paid, FY table, statutory rates, carry-forward, grandfathering) | Ported | `ms_port/tax.py`, report 93 `tax_report`, `/tax`, HTML panel | Exit-date FY assignment; 4% cess; no surcharge, no advance-tax timing, no pre-2018 grandfathering (0 trades affected by s.112A here). |
| Fit % = daily percentile vs eligible universe | Ported | `ms_port/fit.py`, engine ranks/trades, TradeLog columns, `/ranks` | First-class column + Δ vs last review. |
| Δ vs previous ranking date | Ported | `ranks.rows[].rank_delta` / `fit_delta`, `/ranks` | |
| Exit-rank hysteresis (2.5×N rule of thumb) | Ported | `backtest93.py` (`exit_rank: 52` for N=10) | Hold-zone semantics: sell only at a review, only below the exit rank. |
| Rebalances log (state, sells/buys with rank+fit, park/unpark, reasons) | Ported | `results92.json` `rebalances`, webapp RebalancesPanel + CSV, HTML panel | 153 events with per-name reasons ("exit rank", "regime exit", "regime re-entry"). |
| Closed trades table (rank in→out, fit in→out, reason) | Ported | `results92.json` `trades`; TradeLog renders the extra columns conditionally | Also in CSV export. |
| Before costs / After costs toggle | Ported | `before_costs` / `after_costs` / `after_tax` series everywhere | Also shown as 3 lines at once — no toggle needed. |
| "If you rebalanced on <date>: SELL x, BUY y" preview | Ported | `ranks.preview`, `/ranks`, report panel | Regime-aware: empty preview while the filter is off (currently holding the gold hedge). |
| Multi-System mixer | Partial | `/mix` | Up to 8 strategies, constant-weight daily blend, NIFTY overlay, CSV. No per-system ₹ amounts, no mix-level SIP/step-up. Curves are archived chart-resolution series (≤1500 points) — close estimates, disclosed on the page. |
| My Portfolios (paper tracking) | Partial | `/track` (localStorage) | Lump-sum "started then" tracking with live P&L vs latest data. No broker connect, no "start today vs next rebalance" live engine, no reminders. |
| Export (Excel / PDF / PDF masked) | Partial | `⇩ CSV` on KPI tables, trade log, rebalance log, mixer | CSV only; no XLSX/PDF/masked variants. |
| Compare up to 8 strategies | Pre-existing | `master_comparison.html` + `/compare` | |
| Formula scoring language `ret(1m)/vol(6m)` + validator | Partial | `ms_port/formula.py` (`compile_formula`) | Evaluator + validation exist with tests; not wired to a UI editor. |
| Whole units + cost/slippage stack | Partial | `backtest93.py` | Whole units and 0.1%/side costs on every leg; slippage not modeled separately; single execution model (review-day close). Report 88 studied timing sensitivity separately. |
| Benchmark comparison (16+ indices, Δ CAGR table) | Pre-existing | `master_comparison`, per-report tables | Report 93 compares NIFTY 50 + GOLDBEES directly. |
| Stock scoring `/ranks` table | Ported (lighter) | `/ranks` | Rank / Δ rank / fit / Δ fit / held / action + regime state. No industry, close, 3M/6M/1Y, volatility columns. |
| "Why?" per rank (factor marks, funnel cuts) | Partial | Trade `why_in` / `why_out`, rebalance reasons | Reasons + rank/fit history per trade; no factor-contribution breakdown popup. |
| Steadiness ("N of M years beat benchmark") | Partial | Both-halves check is the ported analog | No year-by-year beat table. |
| Risk tab (top-5 drawdowns, rolling windows, trade histogram) | Skipped | — | Existing reports cover drawdowns; could be added to the lab later. |
| What-if Lab (7 one-change re-runs) | Partial | Pre-existing sweep reports (46–47, 76–79, f3/f5/f6) | Targeted sweeps exist; no single 7-dial page. |
| Conditions gate (40 indicators, Keep if / Buy only if / Sell when) | Skipped | Targeted variants exist (f1–f6 findings) | A general rule builder is a product, not a port; the inventory's indicator semantics are documented in `momentumscore-feature-inventory.md` for future use. |
| Protect: cash/half action + multi-ETF park basket (≤4, %) | Partial | Regime filter parks 100% in GOLDBEES (report 48 lineage) | No half-portfolio mode, no multi-instrument park basket, no VIX filter, no park-to-cash listing-date realism. |
| Sector caps / entry rank / liquidity-rank universe / ETF mode / historical members | Skipped | — | Engine is single-universe equal-weight top-10; survivorship (static constituent list) is a documented limitation in every report. |
| SIP / step-up / buy-the-dip | Partial | Pre-existing SIP reports; dip-buy in f1 findings | Not part of report 93. |
| Weekly / monthly rebalance options | Partial | Calendar variants in reports 85 / 92 | Engine uses Jun/Dec month-end; the date-luck variant re-runs mid-month. |
| 4 execution models | Skipped | — | One model (review-day close → trade at that close); report 88 studied the timing dimension. |
| Broker Connect + live broker orders | Skipped | — | SaaS + Windows helper + broker APIs; not portable to a static repo. `/track` is paper-only. |
| Telegram / WhatsApp alerts via own bot | Skipped | — | Needs a live scheduler and bot token; the pattern is documented in the inventory. |
| Quota / add-ons / referrals / payments | Skipped | — | SaaS billing surface. |
| AI support widget / live agent handoff | Skipped | — | SaaS support surface. |
| Share links + PDF masked export | Skipped | — | Local static reports; CSV export instead. |
| Point-in-time historical index membership | Skipped | — | Static `*_symbols.py` lists; biggest known trust gap, documented in every report's limitations. |

---

## 3. Known proxies & caveats (read before trusting the new numbers)

- **Tail risk = skewness.** MomentumScore publishes the target range (−2..+2)
  but not the exact statistic; monthly and per-trade return skewness is used as
  a documented proxy (`ms_port/health.py`).
- **Two resolutions of health.** Report 93's embedded card runs on the engine's
  full-resolution daily curve; the cross-report lab (`ms_lab.json`) scores
  archived chart series (≤1500 points), so a lab score can differ by a check.
- **Date luck = one variant.** The engine re-runs with mid-month (day ~15)
  reviews — a smoke test, not the six-calendar sweep of reports 85/92.
- **Whipsaw is inherited, deliberately.** Report 93 logs 65 regime exits and 64
  re-entries — faithful to report 48's filter (its 69 re-entries). The review
  layer changes stock selection, not the market-timing rule.
- **Tax is an estimate.** Exit-date FY assignment, no surcharge/advance tax,
  0 grandfathered trades (all holds under a year), equity/STT assumptions.
- **Alloc-unit scaling.** Rupee figures come from scaling the window start to
  ₹1,00,000 through the engine's own unit accounting; percentage curves are
  scale-free.

---

## 4. How to reproduce

```powershell
# analytics core tests
py -3 -m pytest ms_port/tests

# report 93 engine (writes results92.json at repo root; uses cached price pickles)
py -3 backtest93.py
Copy-Item results92.json webapp\public\data\results92.json

# cross-report lab (writes webapp\public\data\ms_lab.json)
py -3 build_ms_lab.py

# static HTML report
py -3 build_html93.py

# webapp (dev server, or build for the static deploy)
cd webapp
npm install
npm run dev        # or: npm run build
```

---

## 5. Files added / modified in this port

**New:** `ms_port/` (6 modules + tests), `build_ms_lab.py`,
`webapp/public/data/ms_lab.json`, `backtest93.py`, `results92.json` (+ webapp
copy), `build_html93.py`, `93_midcap150_momentumscore_style_review.html`,
`webapp/src/lib/{datacache,csv,mslab}.js`,
`webapp/src/components/{HealthCard,RobustnessCard,TaxTable,RanksTable,MsPill,ReviewPanels}.jsx`,
`webapp/src/pages/{Health,Tax,Mixer,Track,Ranks}.jsx`, `docs/ms-recon/` (raw
recon artifacts), this file, `momentumscore-feature-inventory.md`.

**Modified:** `webapp/src/App.jsx` (routes), `components/Layout.jsx` (tool
titles), `components/Sidebar.jsx` (Tools section), `components/TradeLog.jsx`
(rank/fit columns + CSV), `pages/ReportPage.jsx` (review panels + CSV),
`data/reportsIndex.js` (report 93 entry).

# MomentumScore (momentumscore.in) — Full Feature Inventory

Collected 16 Oct 2026. **Public surface** (landing, pricing, signup/login, `/learn`,
robots.txt, sitemap) **plus a full logged-in walkthrough** of every screen via
Chrome DevTools Protocol (read-only tour: no backtests run, no orders, no settings
changed, no deletions — daily quota untouched, 22/25 before and after).

Reference account observed: `sachinapatil2003@gmail.com` — Trial/launch plan,
1 strategy (`hawda`, id 215), data to 16 Oct 2026.

Company: Technobot Technolgies Pvt Ltd · PHP server-rendered app · Bootstrap 5.3 ·
Inter/JetBrains Mono · Cloudflare · PWA manifest. Research strategies in the
"Research" section are prepared by Rishabh Kumar Sharma, SEBI RA (INH000018081),
also a MomentumScore partner. Positioning: SEBI-disclaimer-heavy research/backtest
tool — "your rules, your orders"; never recommends securities.

Raw tour artifacts (HTML, JSON digests, extracted text) are archived in
`docs/ms-recon/` in this repo.

---

## 1. App shell & routes (observed logged-in)

- **Top nav (desktop):** Research (Stock Scoring `/ranks`, ETF Scoring
  `/ranks?asset=etf`) · Build & Test (My Strategies `/strategies`, Backtest
  `/backtest`, Compare `/compare`, Multi-System `/multi`) · My Portfolio
  `/portfolio` · My Broker `/broker` · Learn (`/learn` video guides+articles,
  Ranking Guide `/guide`, Help & Requests `/support`, Telegram group).
- **Right side:** remaining quota chip ("22 / 25 backtests today"), avatar menu
  (Account `/account`, Invite friends `/account#invite`, Download Broker Connect
  v2.5.2 `/connect`, Log out). "Beta Access Enabled" badge. Mobile collapses nav
  into a "More" sheet.
- **Floating support widget on every page:** "Ask doubt" / "New" / "Ask a live
  agent" — AI help for using the app (quota shown: "9 AI questions left today"),
  with human-agent handoff.
- **Routing quirks:** `/sweep` → `/backtest` · `/live` → `/portfolio` ·
  `/kite` → `/portfolio` · `/swing` → `/home` · `/assistant` → `/home` ·
  `/connect` serves the Broker Connect installer file directly ·
  `/shared?id=…` = resolver for share links ("This link is not available" without
  a live id) · `/run_job`, `/progress`, `/formula_check` are internal action
  endpoints (not linked anywhere in the UI).
- **Conventions:** GET pages + GET-param view state (`dt` = ranks date, `id` =
  strategy/backtest); mutations are POSTs with `csrf_token`, `action`, `id`
  (strategy folder ops, deletes, profile, password, Telegram token, support
  tickets, AI `aiQ`). Google OAuth start route `/google`.

## 2. Dashboard `/home`

- Greeting + "data to <date>" + quota chip; strategy-shape wizard entries:
  Rocket / Steady climber / Marathon / All-rounder →
  `strategies?new=1&shape=<shape>#score`; "New strategy" (`?new=1`), "New ETF
  strategy" (`?new=etf`); "Ranking guide" link.
- Onboarding strip "Your first portfolio in three steps" (describe rules →
  backtest → add to My Portfolio with reminders).
- "Your strategies" card(s): style line, universe, hold/exit, growth, worst fall.
- Tools tiles: Stock scoring ("Why? on every row"), ETF scoring, Compare,
  Multi-System.
- Tips panel (e.g. robustness explainer), full disclaimer footer.
- The AI/chat widget can describe a strategy from a prompt ("describe a new
  strategy by the rise you want").

## 3. Strategy builder — complete field map (`/strategies?new=1`, `?new=etf`, `?edit=<id>`)

**Shell:** Name · Backtest from / to (blank = latest) · Invest in Stocks|ETFs ·
7 numbered steps with a review line each + combined "Review" block; "Save &
backtest" and "Save"; Back/Next; **Quick check** panel (live mini-result —
growth/yr, worst fall, benchmark/yr — "the same run as Save & backtest").

**1 · Universe**
- Index members | Liquidity rank mode. Indices: NIFTY 500, MIDCAP 150,
  SMALLCAP 250, MIDSMALLCAP 400, MICROCAP 250, TOTAL MARKET — any number can be
  combined with % weights ("Midcap 25% + Microcap 75%").
- Liquidity rank: rank all NSE stocks by 6-month average traded value each day;
  rank from/to (251–750 ≈ small/microcap band).
- **Historical members toggle** (point-in-time): NSE's real lists rebuilt from
  announced changes — Nifty 500 from 2012, Midcap 150 & Smallcap 250 from 2016,
  Microcap 250 from 2021; earlier years estimated from mcap/turnover. Off =
  today's members for all dates (survivorship-biased, explicitly labelled).
- **Sectors:** All / Only these / Leave these out, plus per-sector % weights
  (22 NSE "Industry" buckets, full list in app; ≥2 sectors need >0 weight when
  weighting; weights set how many of the top-N come from each). Today's sectors
  used for past dates (stated limitation).
- **ETF mode:** category pickers (Broad Market / Sectoral / Factor-Strategy /
  Thematic / Funds) covering 46 ETFs (42 selected by default) — e.g. NIFTYIETF,
  JUNIORBEES, MONIFTY500, BANKBEES, ITBEES, MODEFENCE, GOLDBEES, SILVERBEES,
  LIQUIDCASE, MOM30IETF etc.; per-ETF **tracking error %/yr**; **"only ETFs
  listed that day"** realism toggle; **editable mapping sheet** (`RANK ON = BUY`
  lines, e.g. `NIFTY MIDCAP 150 = MID150BEES`) — rank on an index (less tracking
  error) or an ETF's own price; lines kept if ticked; ETFs without an NSE tracker
  listed as not buyable.

**2 · Conditions (the gate)** — rows of `Keep if | Buy only if | Sell when` ×
indicator × comparator (`is above / is at least / is below / is at most`) × value;
interval context selector (Day/Week/Month/Calendar candles; "3 Week Performance"
= close vs weekly candle 3 weeks back; Day = 15 trading days).
- **40 indicators:** returns 1w–5w, 1m–6m, 9m, 1y; swings (volatility) 1w–5w,
  1m–6m, 9m, 1y; Price; Daily turnover (6-month avg); Price vs EMA 20/50/100/200;
  Price vs SMA 50/200; EMA50 vs EMA200; Supertrend (10,3,daily) — is green/red;
  RSI(14); From 52-week high; From all-time high; India VIX.
- **Semantics:** Keep if = checked at each review (a held stock that stops
  passing is sold at the next review); Buy only if = entry-only; Sell when =
  checked **every day**, sold that day, slot waits in cash until next rebalance.
  Failing any Keep-if condition = never ranked.
- **Quick adds:** only rising (6M ret > 0) · swings < 45% · turnover ≥ ₹5 Cr ·
  price ≥ ₹50 · above 200-EMA · Supertrend green · exit on Supertrend red ·
  RSI > 50 · golden cross · within 10% of all-time high · India VIX < 20 ·
  index P/E below 25 (P/E exists only for index-tracking lines; applies before
  buys; VIX data from mid-2014, earlier dates pass).
- Min price / max price range (held stocks stay until rank exit).

**3 · Rank by (the race)** — three modes:
- **Style:** 4 shapes (Rocket, Steady climber, Marathon, All-rounder) × 3 dials
  (Speed slow-1y ↔ fast-1m, Smoothness, Staying power). Each stock gets a
  **fit 0–100%** = its percentile vs the universe that day. Under the hood a
  style = a Factor Mix (e.g. All-rounder ≈ 6M risk-adjusted 43% + 3M momentum
  29% + steadiness 29%; Rocket emphasizes short momentum, Marathon 1Y, etc.).
- **Factor Mix:** factors blended by % weight; presets include 6M risk-adjusted
  (ret(6m)/vol(6m)), Blend (5%*ret1m+5%*ret3m+60%*ret6m+20%*ret9m+10%*ret1y all
  ÷ vol(6m)), Each period ÷ own vol (equal-weight 1m..1y of ret/vol), Short-term
  ETF (ret1w+2w+3w+4w), Plain 12M momentum. Each factor → 0–100 rank per day;
  weights → total.
- **Funnel:** rounds keep the best % ("top 50% by 1Y momentum → 250 → top 40% by
  3M → 100"), then final sort; counts shown live.
- **Scoring formula editor (fx):** free formula over `ret(1w..1y)`, `vol(1w..1y)`
  with numbers/percentages, + − × ÷, brackets; validity check + char count;
  "Load example"/Clear; measured on the interval selected. Higher score = higher
  rank. (Internal `formula_check` route corresponds.)

**4 · Pick & rebalance**
- Number of stocks/ETFs (Top N), optional **entry rank** (buy only from top K;
  slots wait in cash), optional **max per sector**, **exit rank** hysteresis
  (rule of thumb shown: exit ≈ 2.5 × N).
- Rebalance monthly (day 1–31) or weekly (weekday); NSE-holiday shift next/prev.
- Cost % / side + slippage % / side (default 0.1); 4 execution models: prev
  close signal → next open trade (default) · same-day close · buy close / sell
  next open · next-day close. Whole-units buying (leftover stays cash).

**5 · Money**
- Capital; compounding on/off (reinvest vs fixed per-position amount); monthly
  **SIP** + **step-up %/yr**; "only buy what is going up" (skip negative
  momentum among top-N, slot waits in cash) + "also sell once it turns negative";
  **Buy the dip**: extra ₹ when an index's RSI(period) < level, checked daily at
  close (weekly candles option), at most once a month; live portfolios get a
  Telegram/WhatsApp alert that evening. Report shows top-ups + money in + XIRR.

**6 · Protect (trend filter & benchmark)**
- Signal: SUPERTREND (ATR period + multiplier) or "below moving average"
  (DMA days) on a chosen index; action: **Go cash** / **Half portfolio**
  (keep best-ranked half, run half the slots); check frequency: each rebalance
  day / every day sell-only / every day sell-and-rebuy.
- **Park freed cash** in up to 4 instruments with % (any NSE symbol with prices;
  e.g. GOLDBEES 100%, or GOLDBEES 50% + SILVERBEES 25%, rest cash); instruments
  listed later than a backtest date park to cash until then; LIQUIDBEES-style
  dividend-unit liquid ETFs show ~0% (growth-type liquid ETFs work).
- **India VIX filter** (treat high VIX as down-market; same actions; works with
  or without trend filter).
- **Benchmark** (comparison-only; dashed line, benchmark CAGR, year-by-year):
  16+ indices incl. NIFTY 500/50/100/NEXT50, MIDCAP150, SMALLCAP250,
  MICROCAP250, MIDSMALLCAP400, MOMENTUM30, 500 MOMENTUM 50, MIDCAP150 MOMENTUM
  50, ALPHA50, 200 ALPHA30, 200 QUALITY30, 100 LOW VOLATILITY30.

**7 · Run** — Save & backtest (or Save). "A backtest replays every rebalance on
point-in-time data with your costs."

## 4. My Strategies `/strategies`

- List with columns: NAME · SCORING (e.g. "Style: All-rounder (speed medium ·
  smooth · staying power medium)") · UNIVERSE (e.g. NIFTY MIDCAP 150) · HOLD/EXIT
  ("10 / 52") · DAY (rebalance day). New stock/ETF strategy buttons; **folders**
  (create folder, move strategy via POST action+id+folder); per-row ops encoded
  as POST forms (rename/duplicate/delete/move — same endpoint with `action`).
- Backtest entry selects a strategy + Run (list page `/backtest`).

## 5. Backtest report `/backtest?id=<n>` (9 tabs)

Header: backtest list breadcrumb · actions **Edit rules · Share · Re-run · Add
to My Portfolio · Export**. Strategy summary one-liner (style, universe,
conditions, N, exit, day, period, run time, data date) + disclaimer.

- **Headline cards:** grew (start → final, CAGR, ×money) · worst fall (+ month,
  recovery months) · steadiness ("N of M years beat benchmark") · busy-ness
  (trades/yr, closed, win%, cost/side) · **Before costs / After costs** toggle.
- **Health score /100** (overview) — 10 rule-of-thumb checks with targets:
  win% ≥50 · avg win ≥30% · avg loss ≤15% · gain/loss ≥2 · worst daily fall ≤20%
  · CAGR ≥40% · tail-risk monthly −2..+2 · tail-risk trade −2..+2 · monthly
  swing ≤15 · growth-per-fall ≥2.5. Score = share of target ranges met.
- **GROWTH / FALLS / HIT RATE / STEADINESS / EFFICIENCY** blocks: CAGR, final,
  money in, benchmark CAGR; worst daily fall, worst closed-trade fall; win%,
  won/lost counts, avg win/loss, gain-to-loss, best/worst trade; monthly std
  dev, tail risks; growth-per-fall, trades/yr.
- **Compare with indices:** per-index CAGR, index maxDD, strategy CAGR/maxDD,
  CAGR difference, "show on chart" (16 indices, same period, no re-run).
- **Tabs:**
  - *Overview* — equity curve vs benchmark (and 15 more indices; log scale),
    health check, summary blocks, index comparison.
  - *Returns* — growth/returns detail (year-by-year view; exact layout not
    captured).
  - *Risk* — top-5 drawdowns (dates, %, value range, recovery months) + rolling
    12-month return stats ("worst/best window, % of windows positive") +
    histogram of closed trades by return.
  - *Trades* — current holdings table (symbol, since, qty, entry, now,
    invested/value/P&L, ROI, weight, rank now, fit now; regime positions like
    GOLDBEES labelled "Regime filter") + **Closed trades** table (entry/exit
    dates, days, qty, entry/exit/buy/sell ₹, P&L, ROI, **rank in→out, fit
    in→out, reason** e.g. "regime", "unpark").
  - *Rebalances* — per rebalance date: market state Up/Down, sells and buys
    with rank+fit ("SYMBOL · #k · 94%"), "Park · GOLDBEES"/unpark events, plus
    that day's top-8 ranked list with fits; footer explains fit definition.
  - *Robustness* ("Rules or luck?") — **"Run the robustness check"** button:
    re-runs rules on every other rebalance day (days 15–25) + each half of the
    period; **costs 12 backtests of the daily quota** ("saved results are free
    next time"); verdict labels **Holds up / Mixed / Fragile** with per-check
    details (date-luck bars, halves vs benchmark).
  - *What-if Lab* — 7 one-change re-runs offered: hold more stocks (10→20, exit
    52→104) · hold fewer (→5, exit 26) · hold longer (exit→78) · sell sooner
    (exit→34) · weekly rebalance (Wednesdays) · no trend filter · only buy
    rising; **costs 7 backtests**; result says if each change did better/worse.
  - *Tax* — optional after-tax estimate: CAGR after tax vs before, tax paid,
    value after tax, "if sold everything: ₹X on open holdings"; **year-by-year
    FY table** (booked gain, ST taxed, LT, exemption used, pre-2018 exempt,
    losses carried, tax); **statutory rate table by sale date** (pre-Apr-2018
    15% + exempt 10(38); Apr 2018–22 Jul 2024 15%/10% + ₹1L exemption; from
    23 Jul 2024 20%/12.5% + ₹1.25L; 4% cess; ending 3%→4% cess detail); method:
    LT = >12 months held, grandfathering at 31 Jan 2018, ST losses offset all,
    LT only LT, losses carry 8 years, tax assumed paid each 31 March;
    equity-STT assumption, gold/intl/debt ETFs treated as equity (stated
    simplification); exclusions: surcharge, other income, basic-exemption
    relief. Not tax advice.
  - *Inputs* — full settings dump of the run (period, capital, universe, N,
    entry/exit ranks, per-sector, weights, compounding, SIP, dip, conditions,
    only-rising, trend signal/action/index/park, rebalance freq/day/holiday/
    execution, cost/slippage, price range, historical members, scoring).
- **Share** — off by default ("turn on to get a link"); share link resolves at
  `/shared?id=…`.
- **Export** — Excel (.xlsx) · PDF report (with strategy rules) · **PDF masked**
  (results only, rules hidden; optional title; optional "hide stock/ETF names —
  rebalances show counts only").
- **Add to My Portfolio** — capital input with presets (₹50k/₹1L/₹2.5L/₹5L/₹10L);
  portfolio name; destination **Paper ("Track only: no orders placed")** or a
  connected broker account (choice immutable afterwards; broker name suffixed);
  "Start today" (buys today's top-N at latest close, whole shares, even mid-cycle)
  or "Start on the next rebalance · Wed, 21 Oct"; then the app follows the rules
  and shows what to trade each rebalance (user confirms every list; Paper only
  tracks).
- **Quota modal** — when the day's runs are used: "Results you already ran stay
  open… Ask us for a higher daily limit" (prefilled support request).

## 6. Stock Scoring `/ranks` · ETF Scoring `/ranks?asset=etf`

- Strategy selector (`id`), **as-of date** selector (`dt` — re-ranks as of a past
  date), edit-rules link; header shows universe size scored (e.g. "NIFTY MIDCAP
  150 (53 scored)"), top-N buy, hold-to rank, and **Δ vs <previous ranking
  date>**.
- **Model portfolio strip:** current holdings count, run period, CAGR; **"If you
  rebalanced on <date>: SELL x, BUY a b c …"** preview; sector counts within the
  exit rank (as filter chips).
- **Full ranking table:** # · Δ (▲/▼/new/–) · stock · industry · close · 3M ·
  6M · 6M volatility · 1Y · **Fit %** · **Why?** per row. "no buy" flag on rows
  inside the hold zone that can't be newly bought (e.g. failing a Buy-only-if
  condition). Zone separators: "Top N end here" and "Exit rank K: a holding that
  falls below is sold at the next rebalance".
- ETF variant lists all ETFs in the strategy universe with the same mechanics;
  empty state offers "Create your own".
- **Why?** opens per-row explainability (factor ranks/weights, real values,
  funnel cut-offs) — content not captured (no click).

## 7. My Portfolios `/portfolio`

- Portfolio cards: what to hold in whole shares, next rebalance changes, P&L;
  live follow from the day it started with your capital; "Start a portfolio" /
  empty state instructions; Telegram CTA banner (rebalance reminders + buy-the-
  dip alerts via your own private bot, 2-minute setup); paper vs broker
  portfolios; delete flow asks sell/keep handling (per prior public materials).
- Portfolio creation entry lives in the backtest report (see §5).

## 8. Compare `/compare`

- Select up to **8** strategies of your own; Compare button. "A strategy not yet
  run on the latest data is run now, so the first compare can take a minute." —
  i.e. Compare can consume quota for stale strategies. Showcase: who grows most,
  falls least, wins on each measure (side-by-side + disclaimer block).

## 9. Multi-System `/multi`

- Combine up to **10** strategies ("split your money across strategies with
  different approaches"); per-system capital (₹), "Add system" rows; optional
  monthly **SIP for the whole mix** + **step-up %/yr** ("split across systems in
  proportion to capital, added on each one's first rebalance of the month");
  Combine (GET params `s[]`, `cap[]`, `sip`, `step`). Mix covers the common
  period; with SIP all systems start on the latest start date and the mix SIP
  replaces per-strategy SIPs.

## 10. My Broker `/broker` + Broker Connect

- Helper: **Broker Connect v2.5.2** Windows app (downloaded from `/connect`);
  "read your broker accounts by the helper on your PC; nothing stored by
  MomentumScore; shown only in this browser"; pairing code flow ("New code"),
  accounts list, "Add an account".
- Supported brokers (13, select observed): FlatTrade, Shoonya (Finvasia),
  Angel One, Dhan, Zerodha, Upstox, Fyers, Kotak Neo, Alice Blue, 5paisa, IIFL,
  AC Agarwal, Zebu.
- **DDPI guidance**: without DDPI sells need CDSL T-PIN authorisation (rejected
  otherwise); Dhan helper can send T-PIN/open CDSL automatically; mark DDPI per
  account in helper so it stops asking.

## 11. Account `/account` — plans, add-ons, alerts, referrals

- Plan status ("Launch offer 90 days left · until 2027-01-14"), **Backtests
  today: used / 25** (viewing already-run results is free; resets midnight;
  quota chip in nav shows remaining).
- Profile: name, email, WhatsApp mobile (+91, verified via code; re-verify on
  change), reminder toggles (WhatsApp: plan/renewal; email: plan/rebalance);
  change password.
- **Invite friends:** referral link (`signup.php?ref=…`) — both sides get 7 free
  days once the friend confirms email (credited after a manual check, ~1 day);
  share via copy/WhatsApp/Telegram.
- **Telegram alerts:** connect via your own bot — open @BotFather → /newbot →
  paste the token → "Save bot". "Service messages only: reminders and updates,
  never stock tips or buy/sell calls."
- **Plans (observed):** Trial Free — 25 backtests/day, 10 own strategies, full
  tools, 1 broker account. **Pro Monthly ₹599 +GST/30d; Pro Quarterly ₹1,599
  +GST/90d; Pro Yearly ₹5,399 +GST/365d** — 100 backtests/day, unlimited
  strategies, 4 broker accounts, everything in Trial, robustness check, priority
  support. "Online payment is coming soon… we upgrade by hand via
  support@momentumscore.in."
- **Add-ons:** Backtest pack ₹100 +GST = 500 extra backtests (used only after the
  day's 25, never expire; pack balance shown) · Extra broker account ₹200 +GST/
  month each (on top of the plan's included ones).

## 12. Support & AI

- `/support` "Ask us anything": request type (Question / Something is wrong /
  Feature request), subject, details, optional screenshot ≤3 MB; replies on the
  page + email; earlier requests listed. "We can't give investment advice…
  happy to explain how any part works."
- AI widget: app-help assistant with daily question quota (9–10/day), "Not
  understood? Ask a live agent" handoff.
- Telegram community group linked in Learn/footers.

## 13. Education

- `/learn`: 5 articles (momentum 101, survivorship bias, Supertrend/200-EMA/RSI,
  capital-gains tax, Tamil explainer) + video walkthroughs in 6 languages
  (Tamil, English, Hindi, Telugu, Kannada, Malayalam): Part 1 builder (14 steps),
  Part 2 broker connect & live (16–17 steps).
- `/guide` Ranking guide (interactive): journey diagram (500 → gate → race →
  basket → monthly), gate explainer, **Style lab** (4 made-up stocks; move dials
  and watch the ranking change live), factor definitions ("Under the hood" five
  plain measures: momentum, risk-adjusted, low volatility, steadiness,
  liquidity), Factor Mix demo (marks 0–100, Off/Low/Medium/High weights), Funnel
  demo with live counts, review-day walkthrough (buy zone / hold zone / exit
  line), trend filter, **Rules-or-luck** explainer (date-luck bars, both halves),
  and FAQ with real definitions: fit = percentile vs universe ("matched better
  than 86% of others, a comparison not a forecast"); Conditions vs Rank by
  ("minimum qualification vs interview marks"); 6-month momentum = close vs 126
  trading days ago (week = 5 days, month = 21, year = 252, split/bonus
  adjusted); short vs long periods trade-off; why a stock can be missing
  (universe/conditions/price range/insufficient history); falling stocks can
  rank; backtests are not promises.

## 14. Data & engine notes (observed + stated)

- Daily EOD data to 16 Oct 2026; strategy run 2013-04-18 → today executed in
  ~7.5s; equity curve, 16-index comparison, "data to" stamps everywhere.
- Historical members: N500 from 2012 / Midcap & Smallcap 2016 / Microcap 2021
  real NSE change logs; earlier years estimated (stated).
- Fit = per-day percentile vs the strategy's eligible universe; ranks include
  Δ vs previous ranking date; hold-zone semantics with exit-rank hysteresis.
- Quota model: 25/day (Trial) & 100/day (Pro) "backtest runs": fresh runs,
  Compare re-runs, Robustness (12) and What-if (7) consume; opening saved
  results and viewing ranks are free; pack backtests after daily.
- Tax engine implements the 23 Jul 2024 régime change incl. grandfathering and
  loss carry-forward (equity/STT assumptions stated).

## 15. Not captured / open points

- "Why?" popup contents (needs a click), Compare results screen, Robustness /
  What-if result screens (would consume quota — skipped), live portfolio with an
  actual holding, Broker Connect Windows app UI, share link page with a live id,
  admin (`/super/`) surface, price action of `/pricing` after plan changes.

---

## How this maps to our investment-backtest repo

| MomentumScore feature | Closest thing we have | Gap / idea to port |
|---|---|---|
| Historical (point-in-time) index membership | Static `*_symbols.py` lists + `EQUITY_L.csv` | Biggest trust win. Reconstruct membership over time (low-risk: hardcode known index-change dates; note limitation) |
| Robustness verdict (date-luck + halves, "Holds up / Mixed / Fragile") | Reports 25/85/86 offsets, 46/47 sensitivity | Formal verdict block + per-check details; own "run count" cost model mirrors quota idea (12 runs) |
| What-if Lab (7 standard one-change re-runs) | `wild5_sweep.py`, sweeps 46–47, 76–79 | Standard 7-dial compare page: N up/down, exit up/down, weekly, no-filter, only-rising |
| Health score /10-check /100 | — | Add rule-of-thumb target checklist block to every HTML report |
| "Why?" per rank (fit %, factor marks, funnel cuts) | — | Factor-contribution breakdown per holding in reports |
| Fit = daily percentile vs eligible universe | Rank-based scoring in engines | Percentile output (0–100) as first-class column + "Δ vs last review" |
| Protect: trend filter → cash/half + multi-ETF parking (≤4, %) | EMA200/400 filters (42–45, 90), gold-vs-cash (48–50) | Add "half portfolio" + weighted park basket; VIP: listing-date realism (park→cash before ETF existed) |
| Only buy what is going up / sell when negative | — | Entry gate + daily exit condition variant |
| Buy the dip (index RSI, once/month, XIRR shown) + SIP + step-up | Reports 03/05/07/08/09 (SIP, dip) | Index-RSI top-ups, monthly cap, XIRR in report, live alert tie-in |
| Sell when = daily-checked exits (slot waits in cash) | — | Daily exit-condition check between rebalances |
| Sector caps by weight + max-per-sector + entry rank | — | Sector quota for top-N selection |
| Exit-rank hysteresis (2.5×N heuristic) | Rebalance offsets (85/86) | Easy add; hold zone semantics |
| Whole shares + full cost stack + 4 execution models | Slippage report 89 | STT/stamp/DP + whole-share rounding; prev-close→next-open as default |
| Cost/slippage before-vs-after toggle | — | Show both lines in reports |
| Capital-gains tax engine (2024 régime, grandfathering, carry-forward, FY table) | — | We could emit the same FY tax table from our trade logs |
| Equity curve vs 16 indices + Δ CAGR table | `master_comparison.html/json` | Extend benchmark set incl. factor indices (MOMENTUM 30/50, QUALITY, ALPHA, LOWVOL) |
| Rebalances log (state Up/Down, buys/sells w/ rank+fit, park events, top-8 snapshot) | `rebalance_signal.py` outputs | Audit-style rebalance log in HTML with reasons per trade |
| Share: link toggle + PDF masked (rules/names hidden) | Static HTML reports | Generate masked PDF variant for sharing |
| Export .xlsx / PDF | results*.json + HTML | XLSX export of trades/inputs |
| Portfolios: paper vs broker, start today vs next rebalance, immutable destination | `notify_rebalance.py` | Order-list CSV + "start today" warm-up logic |
| Multi-System mix (cap per system, mix-level SIP + step-up, common period) | `master_comparison` | Mixed-portfolio equity + proportioned SIP |
| Telegram via own bot token; WhatsApp reminders | notify scripts | Own-bot pattern is the easiest to adopt (no service fees) |
| Quota/add-on model, invite referrals (7 days) | — | If we ever ship a hosted service |
| Formula scoring language `ret(1m)/vol(6m)` + validator | Ad-hoc scoring in engines | Tiny expression evaluator for ranking formulas |

# ProPicks India — public-source reconstruction of selection logic

Status: **RECONSTRUCTED FROM PUBLIC SOURCES ONLY.** No paywall was bypassed, no
private endpoint was called, no proprietary code or model weights were obtained.
Everything below comes from Investing.com's own public methodology page, their
support-centre articles, and the free press releases they publish to their news
wire on every monthly rebalance.

Collected 18 Oct 2026.

---

## 0. What was mined, and why it's enough

Investing.com publishes a press release for **every** rebalance, naming the
added/removed tickers, the entry price, and the model's own rationale text
verbatim. Those are free, indexed, and were the primary source here. The
methodology page and support centre supply the structural rules.

The rationale text is the useful part: the model explains its own reasoning
using concrete numbers every single time. That is enough to reverse the
*factor structure* — which is what matters for a clean-room rebuild. The exact
learned metric weights are not recoverable (and would be pointless to chase;
they re-learn monthly across 150+ models).

---

## 1. The five India strategies

| Code | Name | N | Universe | Benchmark | 1Y | 5Y |
|---|---|---|---|---|---|---|
| `NIFTY20` | Bharat Market Outperformers | 20 | large cap | Nifty 50 | +6.96% (2026 YTD) | — |
| `INMM20` | Bharat Mid-Cap Movers | 20 | mid cap | NIFTY Midcap 100 | +7.9% | +432.7% |
| `INSG20` | Bharat Small Cap Gems | 20 | small cap | NIFTY Smallcap 100 | +21.58% (2026 YTD) | — |
| `INB15` | Bharat Bargains | 15 | value | Nifty 50 Value 20 | −1.9% | +404.8% |
| `INIT15` | Bharat Infra Titans | 15 | infra theme | Nifty Infrastructure | −3.1% | +353.4% |

All five went live January 2025. Numbers before that are backtest.

---

## 2. Structural rules (confirmed across ≥4 independent sources)

1. **Rebalance: end of the first trading day of each month** (not the 1st if
   it's a holiday). Every source says this independently.
2. **4–8 names rotated per rebalance** (one source says 6–10). On a 20-slot
   book that is **20–40% monthly turnover**.
3. **Equal weight**, 1/N. Always.
4. **Removal ≠ sell.** Their own words: a stock can be kicked out simply for
   falling to rank #N+1. Also removed on hard criteria failure: index exit,
   market cap drifting out of band, no longer meeting liquidity/sector rules.
   They say this repeatedly and explicitly.
5. **Universe filters before ranking**: market-cap band, index membership,
   liquidity floor, sector, trading frequency, penny stocks stripped out.
6. **Fair-value gate**: the model must see the stock below its own fair value.
   Observed entry upside ranges **+13% to +52%**.
7. Engine: 15+ years of data (sometimes quoted as 25), 50–150 quantitative
   models, 50–150 metrics, per-stock **Financial Health score out of 5** with
   per-factor **sub-scores out of 5** (momentum sub-score 3.9/5 observed as a
   "strongest sub-score").
8. Every addition/removal ships with a written rationale.

---

## 3. Reconstructed pick history (public announcements only)

### `INSG20` Bharat Small Cap Gems

| Rebalance | Action | Names (entry price where published) |
|---|---|---|
| 2026-01-01 | add | InfoBeans Technologies @ ₹812.10 |
| 2026-04-01 | add | auto-components maker (P/E 32.5, PEG −1.67, P/B 2.99, EV/EBITDA 12.4) |
| 2026-06-01 | add | Stove Kraft @ ₹618.31 · Updater Services @ ₹174.45 · Krishna Defence · Gayatri Projects · Muthoot Microfin · Uniparts India |
| 2026-07-01 | add | Datamatics Global Services · Andhra Sugars @ ₹78.27 · Confidence Petroleum @ ₹77.04 · Rishabh Instruments · Gandhar Oil Refinery |
| 2026-08-01 | add | Electronics Mart India · Rolex Rings · Bhansali Engineering Polymers @ ₹115.90 |
| 2026-09-01 | remove | Rishabh Instruments (**+48% booked**); add Rajesh Exports |
| 2026-10-01 | rebal | full 20 refreshed |

Known 2026-10-01 holdings: Stove Kraft, Updater Services, Andhra Sugars, BEPL,
Confidence Petroleum, Rajesh Exports, BCL Industries, Gujarat Industries,
Reliance Infrastructure, TGV SRAAC, Triveni Engineering, Jamna Auto.
That month: 11 up / 9 down. Worst: Rajesh Exports −26.1% (entered 01 Sep),
BCL Industries −16.6%, Gujarat Industries −13.9%.

### `INMM20` Bharat Mid-Cap Movers

| Rebalance | Action | Names |
|---|---|---|
| 2025-05-01 | add | MedPlus Health Services @ ₹806.10 |
| 2025-06-01 | remove | Edelweiss (+37.9%), Nazara Technologies (+37%) |
| 2025-07-01 | remove ×9 | Reliance Infra **+62%** · Mahanagar Gas +19.5% · EID Parry +16.8% · RailTel +7.5% · Gulf Oil +6.4% · Akums Drugs +2.5% · Rallis +2% · Niva Bupa **−11.4%** · Aditya Birla Fashion **−12.6%** |
| 2025-09-01 | remove | KRBL (+19.2%), Ujjivan SFB (+18.2%) |
| 2026-08-01 | hold | Akums Drugs (+17% in Aug), Karnataka Bank, DCB Bank |

Survivors through the Jul-2025 purge: Tanla Platforms, Ujjivan SFB, South
Indian Bank.

Note the July-2025 batch: **7 of 9 exits were profitable, only 2 losses, and
the two losses were the smallest in magnitude.** The model cut winners after
the run and let small losses go too — consistent with a rank-based rotation,
not a stop-loss.

### `NIFTY20` Bharat Market Outperformers

| Rebalance | Action | Names |
|---|---|---|
| 2025-05-01 | add | Vedanta · Nuvama Wealth · SAIL |
| 2026-08-01 | add | Bank of India · New India Assurance · Aditya Birla Sun Life AMC |
| 2026-10-01 | add | fresh positions in financials, energy, healthcare |

### `INIT15` Bharat Infra Titans
2025-10-01 add Data Patterns @ ₹2,631 (booked Gujarat State Petronet +10.1%).
2026-01-01 booked HEG +19.6%. Holdings: Mazagon Dock +38.6%, HPCL +12.8%,
BPCL +11.2%.

### `INB15` Bharat Bargains
2025-08-01 booked Tanla Platforms +30%.

---

## 4. The entry rationales — raw numbers

These are the model's own published figures. Every one follows the same
template: **headline + 3–5 bullets**.

**Andhra Sugars** — *INSG20, 01 Jul 2026*
> "rising momentum, very cheap valuation, and a rock-solid financial position"
- P/B **0.64x**, P/E **~10x**
- fair value ₹119 → **+52% upside**
- revenue **+22%** YoY, EBITDA **~2x** YoY

**Gandhar Oil Refinery** — *INSG20, 01 Jul 2026*
> "strong price momentum, attractive valuation, fast-growing earnings"
- 3-month return **+47%**
- P/E **~11x**, **PEG 0.19**
- Q4 FY26 net profit **+200%** YoY, FY earnings **+64%**
- **net debt-free**, dividend +150%

**Bank of India** — *NIFTY20, 01 Aug 2026*
> "strong market performance, compelling valuation, outstanding growth"
- profit **+36%** YoY to ₹3,068cr, advances **+19%**
- P/E **~5x**, **below book value**
- fair value ₹158 → **+15% upside**
- GNPA **2.9% → 1.81%**
- 1-year return **+30%**, dividend yield 3.4%

**New India Assurance** — *NIFTY20, 01 Aug 2026*
> "strong market momentum, robust growth, attractive valuation"
- profit **+40%** YoY, revenue **+15%**
- 6-month return **+18%**
- P/B **0.74x**
- fair value ₹187 → **+13% upside**

**Aditya Birla Sun Life AMC** — *NIFTY20, 01 Aug 2026*
> "strong stock price momentum, attractive valuation, exceptionally clean balance sheet"
- 1-year **+24%**, 6-month **+37%**
- near debt-free, 3-year ROE **26%**, gross margin **77%**, op margin **62%**
- revenue **+11%**, profit **+12%** last quarter
- target ₹1,150 vs price ~₹1,009

**Unnamed auto-components maker** — *INSG20, 01 Apr 2026*
- P/E **32.5**, PEG **−1.67**, P/B **2.99**, EV/EBITDA **12.4**
- revenue **+14%**, EBITDA **+16%** LTM
- fair value ₹163.55, FCF ₹52bn, op margin 5.7%, gross margin 43.8%
- net debt ₹112bn, **31 consecutive years** of dividends
- Financial Health **3.03/5**, **momentum sub-score 3.9/5 — "strongest sub-score"**
- trading at **91.0% of 52-week high**

---

## 5. The exit rationales — the mirror image

**Rishabh Instruments** — *INSG20, 01 Sep 2026, exited at **+48%***
> "Valuation, Growth, and Price Momentum Lag Peers"
- trades **near 52-week high**
- net profit **dipped ~1%** last quarter
- revenue growing only **5–6%, below industry peers**
- P/E **~32x** "a touch stretched", **fair value estimate sits BELOW current price**
- governance headlines: regulatory warnings, promoter stake-sale rumours
- "This change reflects **portfolio rotation, not a sell signal**."

**Emergent BioSolutions** (same engine, US strategy) — exit after **+97.5%**
- revenue **−30%** LTM / **−21%** quarterly
- valuation still cheap (4.6x earnings, below book) **but growth unsustainable**
- "higher-ranked opportunities elsewhere in the portfolio"

---

## 6. Decoded logic — the cross-month pattern

### 6.1 The four-pillar template (invariant across every rationale)

| # | Pillar | Always present as |
|---|---|---|
| 1 | **Momentum** | a 3m / 6m / 12m price return **percentage** |
| 2 | **Value** | P/E **and** P/B **and/or** PEG/EV-EBITDA, **plus** a fair-value number and its % upside |
| 3 | **Growth** | revenue / EBITDA / net profit **YoY percentage** |
| 4 | **Balance sheet** | "net debt-free" / D/E / ROE / margin figures |

Headline is always a three-word-ish alliteration
("Deep Value Meets Explosive Growth", "Debt-Free, High-Margin, Market Momentum",
"Momentum, Value, and Surging Profits").

Exits are the exact mirror: 52w high → fair value below price → growth
decelerating → multiple stretched → (optional) governance noise.

### 6.2 The actual selection rule

The model is **not** a deep-value screen (that's `INB15` Bharat Bargains, and
note Bargains is *underperforming* at −1.9% 1Y while Small Cap Gems is +21.6%).
It is **not** pure momentum either.

It is **momentum AND still cheap**:

- **Price is up hard** over 3–12 months → trend already confirmed.
- **But the multiple hasn't expanded** — still below fair value, low P/E or
  P/B, PEG compressed.
- **Because earnings are accelerating faster than price.**
- **On a clean balance sheet** (net debt-free repeatedly emphasised).

**The mechanism in one line: buy earnings acceleration *before* the multiple
re-rates; sell once the re-rating has caught up with fair value.**

That's why a stock can be "+47% in 3 months" and simultaneously "trades at
just 11x with PEG 0.19" in the same sentence. Earnings grew faster than price
→ price rose *and* the multiple compressed. That divergence is the whole
edge, and it is the thing to replicate.

### 6.3 Entry conditions (quantified from published examples)

- 3–12m momentum: **strongly positive** (observed +18% 6m to +47% 3m)
- Price vs fair value: **below**, upside **+13% to +52%**
- P/E: wide tolerance — **5x to 32.5x** — *because it's gated on growth*,
  not screened absolutely. P/B **0.64–2.99**; P/B **< 1** is common for
  large-cap picks.
- PEG: **0.19** and **−1.67** both accepted → the *discount to fair value*
  does the work, not a PEG cutoff.
- Debt: **net debt-free** preferred and repeatedly cited
- Growth: revenue/EBITDA **double-digit**, often with an acceleration kicker
  (EBITDA nearly doubling, profit +200%)
- Not at an exhaustive 52w high *at entry* (the 91%-of-52w-high entry was
  still inside the band; entries past 100% of fair value get rejected)

### 6.4 Exit conditions

Rotation out when **any** of:
1. Price at/near 52w high **and** fair value now sits **below** price
2. P/E stretched relative to growth (32x with only 5–6% revenue growth)
3. Growth decelerating below peers
4. Net profit inflects negative for a quarter
5. Governance/regulatory headline risk
6. A higher-ranked candidate simply exists (rank #N+1 push-out)

Explicitly **not** a sell signal. Winners are routinely cut at +48%, +62%,
+37%, +30% — the model harvests before the multiple tops out.

### 6.5 Portfolio mechanics to copy

- Rebalance **first trading day of month**, at close
- **Top 20 (or 15), equal weight**
- Rotate **4–8 names** per month — deliberate ~20–40% churn
- Rank, don't time: no stops, no trailing exits, no profit-taking rules
  outside the monthly re-rank
- Hard universe filters *before* scoring: mcap band, index membership,
  liquidity floor, no penny stocks

### 6.6 What this implies about their small/mid-cap "bait"

For `INSG20`/`INMM20` specifically the target profile is:

> A small/mid-cap that has already re-rated on price but **not on earnings** —
> mid-cycle, cash-generative or net debt-free, revenue/EBITDA inflecting
> double-digit, sitting 15–50% below a fair-value anchor, and visibly leading
> its sector over 3–12 months.

They are fishing in the **gap between price momentum and multiple expansion**
in liquid small/mid-caps — riding the leg where fundamentals have already
turned but the market hasn't finished repricing. Once repriced, it rotates
out and the capital moves to the next un-repriced name.

The churn is the feature: at 4–8 names a month on 20 slots, a full book
turnover happens roughly every **3–5 months**.

---

## 7. Confidence and caveats

**High confidence** (stated verbatim by Investing.com in ≥3 places): monthly
1st-trading-day rebalance, equal weight, 15–20 slots, 4–8 rotates, rank-based
removal ≠ sell, fair-value gate, the four-pillar rationale structure, universe
filters.

**Medium confidence**: the specific factor *weights* — the pillar order and
consistent emphasis suggest momentum and value-to-fair-value dominate, with
growth and balance-sheet as qualifiers rather than primary ranks. Not verifiable.

**Not recoverable** (and not attempted): learned metric weights, the
"fair value" model itself (likely a DCF/Graham-style anchor — the % upside
numbers are consistent with a simple anchor model), the 150 sub-models, and
the Financial Health scoring internals.

**Known gap**: the pick history above is assembled from press releases, which
are written when a move is *interesting*. It is a **biased sample of
rebalances**, not a complete holdings ledger. Months where nothing notable
happened have no article. Treat the history as illustrative of *logic*, not as
a complete portfolio series to benchmark against.

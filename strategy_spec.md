# Trading Strategy Specification (Plain English)

Status: **DRAFT v2 — not approved. No code has been written.**

Changes from v1: position sizing set to 10% of equity per trade (was 100%); the backtest is now run as **two variants** per instrument — frictionless, and a cost-loaded version with 0.05% commission plus one tick of slippage per side.

## 1. Overview

This is a trend-following, breakout system. It holds a **long position or is flat** — it never shorts. It enters when price shows strength (a new 20-day closing high breakout) and exits when price shows weakness (a 10-day closing low breakdown). It is evaluated independently on two instruments:

- **QQQ** (Invesco QQQ Trust, USA)
- **NIFTY 50** (India)

using **daily bars**, over the **full history available from Yahoo Finance** for each symbol.

## 2. Data

- **Source:** Yahoo Finance, daily OHLC(V) bars.
- **History window:** the earliest date Yahoo Finance has data for each symbol through the most recent completed daily bar. (The two instruments will have different start dates — Yahoo's NIFTY 50 history starts later than QQQ's.)
- **Two separate, independent backtests** — one for QQQ, one for NIFTY 50. They are not combined into a single portfolio and do not share capital or interact with each other.
- Each instrument uses its own local trading calendar (US market days for QQQ, Indian market days for NIFTY 50) — no attempt is made to align the two calendars.

## 3. Definitions

- **"Today"** = the current daily bar being evaluated, after its close is known.
- **Highest High of the previous 20 days** = the maximum of the `High` price over the 20 trading days immediately *before* today (today itself is excluded from that lookback window).
- **Lowest Low of the previous 10 days** = the minimum of the `Low` price over the 10 trading days immediately *before* today (today itself is excluded).
- **"Closes above/below"** compares today's `Close` price to that lookback level.

## 4. Entry Rule (Buy)

- Condition: today's `Close` > Highest High of the previous 20 days.
- Action: if currently flat (no position), enter long.
- If already long, this condition is simply ignored (no adding to the position, no pyramiding).

## 5. Exit Rule (Sell / Flatten)

- Condition: today's `Close` < Lowest Low of the previous 10 days.
- Action: if currently long, exit the entire position and go flat.
- If already flat, this condition is ignored (there's nothing to exit).

## 6. Position Rules

- Only ever one of two states per instrument: **long** or **flat**. Never short, never partial size changes.
- No stop-loss other than the 10-day-low close-exit rule above (i.e., no separate hard stop, no trailing stop, no take-profit target).
- No pyramiding / scaling in or out — one entry, one exit per trade cycle.
- No overlapping signals: because the entry needs a new 20-day high close and the exit needs a new 10-day low close, they can't both be true on the same bar under normal conditions.

## 7. Signal & Execution Timing

- Signals (entry/exit) are determined using the **daily closing price**, which is only known once the day's bar is complete.
- See **ASSUMPTIONS** below for exactly when the resulting trade is assumed to execute (this was not specified and materially affects results).

## 8. Warm-Up Period

- No entry signal can be evaluated until at least 20 prior daily bars exist.
- No exit signal can be evaluated until at least 10 prior daily bars exist (only relevant once in a position).

## 9. Position Sizing

- On entry, **10% of current equity** is committed to the position (not 100%). The remaining 90% is held in cash and is not deployed elsewhere.
- Since this system only ever holds zero or one position per instrument at a time, "10% of equity" is a fixed sizing rule, not a scaling/pyramiding mechanism — there is still only ever one position open at once.
- See ASSUMPTIONS for how "equity" is measured at the moment of sizing, and how the un-deployed 90% cash is treated.

## 10. Two Cost Variants

Every backtest (QQQ and NIFTY 50 alike) is produced in **two versions**, otherwise identical:

- **Variant A — Frictionless:** no commission, no slippage. Fills exactly at the assumed execution price (see §7 / Assumption 1).
- **Variant B — Cost-loaded:** on **every fill** (both the entry and the exit, i.e. "per side"):
  - a **0.05% commission** is charged on the notional value of that fill, and
  - **one tick of slippage** is applied against the trader (worse fill price than the frictionless execution price) — buys fill one tick higher, sells fill one tick lower.
  - These two costs stack (both apply to the same fill).

This yields **four total result sets**: QQQ-frictionless, QQQ-cost-loaded, NIFTY50-frictionless, NIFTY50-cost-loaded.

---

## ASSUMPTIONS

Everything below is a decision I made because the request didn't specify it. Please confirm, correct, or override each one before any code is written.

1. **Order execution price/timing:** I'm assuming the trade (both entry and exit) is executed at the **next bar's open**, one day after the signal bar's close, since the close itself can't be traded on in real life. (Alternative: execute at the signal bar's own close, which assumes fills at/near the close — this has look-ahead/fill risk but is common in simplified backtests.)
2. **Price series used for signals:** I'm assuming **unadjusted/raw daily Close, High, Low** as Yahoo Finance returns in its default `Close`/`High`/`Low` columns (not the dividend/split-`Adj Close`-adjusted series), unless you'd rather use adjusted prices throughout (adjusted is usually better practice for QQQ given dividends; NIFTY 50 index itself doesn't pay dividends directly since it's an index level).
3. **NIFTY 50 tradability:** NIFTY 50 is an index, not a directly tradable instrument. I'm assuming you want the backtest run on the **index level itself** (Yahoo ticker `^NSEI`) as a price proxy, not on a specific ETF/futures contract that tracks it. Real-world implementation would need an instrument like Nifty futures or an ETF (e.g., NIFTYBEES) — that's out of scope unless you say otherwise.
4. **Position sizing basis — "10% of equity" measured how:** I'm assuming this means 10% of **total current equity (cash + mark-to-market value of any open position)** at the moment of entry, i.e. it compounds — as equity grows or shrinks over time, each new trade's dollar size grows or shrinks with it. (Alternative: 10% of the *original* starting capital every time, fixed dollar size, no compounding.)
5. **Idle cash (the other 90%):** Assumed to sit in cash earning **zero interest/return** — it's not invested elsewhere and doesn't accrue a risk-free rate. This matters because it drags down overall equity-curve returns compared to a "fully invested" comparison.
6. **Starting capital:** Arbitrary, e.g. 1,000,000 units of the relevant currency (INR for NIFTY 50, USD for QQQ) — since sizing is now 10%-of-equity (a ratio), the absolute starting number doesn't affect % returns/CAGR, only absolute currency figures. Will confirm a number when we build it.
7. **Transaction costs & slippage:** Now split into the two variants described in §10. For the cost-loaded variant:
   - **Commission (0.05%)** is assumed charged on the **notional traded** (10%-of-equity position value) on both the entry fill and the exit fill — not on total equity, and not a flat per-trade fee.
   - **"One tick" of slippage:** for **QQQ**, one tick is assumed to be **$0.01** (the standard US equity minimum price increment). For **NIFTY 50**, since `^NSEI` is an index level with no exchange-defined tick, I'm assuming one tick = **0.05 index points** (mirroring NSE's typical 0.05 tick convention for equity/index-linked instruments quoted to two decimals) — this is a judgment call and should be confirmed, especially since a real NIFTY 50 trade would actually be in a futures or ETF instrument with its own tick size (see Assumption 3).
   - No other cost types (taxes, STT, stamp duty, GST on brokerage, financing/borrow cost) are modeled in either variant.
8. **Dividends (QQQ):** Since I'm assuming unadjusted prices (see #2), dividend cash flows are **not** modeled/reinvested. If you want dividends included, we'd need to switch to adjusted close and reconsider point #2.
9. **End-of-data handling:** If a position is still open on the last available bar of history, I'm assuming it's **marked-to-market / closed out at the last close** for performance reporting purposes (not counted as a realized "exit signal" trade).
10. **Gaps through the trigger level:** If price gaps well beyond the breakout/breakdown level, I'm assuming the trade still just executes at whatever the next bar's open is (no attempt to fill at the exact 20-day-high or 10-day-low price), with slippage in the cost-loaded variant applied on top of that open price — consistent with assumption #1.
11. **Corporate actions / index reconstitution:** No special handling — we just take whatever price history Yahoo Finance serves for the ticker as-is, splits and all (relevant mainly to QQQ; NIFTY 50 as an index doesn't have splits).
12. **Timezone / "day" boundary:** Each instrument's daily bar is whatever Yahoo Finance reports as that day's bar in the exchange's own local session — no timezone conversion or realignment between the two markets.
13. **Benchmark/comparison:** Not specified — I haven't assumed a benchmark (e.g., buy-and-hold QQQ or buy-and-hold NIFTY 50) for comparison, but that's a natural addition once we backtest, if wanted.

---

**Next step:** once you've confirmed/adjusted the assumptions above, I'll write the backtest code (most likely Python with `yfinance` for data).

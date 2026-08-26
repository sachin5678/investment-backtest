"""
Midcap150 Momentum 10 — WITH 2x leverage via Kotak Neo's Margin Trading
Facility (MTF), every disclosed real-world charge modeled, vs. the
original unleveraged strategy on plain cash. Full 2008-2026 history.

Same exact selection/weighting/rebalance logic as every other Midcap
Momentum 10 report (11-19, 24-27, 30-31): equal-weight top 10 by 6m/12m
risk-adjusted momentum, June/December rebalance, no strategy-side stop-
loss (matches report 27's "original" baseline, since the user asked for
the strategy as-is with leverage layered on top, not the stop-loss
variant).

THREE LADDER RUNGS, so the leverage-specific cost can be isolated from
the "just paying real brokerage" cost:
  1. frictionless        — reports 16/17's own number, zero costs at all.
  2. cash + real charges — same strategy, 1x (no leverage), but every
                            statutory + brokerage charge below IS applied.
  3. 2x MTF + all charges — same strategy, but every rebalance buys 2x the
                            notional per position (50% own capital / 50%
                            borrowed), pays MTF interest on the borrowed
                            half, pays the SAME % charges but on 2x the
                            transacted value, AND is subject to a modeled
                            margin call if a position's price falls far
                            enough to breach an assumed maintenance-margin
                            threshold before the next rebalance.

SOURCED CHARGES (Kotak Neo / Kotak Securities, checked 2026-08; see
build_html32.py's rendered citations for the exact pages):
  - MTF interest: 9.69% p.a., simple interest on the funded (borrowed)
    amount only, Trade Free Pro plan — the plan required for this rate;
    that plan also carries 0.10% equity-delivery brokerage (vs. 0.20% on
    the free plan), used below for BOTH the cash and MTF ladder rungs so
    the comparison isn't skewed by picking different plans.
    https://www.kotakneo.com/margin-trading-facility/
    https://www.kotakneo.com/investing-guide/margin-trading/mtf-interest-rate/
  - MTF minimum own-capital margin: 25% of trade value (= 4x max
    leverage) is Kotak's stated minimum; 2x leverage means putting up 50%
    of trade value as your own margin, borrowing the other 50%.
    https://www.kotakneo.com/support/how-much-margins-or-leverage-does-kotak-securities-provide/
  - Pledge/unpledge fee: Rs 20 + GST per ISIN, each way (charged once to
    pledge collateral into MTF at entry, once to unpledge at exit) — a
    FLAT rupee fee, so it's shown separately in build_html32.py against
    an assumed real account size rather than baked into the % index,
    since a flat fee's impact depends entirely on account size.
    https://www.kotakneo.com/support/is-there-any-charge-for-pledge-the-stocks-under-pay-later-mtf/
  - Equity delivery brokerage: 0.10% (Trade Free Pro plan).
    https://www.kotakneo.com/pricing/
  - STT: 0.1% of transaction value, BOTH the buy and sell leg (delivery
    equity — unlike intraday, where STT is sell-side only).
  - NSE cash-segment exchange transaction charge: Rs 2.97 per lakh
    (0.00297%), uniform since SEBI's October 2024 circular replaced the
    old volume-tiered slabs.
  - SEBI turnover fee: Rs 10 per crore (0.0001%).
  - Stamp duty: 0.015%, BUY side only (nationwide flat rate since 2020).
  - GST: 18% on (brokerage + exchange transaction charge + SEBI fee) —
    not levied on STT or stamp duty, which are themselves taxes.

MAINTENANCE MARGIN — THE ONE ASSUMPTION IN THIS REPORT, DISCLOSED UP
FRONT: Kotak does not publish a single maintenance-margin percentage —
SEBI requires dynamic, stock-specific VaR-based margins that move with
each stock's own volatility, and Kotak doesn't expose that full
day-by-day schedule publicly. This report tests three plausible flat
maintenance-margin assumptions (20%/30%/40% of position value) as a
sensitivity range, headlining 30% as the middle scenario — see
build_html32.py's honesty note for exactly what this does and doesn't
capture (real VaR margins move with volatility, a flat assumption here
does not).

Margin-call mechanics: checked daily via the day's intraday LOW (a
maintenance-margin breach is a live, intraday event, not something that
waits for the close); the forced-liquidation fill uses the same
realistic-fill convention as every stop-loss report in this project —
min(day's Open, the exact price at which the breach occurs) — so an
overnight gap through the trigger isn't given an unrealistically kind
fill. No grace period / top-up behaviour is modeled: the position is
force-sold the moment the threshold breaks, which is the conservative,
no-discretion assumption used for every mechanical rule in this project.
"""
import json

import numpy as np
import pandas as pd

from backtest10 import select_top30, rebalance_dates, cumret_drawdown, series_to_points, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes
from backtest27 import load_midcap150_field, build_original

TOP_N = 10
MIN_ELIGIBLE = 30

# ---- Kotak Neo MTF terms, sourced 2026-08 (see module docstring) ----
MTF_MARGIN_PCT = 0.50            # 2x leverage = 50% own capital, 50% borrowed
MTF_RATE_ANNUAL = 0.0969         # Trade Free Pro plan, simple interest on the funded amount
MAINTENANCE_SCENARIOS = [0.20, 0.30, 0.40]   # disclosed assumption, see docstring
HEADLINE_MAINTENANCE = 0.30
PLEDGE_FEE_INR = 20.0             # + GST, per ISIN, per pledge/unpledge event
ILLUSTRATIVE_CAPITAL_INR = 1_000_000.0   # for the flat-fee worked example only

# ---- standard statutory + brokerage charges (both ladder rungs) ----
BROKERAGE_PCT = 0.0010
STT_PCT = 0.0010
EXCH_PCT = 0.0000297
SEBI_PCT = 0.000001
STAMP_PCT_BUY_ONLY = 0.00015
GST_RATE = 0.18


def leg_cost_pct(side):
    base = BROKERAGE_PCT + EXCH_PCT + SEBI_PCT
    gst = base * GST_RATE
    stamp = STAMP_PCT_BUY_ONLY if side == "buy" else 0.0
    return base + gst + STT_PCT + stamp


BUY_COST_PCT = leg_cost_pct("buy")
SELL_COST_PCT = leg_cost_pct("sell")


def metrics_only(series, common_idx):
    series = series.loc[series.index.intersection(common_idx)]

    def norm(s):
        return s / s.iloc[0] * 100.0

    mdd, peak, trough, uw = cumret_drawdown(series, pd.Series(1.0, index=series.index))

    def cagr_of(s):
        y = (s.index[-1] - s.index[0]).days / 365.25
        return float((s.iloc[-1] / s.iloc[0]) ** (1 / y) * 100 - 100) if y > 0 else None

    return {
        "equity_curve": series_to_points(norm(series)),
        "net_return_pct": float((series.iloc[-1] / series.iloc[0] - 1) * 100),
        "cagr_pct": cagr_of(series),
        "max_drawdown_pct": mdd, "max_drawdown_peak_date": peak, "max_drawdown_trough_date": trough,
        "longest_underwater_days": uw,
    }


def build_cash_with_charges(closes, rbdates):
    """Same as build_original, but every buy/sell leg pays the real,
    sourced statutory + brokerage charges above — no leverage, no
    interest, no margin-call risk (a cash position can't be margin-called)."""
    dates = closes.index
    rb_set = set(rbdates)
    date_pos = {d: i for i, d in enumerate(dates)}
    index_level = pd.Series(np.nan, index=dates)
    shares = {}
    started = False

    for i, d in enumerate(dates):
        if d in rb_set:
            t_idx = date_pos[d]
            selected = select_top30(closes, t_idx, top_n=TOP_N, min_eligible=MIN_ELIGIBLE)
            if selected is not None:
                price_today = closes.iloc[t_idx]
                if not started:
                    value_before = 100.0
                    started = True
                else:
                    gross = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares)
                    sell_cost = gross * SELL_COST_PCT
                    value_before = gross - sell_cost
                dollar_each = value_before / len(selected)
                buy_cost_each = dollar_each * BUY_COST_PCT
                net_each = dollar_each - buy_cost_each
                shares = {tk: net_each / price_today[tk] for tk in selected}
        if started:
            price_today = closes.iloc[i]
            val = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares if pd.notna(price_today.get(tk)))
            index_level.iloc[i] = val
    return index_level.dropna()


def build_mtf_leveraged(closes, lows, opens, rbdates, maintenance_margin):
    dates = closes.index
    rb_set = set(rbdates)
    date_pos = {d: i for i, d in enumerate(dates)}
    index_level = pd.Series(np.nan, index=dates)
    positions = {}  # ticker -> {shares, entry_price, entry_date, borrowed, own_capital}
    cash = 0.0
    started = False
    trades = []

    def interest_cost(borrowed, entry_date, exit_date):
        days = max((exit_date - entry_date).days, 0)
        return borrowed * MTF_RATE_ANNUAL / 365.0 * days

    def portfolio_equity(price_today):
        eq = cash
        for tk, p in positions.items():
            px = price_today.get(tk)
            if pd.notna(px):
                eq += p["shares"] * px - p["borrowed"]
        return eq

    def close_position(tk, p, exit_price, exit_date, reason):
        notional_exit = p["shares"] * exit_price
        sell_cost = notional_exit * SELL_COST_PCT
        interest = interest_cost(p["borrowed"], p["entry_date"], exit_date)
        net_proceeds = notional_exit - p["borrowed"] - sell_cost - interest
        pct = (net_proceeds / p["own_capital"] - 1.0) * 100.0
        interest_pct_of_capital = (interest / p["own_capital"]) * 100.0
        trades.append({
            "ticker": tk.replace(".NS", ""), "entry_date": p["entry_date"].strftime("%Y-%m-%d"),
            "exit_date": exit_date.strftime("%Y-%m-%d"), "entry_price": round(p["entry_price"], 2),
            "exit_price": round(exit_price, 2), "pct_return_on_capital": round(pct, 2),
            "interest_paid": round(interest, 4), "interest_pct_of_capital": round(interest_pct_of_capital, 2),
            "reason": reason,
        })
        return net_proceeds

    for i, d in enumerate(dates):
        price_today = closes.iloc[i]
        low_today = lows.iloc[i]
        open_today = opens.iloc[i]

        if not started and d in rb_set:
            t_idx = date_pos[d]
            selected = select_top30(closes, t_idx, top_n=TOP_N, min_eligible=MIN_ELIGIBLE)
            if selected is not None:
                started = True
                own_each = 100.0 / len(selected)
                positions = {}
                for tk in selected:
                    entry_price = float(price_today[tk])
                    notional = own_each / MTF_MARGIN_PCT
                    borrowed = notional - own_each
                    shares = notional / entry_price
                    buy_cost = notional * BUY_COST_PCT
                    positions[tk] = {"shares": shares, "entry_price": entry_price, "entry_date": d,
                                       "borrowed": borrowed, "own_capital": own_each}
                    cash -= buy_cost
            index_level.iloc[i] = portfolio_equity(price_today) if started else np.nan
            continue

        if not started:
            continue

        # 1) margin-call check FIRST, via today's intraday low (skip the
        #    entry day — nothing to check intraday on day 0)
        called = []
        for tk, p in positions.items():
            if d == p["entry_date"]:
                continue
            lo = low_today.get(tk)
            if pd.isna(lo):
                continue
            equity_at_low = p["shares"] * lo - p["borrowed"]
            margin_ratio_at_low = equity_at_low / (p["shares"] * lo) if lo > 0 else 1.0
            if margin_ratio_at_low <= maintenance_margin:
                # exact price at which the ratio would hit the threshold
                trigger_price = p["borrowed"] / (p["shares"] * (1 - maintenance_margin))
                op = open_today.get(tk)
                fill_price = min(op, trigger_price) if pd.notna(op) else trigger_price
                proceeds = close_position(tk, p, fill_price, d, "margin_call")
                cash += proceeds
                called.append(tk)
        for tk in called:
            del positions[tk]

        # 2) rebalance day: close everything remaining, open the new top 10
        if d in rb_set:
            t_idx = date_pos[d]
            for tk, p in positions.items():
                exit_price = float(price_today[tk])
                proceeds = close_position(tk, p, exit_price, d, "rebalance")
                cash += proceeds
            positions = {}
            selected = select_top30(closes, t_idx, top_n=TOP_N, min_eligible=MIN_ELIGIBLE)
            if selected is not None:
                own_each = cash / len(selected)
                for tk in selected:
                    entry_price = float(price_today[tk])
                    notional = own_each / MTF_MARGIN_PCT
                    borrowed = notional - own_each
                    shares = notional / entry_price
                    buy_cost = notional * BUY_COST_PCT
                    positions[tk] = {"shares": shares, "entry_price": entry_price, "entry_date": d,
                                       "borrowed": borrowed, "own_capital": own_each}
                    # own_each is the margin capital committed to this position
                    # (it isn't "spent" out of cash anywhere else — the
                    # notional/borrowed split only determines HOW the position
                    # is funded, not how much of OUR cash it consumes) — must
                    # be drained here, or it silently double-counts: once as
                    # this leftover cash balance, once as the new position's
                    # own mark-to-market equity.
                    cash -= own_each
                    cash -= buy_cost
                cash = 0.0 if abs(cash) < 1e-6 else cash

        index_level.iloc[i] = portfolio_equity(closes.iloc[i])

    # mark remaining open positions to the last available price (interest
    # accrued to date included; sell-side costs/interest-to-exit are NOT,
    # since nothing has actually been sold yet)
    if positions:
        last_price = closes.iloc[-1]
        last_date = dates[-1]
        for tk, p in positions.items():
            px = last_price.get(tk)
            if pd.isna(px):
                continue
            interest_so_far = interest_cost(p["borrowed"], p["entry_date"], last_date)
            equity_now = p["shares"] * px - p["borrowed"] - interest_so_far
            pct = (equity_now / p["own_capital"] - 1.0) * 100.0
            interest_pct_of_capital = (interest_so_far / p["own_capital"]) * 100.0
            trades.append({
                "ticker": tk.replace(".NS", ""), "entry_date": p["entry_date"].strftime("%Y-%m-%d"),
                "exit_date": last_date.strftime("%Y-%m-%d"), "entry_price": round(p["entry_price"], 2),
                "exit_price": round(float(px), 2), "pct_return_on_capital": round(pct, 2),
                "interest_paid": round(interest_so_far, 4), "interest_pct_of_capital": round(interest_pct_of_capital, 2),
                "reason": "still_open",
            })

    return index_level.dropna(), trades


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]

    tickers = list(closes.columns)
    lows = load_midcap150_field("Low", tickers).loc[closes.index, tickers]
    opens = load_midcap150_field("Open", tickers).loc[closes.index, tickers]

    rbdates = rebalance_dates(closes.index, months=(6, 12))

    frictionless = build_original(closes, rbdates)
    cash_charged = build_cash_with_charges(closes, rbdates)

    scenario_series = {}
    scenario_trades = {}
    common_idx = frictionless.index.intersection(cash_charged.index)
    for m in MAINTENANCE_SCENARIOS:
        series, trades = build_mtf_leveraged(closes, lows, opens, rbdates, m)
        scenario_series[m] = series
        scenario_trades[m] = trades
        common_idx = common_idx.intersection(series.index)

    frictionless_metrics = metrics_only(frictionless, common_idx)
    cash_metrics = metrics_only(cash_charged, common_idx)

    def avg(lst):
        return round(float(np.mean([t["pct_return_on_capital"] for t in lst])), 2) if lst else None

    scenarios_out = {}
    for m in MAINTENANCE_SCENARIOS:
        metrics = metrics_only(scenario_series[m], common_idx)
        trades = scenario_trades[m]
        margin_calls = [t for t in trades if t["reason"] == "margin_call"]
        rebalance_exits = [t for t in trades if t["reason"] == "rebalance"]
        still_open = [t for t in trades if t["reason"] == "still_open"]
        # scale-invariant: what share of a position's OWN capital did
        # interest eat, on average, per holding period — unlike a summed
        # rupee/index-point total, this doesn't get swamped by 18 years of
        # compounding making later trades' absolute numbers meaningless
        # relative to earlier ones.
        avg_interest_pct = round(float(np.mean([t["interest_pct_of_capital"] for t in trades])), 2) if trades else None

        trade_stats = {
            "total_positions": len(trades),
            "margin_calls": len(margin_calls),
            "rebalance_exits": len(rebalance_exits),
            "still_open": len(still_open),
            "margin_call_pct_of_positions": round(len(margin_calls) / len(trades) * 100, 1) if trades else None,
            "avg_margin_call_return_on_capital": avg(margin_calls),
            "avg_rebalance_return_on_capital": avg(rebalance_exits),
            "avg_interest_pct_of_capital_per_holding": avg_interest_pct,
        }
        margin_call_sample = (margin_calls[:10] + margin_calls[-10:]) if len(margin_calls) > 20 else margin_calls
        scenarios_out[f"m{int(m*100)}"] = {
            "maintenance_margin_pct": m * 100, "metrics": metrics, "trade_stats": trade_stats,
            "margin_call_trades_sample": margin_call_sample,
        }

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": common_idx[0].strftime("%Y-%m-%d"), "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "mtf_rate_annual_pct": MTF_RATE_ANNUAL * 100,
        "mtf_margin_pct": MTF_MARGIN_PCT * 100,
        "buy_cost_pct": round(BUY_COST_PCT * 100, 4), "sell_cost_pct": round(SELL_COST_PCT * 100, 4),
        "pledge_fee_inr": PLEDGE_FEE_INR, "illustrative_capital_inr": ILLUSTRATIVE_CAPITAL_INR,
        "headline_maintenance_margin_pct": HEADLINE_MAINTENANCE * 100,
        "frictionless": frictionless_metrics,
        "cash_with_charges": cash_metrics,
        "scenarios": scenarios_out,
    }

    with open("results31.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"window {results['start_date']} -> {results['end_date']}")
    print(f"frictionless      CAGR {frictionless_metrics['cagr_pct']:.2f}% / DD {frictionless_metrics['max_drawdown_pct']:.1f}%")
    print(f"cash + charges    CAGR {cash_metrics['cagr_pct']:.2f}% / DD {cash_metrics['max_drawdown_pct']:.1f}%")
    for m in MAINTENANCE_SCENARIOS:
        key = f"m{int(m*100)}"
        sc = scenarios_out[key]
        ts = sc["trade_stats"]
        print(f"2x MTF (maint={m*100:.0f}%)  CAGR {sc['metrics']['cagr_pct']:.2f}% / DD {sc['metrics']['max_drawdown_pct']:.1f}%  "
              f"margin calls {ts['margin_calls']}/{ts['total_positions']} ({ts['margin_call_pct_of_positions']}%)  "
              f"avg margin-call return {ts['avg_margin_call_return_on_capital']}%  avg rebalance return {ts['avg_rebalance_return_on_capital']}%")


if __name__ == "__main__":
    main()

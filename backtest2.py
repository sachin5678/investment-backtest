"""
Strategy 2: "Wait for the dip" — cash-and-wait, once a year, NIFTY 50 only.

Rule (as approved in chat):
  - Each calendar year starts fully in CASH (the prior year's ending balance
    carries over — this compounds year to year).
  - Reference price for the year = NIFTY 50 Close on the FIRST trading day of
    that calendar year (its "Jan 1" anchor).
  - Each day, if still in cash and today's Close <= 90% of that year's
    reference price (a year-to-date decline of 10%, measured off closes),
    deploy 100% of the year's cash into NIFTY. One entry per year, at most.
  - The position (if any) is force-liquidated on the LAST trading day of that
    same calendar year ("withdraw at 31 Dec") — modelled as a scheduled sale
    AT that day's close (not a reactive signal, so no next-day fill lag).
  - If the year never closes 10% below its reference price, the year is spent
    entirely in cash (0% return that year).
  - Two cost variants, same convention as backtest.py: frictionless, and
    cost-loaded (0.05% commission + 1 tick slippage per fill; NIFTY tick =
    0.05 index points). The entry (a reactive signal) fills at the NEXT bar's
    open with slippage against the buyer; the year-end exit is a scheduled
    sale modelled at that day's close, with slippage against the seller.
  - Benchmark: buy-and-hold NIFTY 50, 100% invested from the first usable bar
    to the last, same starting balance, no rebalancing — for direct comparison.

Only full calendar years are used for the year-start anchor (2007 is a partial
year — NIFTY 50 data on Yahoo only starts 2007-09-17 — so the cycle begins in
2008). The final year in the data (2026) may be partial/in-progress; that is
reported separately, not blended into the closed-year statistics.
"""
import json
import math
import numpy as np
import pandas as pd
import yfinance as yf

INITIAL_CAPITAL = 1_000_000.0
COMMISSION_RATE = 0.0005
DIP_THRESHOLD = 0.10   # trigger at -10% from the year's reference price
TICK = 0.05
TICKER = "^NSEI"
CURRENCY_SYMBOL = "₹"


def fetch(ticker):
    df = yf.download(ticker, period="max", auto_adjust=False, progress=False)
    df.columns = df.columns.droplevel(1)
    df = df[["Open", "High", "Low", "Close"]].dropna()
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    return df


def run(df, cost_loaded, initial_capital=INITIAL_CAPITAL):
    dates = df.index
    opens = df["Open"].to_numpy()
    closes = df["Close"].to_numpy()
    years = np.array([d.year for d in dates])
    n = len(df)

    # Skip the partial first calendar year (no true Jan-1 anchor for it).
    first_full_year = years[0] if dates[0].strftime("%m-%d") == "01-01" else years[0] + 1
    start_idx = np.searchsorted(years, first_full_year)

    cash = initial_capital
    shares = 0.0
    state = "waiting"   # 'waiting' or 'deployed'
    pending_buy = False
    year_ref_price = None
    entry_info = None

    equity_curve = np.full(n, np.nan)
    year_records = []
    current_year = None
    in_progress_year = None

    for i in range(start_idx, n):
        y = years[i]
        is_first_day_of_year = (i == start_idx) or (years[i - 1] != y)
        # A true calendar year-end only exists if the data actually rolls into the next
        # year. The dataset's very last row is often mid-year (data pulled today) — that
        # case is NOT a real "31 Dec withdrawal" and must not be forced closed here.
        is_last_day_of_year = (i < n - 1) and (years[i + 1] != y)

        if is_first_day_of_year:
            current_year = y
            year_ref_price = closes[i]
            state = "waiting"
            pending_buy = False

        # execute a pending buy signal (generated on a prior day's close) at today's open
        if pending_buy and state == "waiting":
            fill_price = opens[i] + (TICK if cost_loaded else 0.0)
            notional = cash
            shares = notional / fill_price
            gross = shares * fill_price
            commission = COMMISSION_RATE * gross if cost_loaded else 0.0
            cash -= (gross + commission)
            entry_info = {
                "entry_date": dates[i], "entry_price": float(fill_price),
                "shares": float(shares), "entry_commission": float(commission),
                "entry_cost_basis": float(gross + commission),
            }
            state = "deployed"
            pending_buy = False

        # scheduled year-end liquidation, modelled at TODAY's close (today is the last day of the year)
        was_deployed_at_year_end = is_last_day_of_year and state == "deployed"
        if was_deployed_at_year_end:
            fill_price = closes[i] - (TICK if cost_loaded else 0.0)
            gross = shares * fill_price
            commission = COMMISSION_RATE * gross if cost_loaded else 0.0
            net_proceeds = gross - commission
            cash += net_proceeds
            pnl = net_proceeds - entry_info["entry_cost_basis"]
            year_records.append({
                "year": int(current_year), "triggered": True,
                "entry_date": entry_info["entry_date"], "entry_price": entry_info["entry_price"],
                "exit_date": dates[i], "exit_price": float(fill_price),
                "days_deployed": int((dates[i] - entry_info["entry_date"]).days),
                "pnl": float(pnl), "return_pct": float(pnl / entry_info["entry_cost_basis"] * 100.0),
                "year_ref_price": float(year_ref_price),
            })
            shares = 0.0
            state = "waiting"
            entry_info = None

        # a year that never triggered, now genuinely ending (a real 31 Dec has passed)
        if is_last_day_of_year and not was_deployed_at_year_end:
            year_records.append({
                "year": int(current_year), "triggered": False,
                "entry_date": None, "entry_price": None, "exit_date": None, "exit_price": None,
                "days_deployed": 0, "pnl": 0.0, "return_pct": 0.0, "year_ref_price": float(year_ref_price),
            })

        equity_today = cash + (shares * closes[i] if state == "deployed" else 0.0)
        equity_curve[i] = equity_today

        # generate a new signal from today's close (fills tomorrow's open)
        if state == "waiting" and not pending_buy and closes[i] <= year_ref_price * (1 - DIP_THRESHOLD):
            pending_buy = True

    # in-progress final year (data ends mid-year)
    if state == "deployed":
        in_progress_year = {
            "year": int(current_year), "entry_date": entry_info["entry_date"].strftime("%Y-%m-%d"),
            "entry_price": entry_info["entry_price"], "mark_to_market_price": float(closes[-1]),
            "mark_to_market_value": float(shares * closes[-1]), "as_of": dates[-1].strftime("%Y-%m-%d"),
        }
    elif not (year_records and year_records[-1]["year"] == current_year):
        # loop ended mid-year (data doesn't reach a real 31 Dec yet) and still waiting in cash —
        # not a resolved/closed year, so it was never appended to year_records above.
        in_progress_year = {"year": int(current_year), "status": "still waiting for a -10% dip",
                             "as_of": dates[-1].strftime("%Y-%m-%d"), "year_ref_price": float(year_ref_price)}

    equity_series = pd.Series(equity_curve[start_idx:], index=dates[start_idx:])
    return equity_series, year_records, in_progress_year, dates[start_idx]


def buy_and_hold(df, start_idx, initial_capital=INITIAL_CAPITAL):
    sub = df.iloc[start_idx:]
    entry_price = sub["Open"].iloc[0]
    shares = initial_capital / entry_price
    equity = shares * sub["Close"].to_numpy()
    return pd.Series(equity, index=sub.index), float(entry_price)


def max_drawdown(equity):
    running_max = equity.cummax()
    dd = (equity - running_max) / running_max
    trough_idx = dd.idxmin()
    mdd = dd.min()
    peak_idx = equity.loc[:trough_idx].idxmax()
    return float(mdd * 100.0), peak_idx, trough_idx


def longest_underwater(equity):
    running_max = equity.cummax()
    underwater = equity < running_max
    longest = 0
    longest_start = longest_end = None
    start = None
    dates = equity.index
    for i, uw in enumerate(underwater):
        if uw and start is None:
            start = dates[i - 1] if i > 0 else dates[i]
        if not uw and start is not None:
            span = (dates[i] - start).days
            if span > longest:
                longest = span
                longest_start, longest_end = start, dates[i]
            start = None
    if start is not None:
        span = (dates[-1] - start).days
        if span > longest:
            longest = span
            longest_start, longest_end = start, dates[-1]
    return int(longest), longest_start, longest_end


def cagr(equity):
    total_days = (equity.index[-1] - equity.index[0]).days
    if total_days <= 0:
        return 0.0
    years = total_days / 365.25
    ratio = equity.iloc[-1] / equity.iloc[0]
    if ratio <= 0:
        return -100.0
    return float((ratio ** (1.0 / years) - 1.0) * 100.0)


def year_stats(records):
    triggered = [r for r in records if r["triggered"]]
    n_years = len(records)
    n_triggered = len(triggered)
    wins = [r for r in triggered if r["pnl"] > 0]
    losses = [r for r in triggered if r["pnl"] <= 0]
    win_rate = (len(wins) / n_triggered * 100.0) if n_triggered else None
    avg_win_pct = float(np.mean([r["return_pct"] for r in wins])) if wins else None
    avg_loss_pct = float(np.mean([r["return_pct"] for r in losses])) if losses else None
    net_profit = float(sum(r["pnl"] for r in triggered))
    pnls = sorted([r["pnl"] for r in triggered], reverse=True)
    top_n = min(5, len(pnls))
    top_sum = float(sum(pnls[:top_n])) if pnls else 0.0
    top_pct = (top_sum / net_profit * 100.0) if net_profit != 0 else None
    return {
        "num_years_total": n_years, "num_years_triggered": n_triggered,
        "pct_years_triggered": (n_triggered / n_years * 100.0) if n_years else None,
        "win_rate": win_rate, "avg_win_pct": avg_win_pct, "avg_loss_pct": avg_loss_pct,
        "net_profit": net_profit, "top_n": top_n, "top_n_sum": top_sum, "top_n_pct_of_profit": top_pct,
        "avg_days_deployed": float(np.mean([r["days_deployed"] for r in triggered])) if triggered else None,
    }


def series_to_points(s, max_points=1500):
    if len(s) > max_points:
        idx = np.linspace(0, len(s) - 1, max_points).round().astype(int)
        idx = np.unique(idx)
        s = s.iloc[idx]
    return [[d.strftime("%Y-%m-%d"), float(v)] for d, v in s.items()]


def build():
    df = fetch(TICKER)
    results = {"generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
               "ticker": TICKER, "currency_symbol": CURRENCY_SYMBOL,
               "initial_capital": INITIAL_CAPITAL, "dip_threshold_pct": DIP_THRESHOLD * 100,
               "tick": TICK, "commission_rate_pct": COMMISSION_RATE * 100,
               "data_start": df.index[0].strftime("%Y-%m-%d"), "data_end": df.index[-1].strftime("%Y-%m-%d"),
               "variants": {}}

    strategy_start_idx = None
    for variant_key, cost_loaded in [("frictionless", False), ("cost_loaded", True)]:
        equity, records, in_progress, strat_start_date = run(df, cost_loaded)
        mdd, peak_idx, trough_idx = max_drawdown(equity)
        uw_days, uw_start, uw_end = longest_underwater(equity)
        stats = year_stats(records)
        results["variants"][variant_key] = {
            "equity_curve": series_to_points(equity),
            "start_date": strat_start_date.strftime("%Y-%m-%d"),
            "final_equity": float(equity.iloc[-1]),
            "net_return_pct": float((equity.iloc[-1] / equity.iloc[0] - 1.0) * 100.0),
            "cagr_pct": cagr(equity),
            "max_drawdown_pct": mdd,
            "max_drawdown_peak_date": peak_idx.strftime("%Y-%m-%d"),
            "max_drawdown_trough_date": trough_idx.strftime("%Y-%m-%d"),
            "longest_underwater_days": uw_days,
            "longest_underwater_start": uw_start.strftime("%Y-%m-%d") if uw_start is not None else None,
            "longest_underwater_end": uw_end.strftime("%Y-%m-%d") if uw_end is not None else None,
            "years": [
                {**r, "entry_date": r["entry_date"].strftime("%Y-%m-%d") if r["entry_date"] is not None else None,
                 "exit_date": r["exit_date"].strftime("%Y-%m-%d") if r["exit_date"] is not None else None}
                for r in records
            ],
            "in_progress_year": in_progress,
            "stats": stats,
        }
        if strategy_start_idx is None:
            strategy_start_idx = df.index.get_loc(strat_start_date)

    bh_equity, bh_entry_price = buy_and_hold(df, strategy_start_idx)
    bh_mdd, bh_peak_idx, bh_trough_idx = max_drawdown(bh_equity)
    bh_uw_days, bh_uw_start, bh_uw_end = longest_underwater(bh_equity)
    results["benchmark"] = {
        "equity_curve": series_to_points(bh_equity),
        "entry_price": bh_entry_price,
        "start_date": bh_equity.index[0].strftime("%Y-%m-%d"),
        "final_equity": float(bh_equity.iloc[-1]),
        "net_return_pct": float((bh_equity.iloc[-1] / bh_equity.iloc[0] - 1.0) * 100.0),
        "cagr_pct": cagr(bh_equity),
        "max_drawdown_pct": bh_mdd,
        "max_drawdown_peak_date": bh_peak_idx.strftime("%Y-%m-%d"),
        "max_drawdown_trough_date": bh_trough_idx.strftime("%Y-%m-%d"),
        "longest_underwater_days": bh_uw_days,
        "longest_underwater_start": bh_uw_start.strftime("%Y-%m-%d") if bh_uw_start is not None else None,
        "longest_underwater_end": bh_uw_end.strftime("%Y-%m-%d") if bh_uw_end is not None else None,
    }
    return results


if __name__ == "__main__":
    r = build()
    with open("results2.json", "w") as f:
        json.dump(r, f)
    for vk in ("frictionless", "cost_loaded"):
        v = r["variants"][vk]
        s = v["stats"]
        print(f"[{vk}] years_total={s['num_years_total']} triggered={s['num_years_triggered']} "
              f"win_rate={s['win_rate']} net_return={v['net_return_pct']:.1f}% cagr={v['cagr_pct']:.2f}% "
              f"mdd={v['max_drawdown_pct']:.1f}% uw_days={v['longest_underwater_days']} "
              f"top_pct={s['top_n_pct_of_profit']}")
        print("  years:", [(y["year"], y["triggered"], round(y["return_pct"], 1) if y["triggered"] else 0) for y in v["years"]])
        print("  in_progress:", v["in_progress_year"])
    b = r["benchmark"]
    print(f"[buy_and_hold from {b['start_date']}] net_return={b['net_return_pct']:.1f}% cagr={b['cagr_pct']:.2f}% "
          f"mdd={b['max_drawdown_pct']:.1f}% uw_days={b['longest_underwater_days']}")

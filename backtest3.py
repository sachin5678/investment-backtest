"""
Strategy 3: "Flight to Midcap" — NIFTY 50 by default; on a -15%-from-ATH
drawdown, rotate 100% of the money into midcap for exactly one year, then
rotate back to NIFTY and watch for the next -15% dip. Repeats.

Rule, as specified in chat:
  - Default holding = 100% NIFTY 50. Never idle in cash (unlike strategies 1-2).
  - "ATH" = the running all-time-high of NIFTY 50's daily Close, tracked over
    NIFTY's FULL available history (from 2007) — not reset at the backtest's
    start date — so a drawdown-from-ATH reading at any point is historically
    honest, not an artifact of a late data start.
  - Trigger (reactive signal, close-based, consistent with the other reports):
    while holding NIFTY, if today's Close <= 85% of the running ATH, switch
    ALL money out of NIFTY and into midcap. Fills at the NEXT day's open
    (both the NIFTY sale and the midcap purchase).
  - Hold midcap for exactly 365 calendar days from the switch date, then
    rotate back into NIFTY. This is a scheduled, known-in-advance event, so
    (consistent with the prior report's convention) it is modelled as filling
    AT that day's own close (both legs) rather than the next open.
  - Once back in NIFTY, the -15%-from-ATH trigger is evaluated again starting
    the NEXT trading day (not the same day as the rotation-back) — this
    avoids an artificial same-day double-flip and is disclosed as an
    assumption.
  - Two cost variants: frictionless, and cost-loaded (0.05% commission + one
    tick of slippage on EACH leg of EACH rotation — i.e. 4 fills total per
    full NIFTY->midcap->NIFTY round trip). NIFTY tick = 0.05 index points
    (it's a raw index). The midcap leg uses a real, tradable ETF, so its tick
    is the standard NSE minimum of ₹0.01.
  - Midcap proxy (confirmed in chat): NIFTY Midcap 150 via the MID150BEES.NS
    tracking ETF. Yahoo history for it only starts 2019-02-04, so the actual
    simulated backtest window is 2019-02-04 to the present — much shorter
    than the NIFTY-only reports — even though the ATH used to decide the
    2019+ triggers reflects the full 2007+ NIFTY history.
  - Benchmark: buy-and-hold NIFTY 50 over the identical 2019-02-04-to-present
    window, same starting balance.
"""
import json
import numpy as np
import pandas as pd
import yfinance as yf

INITIAL_CAPITAL = 1_000_000.0
COMMISSION_RATE = 0.0005
ATH_DRAWDOWN_TRIGGER = 0.15   # switch to midcap at -15% from ATH
HOLD_DAYS = 365
NIFTY_TICKER = "^NSEI"
MIDCAP_TICKER = "MID150BEES.NS"
NIFTY_TICK = 0.05
MIDCAP_TICK = 0.01
CURRENCY_SYMBOL = "₹"


def fetch(ticker):
    df = yf.download(ticker, period="max", auto_adjust=False, progress=False)
    df.columns = df.columns.droplevel(1)
    df = df[["Open", "High", "Low", "Close"]].dropna()
    df.index = pd.to_datetime(df.index)
    return df.sort_index()


def run(nifty, midcap, cost_loaded, initial_capital=INITIAL_CAPITAL):
    # ATH tracked over NIFTY's FULL history; backtest itself starts once midcap data exists.
    nifty_full = nifty.copy()
    nifty_full["ath"] = nifty_full["Close"].cummax()

    start_date = midcap.index[0]
    dates = nifty_full.index[nifty_full.index >= start_date]
    dates = dates[dates.isin(midcap.index)]   # only days both instruments actually traded

    n = len(dates)
    nifty_o = nifty_full.loc[dates, "Open"].to_numpy()
    nifty_c = nifty_full.loc[dates, "Close"].to_numpy()
    nifty_ath = nifty_full.loc[dates, "ath"].to_numpy()
    mid_o = midcap.loc[dates, "Open"].to_numpy()
    mid_c = midcap.loc[dates, "Close"].to_numpy()

    state = "nifty"          # 'nifty' or 'midcap'
    shares_nifty = initial_capital / nifty_o[0]
    gross0 = shares_nifty * nifty_o[0]
    commission0 = COMMISSION_RATE * gross0 if cost_loaded else 0.0
    cash_spent = gross0 + commission0
    # (initial buy is frictionless-of-slippage — it's the starting position, not a signal-driven trade)
    shares_midcap = 0.0
    pending_switch_to_midcap = False
    pending_signal = None    # the close/ATH on the day the -15% signal actually fired
    entry_info = None
    switch_back_date = None

    equity_curve = np.empty(n)
    episodes = []

    for i in range(n):
        just_rotated_back_today = False

        # 1) execute a pending NIFTY -> midcap switch (signal from a prior close), at today's open
        if pending_switch_to_midcap and state == "nifty":
            nifty_fill = nifty_o[i] - (NIFTY_TICK if cost_loaded else 0.0)   # selling NIFTY: slippage against seller
            proceeds = shares_nifty * nifty_fill
            sell_commission = COMMISSION_RATE * proceeds if cost_loaded else 0.0
            net_cash = proceeds - sell_commission
            mid_fill = mid_o[i] + (MIDCAP_TICK if cost_loaded else 0.0)      # buying midcap: slippage against buyer
            buy_commission = COMMISSION_RATE * net_cash if cost_loaded else 0.0
            shares_midcap = (net_cash - buy_commission) / mid_fill
            entry_info = {
                "switch_date": dates[i],
                "nifty_exit_price": float(nifty_fill), "midcap_entry_price": float(mid_fill),
                "cost_basis_inr": float(net_cash - buy_commission),
                "nifty_ref_at_switch": float(nifty_c[i]),
                "ath_at_switch": float(nifty_ath[i]),
                # the actual trigger reading, taken on the day the -15% signal fired (one day
                # earlier than the fill) — NOT the fill day's own close, which may have already
                # partly recovered by the time the trade executes the next morning.
                "signal_date": pending_signal["date"], "drawdown_at_signal_pct": pending_signal["drawdown_pct"],
            }
            switch_back_date = dates[i] + pd.Timedelta(days=HOLD_DAYS)
            shares_nifty = 0.0
            state = "midcap"
            pending_switch_to_midcap = False
            pending_signal = None

        # 2) scheduled midcap -> NIFTY switch back, modelled AT today's close (today >= the 1-year mark)
        if state == "midcap" and dates[i] >= switch_back_date:
            mid_fill = mid_c[i] - (MIDCAP_TICK if cost_loaded else 0.0)
            proceeds = shares_midcap * mid_fill
            sell_commission = COMMISSION_RATE * proceeds if cost_loaded else 0.0
            net_cash = proceeds - sell_commission
            nifty_fill = nifty_c[i] + (NIFTY_TICK if cost_loaded else 0.0)
            buy_commission = COMMISSION_RATE * net_cash if cost_loaded else 0.0
            shares_nifty = (net_cash - buy_commission) / nifty_fill

            nifty_return_over_same_window = float((nifty_c[i] / entry_info["nifty_ref_at_switch"] - 1.0) * 100.0)
            midcap_return = float((net_cash / entry_info["cost_basis_inr"] - 1.0) * 100.0)
            episodes.append({
                "switch_to_midcap_date": entry_info["switch_date"], "switch_back_date": dates[i],
                "days_held": int((dates[i] - entry_info["switch_date"]).days),
                "nifty_exit_price": entry_info["nifty_exit_price"], "midcap_entry_price": entry_info["midcap_entry_price"],
                "midcap_exit_price": float(mid_fill), "nifty_reentry_price": float(nifty_fill),
                "ath_at_switch": entry_info["ath_at_switch"],
                "signal_date": entry_info["signal_date"],
                "drawdown_at_switch_pct": entry_info["drawdown_at_signal_pct"],
                "midcap_episode_return_pct": midcap_return,
                "nifty_same_window_return_pct": nifty_return_over_same_window,
                "outperformance_pct": midcap_return - nifty_return_over_same_window,
            })
            shares_midcap = 0.0
            state = "nifty"
            entry_info = None
            just_rotated_back_today = True   # suppress a new trigger check TODAY; resume from tomorrow

        equity_today = shares_nifty * nifty_c[i] if state == "nifty" else shares_midcap * mid_c[i]
        equity_curve[i] = equity_today

        # generate a new signal from today's close (fills tomorrow's open) — not on the same day
        # we just scheduled-rotated back into NIFTY.
        if state == "nifty" and not just_rotated_back_today and not pending_switch_to_midcap:
            if nifty_c[i] <= nifty_ath[i] * (1 - ATH_DRAWDOWN_TRIGGER):
                pending_switch_to_midcap = True
                pending_signal = {
                    "date": dates[i].strftime("%Y-%m-%d"),
                    "drawdown_pct": float((nifty_c[i] / nifty_ath[i] - 1.0) * 100.0),
                }

    equity_series = pd.Series(equity_curve, index=dates)

    in_progress = None
    if state == "midcap":
        in_progress = {
            "switch_to_midcap_date": entry_info["switch_date"].strftime("%Y-%m-%d"),
            "signal_date": entry_info["signal_date"],
            "midcap_entry_price": entry_info["midcap_entry_price"],
            "scheduled_switch_back": switch_back_date.strftime("%Y-%m-%d"),
            "as_of": dates[-1].strftime("%Y-%m-%d"),
            "mark_to_market_value": float(shares_midcap * mid_c[-1]),
            "drawdown_at_switch_pct": entry_info["drawdown_at_signal_pct"],
        }

    return equity_series, episodes, in_progress, dates[0]


def buy_and_hold(nifty, start_date, initial_capital=INITIAL_CAPITAL):
    sub = nifty.loc[nifty.index >= start_date]
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


def episode_stats(episodes):
    n = len(episodes)
    if n == 0:
        return {"num_episodes": 0}
    wins = [e for e in episodes if e["outperformance_pct"] > 0]
    return {
        "num_episodes": n,
        "win_rate": len(wins) / n * 100.0,
        "avg_outperformance_pct": float(np.mean([e["outperformance_pct"] for e in episodes])),
        "avg_midcap_return_pct": float(np.mean([e["midcap_episode_return_pct"] for e in episodes])),
        "avg_nifty_same_window_return_pct": float(np.mean([e["nifty_same_window_return_pct"] for e in episodes])),
    }


def series_to_points(s, max_points=1500):
    if len(s) > max_points:
        idx = np.linspace(0, len(s) - 1, max_points).round().astype(int)
        idx = np.unique(idx)
        s = s.iloc[idx]
    return [[d.strftime("%Y-%m-%d"), float(v)] for d, v in s.items()]


def build():
    nifty = fetch(NIFTY_TICKER)
    midcap = fetch(MIDCAP_TICKER)

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "nifty_ticker": NIFTY_TICKER, "midcap_ticker": MIDCAP_TICKER, "currency_symbol": CURRENCY_SYMBOL,
        "initial_capital": INITIAL_CAPITAL, "ath_trigger_pct": ATH_DRAWDOWN_TRIGGER * 100, "hold_days": HOLD_DAYS,
        "nifty_data_start": nifty.index[0].strftime("%Y-%m-%d"), "nifty_data_end": nifty.index[-1].strftime("%Y-%m-%d"),
        "midcap_data_start": midcap.index[0].strftime("%Y-%m-%d"), "midcap_data_end": midcap.index[-1].strftime("%Y-%m-%d"),
        "variants": {},
    }

    strat_start = None
    for variant_key, cost_loaded in [("frictionless", False), ("cost_loaded", True)]:
        equity, episodes, in_progress, start_date = run(nifty, midcap, cost_loaded)
        mdd, peak_idx, trough_idx = max_drawdown(equity)
        uw_days, uw_start, uw_end = longest_underwater(equity)
        stats = episode_stats(episodes)
        results["variants"][variant_key] = {
            "equity_curve": series_to_points(equity),
            "start_date": start_date.strftime("%Y-%m-%d"),
            "final_equity": float(equity.iloc[-1]),
            "net_return_pct": float((equity.iloc[-1] / equity.iloc[0] - 1.0) * 100.0),
            "cagr_pct": cagr(equity),
            "max_drawdown_pct": mdd,
            "max_drawdown_peak_date": peak_idx.strftime("%Y-%m-%d"),
            "max_drawdown_trough_date": trough_idx.strftime("%Y-%m-%d"),
            "longest_underwater_days": uw_days,
            "longest_underwater_start": uw_start.strftime("%Y-%m-%d") if uw_start is not None else None,
            "longest_underwater_end": uw_end.strftime("%Y-%m-%d") if uw_end is not None else None,
            "episodes": [
                {**e, "switch_to_midcap_date": e["switch_to_midcap_date"].strftime("%Y-%m-%d"),
                 "switch_back_date": e["switch_back_date"].strftime("%Y-%m-%d")}
                for e in episodes
            ],
            "in_progress_episode": in_progress,
            "stats": stats,
        }
        strat_start = start_date

    bh_equity, bh_entry_price = buy_and_hold(nifty, strat_start)
    bh_mdd, bh_peak_idx, bh_trough_idx = max_drawdown(bh_equity)
    bh_uw_days, bh_uw_start, bh_uw_end = longest_underwater(bh_equity)
    results["benchmark_nifty"] = {
        "equity_curve": series_to_points(bh_equity), "entry_price": bh_entry_price,
        "start_date": bh_equity.index[0].strftime("%Y-%m-%d"),
        "final_equity": float(bh_equity.iloc[-1]),
        "net_return_pct": float((bh_equity.iloc[-1] / bh_equity.iloc[0] - 1.0) * 100.0),
        "cagr_pct": cagr(bh_equity), "max_drawdown_pct": bh_mdd,
        "max_drawdown_peak_date": bh_peak_idx.strftime("%Y-%m-%d"), "max_drawdown_trough_date": bh_trough_idx.strftime("%Y-%m-%d"),
        "longest_underwater_days": bh_uw_days,
        "longest_underwater_start": bh_uw_start.strftime("%Y-%m-%d") if bh_uw_start is not None else None,
        "longest_underwater_end": bh_uw_end.strftime("%Y-%m-%d") if bh_uw_end is not None else None,
    }

    # supplementary: buy-and-hold midcap over the same window, for context only
    mid_sub = midcap.loc[midcap.index >= strat_start]
    mid_shares = INITIAL_CAPITAL / mid_sub["Open"].iloc[0]
    mid_equity = pd.Series(mid_shares * mid_sub["Close"].to_numpy(), index=mid_sub.index)
    bh_mid_mdd, _, _ = max_drawdown(mid_equity)
    results["benchmark_midcap"] = {
        "equity_curve": series_to_points(mid_equity),
        "net_return_pct": float((mid_equity.iloc[-1] / mid_equity.iloc[0] - 1.0) * 100.0),
        "cagr_pct": cagr(mid_equity), "max_drawdown_pct": bh_mid_mdd,
    }

    return results


if __name__ == "__main__":
    r = build()
    with open("results3.json", "w") as f:
        json.dump(r, f)
    for vk in ("frictionless", "cost_loaded"):
        v = r["variants"][vk]
        print(f"\n[{vk}] start={v['start_date']} net_return={v['net_return_pct']:.1f}% cagr={v['cagr_pct']:.2f}% "
              f"mdd={v['max_drawdown_pct']:.1f}% uw_days={v['longest_underwater_days']} stats={v['stats']}")
        for e in v["episodes"]:
            print("  episode:", e["switch_to_midcap_date"], "->", e["switch_back_date"],
                  "dd_at_switch=", round(e["drawdown_at_switch_pct"], 1),
                  "midcap_ret=", round(e["midcap_episode_return_pct"], 1),
                  "nifty_ret_same_window=", round(e["nifty_same_window_return_pct"], 1),
                  "outperf=", round(e["outperformance_pct"], 1))
        print("  in_progress:", v["in_progress_episode"])
    print("\nbenchmark_nifty:", r["benchmark_nifty"]["net_return_pct"], r["benchmark_nifty"]["cagr_pct"], r["benchmark_nifty"]["max_drawdown_pct"])
    print("benchmark_midcap:", r["benchmark_midcap"]["net_return_pct"], r["benchmark_midcap"]["cagr_pct"], r["benchmark_midcap"]["max_drawdown_pct"])

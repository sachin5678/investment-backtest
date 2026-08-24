"""
Breakout long/flat backtest — hand-written event loop (no backtesting library).

Strategy (per strategy_spec.md):
  Entry: Close > highest High of the PREVIOUS 20 trading days  -> buy next bar's open
  Exit:  Close < lowest  Low  of the PREVIOUS 10 trading days  -> sell next bar's open
  Long or flat only. Position size = 10% of equity at the moment of signal (compounds).
  Two variants:
    A) Frictionless      - no commission, no slippage
    B) Cost-loaded       - 0.05% commission per fill (on notional) + 1 tick slippage per side
       tick size: QQQ = $0.01 ; NIFTY 50 (^NSEI index) = 0.05 index points (assumption)

Also computes a buy-and-hold benchmark on the same instrument, starting on the
first available bar of the full history, with the same starting balance.

Outputs one JSON file (results.json) consumed by the two HTML report builders.
"""
import json
import math
import numpy as np
import pandas as pd
import yfinance as yf

INITIAL_CAPITAL = 1_000_000.0   # currency units (USD for QQQ, INR for NIFTY 50)
SIZE_FRAC = 0.10                # 10% of equity per trade
COMMISSION_RATE = 0.0005        # 0.05% per fill, cost-loaded variant only
ENTRY_LOOKBACK = 20
EXIT_LOOKBACK = 10

INSTRUMENTS = {
    "QQQ": {"ticker": "QQQ", "label": "QQQ (Invesco QQQ Trust, USA)", "currency": "USD",
             "currency_symbol": "$", "tick": 0.01},
    "NIFTY50": {"ticker": "^NSEI", "label": "NIFTY 50 Index (India)", "currency": "INR",
             "currency_symbol": "₹", "tick": 0.05},
}


def fetch(ticker):
    df = yf.download(ticker, period="max", auto_adjust=False, progress=False)
    df.columns = df.columns.droplevel(1)  # drop the Ticker level
    df = df[["Open", "High", "Low", "Close"]].dropna()
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    return df


def compute_levels(df):
    # Level at row i uses ONLY the 20 (or 10) days strictly BEFORE row i.
    entry_level = df["High"].shift(1).rolling(ENTRY_LOOKBACK).max()
    exit_level = df["Low"].shift(1).rolling(EXIT_LOOKBACK).min()
    return entry_level, exit_level


def run_backtest(df, entry_level, exit_level, tick, cost_loaded, initial_capital=INITIAL_CAPITAL):
    """Event-driven simulation. Signals evaluated on close of day i, orders fill at
    open of day i+1 (see spec Assumption 1). Returns equity curve (pd.Series) and
    a list of closed trades (dicts)."""
    n = len(df)
    dates = df.index
    opens = df["Open"].to_numpy()
    closes = df["Close"].to_numpy()
    el = entry_level.to_numpy()
    xl = exit_level.to_numpy()

    cash = initial_capital
    shares = 0.0
    position = "flat"
    pending = None          # 'buy' / 'sell'
    equity_at_signal = None
    entry_info = None       # dict while a trade is open

    equity_curve = np.empty(n)
    trades = []

    for i in range(n):
        # --- execute any order pending from yesterday's signal, at TODAY's open ---
        if pending == "buy":
            fill_price = opens[i] + (tick if cost_loaded else 0.0)   # slippage against buyer
            notional_target = SIZE_FRAC * equity_at_signal
            shares = notional_target / fill_price
            gross = shares * fill_price
            commission = COMMISSION_RATE * gross if cost_loaded else 0.0
            cash -= (gross + commission)
            position = "long"
            entry_info = {
                "entry_date": dates[i],
                "entry_price": float(fill_price),
                "shares": float(shares),
                "entry_commission": float(commission),
                "entry_cost_basis": float(gross + commission),
            }
            pending = None
        elif pending == "sell":
            fill_price = opens[i] - (tick if cost_loaded else 0.0)   # slippage against seller
            gross = shares * fill_price
            commission = COMMISSION_RATE * gross if cost_loaded else 0.0
            net_proceeds = gross - commission
            cash += net_proceeds
            pnl = net_proceeds - entry_info["entry_cost_basis"]
            trades.append({
                **entry_info,
                "exit_date": dates[i],
                "exit_price": float(fill_price),
                "exit_commission": float(commission),
                "exit_proceeds": float(net_proceeds),
                "pnl": float(pnl),
                "return_pct": float(pnl / entry_info["entry_cost_basis"] * 100.0),
                "holding_days": int((dates[i] - entry_info["entry_date"]).days),
            })
            shares = 0.0
            position = "flat"
            entry_info = None
            pending = None

        # --- mark to market for today ---
        equity_today = cash + (shares * closes[i] if position == "long" else 0.0)
        equity_curve[i] = equity_today

        # --- generate a new signal from TODAY's close (fills tomorrow) ---
        if pending is None and not math.isnan(el[i]) and not math.isnan(xl[i]):
            if position == "flat" and closes[i] > el[i]:
                pending = "buy"
                equity_at_signal = equity_today
            elif position == "long" and closes[i] < xl[i]:
                pending = "sell"

    equity_series = pd.Series(equity_curve, index=dates)

    open_trade = None
    if position == "long":
        open_trade = {
            **entry_info,
            "still_open_at": dates[-1],
            "mark_to_market_price": float(closes[-1]),
            "mark_to_market_value": float(shares * closes[-1]),
        }

    return equity_series, trades, open_trade


def buy_and_hold(df, initial_capital=INITIAL_CAPITAL):
    """Invest 100% of capital at the first bar's open, hold to the last close."""
    opens = df["Open"].to_numpy()
    closes = df["Close"].to_numpy()
    entry_price = opens[0]
    shares = initial_capital / entry_price
    equity = shares * closes
    return pd.Series(equity, index=df.index), entry_price, shares


def max_drawdown(equity):
    running_max = equity.cummax()
    dd = (equity - running_max) / running_max
    trough_idx = dd.idxmin()
    mdd = dd.min()
    peak_idx = equity.loc[:trough_idx].idxmax()
    return float(mdd * 100.0), peak_idx, trough_idx


def longest_underwater(equity):
    """Longest stretch (in calendar days) equity stays below its prior running peak
    before it makes a new all-time high."""
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
    if start is not None:  # still underwater at the end of data
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


def trade_stats(trades):
    n = len(trades)
    if n == 0:
        return {
            "num_trades": 0, "win_rate": None, "avg_win_pct": None, "avg_loss_pct": None,
            "avg_win_amt": None, "avg_loss_amt": None, "top5_pct_of_profit": None,
            "gross_profit": 0.0, "gross_loss": 0.0, "net_profit": 0.0,
        }
    pnls = [t["pnl"] for t in trades]
    wins = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] <= 0]
    win_rate = len(wins) / n * 100.0
    avg_win_amt = float(np.mean([t["pnl"] for t in wins])) if wins else 0.0
    avg_loss_amt = float(np.mean([t["pnl"] for t in losses])) if losses else 0.0
    avg_win_pct = float(np.mean([t["return_pct"] for t in wins])) if wins else 0.0
    avg_loss_pct = float(np.mean([t["return_pct"] for t in losses])) if losses else 0.0
    net_profit = float(sum(pnls))
    gross_profit = float(sum(t["pnl"] for t in wins))
    gross_loss = float(sum(t["pnl"] for t in losses))
    top5 = sorted(pnls, reverse=True)[:5]
    top5_sum = float(sum(top5))
    top5_pct_of_profit = (top5_sum / net_profit * 100.0) if net_profit != 0 else None
    return {
        "num_trades": n, "win_rate": win_rate,
        "avg_win_pct": avg_win_pct, "avg_loss_pct": avg_loss_pct,
        "avg_win_amt": avg_win_amt, "avg_loss_amt": avg_loss_amt,
        "top5_pct_of_profit": top5_pct_of_profit,
        "gross_profit": gross_profit, "gross_loss": gross_loss, "net_profit": net_profit,
        "top5_sum": top5_sum,
    }


def series_to_points(s, max_points=1500):
    """Downsample a date-indexed series to at most max_points (date, value) pairs
    for compact embedding in HTML, always keeping first and last points."""
    if len(s) > max_points:
        idx = np.linspace(0, len(s) - 1, max_points).round().astype(int)
        idx = np.unique(idx)
        s = s.iloc[idx]
    return [[d.strftime("%Y-%m-%d"), float(v)] for d, v in s.items()]


def build_results():
    results = {"generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"), "instruments": {}}

    for key, meta in INSTRUMENTS.items():
        df = fetch(meta["ticker"])
        entry_level, exit_level = compute_levels(df)

        variants = {}
        for variant_key, cost_loaded in [("frictionless", False), ("cost_loaded", True)]:
            equity, trades, open_trade = run_backtest(df, entry_level, exit_level, meta["tick"], cost_loaded)
            mdd, peak_idx, trough_idx = max_drawdown(equity)
            uw_days, uw_start, uw_end = longest_underwater(equity)
            stats = trade_stats(trades)
            variants[variant_key] = {
                "equity_curve": series_to_points(equity),
                "final_equity": float(equity.iloc[-1]),
                "net_return_pct": float((equity.iloc[-1] / equity.iloc[0] - 1.0) * 100.0),
                "cagr_pct": cagr(equity),
                "max_drawdown_pct": mdd,
                "max_drawdown_peak_date": peak_idx.strftime("%Y-%m-%d"),
                "max_drawdown_trough_date": trough_idx.strftime("%Y-%m-%d"),
                "longest_underwater_days": uw_days,
                "longest_underwater_start": uw_start.strftime("%Y-%m-%d") if uw_start is not None else None,
                "longest_underwater_end": uw_end.strftime("%Y-%m-%d") if uw_end is not None else None,
                "trades": [
                    {**t, "entry_date": t["entry_date"].strftime("%Y-%m-%d"),
                     "exit_date": t["exit_date"].strftime("%Y-%m-%d")}
                    for t in trades
                ],
                "open_trade": ({**open_trade,
                                 "entry_date": open_trade["entry_date"].strftime("%Y-%m-%d"),
                                 "still_open_at": open_trade["still_open_at"].strftime("%Y-%m-%d")}
                                if open_trade else None),
                "stats": stats,
            }

        bh_equity, bh_entry_price, bh_shares = buy_and_hold(df)
        bh_mdd, bh_peak_idx, bh_trough_idx = max_drawdown(bh_equity)
        bh_uw_days, bh_uw_start, bh_uw_end = longest_underwater(bh_equity)
        benchmark = {
            "equity_curve": series_to_points(bh_equity),
            "entry_price": float(bh_entry_price),
            "start_date": df.index[0].strftime("%Y-%m-%d"),
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

        results["instruments"][key] = {
            "label": meta["label"], "ticker": meta["ticker"], "currency": meta["currency"],
            "currency_symbol": meta["currency_symbol"], "tick": meta["tick"],
            "data_start": df.index[0].strftime("%Y-%m-%d"),
            "data_end": df.index[-1].strftime("%Y-%m-%d"),
            "num_bars": int(len(df)),
            "initial_capital": INITIAL_CAPITAL,
            "variants": variants,
            "benchmark": benchmark,
        }

    return results


if __name__ == "__main__":
    results = build_results()
    with open("results.json", "w") as f:
        json.dump(results, f, indent=None)
    # quick console summary
    for key, inst in results["instruments"].items():
        print(f"\n=== {inst['label']} ({inst['data_start']} to {inst['data_end']}, {inst['num_bars']} bars) ===")
        for vk in ("frictionless", "cost_loaded"):
            v = inst["variants"][vk]
            s = v["stats"]
            print(f"  [{vk}] trades={s['num_trades']} win_rate={s['win_rate']} "
                  f"net_return={v['net_return_pct']:.1f}% cagr={v['cagr_pct']:.2f}% "
                  f"mdd={v['max_drawdown_pct']:.1f}% uw_days={v['longest_underwater_days']} "
                  f"top5_pct={s['top5_pct_of_profit']}")
        b = inst["benchmark"]
        print(f"  [buy_and_hold] net_return={b['net_return_pct']:.1f}% cagr={b['cagr_pct']:.2f}% "
              f"mdd={b['max_drawdown_pct']:.1f}% uw_days={b['longest_underwater_days']}")
    print("\nWrote results.json")

"""
Monthly RSI-70 crossover rotation — a genuinely different SIGNAL from every
earlier reconstruction in this project (all of which use the 6m/12m
risk-adjusted momentum formula). This one uses classic technical-analysis
RSI instead:

  - Universe: NIFTY 500 (this project's standing proxy for "the Indian
    market" — see every earlier report; a true all-listed-stocks universe
    isn't in this project's data).
  - Market-cap filter (> Rs 2,000 Cr): checked against today's market cap
    (the only snapshot available — no historical point-in-time market cap
    data exists in this project, same limitation as every quality/sector
    report). IMPORTANT, disclosed finding: this filter turned out to be a
    NO-OP — all 500 NIFTY 500 constituents already have a market cap above
    Rs 2,000 Cr today (min. observed: ~Rs 5,430 Cr), because NIFTY 500 is
    already "the 500 largest listed companies" by construction. The filter
    would only bind on a universe that also included true small/micro-caps
    below the NIFTY 500 cutoff, which this project doesn't have.
  - Signal: monthly RSI(14), Wilder-smoothed, computed on MONTH-END closing
    prices (not daily RSI — deliberately slower-moving). At the start of
    every calendar month, look at whether a stock's RSI genuinely CROSSED
    above 70 at the end of the just-completed month (RSI(m-1) > 70 AND
    RSI(m-2) <= 70) — a fresh crossover event, not merely "RSI is currently
    above 70" (a materially different, and more selective, condition).
  - Selection: among stocks with a fresh cross this month, rank by RSI
    value (highest first), take the top 5. If fewer than 5 stocks cross,
    hold however many did; if none cross, hold 100% cash that month (a
    judgment call — not specified in the request).
  - Equal-weighted, bought at the close of the month's first trading day,
    held to the close of the day before next month's first trading day,
    then the whole process repeats.

No transaction costs modeled — worth flagging especially here, since up to
5 positions can turn over completely every single month.
"""
import json

import numpy as np
import pandas as pd

from backtest10 import fetch, cumret_drawdown, series_to_points, CURRENCY_SYMBOL
from backtest13 import metrics
from backtest17 import load_nifty500_closes

RSI_PERIOD = 14
RSI_THRESHOLD = 70.0
TOP_N = 5
MIN_CAP_CR = 2000.0
MIN_ELIGIBLE_SIGNAL_POOL = 50  # require at least this many stocks with a valid RSI reading before trusting a month


def compute_monthly_rsi(monthly_closes, period=RSI_PERIOD):
    """Wilder-smoothed RSI on a (dates x tickers) monthly-close DataFrame."""
    delta = monthly_closes.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - 100 / (1 + rs)
    # "no losses in the lookback at all" -> RSI defined as 100, but ONLY where
    # avg_loss is a genuine, defined ~zero — NOT wherever avg_loss is NaN
    # (not enough history yet). NaN > 1e-9 evaluates to False in pandas, so a
    # naive avg_loss.abs() > 1e-9 mask would wrongly treat "no data yet" the
    # same as "zero losses" and fabricate RSI=100 for unlisted stocks.
    zero_loss = avg_loss.notna() & (avg_loss.abs() <= 1e-9)
    rsi = rsi.where(~zero_loss, 100.0)
    return rsi


def first_trading_day_of_month(dates):
    df = pd.Series(dates, index=dates)
    out = []
    for (_y, _m), grp in df.groupby([dates.year, dates.month]):
        out.append(grp.iloc[0])
    return sorted(out)


def load_market_caps():
    with open("fundamentals_raw.pkl", "rb") as f:
        import pickle
        raw = pickle.load(f)
    return {t: v.get("market_cap") for t, v in raw.items() if v.get("market_cap")}


def build_rotation(closes, monthly_rsi, crossed, rebal_dates, eligible_tickers):
    """Event loop keyed off a persistent scalar `current_value` — NOT off
    reading the previous row of the output Series, which is still NaN for
    every day before the very first rebalance and would (did, in an
    earlier version of this function) silently poison the first cash
    month's value into NaN."""
    dates = closes.index
    rebal_set = set(rebal_dates)

    value = pd.Series(np.nan, index=dates)
    shares = {}
    current_value = 100.0
    selections = []
    started = False

    for i, d in enumerate(dates):
        price_today = closes.iloc[i]
        if d in rebal_set:
            # the most recently completed monthly bar strictly before this rebalance date
            past_monthly = monthly_rsi.index[monthly_rsi.index < d]
            if len(past_monthly) > 0:
                m_end = past_monthly[-1]
                crossed_today = crossed.loc[m_end]
                candidates = [
                    t for t in eligible_tickers
                    if bool(crossed_today.get(t, False)) and pd.notna(price_today.get(t))
                ]
                candidates_ranked = sorted(candidates, key=lambda t: monthly_rsi.loc[m_end, t], reverse=True)
                selected = candidates_ranked[:TOP_N]

                if started and shares:
                    current_value = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares if pd.notna(price_today.get(tk)))
                started = True  # current_value already correct either way (100.0 on day 1, marked-to-market above otherwise)

                if selected:
                    dollar_each = current_value / len(selected)
                    shares = {tk: dollar_each / price_today[tk] for tk in selected}
                else:
                    shares = {}  # cash month — current_value stays flat until the next rebalance

                selections.append({
                    "date": d.strftime("%Y-%m-%d"),
                    "signal_month_end": m_end.strftime("%Y-%m-%d"),
                    "num_crossed": len(candidates),
                    "tickers": selected,
                    "rsi_values": {t: round(float(monthly_rsi.loc[m_end, t]), 1) for t in selected},
                    "portfolio_value": float(current_value),
                })
        if started:
            if shares:
                current_value = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares if pd.notna(price_today.get(tk)))
            # else: cash month — current_value intentionally left unchanged (flat)
            value.iloc[i] = current_value

    value = value.dropna()
    return value, selections


def main():
    closes = load_nifty500_closes()
    nifty = fetch("^NSEI")
    midcap_etf = fetch("MID150BEES.NS")
    closes = closes.loc[closes.index.intersection(nifty.index)]

    market_caps = load_market_caps()
    eligible_tickers = [t for t in closes.columns if (market_caps.get(t) or 0) / 1e7 > MIN_CAP_CR]
    excluded_by_cap = [t for t in closes.columns if t not in eligible_tickers]

    monthly_closes = closes.resample("ME").last()
    monthly_rsi = compute_monthly_rsi(monthly_closes)
    crossed = (monthly_rsi > RSI_THRESHOLD) & (monthly_rsi.shift(1) <= RSI_THRESHOLD)

    # backtest starts once a reasonably broad signal pool is available
    signal_pool_size = monthly_rsi.notna().sum(axis=1)
    valid_months = signal_pool_size[signal_pool_size >= MIN_ELIGIBLE_SIGNAL_POOL].index
    if len(valid_months) == 0:
        raise RuntimeError("Never reached the minimum eligible signal pool size.")
    earliest_valid_month = valid_months[0]

    all_rebal_dates = first_trading_day_of_month(closes.index)
    rebal_dates = [d for d in all_rebal_dates if d > earliest_valid_month]

    rotation_value, selections = build_rotation(closes, monthly_rsi, crossed, rebal_dates, eligible_tickers)
    start_date, end_date = rotation_value.index[0], rotation_value.index[-1]

    common = nifty.index[(nifty.index >= start_date) & (nifty.index <= end_date)]
    common = common.intersection(rotation_value.index)
    rotation_series = rotation_value.loc[common]
    nifty_series = nifty.loc[common, "Close"]
    midcap_common = common[common.isin(midcap_etf.index)]
    midcap_series = midcap_etf.loc[midcap_common, "Close"]

    def norm(s):
        return s / s.iloc[0] * 100.0

    cash_months = sum(1 for s in selections if len(s["tickers"]) == 0)
    partial_months = sum(1 for s in selections if 0 < len(s["tickers"]) < TOP_N)
    full_months = sum(1 for s in selections if len(s["tickers"]) == TOP_N)
    avg_stocks_held = float(np.mean([len(s["tickers"]) for s in selections])) if selections else 0.0

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "universe_size": len(closes.columns),
        "eligible_after_mcap_filter": len(eligible_tickers),
        "excluded_by_mcap_filter": len(excluded_by_cap),
        "min_cap_cr": MIN_CAP_CR,
        "rsi_period": RSI_PERIOD,
        "rsi_threshold": RSI_THRESHOLD,
        "top_n": TOP_N,
        "start_date": start_date.strftime("%Y-%m-%d"), "end_date": end_date.strftime("%Y-%m-%d"),
        "num_rebalances": len(selections),
        "cash_months": cash_months, "partial_months": partial_months, "full_months": full_months,
        "avg_stocks_held": round(avg_stocks_held, 2),
        "selections_sample": (selections[:4] + selections[-4:]) if len(selections) > 8 else selections,
        "rsi_rotation": {"equity_curve": series_to_points(norm(rotation_series)), **metrics(rotation_series)},
        "nifty": {"equity_curve": series_to_points(norm(nifty_series)), **metrics(nifty_series)},
        "midcap_etf": {"equity_curve": series_to_points(norm(midcap_series)), **metrics(midcap_series)},
    }
    with open("results21.json", "w") as f:
        json.dump(results, f)

    print("start", start_date.date(), "end", end_date.date(), "rebalances", len(selections))
    print("eligible after mcap filter:", len(eligible_tickers), "of", len(closes.columns), "-- excluded:", len(excluded_by_cap))
    for k in ("rsi_rotation", "nifty", "midcap_etf"):
        v = results[k]
        print(f"[{k}] net_return={v['net_return_pct']:.1f}% cagr={v['cagr_pct']:.2f}% "
              f"mdd={v['max_drawdown_pct']:.1f}% uw_days={v['longest_underwater_days']}")
    print(f"\ncash months (0 stocks): {cash_months} / {len(selections)}")
    print(f"partial months (1-4 stocks): {partial_months}")
    print(f"full months (5 stocks): {full_months}")
    print(f"avg stocks held per month: {avg_stocks_held:.2f}")
    print("\nfirst 4 rebalances:")
    for s in selections[:4]:
        print(" ", s["date"], s["num_crossed"], "crossed ->", s["tickers"], s["rsi_values"])
    print("last 4 rebalances:")
    for s in selections[-4:]:
        print(" ", s["date"], s["num_crossed"], "crossed ->", s["tickers"], s["rsi_values"])


if __name__ == "__main__":
    main()

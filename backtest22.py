"""
Monthly RSI-70 crossover rotation — REVISED per your corrections:

  - No minimum eligible-pool floor. The backtest starts the moment even a
    single stock has enough history for a valid RSI reading — no
    MIN_ELIGIBLE_SIGNAL_POOL gate.
  - RSI is a "monthly RSI" in the sense that it's Wilder(14) on monthly
    closes, but it's evaluated EVERY trading day, not just once a month.
    Concretely: take the Wilder EMA (avg gain / avg loss) state as of the
    end of the last COMPLETED calendar month, then compute a "developing"
    RSI value for each day of the current month by treating that day's
    close as a stand-in for "this month's close so far" — one more Wilder
    step from the same fixed base. This is the standard way a "monthly
    RSI" updates live on a chart before the month closes, and it means a
    crossover can be caught on ANY trading day, not just month boundaries.
  - Entries happen on the exact day a stock's developing RSI crosses above
    70 (yesterday's developing value <=70, today's >70) — not gated to the
    first of the month. Up to 5 positions can be held CONCURRENTLY. If
    more stocks cross on a single day than there are open slots, the ones
    that fill the remaining slots are chosen AT RANDOM (not ranked) among
    that day's crossers, per your instruction.
  - Each position exits on whichever comes first: (a) a 15% drop from its
    OWN entry price, or (b) the last trading day of the calendar month it
    was entered in. Exiting frees a slot for a new crossing candidate.
  - New entries are funded from whatever cash is currently uninvested,
    split equally among however many new entries happen that day. Existing
    positions are never rebalanced mid-flight — they run untouched until
    their own exit.

UNIVERSE — the full ask, not just NIFTY 500: "any NSE stock with market cap
above Rs 2,000 Cr." Built from NSE's own official listed-equity CSV
(archives.nseindia.com/content/equities/EQUITY_L.csv, 2,296 EQ-series
tickers — the trade-to-trade BE/BZ segments are excluded, different
settlement mechanics this project doesn't model), with today's market cap
fetched per ticker (1,975 of 2,296 succeeded even after retries — 321
genuinely unreachable, excluded rather than guessed at). 1,091 of the 1,975
qualify at > Rs 2,000 Cr — more than double the NIFTY 500's 498, exactly
because NIFTY 500 by construction only holds the 500 LARGEST names and
misses a real population of smaller (but still > Rs 2,000 Cr) companies.
Full daily price history was fetched fresh for the ~591 qualifying tickers
not already cached from this project's other reports.
"""
import json
import pickle
import random

import numpy as np
import pandas as pd

from backtest10 import fetch, series_to_points, CURRENCY_SYMBOL
from backtest13 import metrics

MARKETCAP_FILE = "nse_marketcaps_merged.json"
EXTRA_PRICES_FILE = "rsi_universe_extra_raw.pkl"

RSI_PERIOD = 14
RSI_THRESHOLD = 70.0
MAX_POSITIONS = 5
STOP_LOSS_PCT = 0.15
MIN_CAP_CR = 2000.0
RANDOM_SEED = 42  # for the "pick randomly among same-day crossers" rule — fixed so the report is reproducible


def compute_developing_rsi(closes, period=RSI_PERIOD):
    """Returns a (dates x tickers) DataFrame of the "developing monthly
    RSI" for every trading day: Wilder(14) RSI computed on monthly closes,
    but re-evaluated daily by treating each day's close as a stand-in for
    "this month's close so far," extending from the fixed EMA state as of
    the end of the last COMPLETED month. Continuous across month
    boundaries: the last trading day of month M has a developing value
    that exactly equals month M's own officially-completed RSI, since
    that day's close IS the month-end close by definition."""
    monthly_closes = closes.resample("ME").last()
    delta = monthly_closes.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()

    # map each trading day to the most recently COMPLETED month's EMA state
    month_end_dates = monthly_closes.index
    daily_month_end_pos = month_end_dates.searchsorted(closes.index, side="left") - 1
    valid = daily_month_end_pos >= 0
    prev_month_end = pd.DatetimeIndex(
        [month_end_dates[p] if v else pd.NaT for p, v in zip(daily_month_end_pos, valid)]
    )

    base_close = monthly_closes.reindex(prev_month_end).set_axis(closes.index)
    base_avg_gain = avg_gain.reindex(prev_month_end).set_axis(closes.index)
    base_avg_loss = avg_loss.reindex(prev_month_end).set_axis(closes.index)

    change = closes - base_close
    dev_gain = change.clip(lower=0)
    dev_loss = (-change).clip(lower=0)
    dev_avg_gain = (base_avg_gain * (period - 1) + dev_gain) / period
    dev_avg_loss = (base_avg_loss * (period - 1) + dev_loss) / period

    rs = dev_avg_gain / dev_avg_loss
    rsi = 100 - 100 / (1 + rs)
    zero_loss = dev_avg_loss.notna() & (dev_avg_loss.abs() <= 1e-9)
    rsi = rsi.where(~zero_loss, 100.0)
    return rsi


def qualifying_tickers(min_cap_cr=MIN_CAP_CR):
    """Every NSE EQ-series ticker with a known market cap above the
    threshold — see MARKETCAP_FILE's own generation scripts
    (fetch_all_nse_marketcaps.py + retry_missing_marketcaps.py) for how
    it was built and which tickers were unreachable."""
    with open(MARKETCAP_FILE) as f:
        mcaps = json.load(f)
    return sorted(t for t, v in mcaps.items() if v and v / 1e7 > min_cap_cr)


def _all_price_sources():
    names = ["universe_raw.pkl", "quality50_extra_raw.pkl", "midcap150_extra_raw.pkl",
             "smallcap250_extra_raw.pkl", EXTRA_PRICES_FILE]
    sources = []
    for name in names:
        try:
            sources.append(pd.read_pickle(name))
        except FileNotFoundError:
            pass
    return sources


def load_universe_field(field, tickers, index_like=None):
    """Pulls one OHLC field for an arbitrary ticker list across every price
    cache this project has accumulated (the original NIFTY 200 fetch, the
    three "extra" caches built for quality/midcap150/smallcap250 reports,
    and this report's own new ~591-ticker fetch for names beyond NIFTY
    500) — whichever source actually has the ticker. Used for Close, Low,
    and Open: Low/Open specifically so the stop-loss can be checked
    against the day's actual traded range rather than only the close,
    which let losses run to -80/-90% on overnight gaps in an earlier
    version of this backtest before the check ever fired."""
    sources = _all_price_sources()
    cols = {}
    for t in tickers:
        for src in sources:
            if t in set(c[0] for c in src.columns):
                s = src[(t, field)]
                if s.notna().any():
                    cols[t] = s
                break
    df = pd.DataFrame(cols).sort_index().ffill()
    return df.reindex(index_like) if index_like is not None else df


def last_trading_day_of_month(dates):
    """For every date, the last trading day of ITS calendar month — used
    to compute each position's own forced exit date at entry time."""
    df = pd.Series(dates, index=dates)
    last_day_map = {}
    for (y, m), grp in df.groupby([dates.year, dates.month]):
        last_day_map[(y, m)] = grp.iloc[-1]
    return pd.DatetimeIndex([last_day_map[(d.year, d.month)] for d in dates])


def build_rotation(closes, lows, opens, crossed, eligible_tickers):
    dates = closes.index
    month_end_of = last_trading_day_of_month(dates)
    rng = random.Random(RANDOM_SEED)

    cash = 100.0
    positions = {}  # ticker -> {"shares": float, "entry_price": float, "exit_by": Timestamp}
    value = pd.Series(np.nan, index=dates)
    events = []
    started = False

    for i, d in enumerate(dates):
        price_today = closes.iloc[i]
        low_today = lows.iloc[i]
        open_today = opens.iloc[i]

        # 1) exits first — stop-loss checked against the day's LOW (not just
        # the close), since a stock can gap through -15% overnight; if the
        # day's OPEN already gapped below the stop level, that open is the
        # realistic fill price (the theoretical stop price was never
        # actually available to trade at).
        for t in list(positions.keys()):
            p = positions[t]
            px = price_today.get(t)
            lo = low_today.get(t)
            op = open_today.get(t)
            if pd.isna(px):
                continue
            stop_price = p["entry_price"] * (1 - STOP_LOSS_PCT)
            stop_hit = pd.notna(lo) and lo <= stop_price
            month_end_hit = d >= p["exit_by"]
            if stop_hit or month_end_hit:
                if stop_hit:
                    fill_price = min(op, stop_price) if pd.notna(op) else stop_price
                else:
                    fill_price = px
                proceeds = p["shares"] * fill_price
                cash += proceeds
                del positions[t]
                events.append({
                    "date": d.strftime("%Y-%m-%d"), "event": "exit", "ticker": t,
                    "reason": "stop_loss_15pct" if stop_hit else "month_end",
                    "entry_price": round(p["entry_price"], 2), "exit_price": round(float(fill_price), 2),
                    "pnl_pct": round((fill_price / p["entry_price"] - 1) * 100, 2),
                })

        # 2) entries — only on days with at least one open slot and one fresh crosser
        open_slots = MAX_POSITIONS - len(positions)
        if open_slots > 0:
            candidates = [
                t for t in eligible_tickers
                if t not in positions and bool(crossed.iloc[i].get(t, False)) and pd.notna(price_today.get(t))
            ]
            if candidates:
                if len(candidates) > open_slots:
                    chosen = rng.sample(candidates, open_slots)
                else:
                    chosen = candidates
                if chosen:
                    started = True
                    dollar_each = cash / len(chosen)
                    for t in chosen:
                        px = price_today[t]
                        shares = dollar_each / px
                        cash -= dollar_each
                        positions[t] = {"shares": shares, "entry_price": float(px), "exit_by": month_end_of[i]}
                        events.append({
                            "date": d.strftime("%Y-%m-%d"), "event": "entry", "ticker": t,
                            "entry_price": round(float(px), 2), "dollar_allocated": round(dollar_each, 2),
                            "num_crossed_today": len(candidates), "num_slots_open": open_slots,
                        })

        if started:
            mtm = cash + sum(p["shares"] * price_today.get(t, np.nan) for t, p in positions.items() if pd.notna(price_today.get(t)))
            value.iloc[i] = mtm

    value = value.dropna()
    return value, events


def main():
    eligible_tickers = qualifying_tickers()
    nifty = fetch("^NSEI")
    midcap_etf = fetch("MID150BEES.NS")

    closes = load_universe_field("Close", eligible_tickers)
    closes = closes.loc[closes.index.intersection(nifty.index)]
    eligible_tickers = [t for t in eligible_tickers if t in closes.columns]
    closes = closes[eligible_tickers]
    lows = load_universe_field("Low", eligible_tickers, closes.index)[eligible_tickers]
    opens = load_universe_field("Open", eligible_tickers, closes.index)[eligible_tickers]

    developing_rsi = compute_developing_rsi(closes)
    crossed = (developing_rsi > RSI_THRESHOLD) & (developing_rsi.shift(1) <= RSI_THRESHOLD)

    rotation_value, events = build_rotation(closes, lows, opens, crossed, eligible_tickers)
    start_date, end_date = rotation_value.index[0], rotation_value.index[-1]

    common = nifty.index[(nifty.index >= start_date) & (nifty.index <= end_date)]
    common = common.intersection(rotation_value.index)
    rotation_series = rotation_value.loc[common]
    nifty_series = nifty.loc[common, "Close"]
    midcap_common = common[common.isin(midcap_etf.index)]
    midcap_series = midcap_etf.loc[midcap_common, "Close"]

    def norm(s):
        return s / s.iloc[0] * 100.0

    entries = [e for e in events if e["event"] == "entry"]
    exits = [e for e in events if e["event"] == "exit"]
    stop_loss_exits = [e for e in exits if e["reason"] == "stop_loss_15pct"]
    month_end_exits = [e for e in exits if e["reason"] == "month_end"]
    win_rate = (sum(1 for e in exits if e["pnl_pct"] > 0) / len(exits) * 100) if exits else None
    avg_pnl = float(np.mean([e["pnl_pct"] for e in exits])) if exits else None

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "universe_size": len(closes.columns),
        "universe_note": "Any NSE EQ-series stock with market cap > Rs 2,000 Cr (not restricted to NIFTY 500)",
        "min_cap_cr": MIN_CAP_CR,
        "rsi_period": RSI_PERIOD,
        "rsi_threshold": RSI_THRESHOLD,
        "max_positions": MAX_POSITIONS,
        "stop_loss_pct": STOP_LOSS_PCT * 100,
        "start_date": start_date.strftime("%Y-%m-%d"), "end_date": end_date.strftime("%Y-%m-%d"),
        "num_entries": len(entries), "num_exits": len(exits),
        "stop_loss_exits": len(stop_loss_exits), "month_end_exits": len(month_end_exits),
        "win_rate_pct": round(win_rate, 1) if win_rate is not None else None,
        "avg_trade_pnl_pct": round(avg_pnl, 2) if avg_pnl is not None else None,
        "events_sample": (events[:10] + events[-10:]) if len(events) > 20 else events,
        "rsi_rotation": {"equity_curve": series_to_points(norm(rotation_series)), **metrics(rotation_series)},
        "nifty": {"equity_curve": series_to_points(norm(nifty_series)), **metrics(nifty_series)},
        "midcap_etf": {"equity_curve": series_to_points(norm(midcap_series)), **metrics(midcap_series)},
    }
    with open("results21.json", "w") as f:
        json.dump(results, f)

    print("start", start_date.date(), "end", end_date.date())
    print("entries:", len(entries), "exits:", len(exits), "(stop-loss:", len(stop_loss_exits), ", month-end:", len(month_end_exits), ")")
    print("win rate:", win_rate, "avg trade pnl:", avg_pnl)
    for k in ("rsi_rotation", "nifty", "midcap_etf"):
        v = results[k]
        print(f"[{k}] net_return={v['net_return_pct']:.1f}% cagr={v['cagr_pct']:.2f}% "
              f"mdd={v['max_drawdown_pct']:.1f}% uw_days={v['longest_underwater_days']}")
    print("\nfirst 10 events:")
    for e in events[:10]:
        print(" ", e)
    print("last 10 events:")
    for e in events[-10:]:
        print(" ", e)


if __name__ == "__main__":
    main()

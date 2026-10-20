"""
Report 104 — Smoothed Heikin-Ashi + ATR contraction, applied to NIFTY Midcap 150.

The system under test (refined from the Upsurge Club live session of 20 Oct 2026):

  ENTRY   green flip of the double-smoothed Heikin-Ashi (EMA(10) of OHLC -> HA ->
          EMA(10) of HA open/close), close above the smoothed HA open, and
          ATR(14)/ATR(50) < 0.8 (volatility contraction = tight base).
  STOP    12% intraday from the entry price; filled at min(open, trigger) when gapped.
  EXIT    first red flip, next day's open.
  SIZE    8 slots. Two conventions are reported:
            "slot"  = 12.5% of equity per position (fully deployed when 8 are open)
            "risk"  = 1% of equity risked against the 12% stop (8.33% per position)
  COSTS   0.25% round trip.

Universe: NIFTY Midcap 150, today's constituents (NSE official list), prices from the
project's midcap150_extra_raw.pkl cache (150 names, 1996 -> 2026-10-16).

Why this report exists: the same system was tested on NIFTY 200 / NIFTY 500 (12 years,
Yahoo-sourced data) where it beat its own equal-weight basket on both CAGR and drawdown.
Midcap 150 is the obvious next question — smaller, faster-moving names where trend systems
are usually said to work better. This report tests that claim on the project's own cache.

DISCLOSURES — read before quoting any number:
  - SURVIVORSHIP BIAS IS SEVERE. Today's Midcap 150 membership is applied retroactively
    back to 2005. The equal-weight basket's full-history number (and to a lesser degree
    the strategy's) is flattered by names that survived and were promoted into the index.
    The 2008 row is the tell: the basket shows roughly flat that year, which no real
    midcap portfolio experienced.
  - The basket is equal-weighted and annually rebalanced, no costs — a deliberately
    simple comparator, not the real NIFTY Midcap 150 index.
  - Dividends are excluded (Close, not Adj Close), consistent with the rest of this repo.
  - The ATR threshold (0.80) and the 12% stop were chosen after looking at the NIFTY
    200/500 data; they are not out-of-sample parameters.
  - Next-open fills on midcap names are plausible but optimistic in the smallest names.
  - The 2020 concentration is disclosed in the report body, not buried: the system made
    2.9x that year and roughly half of its modern-window excess return comes from it.
"""
import json
import math
import os

import numpy as np
import pandas as pd

COST_RT = 0.0025
CAPITAL = 1_000_000.0
RISK_PCT = 0.01
MAX_POS = 8
HA_LEN = 10

MODERN_START = pd.Timestamp("2016-01-01")
FULL_START = pd.Timestamp("2005-01-01")

MIDCAP_PKL = "midcap150_extra_raw.pkl"
N200_PKL = "universe_raw.pkl"
SC250_PKL = "smallcap250_extra_raw.pkl"
NIFTY_CSV = "nifty50_daily.csv"


# --------------------------------------------------------------------------- indicators
def ema(arr, length):
    """EMA seeded with the SMA of the first `length` valid values, NaN-propagating —
    identical to the JS engine used for the NIFTY 200/500 study."""
    out = np.full(len(arr), np.nan)
    first = None
    for i, v in enumerate(arr):
        if np.isfinite(v):
            first = i
            break
    if first is None:
        return out
    s = 0.0
    cnt = 0
    seed_idx = -1
    for i in range(first, len(arr)):
        v = arr[i]
        if not np.isfinite(v):
            continue
        s += v
        cnt += 1
        if cnt == length:
            seed_idx = i
            break
    if seed_idx < 0:
        return out
    prev = s / length
    out[seed_idx] = prev
    k = 2.0 / (length + 1.0)
    for i in range(seed_idx + 1, len(arr)):
        v = arr[i]
        if not np.isfinite(v):
            out[i] = prev
            continue
        prev = v * k + prev * (1 - k)
        out[i] = prev
    return out


def smoothed_ha(o, h, l, c, length=HA_LEN):
    o1, h1, l1, c1 = ema(o, length), ema(h, length), ema(l, length), ema(c, length)
    n = len(c)
    ha_o = np.full(n, np.nan)
    ha_c = np.full(n, np.nan)
    for i in range(n):
        if not (np.isfinite(o1[i]) and np.isfinite(h1[i]) and np.isfinite(l1[i]) and np.isfinite(c1[i])):
            continue
        ha_c[i] = (o1[i] + h1[i] + l1[i] + c1[i]) / 4.0
        ha_o[i] = ((ha_o[i - 1] + ha_c[i - 1]) / 2.0) if i > 0 and np.isfinite(ha_o[i - 1]) else (o1[i] + c1[i]) / 2.0
    return ema(ha_o, length), ema(ha_c, length)


def atr_ratio_series(h, l, c):
    prev_c = np.roll(c, 1)
    prev_c[0] = np.nan
    tr = np.maximum(h - l, np.maximum(np.abs(h - prev_c), np.abs(l - prev_c)))
    tr[0] = h[0] - l[0]
    s = pd.Series(tr)
    a14 = s.rolling(14, min_periods=12).mean().to_numpy()
    a50 = s.rolling(50, min_periods=40).mean().to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        r = a14 / a50
    r[~np.isfinite(r)] = np.nan
    r[a50 <= 0] = np.nan
    return r


def fnv(s):
    x = 2166136261
    for ch in s:
        x ^= ord(ch)
        x = (x * 16777619) & 0xFFFFFFFF
    return x


# --------------------------------------------------------------------------- engine
def build_trades(sym, o, h, l, c, green, ha_o, atr, ema50, dates, start, variant):
    n = len(c)
    trades = []
    i = 0
    while i < n - 2:
        if dates[i] < start:
            i += 1
            continue
        if not (green[i] and not green[i - 1]):
            i += 1
            continue
        if variant in ("lean12", "atr80"):
            if not (np.isfinite(ha_o[i]) and c[i] > ha_o[i]):
                i += 1
                continue
        if variant == "atr80":
            if not (np.isfinite(atr[i]) and atr[i] < 0.80):
                i += 1
                continue
        if variant == "video":
            if not (np.isfinite(ha_o[i]) and c[i] > ha_o[i]):
                i += 1
                continue
            if not (np.isfinite(ema50[i]) and c[i] > ema50[i]):
                i += 1
                continue
        e = i + 1
        if e >= n or not np.isfinite(o[e]) or o[e] <= 0:
            i += 1
            continue
        entry = o[e]
        stop_pct = 0.085 if variant == "video" else 0.12
        sl = entry * (1 - stop_pct)
        exit_px = None
        exit_idx = None
        reason = None
        for j in range(e, n):
            if np.isfinite(l[j]) and l[j] <= sl:
                exit_px = o[j] if (np.isfinite(o[j]) and o[j] <= sl) else sl
                exit_idx = j
                reason = "stop"
                break
            if not green[j] and green[j - 1]:
                if j + 1 < n and np.isfinite(o[j + 1]):
                    exit_px = o[j + 1]
                    exit_idx = j + 1
                else:
                    exit_px = c[j]
                    exit_idx = j
                reason = "flip"
                break
        if exit_px is None:
            exit_px = c[n - 1]
            exit_idx = n - 1
            reason = "eod"
        trades.append(dict(symbol=sym, signalDate=dates[i], entryDate=dates[e], exitDate=dates[exit_idx],
                           entry=float(entry), exit=float(exit_px),
                           net=float(exit_px / entry - 1 - COST_RT),
                           bars=int(exit_idx - i), reason=reason))
        i = exit_idx + 1
    return trades


def portfolio(trades, close_map, all_dates, alloc_mode, seed):
    by_entry = {}
    for t in trades:
        by_entry.setdefault(t["entryDate"], []).append(t)
    open_pos = []
    cash = CAPITAL
    curve = []
    taken = []
    peak = CAPITAL
    maxdd = 0.0
    days_inv = 0
    for day in all_dates:
        for k in range(len(open_pos) - 1, -1, -1):
            p = open_pos[k]
            if p["t"]["exitDate"] == day:
                cash += p["qty"] * p["t"]["entry"] * (1 + p["t"]["net"])
                open_pos.pop(k)
        eq_before = cash + sum(p["qty"] * p["last"] for p in open_pos)
        cands = sorted(by_entry.get(day, []), key=lambda t: fnv(t["symbol"] + day.strftime("%Y-%m-%d") + str(seed)))
        for t in cands:
            if len(open_pos) >= MAX_POS:
                break
            if any(p["t"]["symbol"] == t["symbol"] for p in open_pos):
                continue
            if alloc_mode == "slot":
                alloc = min(eq_before / MAX_POS, cash * 0.98)
            else:
                alloc = min(eq_before * (RISK_PCT / 0.12), cash * 0.98)
            if alloc < 1000:
                continue
            qty = math.floor(alloc / t["entry"])
            if qty <= 0:
                continue
            cash -= qty * t["entry"]
            if t["exitDate"] == day:
                cash += qty * t["entry"] * (1 + t["net"])
            else:
                open_pos.append({"t": t, "qty": qty, "last": t["entry"]})
            taken.append(t)
        mv = 0.0
        for p in open_pos:
            px = close_map.get(p["t"]["symbol"], {}).get(day)
            if px is not None and np.isfinite(px):
                p["last"] = px
            mv += p["qty"] * p["last"]
        eq = cash + mv
        curve.append((day, eq))
        if open_pos:
            days_inv += 1
        peak = max(peak, eq)
        maxdd = min(maxdd, eq / peak - 1)
    return curve, maxdd, days_inv, taken


def metrics_block(curve, taken, n_dates, trades_total, days_inv):
    first_d, first_eq = curve[0]
    last_d, last_eq = curve[-1]
    years = (last_d - first_d).days / 365.25
    norm = [(d, eq / first_eq * 100.0) for d, eq in curve]
    peak = first_eq
    mdd = 0.0
    mdd_peak = first_d
    mdd_trough = first_d
    peak_date = first_d
    underwater = []
    daily = []
    uw_run = 0
    longest_uw = 0
    for k, (d, eq) in enumerate(curve):
        if eq >= peak:
            peak = eq
            peak_date = d
            if uw_run:
                longest_uw = max(longest_uw, uw_run)
                uw_run = 0
        else:
            uw_run += 1
        dd = eq / peak - 1
        underwater.append((d, dd * 100))
        if dd < mdd:
            mdd = dd
            mdd_peak = peak_date
            mdd_trough = d
        if k:
            daily.append(eq / curve[k - 1][1] - 1)
    longest_uw = max(longest_uw, uw_run)
    mean = float(np.mean(daily)) if daily else 0.0
    sd = float(np.std(daily, ddof=1)) if len(daily) > 1 else 0.0
    yearly = {}
    prev = first_eq
    last_by_year = {}
    for d, eq in curve:
        last_by_year[d.year] = eq
    for y in sorted(last_by_year):
        yearly[str(y)] = last_by_year[y] / prev - 1
        prev = last_by_year[y]
    ts = trade_stats(trades_total)
    return {
        "equity_curve": [[d.strftime("%Y-%m-%d"), round(v, 4)] for d, v in norm],
        "underwater": [[d.strftime("%Y-%m-%d"), round(v, 3)] for d, v in underwater],
        "net_return_pct": (last_eq / first_eq - 1) * 100,
        "cagr_pct": (last_eq / first_eq) ** (1 / years) * 100 - 100,
        "max_drawdown_pct": mdd * 100,
        "max_drawdown_peak_date": mdd_peak.strftime("%Y-%m-%d"),
        "max_drawdown_trough_date": mdd_trough.strftime("%Y-%m-%d"),
        "longest_underwater_days": int(longest_uw),
        "sharpe": (mean / sd * math.sqrt(252)) if sd else None,
        "exposure_pct": days_inv / n_dates * 100,
        "taken": len(taken),
        "yearly": yearly,
        "trades": ts,
        "start_date": first_d.strftime("%Y-%m-%d"),
        "end_date": last_d.strftime("%Y-%m-%d"),
    }


def trade_stats(trades):
    if not trades:
        return {"n": 0}
    net = np.array([t["net"] for t in trades])
    wins = net[net > 0]
    losses = net[net <= 0]
    avg_w = float(wins.mean()) if len(wins) else 0.0
    avg_l = float(losses.mean()) if len(losses) else 0.0
    gp = float(wins.sum())
    gl = abs(float(losses.sum()))
    return {
        "n": int(len(net)),
        "win_pct": float((net > 0).mean() * 100),
        "avg_win_pct": avg_w * 100,
        "avg_loss_pct": avg_l * 100,
        "payoff": avg_w / abs(avg_l) if avg_l else None,
        "expectancy_pct": float(net.mean() * 100),
        "median_pct": float(np.median(net) * 100),
        "profit_factor": gp / gl if gl else None,
        "stop_share_pct": float(np.mean([t["reason"] == "stop" for t in trades]) * 100),
        "avg_hold_days": float(np.mean([t["bars"] for t in trades])),
    }


def ew_annual(px, dates, start):
    """Equal-weight basket, rebalanced at the first trading day of each year, no costs."""
    syms = list(px.keys())
    first = None
    for i, d in enumerate(dates):
        if d >= start and sum(1 for s in syms if np.isfinite(px[s][i])) >= 30:
            first = i
            break
    if first is None:
        return None
    last_px = {s: np.nan for s in syms}
    qty = {}
    val = 1.0
    curve = []
    for i in range(first, len(dates)):
        d = dates[i]
        for s in syms:
            if np.isfinite(px[s][i]):
                last_px[s] = px[s][i]
        valid = [s for s in syms if np.isfinite(last_px[s]) and last_px[s] > 0]
        is_reb = (i == first) or (i > first and d.year != dates[i - 1].year)
        if is_reb and len(valid) >= 30:
            tot = sum(qty[s] * last_px[s] for s in qty) if qty else val
            per = tot / len(valid)
            qty = {s: per / last_px[s] for s in valid}
            val = tot
        else:
            val = sum(qty[s] * last_px[s] for s in qty) if qty else val
        curve.append((d, val))
    return curve


def benchmark_block(curve, dates_window):
    """Benchmark metrics in the same shape as the strategy block (no trade stats)."""
    m = metrics_block(curve, [], len(dates_window), [], len(curve))
    m["trades"] = {"n": 0}
    return m


def load_ohlc(pkl):
    raw = pd.read_pickle(pkl)
    tickers = sorted(set(c[0] for c in raw.columns))
    dates = list(raw.index)
    o = {t: raw[(t, "Open")].to_numpy(dtype=float) for t in tickers}
    h = {t: raw[(t, "High")].to_numpy(dtype=float) for t in tickers}
    l = {t: raw[(t, "Low")].to_numpy(dtype=float) for t in tickers}
    c = {t: raw[(t, "Close")].to_numpy(dtype=float) for t in tickers}
    return tickers, dates, o, h, l, c


def run_universe(pkl, label, want_full=True):
    tickers, dates, o, h, l, c = load_ohlc(pkl)
    print(f"[{label}] {len(tickers)} names, {len(dates)} dates {dates[0].date()} -> {dates[-1].date()}", flush=True)

    green, ha_o, atr, ema50 = {}, {}, {}, {}
    for t in tickers:
        ho, hc = smoothed_ha(o[t], h[t], l[t], c[t])
        ha_o[t] = ho
        green[t] = np.isfinite(ho) & np.isfinite(hc) & (hc > ho)
        atr[t] = atr_ratio_series(h[t], l[t], c[t])
        ema50[t] = ema(c[t], 50)

    close_map = {t: {dates[i]: c[t][i] for i in range(len(dates)) if np.isfinite(c[t][i])} for t in tickers}
    px = {t: c[t] for t in tickers}

    def build(variant, start):
        out = []
        for t in tickers:
            out.extend(build_trades(t, o[t], h[t], l[t], c[t], green[t], ha_o[t], atr[t], ema50[t],
                                    dates, start, variant))
        out.sort(key=lambda x: (x["entryDate"], x["symbol"]))
        return out

    out = {"label": label, "names": len(tickers), "dates": [str(dates[0].date()), str(dates[-1].date())]}

    for window, start in [("modern", MODERN_START), ("full", FULL_START)]:
        if window == "full" and not want_full:
            continue
        wdates = [d for d in dates if d >= start]
        out[window] = {}
        trade_cache = {}
        for variant in ["video", "lean12", "atr80"]:
            trades = build(variant, start)
            trade_cache[variant] = trades
            curve, mdd, days_inv, taken = portfolio(trades, close_map, wdates, "slot", 5)
            m = metrics_block(curve, taken, len(wdates), trades, days_inv)
            out[window][variant] = m
            print(f"  {window:6} {variant:7} slot | CAGR {m['cagr_pct']:6.1f}% | DD {m['max_drawdown_pct']:6.1f}% | "
                  f"Sharpe {m['sharpe']:.2f} | signals {m['trades']['n']:5} | taken {m['taken']:4} | "
                  f"win {m['trades']['win_pct']:.1f}%", flush=True)
        # recommended config under the literal 1%-risk convention
        trades = trade_cache["atr80"]
        curve, mdd, days_inv, taken = portfolio(trades, close_map, wdates, "risk", 5)
        m = metrics_block(curve, taken, len(wdates), trades, days_inv)
        out[window]["atr80_risk"] = m
        print(f"  {window:6} atr80   risk | CAGR {m['cagr_pct']:6.1f}% | DD {m['max_drawdown_pct']:6.1f}% | "
              f"Sharpe {m['sharpe']:.2f}", flush=True)

        # seed dispersion on the recommended config
        seeds = []
        for s in [1, 2, 3, 5, 7]:
            curve, mdd, days_inv, taken = portfolio(trades, close_map, wdates, "slot", s)
            m = metrics_block(curve, taken, len(wdates), trades, days_inv)
            seeds.append({"seed": s, "cagr_pct": m["cagr_pct"], "max_drawdown_pct": m["max_drawdown_pct"],
                          "sharpe": m["sharpe"], "taken": m["taken"]})
        out[window]["seeds"] = seeds

        bcurve = ew_annual(px, dates, start)
        bcurve = [(d, v) for d, v in bcurve if d >= start]
        b = benchmark_block(bcurve, wdates)
        out[window]["basket"] = b
        print(f"  {window:6} basket       | CAGR {b['cagr_pct']:6.1f}% | DD {b['max_drawdown_pct']:6.1f}% | "
              f"Sharpe {b['sharpe']:.2f}", flush=True)

    # coverage for the data panel
    cov = {}
    for y in range(MODERN_START.year, dates[-1].year + 1):
        day = [d for d in dates if d.year == y][-1]
        cov[str(y)] = int(sum(1 for t in tickers if np.isfinite(c[t][dates.index(day)])))
    out["coverage_by_year"] = cov
    return out


def nifty50_curve():
    if os.path.exists(NIFTY_CSV):
        df = pd.read_csv(NIFTY_CSV, parse_dates=["Date"]).set_index("Date")
    else:
        try:
            from backtest import fetch
            df = fetch("^NSEI")[["Open", "High", "Low", "Close"]]
            df.to_csv(NIFTY_CSV, index_label="Date")
        except Exception as e:
            print("nifty fetch failed:", e)
            return None
    df = df[df.index >= MODERN_START]
    return list(zip(df.index, df["Close"].astype(float)))


def main():
    mid = run_universe(MIDCAP_PKL, "NIFTY Midcap 150")
    cross = [mid]
    for pkl, label in [(N200_PKL, "NIFTY 200"), (SC250_PKL, "NIFTY Smallcap 250")]:
        try:
            cross.append(run_universe(pkl, label, want_full=False))
        except FileNotFoundError:
            print("missing", pkl, "- skipped")

    nif = nifty50_curve()
    nif_block = None
    if nif:
        nif_block = benchmark_block(nif, [d for d, _ in nif])
        print(f"nifty50           | CAGR {nif_block['cagr_pct']:.1f}% | DD {nif_block['max_drawdown_pct']:.1f}%")

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": "₹",
        "universe": "NIFTY Midcap 150 (official NSE list, 150 names, today's membership applied retroactively)",
        "strategy": ("Smoothed Heikin-Ashi (10/10): green flip + close > indicator + ATR14/ATR50 < 0.8; "
                     "12% stop; exit on first red flip at next open; 8 slots"),
        "config": {
            "ha_smoothing": HA_LEN, "atr_ratio_max": 0.80, "stop_pct": 12.0,
            "max_positions": MAX_POS, "cost_round_trip_pct": COST_RT * 100,
            "sizing_reported": ["slot (12.5% of equity per position)", "risk (1% of equity per trade at the 12% stop)"],
        },
        "start_date": mid["modern"]["atr80"]["start_date"],
        "end_date": mid["modern"]["atr80"]["end_date"],
        "start_date_full": mid["full"]["atr80"]["start_date"],
        "disclosures": [
            "survivorship bias: today's Midcap 150 membership applied retroactively to 2005",
            "equal-weight basket is a simple comparator, not the real NIFTY Midcap 150 index",
            "dividends excluded (Close, not Adj Close)",
            "ATR 0.80 threshold and 12% stop chosen after looking at NIFTY 200/500 data",
            "next-open fills on the smallest midcaps are optimistic",
            "2020 concentration disclosed: the system made roughly 2.9x that year",
        ],
        "modern": mid["modern"],
        "full": mid["full"],
        "coverage_by_year": mid["coverage_by_year"],
        "nifty50": nif_block,
        "cross_universe": [
            {
                "universe": u["label"], "names": u["names"],
                "system_cagr_pct": u["modern"]["atr80"]["cagr_pct"],
                "system_max_drawdown_pct": u["modern"]["atr80"]["max_drawdown_pct"],
                "system_sharpe": u["modern"]["atr80"]["sharpe"],
                "basket_cagr_pct": u["modern"]["basket"]["cagr_pct"],
                "basket_max_drawdown_pct": u["modern"]["basket"]["max_drawdown_pct"],
                "basket_sharpe": u["modern"]["basket"]["sharpe"],
            }
            for u in cross
        ],
    }

    with open("results103.json", "w") as f:
        json.dump(results, f, indent=2)

    m = results["modern"]["atr80"]
    b = results["modern"]["basket"]
    print(f"\nMidcap 150, 2016-2026, slot sizing: strategy {m['cagr_pct']:.1f}% CAGR / "
          f"{m['max_drawdown_pct']:.1f}% DD / Sharpe {m['sharpe']:.2f} vs basket "
          f"{b['cagr_pct']:.1f}% / {b['max_drawdown_pct']:.1f}% / {b['sharpe']:.2f}")
    print("wrote results103.json")


if __name__ == "__main__":
    main()

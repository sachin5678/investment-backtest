"""MomentumScore-style strategy builder — the engine behind reports 94+.

One config-driven engine whose knobs mirror momentumscore.in's Build & Test
tabs, run on this repo's cached data. Report 93's run is the reference
configuration: `default_config()` must reproduce results92.json exactly
(checked by check_builder_regression.py) before any new experiment is
trusted.

Config surface (see default_config for the full schema):

  1. Universe      — midcap150 (same loader as every Midcap150 report here)
  2. Conditions    — keep_if / buy_if / sell_when rules over per-stock
                     indicators: ret_6m, swings_6m, above_ema200,
                     supertrend_green, rsi, golden_cross, from_52w_high,
                     from_ath, turnover, price, vix (market-level).
                     keep_if is checked at reviews (a holder that stops
                     passing is sold at that review); buy_if only gates new
                     buys; sell_when is checked EVERY day — the holding is
                     sold that day and its slot waits in cash.
  3. Rank          — fixed: the repo's 6m/12m risk-adjusted momentum, with
                     MomentumScore-style fit percentiles (ms_port.fit).
  4. Pick          — top_n, entry_rank ("buy only from the top K"),
                     exit_rank, exit_mode (sell at the review vs the day it
                     breaches), max_per_sector (current-day sectors from
                     sectors_raw.json), rebalance months / day mode.
                     Slot semantics are MomentumScore's: money is divided
                     over the open slots, and a slot whose candidate fails
                     the buy conditions (or the entry rank) waits in cash —
                     it is never redistributed to the other slots.
  5. Money         — start capital, compounding (reinvest vs fixed amount
                     per position), monthly SIP + yearly step-up, and
                     buy-the-dip top-ups (NIFTY RSI below a level, at most
                     once a month — goes into holdings that day, like a SIP).
  6. Protect       — regime signal (NIFTY 200-EMA by default; or Supertrend,
                     NIFTY 500, a 2-of-3 ensemble, VIX-only), check daily vs
                     on review days only, action when off (park / cash /
                     sell-half-and-re-top-up), park basket (up to 4 symbols
                     with % of freed cash — a symbol listed later leaves its
                     share in cash until then), and a VIX volatility filter.
  7. Costs         — cost % + slippage % per side, whole units or fractional.

Output: one JSON per lab in the house results-file shape — every variant is
a full series object (so the webapp's generic extractSeries picks them up),
carrying its own before-costs curve, after-tax curve, health card, halves
check, tax summary and trade stats.

Honesty notes baked in: ranking/fit math is the report 93 code path;
Supertrend is the standard (10, 3) Wilder-ATR version starting green on the
first valid bar; swings_6m is annualized 6-month return volatility; sectors
are today's classification applied backwards; VIX history starts 2008 on
Yahoo (MomentumScore shows it from ~2014); SILVERBEES data starts Feb 2022
and its park share stays cash before that.
"""
import json
import math
from datetime import datetime

import numpy as np
import pandas as pd

from backtest10 import rebalance_dates, CURRENCY_SYMBOL
from backtest32 import metrics_only
from ms_port import fit as ms_fit
from ms_port import health as ms_health
from ms_port import robustness as ms_rob
from ms_port import tax as ms_tax
from niftymidcap150_symbols import NIFTY_MIDCAP150_SYMBOLS

EXTRAS_PKL = "builder_extras_raw.pkl"
MIN_ELIGIBLE = 30
LOOKBACK_6M = 126
LOOKBACK_12M = 252
FMV_DATE = "2025-01-31"     # s.112A grandfathering reference date
INDEX_LABEL = {"nifty": "NIFTY 50", "nifty500": "NIFTY 500"}


# --------------------------------------------------------------------------
# config
# --------------------------------------------------------------------------

def default_config(**overrides):
    cfg = {
        "universe": "midcap150",
        "conditions": [],            # [{"when": "keep"|"buy"|"sell", "indicator": ..., "op": ..., "value": ...}]
        "top_n": 10,
        "entry_rank": None,          # buy only from the top K ranks
        "exit_rank": 52,
        "exit_mode": "at_review",    # at_review | on_breach
        "max_per_sector": None,
        "rebalance_months": (6, 12),
        "day_mode": "month-end",     # month-end | day
        "day_of_month": None,
        "start_capital": 100_000.0,
        "compounding": "reinvest",   # reinvest | fixed_per_position
        "sip": None,                 # {"monthly": 25000, "step_up_pct": 10}
        "dip": None,                 # {"amount": 25000, "rsi_period": 14, "rsi_below": 30}
        "regime": {
            "enabled": True,
            "signal": "below_ma",    # below_ma | supertrend | ensemble_2of3 | none
            "index": "nifty",        # nifty | nifty500
            "dma_days": 200,
            "check": "daily",        # daily | at_review
            "action": "park",        # park | cash | half
            "park": [{"symbol": "GOLDBEES", "pct": 100}],
            "vix_filter": None,      # {"above": 20}
            "vix_mode": "or",        # or | and  (combine with the base signal)
        },
        "cost_pct_per_side": 0.001,  # 0.1% — MomentumScore's own convention
        "slippage_pct_per_side": 0.0,
        "whole_units": False,
    }
    for k, v in overrides.items():
        if isinstance(v, dict) and isinstance(cfg.get(k), dict):
            cfg[k] = {**cfg[k], **v}
        else:
            cfg[k] = v
    return cfg


def describe_config(cfg):
    """The human-readable knob summary stored next to every variant."""
    r = cfg["regime"]
    out = {
        "top_n": cfg["top_n"], "exit_rank": cfg["exit_rank"],
        "exit_mode": cfg["exit_mode"], "entry_rank": cfg["entry_rank"],
        "max_per_sector": cfg["max_per_sector"],
        "rebalance": f"months {list(cfg['rebalance_months'])}, {cfg['day_mode']}",
        "compounding": cfg["compounding"],
        "cost_pct_per_side": round((cfg["cost_pct_per_side"] + cfg["slippage_pct_per_side"]) * 100, 3),
        "whole_units": cfg["whole_units"],
        "conditions": [
            f"{c['when']}: {c['indicator']} {c.get('op', 'is')} {c.get('value', '')}".strip()
            for c in cfg["conditions"]
        ],
    }
    if r["enabled"]:
        out["regime"] = (f"{r['signal']} on {INDEX_LABEL[r['index']]}"
                         + (f" ({r['dma_days']}d)" if r["signal"] == "below_ma" else "")
                         + f", check {r['check']}, action {r['action']}")
        if r["park"]:
            out["park"] = ", ".join(f"{p['symbol']} {p['pct']}%" for p in r["park"])
        else:
            out["park"] = "cash"
        if r["vix_filter"]:
            out["vix_filter"] = f"VIX {r['vix_mode']} above {r['vix_filter']['above']}"
    else:
        out["regime"] = "off"
    if cfg["sip"]:
        out["sip"] = f"{cfg['sip']['monthly']:,.0f}/mo + {cfg['sip']['step_up_pct']}%/yr"
    if cfg["dip"]:
        out["dip"] = f"{cfg['dip']['amount']:,.0f} when NIFTY RSI({cfg['dip']['rsi_period']}) < {cfg['dip']['rsi_below']}"
    return out


# --------------------------------------------------------------------------
# market data
# --------------------------------------------------------------------------

def load_midcap150_ohlcv():
    """OHLCV for the Midcap150 universe, same loader convention as
    backtest13.load_midcap150_closes (first source that has the ticker,
    ffilled) — Close here is identical to that loader's output."""
    raw200 = pd.read_pickle("universe_raw.pkl")
    extra_q = pd.read_pickle("quality50_extra_raw.pkl")
    extra_m = pd.read_pickle("midcap150_extra_raw.pkl")
    tickers = [s + ".NS" for s in NIFTY_MIDCAP150_SYMBOLS]
    colsets = [set(c[0] for c in src.columns) for src in (raw200, extra_q, extra_m)]

    def get(t, field):
        for src, cols in zip((raw200, extra_q, extra_m), colsets):
            if t in cols:
                return src[(t, field)]
        raise KeyError(t)

    out = {}
    for field in ("Open", "High", "Low", "Close", "Volume"):
        out[field] = pd.DataFrame({t: get(t, field) for t in tickers}).sort_index().ffill()
    return out


def load_market():
    ohlcv = load_midcap150_ohlcv()
    closes = ohlcv["Close"]
    ex = pd.read_pickle(EXTRAS_PKL)

    def repo_close(sym):
        """Same convention as backtest4.fetch: drop rows with any of
        O/H/L/C missing, then take Close. Used for the two hero-critical
        series (NIFTY 50, GOLDBEES) so the regression matches report 93."""
        sub = ex[sym][["Open", "High", "Low", "Close"]].dropna()
        return sub["Close"].rename(sym)

    nifty = repo_close("^NSEI").rename("nifty")
    gold = repo_close("GOLDBEES.NS")
    gold = gold.drop(index=[d for d in gold.index
                            if pd.Timestamp("2019-12-19") <= d <= pd.Timestamp("2019-12-20")])

    common = closes.index.intersection(nifty.index).intersection(gold.index)
    closes = closes.loc[common]
    ohlcv = {k: v.loc[common] for k, v in ohlcv.items()}
    nifty = nifty.loc[common].ffill()
    gold = gold.loc[common].ffill()

    # variant-only series: align onto the common grid; NaN before listing
    # (a park share with no price yet stays in cash), ffilled after.
    nifty500 = ex[("^CRSLDX", "Close")].dropna().reindex(common).ffill().rename("nifty500")
    vix = ex[("^INDIAVIX", "Close")].dropna().reindex(common).ffill().rename("vix")

    extras = {}
    for sym in ("SILVERBEES.NS", "LIQUIDBEES.NS", "NIFTYBEES.NS"):
        if (sym, "Close") in ex.columns:
            extras[sym] = ex[(sym, "Close")].reindex(common).ffill()

    idx_ohlc = {}
    for key, sym in (("nifty", "^NSEI"), ("nifty500", "^CRSLDX")):
        idx_ohlc[key] = {
            "high": ex[(sym, "High")].reindex(common).ffill(),
            "low": ex[(sym, "Low")].reindex(common).ffill(),
            "close": nifty if key == "nifty" else nifty500,
        }
    return {
        "closes": closes, "ohlcv": ohlcv, "nifty": nifty, "nifty500": nifty500,
        "vix": vix, "gold": gold, "extras": extras, "idx_ohlc": idx_ohlc,
        "common": common,
    }


# --------------------------------------------------------------------------
# features (computed once, reused by every variant)
# --------------------------------------------------------------------------

def supertrend_dir(high, low, close, period=10, mult=3.0):
    """Standard Supertrend: Wilder ATR, bands hl2 ± mult·ATR with the usual
    trailing rules. True = green (uptrend). Starts green on the first valid
    bar (documented convention)."""
    high, low, close = high.astype(float), low.astype(float), close.astype(float)
    hl2 = (high + low) / 2.0
    tr = pd.concat([(high - low), (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1.0 / period, adjust=False).mean()
    upper = (hl2 + mult * atr).to_numpy()
    lower = (hl2 - mult * atr).to_numpy()
    c = close.to_numpy()
    n = len(c)
    fu = np.full(n, np.nan)
    fl = np.full(n, np.nan)
    d = np.full(n, np.nan)
    for i in range(n):
        if not (np.isfinite(upper[i]) and np.isfinite(lower[i]) and np.isfinite(c[i])):
            continue
        if i == 0 or not np.isfinite(fu[i - 1]):
            fu[i], fl[i], d[i] = upper[i], lower[i], 1.0
            continue
        fu[i] = upper[i] if (upper[i] < fu[i - 1] or c[i - 1] > fu[i - 1]) else fu[i - 1]
        fl[i] = lower[i] if (lower[i] > fl[i - 1] or c[i - 1] < fl[i - 1]) else fl[i - 1]
        if c[i] > fu[i - 1]:
            d[i] = 1.0
        elif c[i] < fl[i - 1]:
            d[i] = -1.0
        else:
            d[i] = d[i - 1] if np.isfinite(d[i - 1]) else 1.0
    return pd.Series(d, index=close.index) > 0


def rsi_wilder(close, period=14):
    delta = close.diff()
    up = delta.clip(lower=0.0)
    dn = (-delta).clip(lower=0.0)
    ru = up.ewm(alpha=1.0 / period, adjust=False).mean()
    rd = dn.ewm(alpha=1.0 / period, adjust=False).mean()
    rs = ru / rd
    return 100.0 - 100.0 / (1.0 + rs)


def build_ranks(closes, min_eligible=MIN_ELIGIBLE):
    """The report-93 ranking, precomputed for every date — the same sequence
    of operations as backtest93.select_ranked/rank_map_at, so the values are
    identical (checked by the regression script). Returns (rank, fit, score)
    DataFrames, NaN where a name isn't eligible/ranked."""
    look6, look12 = LOOKBACK_6M, LOOKBACK_12M
    price = closes
    ret6 = price / price.shift(look6) - 1.0
    ret12 = price / price.shift(look12) - 1.0
    vol1y = price.pct_change().rolling(look12, min_periods=2).std()
    ratio6 = ret6 / vol1y
    ratio12 = ret12 / vol1y

    rank = pd.DataFrame(np.nan, index=price.index, columns=price.columns)
    fitm = pd.DataFrame(np.nan, index=price.index, columns=price.columns)
    score = pd.DataFrame(np.nan, index=price.index, columns=price.columns)

    for t_idx in range(look12, len(price)):
        price_t = price.iloc[t_idx]
        price_t6 = price.iloc[t_idx - look6]
        price_t12 = price.iloc[t_idx - look12]
        eligible = price_t.notna() & price_t12.notna() & price_t6.notna()
        if int(eligible.sum()) < min_eligible:
            continue
        r6 = ratio6.iloc[t_idx][eligible]
        r12 = ratio12.iloc[t_idx][eligible]
        valid = r6.notna() & r12.notna() & np.isfinite(r6) & np.isfinite(r12)
        r6v, r12v = r6[valid], r12[valid]
        if len(r6v) < min_eligible:
            continue
        z6 = (r6v - r6v.mean()) / r6v.std()
        z12 = (r12v - r12v.mean()) / r12v.std()
        waz = 0.5 * z6 + 0.5 * z12
        norm_score = waz.apply(lambda w: 1 + w if w >= 0 else 1 / (1 - w))
        ordered = norm_score.sort_values(ascending=False)
        fits = ms_fit.fit_percentiles({tk: float(sc) for tk, sc in ordered.items()})
        idx = price.index[t_idx]
        for i, (tk, sc) in enumerate(ordered.items()):
            rank.at[idx, tk] = i + 1
            fitm.at[idx, tk] = fits[tk]
            score.at[idx, tk] = float(sc)
    return rank, fitm, score


def build_features(market):
    closes = market["closes"]
    o = market["ohlcv"]
    feats = {}
    feats["price"] = closes
    feats["ret_6m"] = (closes / closes.shift(LOOKBACK_6M) - 1.0) * 100.0
    feats["swings_6m"] = closes.pct_change().rolling(LOOKBACK_6M, min_periods=2).std() * math.sqrt(252.0) * 100.0
    ema50 = closes.ewm(span=50, adjust=False).mean()
    ema200 = closes.ewm(span=200, adjust=False).mean()
    feats["ema200"] = ema200
    feats["above_ema200"] = closes > ema200
    feats["golden_cross"] = ema50 > ema200
    feats["rsi"] = rsi_wilder(closes, 14)
    feats["from_52w_high"] = (closes / closes.rolling(252, min_periods=60).max() - 1.0) * 100.0
    feats["from_ath"] = (closes / closes.cummax() - 1.0) * 100.0
    feats["turnover"] = (closes * o["Volume"]).rolling(LOOKBACK_6M, min_periods=2).mean()
    feats["supertrend_green"] = pd.DataFrame(
        {tk: supertrend_dir(o["High"][tk], o["Low"][tk], o["Close"][tk]) for tk in closes.columns})
    feats["nifty_rsi"] = rsi_wilder(market["nifty"], 14)
    feats["vix"] = market["vix"]
    feats["index_ma"] = {}   # filled per (index, dma_days) on demand
    return feats


def index_ma(feats, market, index_key, dma_days):
    cache = feats["index_ma"]
    key = (index_key, dma_days)
    if key not in cache:
        cache[key] = market[index_key].ewm(span=dma_days, adjust=False).mean()
    return cache[key]


# --------------------------------------------------------------------------
# conditions
# --------------------------------------------------------------------------

CONDITION_INDICATORS = {
    "ret_6m": "6-month return %",
    "swings_6m": "6-month swings (annualized vol %)",
    "above_ema200": "price above its 200-day EMA",
    "below_ema200": "price below its 200-day EMA",
    "supertrend_green": "Supertrend (10, 3) green",
    "supertrend_red": "Supertrend (10, 3) red",
    "rsi": "RSI(14)",
    "golden_cross": "50-EMA above 200-EMA",
    "from_52w_high": "% from 52-week high",
    "from_ath": "% from all-time high",
    "turnover": "6-month avg daily turnover (Rs)",
    "price": "price (Rs)",
    "vix": "India VIX",
}


def cond_label(c):
    op = c.get("op", "is")
    val = c.get("value", "")
    return f"{c['indicator']} {op} {val}".strip()


def condition_mask(feats, c):
    """-> boolean DataFrame (stocks) or Series (market-level). NaN = False
    for buy/keep rules; for the negated sell triggers (supertrend_red,
    below_ema200) NaN is NOT a trigger either — a name with no data is never
    sold on a condition it cannot evaluate."""
    ind = c["indicator"]
    op = c.get("op")
    val = c.get("value")
    if ind in ("above_ema200", "supertrend_green", "golden_cross"):
        return feats[ind].fillna(False).astype(bool)
    if ind == "supertrend_red":
        return feats["supertrend_green"] == False  # noqa: E712 — NaN is not red
    if ind == "below_ema200":
        return feats["above_ema200"] == False  # noqa: E712 — NaN is not below
    if ind == "vix":
        m = feats["vix"]
        return ((m < val) if op == "below" else (m > val)).fillna(False)
    m = feats[ind]
    if op == "above":
        return (m > val).fillna(False)
    if op == "below":
        return (m < val).fillna(False)
    raise ValueError(f"unknown op {op} for indicator {ind}")


def build_condition_masks(feats, cfg):
    masks = {"keep": [], "buy": [], "sell": []}
    for c in cfg["conditions"]:
        masks[c["when"]].append(condition_mask(feats, c))
    return masks


def _stock_ok(masks_list, tk, i_arr, tid):
    """All conditions true for ticker at day i (market-level series broadcast)."""
    col = tid[tk]
    for m in masks_list:
        if isinstance(m, pd.DataFrame):
            if not bool(m.iloc[i_arr, col]):
                return False
        else:
            if not bool(m.iloc[i_arr]):
                return False
    return True


# --------------------------------------------------------------------------
# sectors
# --------------------------------------------------------------------------

def load_sector_map(tickers):
    try:
        raw = json.load(open("sectors_raw.json", encoding="utf-8"))
    except FileNotFoundError:
        return {}
    out = {}
    for t in tickers:
        base = t.replace(".NS", "")
        if base in raw:
            out[t] = raw[base].get("sector")
    return out


# --------------------------------------------------------------------------
# rebalance calendar
# --------------------------------------------------------------------------

def rebalance_dates_for(cfg, dates):
    months = tuple(cfg["rebalance_months"])
    if cfg["day_mode"] == "month-end":
        return rebalance_dates(dates, months=months)
    if cfg["day_mode"] == "day":
        day = int(cfg["day_of_month"])
        df = pd.Series(dates, index=dates)
        out = []
        for (_y, m), grp in df.groupby([dates.year, dates.month]):
            if m in months:
                cands = [d for d in grp if d.day >= day]
                if cands:
                    out.append(min(cands))
        return sorted(out)
    raise ValueError(cfg["day_mode"])


# --------------------------------------------------------------------------
# the engine
# --------------------------------------------------------------------------

def run_variant(cfg, market, feats, rank_df, fit_df, rbdates):
    """The portfolio loop — report 93's exact accounting plus the builder
    mechanisms. Returns dict(series, events, trades, extras, contributions,
    final state)."""
    closes = market["closes"]
    tickers = list(closes.columns)
    tid = {tk: j for j, tk in enumerate(tickers)}
    dates = closes.index
    closes_arr = closes.to_numpy()
    rank_arr = rank_df.to_numpy()
    fit_arr = fit_df.to_numpy()
    n, m = closes_arr.shape
    rb_set = set(rbdates)

    r = cfg["regime"]
    top_n = cfg["top_n"]
    exit_rank = cfg["exit_rank"]
    exit_mode = cfg["exit_mode"]
    friction = cfg["cost_pct_per_side"] + cfg["slippage_pct_per_side"]
    whole = cfg["whole_units"]
    fixed_per_slot = (cfg["start_capital"] / top_n) if cfg["compounding"] == "fixed_per_position" else None

    masks = build_condition_masks(feats, cfg)
    sell_when = masks["sell"]
    sector_of = load_sector_map(tickers) if cfg["max_per_sector"] else {}

    park_prices = {"GOLDBEES": market["gold"]}
    for sym, s in market["extras"].items():
        park_prices[sym.replace(".NS", "")] = s

    def park_price(sym, i):
        s = park_prices.get(sym)
        if s is None:
            return np.nan
        v = s.iloc[i] if i < len(s) else np.nan
        return float(v) if pd.notna(v) else np.nan

    # regime signals
    idx_key = r["index"]
    signal_close = market[idx_key]
    sig_arr = signal_close.to_numpy()
    st_green_idx = None
    if r["enabled"] and r["signal"] in ("supertrend", "ensemble_2of3"):
        io = market["idx_ohlc"][idx_key]
        st_green_idx = supertrend_dir(io["high"], io["low"], io["close"]).to_numpy()
    ma_arr = None
    if r["enabled"] and r["signal"] in ("below_ma", "ensemble_2of3"):
        ma_arr = index_ma(feats, market, idx_key, r["dma_days"]).to_numpy()
    vix_arr = market["vix"].to_numpy() if len(market["vix"]) else np.full(n, np.nan)

    def vix_off(i):
        if not r["vix_filter"]:
            return False
        v = vix_arr[i]
        return bool(np.isfinite(v) and v > r["vix_filter"]["above"])

    def base_off(i):
        if not r["enabled"]:
            return False
        if r["signal"] == "below_ma":
            ma = ma_arr[i]
            raw_invested = bool(sig_arr[i] > ma) if np.isfinite(ma) else False
            return not raw_invested
        if r["signal"] == "supertrend":
            return not bool(st_green_idx[i]) if st_green_idx is not None and np.isfinite(sig_arr[i]) else False
        if r["signal"] == "none":
            return False
        if r["signal"] == "ensemble_2of3":
            v1 = not (bool(sig_arr[i] > ma_arr[i]) if np.isfinite(ma_arr[i]) else False)
            v2 = not bool(st_green_idx[i]) if st_green_idx is not None else False
            v3 = bool(np.isfinite(vix_arr[i]) and vix_arr[i] > 20)
            return (int(v1) + int(v2) + int(v3)) >= 2
        raise ValueError(r["signal"])

    def raw_off(i):
        b = base_off(i)
        if not r["enabled"] or not r["vix_filter"]:
            return b
        v = vix_off(i)
        return (b or v) if r["vix_mode"] == "or" else (b and v)

    def why_off():
        if r["signal"] == "below_ma":
            return f"regime exit — {INDEX_LABEL[idx_key]} closed below its {r['dma_days']}-day EMA"
        if r["signal"] == "supertrend":
            return f"regime exit — Supertrend (10, 3) turned red on {INDEX_LABEL[idx_key]}"
        if r["signal"] == "ensemble_2of3":
            return f"regime exit — 2 of 3 signals (EMA, Supertrend, VIX) turned risk-off on {INDEX_LABEL[idx_key]}"
        if r["signal"] == "none":
            return "regime exit — India VIX above its threshold"
        return "regime exit"

    def ranked_tickers(i):
        row = rank_arr[i]
        order = np.argsort(np.where(np.isfinite(row), row, np.inf), kind="stable")
        return [tickers[j] for j in order if np.isfinite(row[j])]

    # state
    positions = {}
    park_units = {}
    cash = 0.0
    started = False
    state = "off" if r["enabled"] else "invested"
    index_level = np.full(n, np.nan)
    events = []
    trades = []
    extras = []
    contributions = []
    dip_month = None

    def pv(i):
        v = cash
        for tk, p in positions.items():
            px = closes_arr[i, tid[tk]]
            if np.isfinite(px):
                v += p["qty"] * px
        for sym, u in park_units.items():
            px = park_price(sym, i)
            if np.isfinite(px):
                v += u * px
        return v

    def park_cash(amount, i):
        """Split freed cash across the park basket; a symbol without a price
        that day leaves its share in cash. Returns leftover cash."""
        if not r["park"] or amount <= 0:
            return amount
        leftover = amount
        for p in r["park"]:
            sym = p["symbol"]
            share = amount * p["pct"] / 100.0
            px = park_price(sym, i)
            if np.isfinite(px) and px > 0 and share > 0:
                park_units[sym] = park_units.get(sym, 0.0) + share * (1 - friction) / px
                leftover -= share
        return leftover

    def close_park(i):
        nonlocal cash
        for sym in list(park_units):
            u = park_units.pop(sym)
            px = park_price(sym, i)
            if np.isfinite(px):
                cash += u * px * (1 - friction)

    def buy_slots(candidates, money, n_slots, i, date_s, why_tag, buys):
        """MomentumScore slot semantics: money is divided over the open
        slots; each candidate fills one slot at its per-slot size; unfilled
        slots' money is returned as leftover cash (never redistributed).
        Fractional mode buys every candidate exactly like report 93's
        do_buys (no cash guard — the caller caps candidates to n_slots);
        fixed mode stops when the cash pool can't fund a full slot."""
        if not candidates or n_slots <= 0:
            return money
        per = fixed_per_slot if fixed_per_slot is not None else money / n_slots
        left = money
        for tk, _rk in candidates:
            if fixed_per_slot is not None and left < per - 1e-9:
                break
            px = closes_arr[i, tid[tk]]
            if not np.isfinite(px) or per <= 0:
                continue
            spend = per
            if whole:
                qty = math.floor(spend * (1 - friction) / px)
                invested = qty * px / (1 - friction) if qty > 0 else 0.0
            else:
                qty = spend * (1 - friction) / px
                invested = spend
            if qty <= 0:
                continue
            rk, ft = rank_arr[i, tid[tk]], fit_arr[i, tid[tk]]
            n_ranked = int(np.isfinite(rank_arr[i]).sum())
            positions[tk] = {
                "qty": qty, "entry_date": date_s, "entry_price": float(px),
                "invested_gross": invested,
                "rank_in": int(rk) if np.isfinite(rk) else None,
                "fit_in": int(ft) if np.isfinite(ft) else None,
                "why_in": f"{why_tag} — rank {int(rk) if np.isfinite(rk) else '—'} of ~{n_ranked}, "
                          f"fit {int(ft) if np.isfinite(ft) else '—'}%",
                "carried_dates": [],
            }
            buys.append({"ticker": tk.replace(".NS", ""),
                         "rank_in": positions[tk]["rank_in"], "fit_in": positions[tk]["fit_in"],
                         "amount": round(invested, 2)})
            left -= invested
        return max(left, 0.0)

    def candidates_for(i, sector_counts=None):
        """Ranked, non-held, buy-condition-passing candidates, honouring
        entry_rank and the sector cap."""
        out = []
        counts = dict(sector_counts or {})
        for tk in ranked_tickers(i):
            if tk in positions:
                continue
            rk = rank_arr[i, tid[tk]]
            if cfg["entry_rank"] is not None and rk > cfg["entry_rank"]:
                continue
            if not _stock_ok(masks["buy"], tk, i, tid):
                continue
            if cfg["max_per_sector"] is not None:
                sec = sector_of.get(tk)
                if counts.get(sec, 0) >= cfg["max_per_sector"]:
                    continue
                counts[sec] = counts.get(sec, 0) + 1
            out.append((tk, rk))
        return out

    def sell_position(tk, i, date_s, why, reason, tag_sells):
        p = positions.pop(tk)
        px = closes_arr[i, tid[tk]]
        gross = p["qty"] * px
        net = gross * (1 - friction)
        rk = rank_arr[i, tid[tk]]
        ft = fit_arr[i, tid[tk]]
        trades.append({
            "ticker": tk.replace(".NS", ""),
            "entry_date": p["entry_date"], "entry_price": round(p["entry_price"], 2),
            "exit_date": date_s, "exit_price": round(float(px), 2),
            "qty": round(p["qty"], 6),
            "pct_return": round((net / p["invested_gross"] - 1) * 100, 2),
            "pnl": round(net - p["invested_gross"], 2),
            "status": "closed", "carried_in": False,
            "num_rebalances_held": len(p["carried_dates"]),
            "carried_dates": p["carried_dates"],
            "rank_in": p["rank_in"], "fit_in": p["fit_in"],
            "rank_out": int(rk) if np.isfinite(rk) else None,
            "fit_out": int(ft) if np.isfinite(ft) else None,
            "why_in": p["why_in"], "why_out": why,
        })
        tag_sells.append({"ticker": tk.replace(".NS", ""), "reason": reason,
                          "rank_out": int(rk) if np.isfinite(rk) else None,
                          "fit_out": int(ft) if np.isfinite(ft) else None,
                          "proceeds": round(net, 2)})
        return net

    for i, d in enumerate(dates):
        is_rb = d in rb_set
        date_s = d.strftime("%Y-%m-%d")
        off_today = raw_off(i)

        # ---- start ----
        if not started:
            if is_rb and int(np.isfinite(rank_arr[i]).sum()) >= MIN_ELIGIBLE:
                started = True
                if not off_today:
                    state = "invested"
                    buys = []
                    cand = candidates_for(i)[:top_n]
                    left = buy_slots(cand, cfg["start_capital"], top_n, i, date_s, "initial entry", buys)
                    cash = left if left > 0.01 else 0.0
                    events.append({"date": date_s, "trigger": "initial_entry",
                                   "value_before": cfg["start_capital"],
                                   "value_after": round(pv(i), 2),
                                   "sells": [], "buys": buys, "keeps": [], "cash_left": round(cash, 2),
                                   "holdings_after": [{"ticker": tk.replace(".NS", ""),
                                                       "rank": positions[tk]["rank_in"], "fit": positions[tk]["fit_in"]}
                                                      for tk in positions]})
                else:
                    state = "off"
                    cash = park_cash(cfg["start_capital"], i) if r["action"] == "park" else cfg["start_capital"]
                    events.append({"date": date_s, "trigger": "initial_entry (hedge)",
                                   "value_before": cfg["start_capital"],
                                   "value_after": round(pv(i), 2),
                                   "sells": [],
                                   "buys": [{"ticker": p["symbol"], "amount": cfg["start_capital"] * p["pct"] / 100.0}
                                            for p in (r["park"] if r["action"] == "park" else [])],
                                   "keeps": [], "cash_left": round(cash, 2),
                                   "holdings_after": [{"ticker": s, "note": "regime off at start"} for s in park_units]})
                index_level[i] = pv(i)
            continue

        # ---- daily exits: sell_when conditions ----
        if state == "invested" and sell_when:
            for tk in list(positions):
                if not _stock_ok(sell_when, tk, i, tid):
                    why = "sell-when rule: " + " / ".join(cond_label(c) for c in cfg["conditions"] if c["when"] == "sell")
                    cash += sell_position(tk, i, date_s, why, "sell-when", [])
                    extras.append({"date": date_s, "kind": "sell_when", "ticker": tk.replace(".NS", ""),
                                   "detail": why})

        # ---- daily exits: exit-rank breach (exit_mode on_breach) ----
        if state == "invested" and exit_mode == "on_breach":
            for tk in list(positions):
                rk = rank_arr[i, tid[tk]]
                if (not np.isfinite(rk)) or rk > exit_rank:
                    why = (f"fell to rank {int(rk)} — below the exit rank {exit_rank} (checked daily)"
                           if np.isfinite(rk) else "no longer ranked (insufficient history)")
                    cash += sell_position(tk, i, date_s, why, "exit rank (daily)", [])
                    extras.append({"date": date_s, "kind": "exit_rank_daily", "ticker": tk.replace(".NS", ""),
                                   "detail": why})

        value_before = pv(i)

        # ---- regime flips, then the scheduled review — one chain, exactly
        # report 93's precedence: a regime action on a review day replaces
        # that day's scheduled review.
        regime_acts = r["enabled"] and (r["check"] == "daily" or is_rb)
        regime_handled = False
        if regime_acts and state == "invested" and off_today:
            regime_handled = True
            sells = []
            if r["action"] == "half":
                for tk in list(positions):
                    p = positions[tk]
                    px = closes_arr[i, tid[tk]]
                    half_qty = p["qty"] / 2.0
                    gross = half_qty * px
                    net = gross * (1 - friction)
                    cash += net
                    rk = rank_arr[i, tid[tk]]
                    ft = fit_arr[i, tid[tk]]
                    trades.append({
                        "ticker": tk.replace(".NS", ""),
                        "entry_date": p["entry_date"], "entry_price": round(p["entry_price"], 2),
                        "exit_date": date_s, "exit_price": round(float(px), 2),
                        "qty": round(half_qty, 6),
                        "pct_return": round((net / (p["invested_gross"] / 2.0) - 1) * 100, 2),
                        "pnl": round(net - p["invested_gross"] / 2.0, 2),
                        "status": "closed", "carried_in": False, "partial": True,
                        "num_rebalances_held": len(p["carried_dates"]),
                        "carried_dates": p["carried_dates"],
                        "rank_in": p["rank_in"], "fit_in": p["fit_in"],
                        "rank_out": int(rk) if np.isfinite(rk) else None,
                        "fit_out": int(ft) if np.isfinite(ft) else None,
                        "why_in": p["why_in"], "why_out": why_off() + " (half de-risk)",
                    })
                    p["qty"] -= half_qty
                    p["invested_gross"] /= 2.0
                    sells.append({"ticker": tk.replace(".NS", ""), "reason": "regime exit (half)",
                                  "rank_out": int(rk) if np.isfinite(rk) else None,
                                  "fit_out": int(ft) if np.isfinite(ft) else None,
                                  "proceeds": round(net, 2)})
                if r["action"] == "park":
                    cash = park_cash(cash, i)
                state = "off"
            else:
                for tk in list(positions):
                    cash += sell_position(tk, i, date_s, why_off(), "regime exit", sells)
                if r["action"] == "park":
                    cash = park_cash(cash, i)
                state = "off"
            events.append({"date": date_s, "trigger": "regime_exit",
                           "value_before": round(value_before, 2),
                           "value_after": round(pv(i), 2),
                           "sells": sells, "buys": [], "keeps": [], "cash_left": round(cash, 2),
                           "holdings_after": ([{"ticker": tk.replace(".NS", ""), "note": "half position kept"}
                                               for tk in positions]
                                              + [{"ticker": s, "note": "regime off"} for s in park_units])})
        elif regime_acts and state == "off" and not off_today:
            regime_handled = True
            park_syms = list(park_units)
            buys = []
            if r["action"] == "half" and positions:
                close_park(i)
                total = sum(p["qty"] * closes_arr[i, tid[tk]] for tk, p in positions.items())
                if total > 0:
                    for tk, p in positions.items():
                        add = cash * (p["qty"] * closes_arr[i, tid[tk]] / total)
                        px = closes_arr[i, tid[tk]]
                        p["qty"] += add * (1 - friction) / px
                        p["invested_gross"] += add
                        buys.append({"ticker": tk.replace(".NS", ""), "amount": round(add, 2),
                                     "note": "re-top-up on re-entry"})
                    cash = 0.0
            else:
                close_park(i)
                cand = candidates_for(i)[:top_n]
                left = buy_slots(cand, cash, top_n, i, date_s, "regime re-entry", buys)
                cash = left if left > 0.01 else 0.0
            state = "invested"
            events.append({"date": date_s, "trigger": "regime_reentry",
                           "value_before": round(value_before, 2),
                           "value_after": round(pv(i), 2),
                           "sells": [{"ticker": s, "reason": "regime re-entry"} for s in park_syms],
                           "buys": buys, "keeps": [], "cash_left": round(cash, 2),
                           "holdings_after": [{"ticker": tk.replace(".NS", ""),
                                               "rank": int(rank_arr[i, tid[tk]]) if np.isfinite(rank_arr[i, tid[tk]]) else None,
                                               "fit": int(fit_arr[i, tid[tk]]) if np.isfinite(fit_arr[i, tid[tk]]) else None}
                                              for tk in positions]})

        # ---- scheduled review: hysteresis + refill ----
        if (not regime_handled) and state == "invested" and not off_today and is_rb:
            sells, buys, keeps = [], [], []
            sector_counts = {}
            for tk in list(positions):
                rk = rank_arr[i, tid[tk]]
                failed = (not np.isfinite(rk)) or rk > exit_rank
                keep_fail = None
                if not failed and masks["keep"] and not _stock_ok(masks["keep"], tk, i, tid):
                    failed = True
                    keep_fail = " / ".join(cond_label(c) for c in cfg["conditions"] if c["when"] == "keep")
                if failed:
                    why = (f"fell to rank {int(rk)} — below the exit rank {exit_rank}" if np.isfinite(rk)
                           else "no longer ranked (insufficient history)")
                    if keep_fail:
                        why = f"stopped passing a keep-if rule: {keep_fail}"
                    cash += sell_position(tk, i, date_s, why, "exit rank", sells)
                else:
                    positions[tk]["carried_dates"].append(date_s)
                    keeps.append({"ticker": tk.replace(".NS", ""),
                                  "rank": int(rk), "fit": int(fit_arr[i, tid[tk]])})
                    sec = sector_of.get(tk)
                    sector_counts[sec] = sector_counts.get(sec, 0) + 1
            cash_left = 0.0
            slots = top_n - len(positions)
            if slots > 0 and cash > 0:
                cand = candidates_for(i, sector_counts)[:slots]
                if cand:
                    left = buy_slots(cand, cash, slots, i, date_s, "review refill", buys)
                    cash = left if left > 0.01 else 0.0
                    cash_left = cash
                else:
                    cash_left = cash
            events.append({"date": date_s, "trigger": "scheduled_rebalance",
                           "value_before": round(value_before, 2),
                           "value_after": round(pv(i), 2),
                           "sells": sells, "buys": buys, "keeps": keeps,
                           "cash_left": round(cash_left, 2),
                           "holdings_after": [{"ticker": tk.replace(".NS", ""),
                                               "rank": int(rank_arr[i, tid[tk]]) if np.isfinite(rank_arr[i, tid[tk]]) else None,
                                               "fit": int(fit_arr[i, tid[tk]]) if np.isfinite(fit_arr[i, tid[tk]]) else None}
                                              for tk in positions]})

        # ---- SIP (first trading day of each month) ----
        if cfg["sip"] and (i == 0 or dates[i - 1].month != d.month):
            amount = cfg["sip"]["monthly"] * (1 + cfg["sip"]["step_up_pct"] / 100.0) ** max(0, d.year - dates[0].year)
            contributions.append({"date": date_s, "amount": round(amount, 2), "kind": "sip"})
            if state == "invested" and positions:
                total = sum(p["qty"] * closes_arr[i, tid[tk]] for tk, p in positions.items())
                for tk, p in positions.items():
                    add = amount * (p["qty"] * closes_arr[i, tid[tk]] / total)
                    px = closes_arr[i, tid[tk]]
                    p["qty"] += add * (1 - friction) / px
                    p["invested_gross"] += add
            else:
                cash += park_cash(amount, i) if r["action"] == "park" else amount

        # ---- buy the dip (NIFTY RSI below level, at most once a month) ----
        if cfg["dip"]:
            dip = cfg["dip"]
            rsi_now = feats["nifty_rsi"].iloc[i]
            if dip_month != (d.year, d.month) and np.isfinite(rsi_now) and rsi_now < dip["rsi_below"]:
                dip_month = (d.year, d.month)
                amount = dip["amount"]
                contributions.append({"date": date_s, "amount": round(amount, 2), "kind": "dip"})
                if state == "invested" and positions:
                    total = sum(p["qty"] * closes_arr[i, tid[tk]] for tk, p in positions.items())
                    for tk, p in positions.items():
                        add = amount * (p["qty"] * closes_arr[i, tid[tk]] / total)
                        px = closes_arr[i, tid[tk]]
                        p["qty"] += add * (1 - friction) / px
                        p["invested_gross"] += add
                else:
                    cash += park_cash(amount, i) if r["action"] == "park" else amount
                extras.append({"date": date_s, "kind": "buy_the_dip", "amount": round(amount, 2),
                               "detail": f"NIFTY RSI(14) {rsi_now:.1f} < {dip['rsi_below']}"})

        index_level[i] = pv(i)

    # open positions at the end, marked to the last close
    open_trades = []
    for tk, p in positions.items():
        px = closes_arr[-1, tid[tk]]
        if np.isfinite(px):
            value_net = p["qty"] * px * (1 - friction)
            rk = rank_arr[-1, tid[tk]]
            ft = fit_arr[-1, tid[tk]]
            open_trades.append({
                "ticker": tk.replace(".NS", ""),
                "entry_date": p["entry_date"], "entry_price": round(p["entry_price"], 2),
                "exit_date": None, "exit_price": None,
                "qty": round(p["qty"], 6),
                "pct_return": round((value_net / p["invested_gross"] - 1) * 100, 2),
                "pnl": round(value_net - p["invested_gross"], 2),
                "status": "open", "carried_in": False,
                "num_rebalances_held": len(p["carried_dates"]),
                "carried_dates": p["carried_dates"],
                "rank_in": p["rank_in"], "fit_in": p["fit_in"],
                "rank_out": int(rk) if np.isfinite(rk) else None,
                "fit_out": int(ft) if np.isfinite(ft) else None,
                "why_in": p["why_in"],
                "why_out": f"still held — rank {int(rk)}" if np.isfinite(rk) else "still held",
            })
    trades.extend(open_trades)

    series = pd.Series(index_level, index=dates).dropna()
    return {"series": series, "events": events, "trades": trades, "extras": extras,
            "contributions": contributions, "final_state": state,
            "final_positions": list(positions.keys())}


# --------------------------------------------------------------------------
# lab runner
# --------------------------------------------------------------------------

def _trade_stats(trades):
    closed = [t for t in trades if t["status"] == "closed"]
    closed_pcts = [t["pct_return"] for t in closed]
    wins = [p for p in closed_pcts if p > 0]
    losses = [p for p in closed_pcts if p <= 0]
    return {
        "total_trades": len(closed_pcts),
        "win_rate_pct": round(len(wins) / len(closed_pcts) * 100, 1) if closed_pcts else None,
        "avg_win_pct": round(sum(wins) / len(wins), 2) if wins else None,
        "avg_loss_pct": round(sum(losses) / len(losses), 2) if losses else None,
        "avg_rebalances_held": round(sum(t["num_rebalances_held"] for t in closed) / len(closed), 1) if closed else None,
        "total_realized_pnl": round(sum(t["pnl"] for t in closed), 2),
        "total_unrealized_pnl": round(sum(t["pnl"] for t in trades if t["status"] == "open"), 2),
        "open_positions": sum(1 for t in trades if t["status"] == "open"),
    }


def evaluate_variant(label, cfg, market, feats, rank_df, fit_df, fmv_map, quiet=False):
    """Run one variant (cost-free + friction run) and build its full
    series object with review-layer extras."""
    closes = market["closes"]
    dates = closes.index
    common = market["common"]
    nifty = market["nifty"]

    rbdates = rebalance_dates_for(cfg, dates)
    cfg_free = dict(cfg, cost_pct_per_side=0.0, slippage_pct_per_side=0.0)

    if not quiet:
        print(f"  [{label}] running (frictionless) ...")
    run_free = run_variant(cfg_free, market, feats, rank_df, fit_df, rbdates)
    if not quiet:
        print(f"  [{label}] running (with costs) ...")
    run = run_variant(cfg, market, feats, rank_df, fit_df, rbdates)

    before_costs = metrics_only(run_free["series"], common)
    after_costs = metrics_only(run["series"], common)

    after_full = [[d.strftime("%Y-%m-%d"), float(v)] for d, v in run["series"].items()]
    nifty_full = [[d.strftime("%Y-%m-%d"), float(v)] for d, v in nifty.items()]

    halves = ms_rob.halves_check(after_full, nifty_full)
    health = ms_health.health_check(after_full, run["trades"])

    closed = [t for t in run["trades"] if t["status"] == "closed"]
    tax_input = [{"ticker": t["ticker"], "entry_date": t["entry_date"], "exit_date": t["exit_date"],
                  "entry_price": t["entry_price"], "exit_price": t["exit_price"], "qty": t["qty"]}
                 for t in closed]
    tax_report = ms_tax.capital_gains_report(tax_input, fmv_by_ticker=fmv_map, fmv_date=FMV_DATE)
    tax_by_fy = {y["fy"]: y["total_tax"] for y in tax_report["years"] if y["total_tax"] > 0}
    at_points, taxes_applied = ms_tax.after_tax_curve(after_full, tax_by_fy)
    at_series = pd.Series([v for _d, v in at_points],
                          index=pd.DatetimeIndex([d for d, _v in at_points]))
    after_tax = metrics_only(at_series, common)

    stats = _trade_stats(run["trades"])
    contributed = cfg["start_capital"] + sum(c["amount"] for c in run["contributions"])

    out = dict(after_costs)
    out["before_costs"] = before_costs
    out["after_tax"] = after_tax
    out["health"] = health
    out["halves"] = halves
    out["tax"] = {
        "total_tax": tax_report["totals"]["total_tax"],
        "tax_pct_of_realised_pnl": tax_report["totals"]["tax_pct_of_realised_pnl"],
        "n_closed_trades": tax_report["n_closed_trades"],
        "growth_before_tax_pct": after_costs["cagr_pct"],
        "growth_after_tax_pct": after_tax["cagr_pct"],
        "taxes_applied_to_curve": taxes_applied,
    }
    out["stats"] = stats
    out["config"] = describe_config(cfg)
    out["contributed_total"] = round(contributed, 2)
    out["final_value"] = round(float(run["series"].iloc[-1]), 2)
    out["n_events"] = len(run["events"])
    out["n_extras"] = len(run["extras"])
    return out, run


def _json_safe(obj, path="root"):
    """Walk a nested structure and convert every non-finite float (NaN/inf)
    to None, plus numpy scalars to Python ones. Bare NaN is valid for
    Python's json module but NOT for JavaScript's JSON.parse — the same
    lesson that broke ms_lab.json once. Warns loudly when it finds one."""
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, (int, np.integer)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        v = float(obj)
        if math.isnan(v) or math.isinf(v):
            print(f"  [warn] non-finite float at {path} -> null")
            return None
        return v
    if isinstance(obj, dict):
        return {str(k): _json_safe(v, f"{path}.{k}") for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v, f"{path}[{i}]") for i, v in enumerate(obj)]
    return obj


def run_lab(lab_key, lab_title, configs, out_path, notes=None):
    """configs: list of (label, overrides_dict). The first entry is the
    lab's hero and should be the report-93 configuration."""
    print("loading market data ...")
    market = load_market()
    closes = market["closes"]
    dates = closes.index
    print(f"window: {dates[0].date()} -> {dates[-1].date()} ({len(dates)} days), "
          f"{len(closes.columns)} symbols")

    print("computing features (ranks, supertrend, RSI, ...) ...")
    rank_df, fit_df, _score = build_ranks(closes)
    feats = build_features(market)

    fmv_idx = closes.index[closes.index <= FMV_DATE]
    fmv_map = {}
    if len(fmv_idx):
        row = closes.loc[fmv_idx[-1]]
        fmv_map = {str(t).replace(".NS", "").upper(): float(v) for t, v in row.items() if v == v}

    variants = {}
    for label, overrides in configs:
        cfg = default_config(**overrides)
        variant, _run = evaluate_variant(label, cfg, market, feats, rank_df, fit_df, fmv_map)
        variants[label] = variant
        print(f"  [{label}] CAGR {variant['cagr_pct']:.1f}%  maxDD {variant['max_drawdown_pct']:.1f}%  "
              f"health {variant['health']['score']}/100  trades {variant['stats']['total_trades']}")

    out = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": dates[0].strftime("%Y-%m-%d"),
        "end_date": dates[-1].strftime("%Y-%m-%d"),
        "lab": lab_key,
        "lab_title": lab_title,
        "hero_label": configs[0][0],
        "variants": variants,
        "nifty": metrics_only(market["nifty"], market["common"]),
        "gold_benchmark": metrics_only(market["gold"], market["common"]),
        "notes": notes or [],
    }
    out = _json_safe(out)
    txt = json.dumps(out, indent=1, ensure_ascii=False, allow_nan=False)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(txt)
    print(f"{out_path} written ({len(variants)} variants)")
    return out

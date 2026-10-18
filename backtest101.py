"""
Report 101 — Clean-room ProPicks India: momentum + value + growth + quality.

WHAT THIS IS
A from-scratch reconstruction of the *factor structure* of Investing.com's
ProPicks India strategies (INSG20 small-cap, INMM20 mid-cap), inferred purely
from their publicly published rebalance press releases and methodology page —
see docs/propicks-india-recon.md for the full reverse-engineering write-up.

Nothing was taken from their product: no paywall bypassed, no private endpoint
called, no proprietary code or model weights obtained. The inference was:
every published rationale cites exactly four pillars — momentum, value-vs-fair-
value, growth, balance-sheet quality — so this builds a four-pillar composite
score and tests whether that structure actually earns anything on Indian
small/mid-caps.

SELECTION (reconstructed rules)
  - Universe: NIFTY Smallcap 250 (stands in for INSG20) and NIFTY Midcap 150
    (stands in for INMM20).
  - Rebalance: FIRST trading day of every month, at that day's close — the
    cadence Investing.com states repeatedly.
  - Top 20 names, equal weight, full re-slice each rebalance.
  - Score = cross-sectional composite of four pillars:
      momentum  risk-adjusted 3m/6m/12m return
      value     earnings yield (E/P) and book yield (B/P)
      growth    revenue and EBITDA YoY
      quality   ROE (higher better) and debt/equity (lower better)
    Each pillar Z-scored across the eligible universe and clipped to +/-3.
  - "pro_4_gate" additionally imposes the fair-value gate: a stock is only
    eligible if it is cheaper than the median peer on P/E and/or P/B — the
    "trades below our fair value" condition in every published rationale,
    implemented as relative cheapness because an absolute anchor proved
    unsuitable (see limitation 4).

THREE VARIANTS PER UNIVERSE
  mom_only   momentum pillar alone — the control, and the project's existing
             method, so the four-pillar score has something to beat.
  pro_4      the four-pillar composite.
  pro_4_gate pro_4 plus the fair-value gate.

DISCLOSED ASSUMPTIONS AND LIMITATIONS (read before trusting any number)
 1. SURVIVORSHIP BIAS: today's NIFTY Smallcap 250 / Midcap 150 constituent
    lists are applied retroactively to every rebalance. Stocks that fell out
    of the index, delisted, merged or went bankrupt are absent from the whole
    history. This flatters every variant here. Strongest for smallcaps.
 2. REPORTING LAG = 90 days: a fundamental period is only usable from
    period_end + 90 days. Indian annual results for a March year-end are due
    within ~60 days (SEBI), so 90 is deliberately conservative — it costs
    staleness rather than risking look-ahead. Without this, every value/
    growth/quality reading would be look-ahead. Disclosed, not hidden.
 3. MARKET CAP IS REBUILT POINT-IN-TIME: price at the rebalance date x share
    count from the most recent balance sheet already published. This is why
    share counts had to be fetched at all.
 4. "FAIR VALUE" IS A DISCLOSED PROXY, NOT THEIR MODEL: their fair-value
    engine is proprietary and not recoverable. TESTED AND REJECTED: the
    classic Graham number sqrt(22.5 x EPS x BVPS) was the first attempt at
    an absolute anchor, and it fails outright on Indian small/mid-caps — the
    median stock in both universes trades 54% to 82% BELOW a Graham anchor
    across 2023-2026, so only 4-24% of names ever clear a "price below fair
    value" gate (measured: 8-48 of ~200 eligible smallcaps, 3-36 of ~130
    midcaps, per rebalance). That is not a tuning problem, it is the wrong
    model: Graham's anchor implies roughly 4.7x earnings at parity, which is
    nowhere near an investable Indian small-cap. USEFUL CONSEQUENCE: their
    own published fair values sit only 13-52% above price, so their anchor
    cannot be Graham-style either — it must be growth-adjusted (DCF or a
    forward-multiple model). WHAT IS USED INSTEAD: a peer-relative anchor —
    fair value = the universe's median P/E (and median P/B) applied to that
    stock's own EPS (and book value), gate = positive upside to it, i.e.
    "cheaper than the median peer". It needs no invented macro assumption
    and is fully computable point-in-time, but it is a stand-in for a
    relative-cheapness requirement, NOT a replication of their model.
 5. EQUALLY WEIGHTED, full re-slice each month: charges buy+sell costs on
    ~100% of the book every month. Real ProPicks rotates only 4-8 of 20 names
    (~20-40% turnover), so the cost-loaded figures here are a CONSERVATIVE
    (pessimistic) upper bound on cost drag relative to the real thing.
 6. NO INTRADAY / SLIPPAGE modelling beyond the sourced statutory + brokerage
    ladder reused from report 32. No taxes, no impact cost, no borrow costs.
 7. FUNDAMENTAL WINDOW IS SHORT by nature: only ~4-5 annual periods are
    available from the data source, so the four-pillar variants can only start
    around mid-2023 once the lag and a prior-year growth base are both
    satisfied. mom_only has full price history but is reported on the SAME
    window as pro_4 for an apples-to-apples comparison; its full-history
    capability is not what is being tested here.
 8. PERIODS are annual, and a stock's "prior year" is its previous annual
    period in the data, not a calendar-aligned fiscal year — Indian companies
    with non-March year-ends will have their growth measured off their own
    fiscal calendar. Disclosed rather than silently re-aligned.

Benchmark: NIFTY Smallcap 250 index, NIFTY Midcap 150 index, NIFTY 50.
"""
import json

import numpy as np
import pandas as pd

from backtest10 import series_to_points, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes, metrics
from backtest15 import load_smallcap250_closes
from backtest32 import BUY_COST_PCT, SELL_COST_PCT

# ---- selection / timing constants -------------------------------------
TOP_N = 20
MIN_ELIGIBLE = 40
REPORTING_LAG_DAYS = 90
LOOKBACK_12M = 252
LOOKBACK_6M = 126
LOOKBACK_3M = 63
Z_CLIP = 3.0
BASE_VALUE = 100.0

FUND_PKL = "fundamentals_sc_mc_raw.pkl"

# equity / debt / share-count / revenue / ebitda / net-income row fallbacks,
# in order of preference — the data source uses slightly different labels
# across tickers and fiscal vintages.
EQUITY_ROWS = ("Stockholders Equity", "Common Stock Equity",
               "Total Equity Gross Minority Interest")
DEBT_ROWS = ("Total Debt",
             "Long Term Debt And Capital Lease Obligation")
SHARE_ROWS = ("Ordinary Shares Number", "Share Issued")
REV_ROWS = ("Total Revenue", "Operating Revenue", "Gross Profit")
EBITDA_ROWS = ("EBITDA", "Normalized EBITDA")
NI_ROWS = ("Net Income", "Net Income Common Stockholders",
           "Net Income Including Noncontrolling Interests")
DEP_ROWS = ("Reconciled Depreciation", "Depreciation And Amortization In Income Statement",
            "Depreciation Income Statement")
OPINC_ROWS = ("Operating Income", "EBIT")


# ---------------------------------------------------------------------
# fundamentals: build a point-in-time lookup per ticker
# ---------------------------------------------------------------------
def _pick(df, rows, col):
    """First row in `rows` that has a usable value at period `col`."""
    if df is None or df.empty:
        return None
    for name in rows:
        if name in df.index:
            try:
                v = df.loc[name, col]
            except KeyError:
                continue
            if isinstance(v, pd.Series):
                v = v.iloc[0]
            if pd.notna(v):
                try:
                    return float(v)
                except (TypeError, ValueError):
                    return None
    return None


def extract_periods(ticker, data):
    """-> list of (period_end, metrics_dict) sorted ascending.

    metrics: equity, debt, shares, revenue, ebitda, net_income, plus
    prior_revenue / prior_ebitda for YoY growth (the previous annual period).
    """
    bs = data.get("balance_sheet")
    fin = data.get("financials")
    if bs is None or bs.empty or fin is None or fin.empty:
        return []

    periods = [c for c in bs.columns if c in fin.columns]
    if not periods:
        return []
    periods = sorted(periods)

    out = []
    for i, p in enumerate(periods):
        equity = _pick(bs, EQUITY_ROWS, p)
        shares = _pick(bs, SHARE_ROWS, p)
        debt = _pick(bs, DEBT_ROWS, p)
        revenue = _pick(fin, REV_ROWS, p)
        net_income = _pick(fin, NI_ROWS, p)
        ebitda = _pick(fin, EBITDA_ROWS, p)
        if ebitda is None:
            opinc = _pick(fin, OPINC_ROWS, p)
            dep = _pick(fin, DEP_ROWS, p)
            if opinc is not None and dep is not None:
                ebitda = opinc + dep

        rec = {
            "equity": equity, "debt": debt, "shares": shares,
            "revenue": revenue, "ebitda": ebitda, "net_income": net_income,
            "prior_revenue": None, "prior_ebitda": None,
        }
        if i > 0:
            prev = out[-1][1]
            rec["prior_revenue"] = prev["revenue"]
            rec["prior_ebitda"] = prev["ebitda"]
        out.append((p, rec))
    return out


def load_fundamentals():
    """-> {ticker: [(period_end, metrics), ...]} sorted ascending."""
    import pickle
    with open(FUND_PKL, "rb") as f:
        raw = pickle.load(f)
    panel = {}
    for ticker, data in raw.items():
        if data.get("error"):
            continue
        periods = extract_periods(ticker, data)
        if periods:
            panel[ticker] = periods
    return panel


def asof_metrics(panel, ticker, asof_date):
    """Latest fundamental period published by `asof_date` (already lagged),
    or None. Pure point-in-time: never returns a period not yet knowable."""
    rows = panel.get(ticker)
    if not rows:
        return None
    best = None
    for p, rec in rows:
        if p + pd.Timedelta(days=REPORTING_LAG_DAYS) <= asof_date:
            best = rec
        else:
            break
    return best


# ---------------------------------------------------------------------
# per-rebalance metric computation
# ---------------------------------------------------------------------
def momentum_pillar(closes, t_idx, tickers):
    """Risk-adjusted 3m/6m/12m returns -> per-ticker score (raw, pre-Z)."""
    if t_idx < LOOKBACK_12M:
        return pd.Series(dtype=float)
    price_t = closes.iloc[t_idx]
    window = closes.iloc[t_idx - LOOKBACK_12M: t_idx + 1][tickers]
    daily_ret = window.pct_change().dropna(how="all")
    vol = daily_ret.std()

    def ratio(offset):
        past = closes.iloc[t_idx - offset]
        ret = price_t[tickers] / past[tickers] - 1.0
        with np.errstate(divide="ignore", invalid="ignore"):
            return ret / vol

    r3, r6, r12 = ratio(LOOKBACK_3M), ratio(LOOKBACK_6M), ratio(LOOKBACK_12M)
    frame = pd.DataFrame({"r3": r3, "r6": r6, "r12": r12}).replace(
        [np.inf, -np.inf], np.nan)
    # weight toward the 6m/12m pair the project's standard formula uses,
    # with a smaller 3m sleeve because every published ProPicks rationale
    # quotes a 3-month return.
    return frame


def zscore(series, clip=Z_CLIP):
    s = pd.to_numeric(series, errors="coerce")
    s = s.replace([np.inf, -np.inf], np.nan).dropna()
    if len(s) < 3 or s.std(ddof=0) == 0:
        return pd.Series(dtype=float)
    z = (s - s.mean()) / s.std(ddof=0)
    return z.clip(-clip, clip)


def fundamental_pillars(panel, closes, t_idx, tickers):
    """Per-ticker value / growth / quality raw metrics at this rebalance."""
    d = closes.index[t_idx]
    rows = {}
    for t in tickers:
        price = closes.iloc[t_idx][t]
        m = asof_metrics(panel, t, d)
        if m is None or not pd.notna(price) or price <= 0:
            continue
        equity, shares = m["equity"], m["shares"]
        if equity is None or shares is None or equity <= 0 or shares <= 0:
            continue

        mcap = price * shares
        bvps = equity / shares
        ni = m["net_income"]
        eps = (ni / shares) if ni is not None else None

        # value: both yields are "higher = cheaper"
        ep = (eps / price) if eps is not None else None
        bp = bvps / price if bvps else None

        # quality: ROE higher better, D/E lower better (negated later)
        roe = (ni / equity) if ni is not None else None
        de = None
        if m["debt"] is not None:
            de = m["debt"] / equity

        # growth
        rev_g = None
        if m["revenue"] is not None and m["prior_revenue"] not in (None, 0):
            rev_g = m["revenue"] / m["prior_revenue"] - 1.0
        ebitda_g = None
        if m["ebitda"] is not None and m["prior_ebitda"] not in (None, 0) \
                and m["prior_ebitda"] > 0:
            ebitda_g = m["ebitda"] / m["prior_ebitda"] - 1.0

        rows[t] = {
            "mcap": mcap, "ep": ep, "bp": bp, "roe": roe, "de": de,
            "rev_g": rev_g, "ebitda_g": ebitda_g,
        }
    return rows


def make_select_fn(mode, panel):
    """Returns select_fn(closes, t_idx) -> list of tickers or None."""

    def select_fn(closes, t_idx):
        if t_idx < LOOKBACK_12M:
            return None
        price_t = closes.iloc[t_idx]
        price_past = closes.iloc[t_idx - LOOKBACK_12M]
        eligible = price_t.notna() & price_past.notna()
        tickers = list(closes.columns[eligible])
        if len(tickers) < MIN_ELIGIBLE:
            return None

        # ---- momentum pillar (always available given the above) ----
        mom_raw = momentum_pillar(closes, t_idx, tickers)
        z_mom = zscore(mom_raw["r3"]) * 0.20 \
            + zscore(mom_raw["r6"]) * 0.40 \
            + zscore(mom_raw["r12"]) * 0.40

        if mode == "mom_only":
            if z_mom.empty:
                return None
            top = z_mom.sort_values(ascending=False).head(TOP_N)
            return list(top.index) if len(top) >= TOP_N else None

        # ---- fundamental pillars ----
        fund = fundamental_pillars(panel, closes, t_idx, tickers)
        if len(fund) < MIN_ELIGIBLE:
            return None
        fidx = list(fund)

        s = lambda k: pd.Series({t: fund[t][k] for t in fidx})  # noqa: E731
        z_ep = zscore(s("ep"))
        z_bp = zscore(s("bp"))
        z_roe = zscore(s("roe"))
        z_de = zscore(s("de")) * -1.0          # lower D/E is better
        z_rev = zscore(s("rev_g"))
        z_ebd = zscore(s("ebitda_g"))

        # pillar composites (mean of whatever is present within the pillar)
        def pillar(*zs):
            frame = pd.concat(zs, axis=1)
            return frame.mean(axis=1, skipna=True).where(frame.notna().any(axis=1))

        z_value = pillar(z_ep, z_bp)
        z_growth = pillar(z_rev, z_ebd)
        z_quality = pillar(z_roe, z_de)

        # require >=3 of the 4 pillars to be present for a stock to score
        comp = pd.concat(
            [z_mom.rename("mom"), z_value.rename("value"),
             z_growth.rename("growth"), z_quality.rename("quality")],
            axis=1)
        n_present = comp.notna().sum(axis=1)
        score = comp.mean(axis=1, skipna=True).where(n_present >= 3)

        if mode == "pro_4_gate":
            # PEER-RELATIVE fair value — see docstring #4 for why an absolute
            # anchor was tested and rejected. Fair value for each stock is the
            # universe's median P/E (resp. median P/B) applied to that stock's
            # own EPS (resp. book value): upside > 0 <=> cheaper than the
            # median peer on that measure. A stock with neither positive EPS
            # nor positive book has no computable anchor and fails the gate.
            ep_s, bp_s = s("ep"), s("bp")
            ups = []
            pe_pos = ep_s[ep_s > 0]
            if len(pe_pos) >= MIN_ELIGIBLE:
                med_pe = (1.0 / pe_pos).median()
                ups.append((ep_s * med_pe - 1.0).rename("up_pe"))
            pb_pos = bp_s[bp_s > 0]
            if len(pb_pos) >= MIN_ELIGIBLE:
                med_pb = (1.0 / pb_pos).median()
                ups.append((bp_s * med_pb - 1.0).rename("up_pb"))
            if not ups:
                return None
            up_frame = pd.concat(ups, axis=1)
            upside = up_frame.mean(axis=1, skipna=True).where(
                up_frame.notna().any(axis=1))
            gate = upside.fillna(-np.inf) > 0
            score = score.where(gate.reindex(score.index, fill_value=False))

        score = score.dropna()
        if len(score) < MIN_ELIGIBLE:
            return None
        top = score.sort_values(ascending=False).head(TOP_N)
        return list(top.index) if len(top) >= TOP_N else None

    return select_fn


# ---------------------------------------------------------------------
# engine
# ---------------------------------------------------------------------
def build_portfolio(closes, rbdates, select_fn, cost_loaded):
    """Full equal-weight re-slice at each rebalance (project convention)."""
    dates = closes.index
    rbset = set(rbdates)
    shares = {}
    series = pd.Series(np.nan, index=dates)
    selections = []
    started = False

    for i, d in enumerate(dates):
        price = closes.iloc[i]
        if d in rbset:
            selected = select_fn(closes, i)
            if selected:
                held = [t for t in shares if pd.notna(price.get(t))]
                value_before = sum(shares[t] * price[t] for t in held) \
                    if started else BASE_VALUE
                if not started:
                    started = True

                if cost_loaded:
                    # sell the whole book, then re-buy equally
                    value_after = value_before * (1 - SELL_COST_PCT) \
                        * (1 - BUY_COST_PCT)
                else:
                    value_after = value_before

                each = value_after / len(selected)
                shares = {t: each / price[t] for t in selected}
                n_changed = len(set(selected) ^ set(held)) if held else len(selected)
                selections.append({
                    "date": d.strftime("%Y-%m-%d"),
                    "num_selected": len(selected),
                    "changed_vs_prev": n_changed,
                    "tickers": selected,
                    "index_value_at_rebalance": float(value_after),
                })
        if started:
            val = sum(shares[t] * price[t] for t in shares
                      if pd.notna(price.get(t)))
            series.iloc[i] = val

    return series.dropna(), selections


def monthly_rebalance_dates(dates):
    """FIRST trading day of each month (ProPicks states end-of-first-session
    rebalance)."""
    df = pd.Series(dates, index=dates)
    out = []
    for (_y, _m), grp in df.groupby([dates.year, dates.month]):
        out.append(grp.iloc[0])
    return sorted(out)


def common_metrics(series, start, end):
    """metrics() plus a normalised equity curve, on [start, end]."""
    s = series[(series.index >= start) & (series.index <= end)]
    if len(s) < 2:
        return None
    m = metrics(s)
    m["equity_curve"] = series_to_points(s / s.iloc[0] * 100.0)
    m["start_date"] = s.index[0].strftime("%Y-%m-%d")
    m["end_date"] = s.index[-1].strftime("%Y-%m-%d")
    return m


def run_universe(closes, panel, label, bench_idx_series, bench_name):
    rbdates = monthly_rebalance_dates(closes.index)

    variants = {}
    for mode in ("mom_only", "pro_4", "pro_4_gate"):
        sel_fn = make_select_fn(mode, panel)
        frictionless, sels = build_portfolio(closes, rbdates, sel_fn, False)
        loaded, sels_l = build_portfolio(closes, rbdates, sel_fn, True)
        variants[mode] = {
            "frictionless": frictionless,
            "loaded": loaded,
            "selections": sels_l,
        }

    # one window shared by every variant AND the benchmarks, so the headline
    # table is apples-to-apples
    starts = [v["loaded"].index[0] for v in variants.values() if len(v["loaded"])]
    ends = [v["loaded"].index[-1] for v in variants.values() if len(v["loaded"])]
    if not starts:
        return None
    start, end = max(starts), min(ends)
    if start >= end:
        return None

    out = {"label": label, "benchmark_name": bench_name,
           "common_start": start.strftime("%Y-%m-%d"),
           "common_end": end.strftime("%Y-%m-%d"),
           "num_rebalances": len(variants["pro_4"]["selections"]),
           "variants": {}, "benchmark": {}}

    # implied turnover: average number of names rotated in/out per rebalance.
    # symmetric difference counts both the leavers and the arrivals.
    chg = [s["changed_vs_prev"] / 2.0
           for s in variants["pro_4"]["selections"][1:]]
    out["avg_names_rotated_per_month"] = float(np.mean(chg)) if chg else None

    # ROBUSTNESS: 40 rebalances over 3.3 years is a thin sample, and this
    # window (mid-2023 onward) was kind to Indian small/mid-caps overall.
    # Split the window in half and report each half separately, so a reader
    # can see whether the ranking holds in both halves or was carried by one.
    mid = start + (end - start) / 2
    sub_windows = {}
    for tag, a, b in (("first_half", start, mid), ("second_half", mid, end)):
        sub_windows[tag] = {
            "start": a.strftime("%Y-%m-%d"), "end": b.strftime("%Y-%m-%d"),
            "variants": {}, "benchmark": {},
        }
        for mode, v in variants.items():
            m = common_metrics(v["loaded"], a, b)
            if m:
                sub_windows[tag]["variants"][mode] = m
        if bench_idx_series is not None:
            bs = bench_idx_series
            bs = bs[(bs.index >= a) & (bs.index <= b)]
            if len(bs) > 1:
                sub_windows[tag]["benchmark"] = common_metrics(bs, a, b) or {}
    out["sub_windows"] = sub_windows

    VARIANT_LABELS = {
        "mom_only": "Momentum only (control)",
        "pro_4": "Momentum + Value + Growth + Quality",
        "pro_4_gate": "Four-pillar + relative-cheapness gate",
    }
    for mode, v in variants.items():
        entry = {"label": VARIANT_LABELS[mode]}
        for tag, key in (("cost_loaded", "loaded"), ("frictionless", "frictionless")):
            m = common_metrics(v[key], start, end)
            if m:
                entry[tag] = m
        sels = v["selections"]
        entry["num_rebalances"] = len(sels)
        entry["first_rebalance"] = sels[0]["date"] if sels else None
        entry["last_rebalance"] = sels[-1]["date"] if sels else None
        entry["selections_sample"] = sels[:2] + sels[-2:] if len(sels) > 4 else sels
        out["variants"][mode] = entry

    # benchmark over the same window
    if bench_idx_series is not None:
        b = bench_idx_series
        b = b[(b.index >= start) & (b.index <= end)]
        if len(b) > 1:
            out["benchmark"] = common_metrics(b, start, end) or {}

    return out


def main():
    panel = load_fundamentals()
    print(f"fundamentals: {len(panel)} tickers with usable periods")

    smallcap = load_smallcap250_closes()
    midcap = load_midcap150_closes()
    nifty = fetch("^NSEI")
    sc_idx = fetch("NIFTYSMLCAP250.NS")
    mc_idx = fetch("NIFTYMIDCAP150.NS")

    # align each universe onto the NIFTY trading calendar (project convention)
    smallcap = smallcap.loc[smallcap.index.intersection(nifty.index)]
    midcap = midcap.loc[midcap.index.intersection(nifty.index)]

    print(f"smallcap universe: {len(smallcap.columns)} tickers, "
          f"{smallcap.index[0].date()} -> {smallcap.index[-1].date()}")
    print(f"midcap universe:   {len(midcap.columns)} tickers, "
          f"{midcap.index[0].date()} -> {midcap.index[-1].date()}")

    sc = run_universe(smallcap, panel, "NIFTY Smallcap 250",
                      sc_idx["Close"], "NIFTY Smallcap 250 index")
    mc = run_universe(midcap, panel, "NIFTY Midcap 150",
                      mc_idx["Close"], "NIFTY Midcap 150 index")

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "report": 101,
        "title": "Clean-room ProPicks India (momentum + value + growth + quality)",
        "top_n": TOP_N,
        "rebalance": "first trading day of month, close, equal weight",
        "reporting_lag_days": REPORTING_LAG_DAYS,
        "fair_value_proxy": "peer-relative: universe median P/E and median P/B "
                            "applied to each stock's own EPS and book value "
                            "(an absolute Graham anchor was tested and rejected "
                            "as unsuitable - see report limitations)",
        "variant_labels": {
            "mom_only": "Momentum only (control)",
            "pro_4": "Momentum + Value + Growth + Quality",
            "pro_4_gate": "Four-pillar + relative-cheapness gate",
        },
        "smallcap": sc,
        "midcap": mc,
        "nifty50": {},
    }

    # NIFTY 50 on the widest common window for context
    if sc and mc:
        s0, e0 = max(sc["common_start"], mc["common_start"]), \
            min(sc["common_end"], mc["common_end"])
        results["nifty50"] = common_metrics(nifty["Close"], s0, e0) or {}
        results["nifty50_window"] = [s0, e0]

    with open("results100.json", "w") as f:
        json.dump(results, f)

    for uni in (sc, mc):
        if not uni:
            continue
        print(f"\n=== {uni['label']} ===  window {uni['common_start']} -> "
              f"{uni['common_end']}  rebalances={uni['num_rebalances']}  "
              f"~{uni['avg_names_rotated_per_month']:.1f} names rotated/month")
        bench = uni.get("benchmark") or {}
        if bench:
            print(f"  [benchmark {uni['benchmark_name']}] "
                  f"net={bench.get('net_return_pct', float('nan')):.1f}% "
                  f"cagr={bench.get('cagr_pct', float('nan')):.2f}% "
                  f"mdd={bench.get('max_drawdown_pct', float('nan')):.1f}%")
        for mode, v in uni["variants"].items():
            a, b = v.get("cost_loaded"), v.get("frictionless")
            if not a or not b:
                continue
            print(f"  [{mode:<10}] loaded net={a['net_return_pct']:8.1f}% "
                  f"cagr={a['cagr_pct']:6.2f}% mdd={a['max_drawdown_pct']:6.1f}% | "
                  f"frictionless net={b['net_return_pct']:8.1f}% "
                  f"cagr={b['cagr_pct']:6.2f}%")

        print("  -- robustness, cost-loaded, by half-window --")
        for tag, sw in uni.get("sub_windows", {}).items():
            bench = sw.get("benchmark") or {}
            line = (f"  [{tag:<12}] {sw['start']}->{sw['end']}  "
                    f"bench cagr={bench.get('cagr_pct', float('nan')):6.2f}%")
            for mode in ("mom_only", "pro_4", "pro_4_gate"):
                m = sw["variants"].get(mode)
                if m:
                    line += f" | {mode}={m['cagr_pct']:6.2f}%"
            print(line)


if __name__ == "__main__":
    main()

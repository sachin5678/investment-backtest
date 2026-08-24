"""
Approximate reconstruction of the NIFTY200 Momentum 30 Index methodology,
run over as much history as the underlying stocks allow — NOT the real,
official index (which Yahoo Finance does not carry historically; the real
ticker NIFTY200MOMENTM30.NS has exactly 1 day of data on Yahoo).

Real methodology (confirmed via NSE's own published documentation, see chat):
  - Universe: NIFTY 200 stocks, >=1 year listing history, F&O-eligible.
  - For each stock: 6-month momentum ratio = 6-month price return / (std
    dev of daily returns over the trailing 1 year); 12-month momentum ratio
    computed the same way over 12 months.
  - Z-score each ratio cross-sectionally against all eligible stocks.
    Weighted Average Z-score (WAZ) = 0.5*Z(6m) + 0.5*Z(12m).
  - Normalised score = 1+WAZ if WAZ>=0, else 1/(1-WAZ).
  - Top 30 stocks by normalised score are selected; real index weights them
    by free-float market cap x normalised score, capped at 5%/stock.
  - Rebalanced semi-annually (June, December).

DISCLOSED APPROXIMATIONS in this reconstruction (agreed with you in chat):
  1. UNIVERSE: today's NIFTY 200 constituent list (fetched fresh from NSE's
     own archive CSV) is used as a FIXED universe applied retroactively for
     every rebalance back to whenever the data allows. The real historical
     index used whichever ~200 stocks were actually in the NIFTY 200 at each
     past date — index membership has changed constantly. This is
     survivorship bias: today's list excludes companies that fell out of
     the top 200 (or delisted, merged, went bankrupt) along the way, which
     tends to make this reconstruction look BETTER than the stocks that
     existed historically actually performed as a whole.
  2. WEIGHTING: the real index weights by free-float market cap x
     normalised momentum score (capped 5%). Historical free-float market
     cap isn't available from this project's data sources, so this
     reconstruction EQUAL-WEIGHTS the 30 selected stocks each rebalance
     instead — a disclosed substitute, not the real weighting rule.
  3. ELIGIBILITY: the F&O-eligibility screen is not modelled (no historical
     F&O-list data available); only the ">=1 year of price history in this
     dataset" condition is enforced.
  4. Rebalance dates are approximated as the last trading day of June and
     December each year (the real index rebalances a few weeks after these
     dates, following a review).
"""
import json
import numpy as np
import pandas as pd
import yfinance as yf

from backtest4 import fetch, xirr, cumret_drawdown, series_to_points, CURRENCY_SYMBOL
from nifty200_symbols import NIFTY_200_SYMBOLS

LOOKBACK_12M = 252
LOOKBACK_6M = 126
TOP_N = 30
MIN_ELIGIBLE = 40   # require a reasonably sized eligible pool before trusting a rebalance


def load_universe_closes():
    raw = pd.read_pickle("universe_raw.pkl")
    tickers = sorted(set(c[0] for c in raw.columns))
    closes = pd.DataFrame({t: raw[(t, "Close")] for t in tickers})
    closes = closes.sort_index()
    closes = closes.ffill()   # fill occasional single-day trading halts; leaves pre-listing NaNs untouched
    return closes


def rebalance_dates(dates, months=(6, 12)):
    """Last trading day of every occurrence of the given months within the
    date range (default: June and December)."""
    df = pd.Series(dates, index=dates)
    out = []
    for (y, m), grp in df.groupby([dates.year, dates.month]):
        if m in months:
            out.append(grp.iloc[-1])
    return sorted(out)


def select_top30(closes, t_idx, top_n=TOP_N, min_eligible=MIN_ELIGIBLE):
    """closes: DataFrame (dates x tickers). t_idx: integer row position of the
    rebalance date. Returns list of selected tickers (<=top_n) or None if
    fewer than min_eligible stocks are eligible."""
    if t_idx < LOOKBACK_12M:
        return None
    price_t = closes.iloc[t_idx]
    price_t12 = closes.iloc[t_idx - LOOKBACK_12M]
    price_t6 = closes.iloc[t_idx - LOOKBACK_6M]
    eligible = price_t.notna() & price_t12.notna() & price_t6.notna()
    tickers = closes.columns[eligible]
    if len(tickers) < min_eligible:
        return None

    window = closes.iloc[t_idx - LOOKBACK_12M: t_idx + 1][tickers]
    daily_ret = window.pct_change().dropna(how="all")
    vol_1y = daily_ret.std()

    ret_6m = price_t[tickers] / price_t6[tickers] - 1.0
    ret_12m = price_t[tickers] / price_t12[tickers] - 1.0
    ratio_6m = ret_6m / vol_1y
    ratio_12m = ret_12m / vol_1y

    valid = ratio_6m.notna() & ratio_12m.notna() & np.isfinite(ratio_6m) & np.isfinite(ratio_12m)
    ratio_6m, ratio_12m = ratio_6m[valid], ratio_12m[valid]
    if len(ratio_6m) < min_eligible:
        return None

    z6 = (ratio_6m - ratio_6m.mean()) / ratio_6m.std()
    z12 = (ratio_12m - ratio_12m.mean()) / ratio_12m.std()
    waz = 0.5 * z6 + 0.5 * z12
    norm_score = waz.apply(lambda w: 1 + w if w >= 0 else 1 / (1 - w))

    top = norm_score.sort_values(ascending=False).head(top_n)
    return list(top.index)


def build_index(closes, top_n=TOP_N, min_eligible=MIN_ELIGIBLE, rebalance_months=(6, 12)):
    dates = closes.index
    rbdates = rebalance_dates(dates, months=rebalance_months)
    date_pos = {d: i for i, d in enumerate(dates)}

    index_level = pd.Series(np.nan, index=dates)
    shares = {}
    selections = []
    started = False
    base_value = 100.0

    for i, d in enumerate(dates):
        if d in rbdates:
            t_idx = date_pos[d]
            selected = select_top30(closes, t_idx, top_n=top_n, min_eligible=min_eligible)
            if selected is not None:
                price_today = closes.iloc[t_idx]
                if not started:
                    value_before = base_value
                    started = True
                else:
                    value_before = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares)
                    if value_before <= 0:
                        value_before = index_level.iloc[i - 1] if i > 0 else base_value
                dollar_each = value_before / len(selected)
                shares = {tk: dollar_each / price_today[tk] for tk in selected}
                selections.append({"date": d.strftime("%Y-%m-%d"), "num_selected": len(selected),
                                     "tickers": selected, "index_value_at_rebalance": float(value_before)})
        if started:
            price_today = closes.iloc[i]
            val = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares if pd.notna(price_today.get(tk)))
            index_level.iloc[i] = val

    index_level = index_level.dropna()
    return index_level, selections


def build():
    closes = load_universe_closes()
    nifty = fetch("^NSEI")
    midcap = fetch("MID150BEES.NS")

    # align the universe onto NIFTY's own trading calendar
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]

    index_level, selections = build_index(closes)
    start_date = index_level.index[0]
    end_date = index_level.index[-1]

    # PRIMARY comparison: momentum reconstruction vs. NIFTY 50, over the FULL long
    # window since 2008 — this is the whole point of the reconstruction, so it must
    # NOT be truncated down to midcap's much shorter (2019+) history.
    long_common = nifty.index[(nifty.index >= start_date) & (nifty.index <= end_date)]
    long_common = long_common.intersection(index_level.index)
    momentum_series = index_level.loc[long_common]
    nifty_series = nifty.loc[long_common, "Close"]

    # SECONDARY comparison: midcap only has data from 2019-02-04 onward, so it is
    # compared over its OWN available sub-window, not the full 2008+ span.
    midcap_common = long_common[long_common.isin(midcap.index)]
    midcap_series = midcap.loc[midcap_common, "Close"]

    def norm(s):
        return s / s.iloc[0] * 100.0

    mdd_m, peak_m, trough_m, uw_m = cumret_drawdown(momentum_series, pd.Series(1.0, index=momentum_series.index))
    mdd_n, peak_n, trough_n, uw_n = cumret_drawdown(nifty_series, pd.Series(1.0, index=nifty_series.index))
    mdd_mc, peak_mc, trough_mc, uw_mc = cumret_drawdown(midcap_series, pd.Series(1.0, index=midcap_series.index))

    def cagr_of(s):
        years = (s.index[-1] - s.index[0]).days / 365.25
        return float((s.iloc[-1] / s.iloc[0]) ** (1 / years) * 100 - 100)

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "universe_size": len(closes.columns),
        "start_date": start_date.strftime("%Y-%m-%d"), "end_date": end_date.strftime("%Y-%m-%d"),
        "midcap_start_date": midcap_series.index[0].strftime("%Y-%m-%d"),
        "num_rebalances": len(selections),
        "selections_sample": selections[:3] + selections[-3:] if len(selections) > 6 else selections,
        "num_selections_total": len(selections),
        "reconstructed_momentum": {
            "equity_curve": series_to_points(norm(momentum_series)),
            "net_return_pct": float((momentum_series.iloc[-1] / momentum_series.iloc[0] - 1) * 100),
            "cagr_pct": cagr_of(momentum_series),
            "max_drawdown_pct": mdd_m, "max_drawdown_peak_date": peak_m, "max_drawdown_trough_date": trough_m,
            "longest_underwater_days": uw_m,
        },
        "nifty": {
            "equity_curve": series_to_points(norm(nifty_series)),
            "net_return_pct": float((nifty_series.iloc[-1] / nifty_series.iloc[0] - 1) * 100),
            "cagr_pct": cagr_of(nifty_series),
            "max_drawdown_pct": mdd_n, "max_drawdown_peak_date": peak_n, "max_drawdown_trough_date": trough_n,
            "longest_underwater_days": uw_n,
        },
        "midcap": {
            "equity_curve": series_to_points(norm(midcap_series)),
            "net_return_pct": float((midcap_series.iloc[-1] / midcap_series.iloc[0] - 1) * 100),
            "cagr_pct": cagr_of(midcap_series),
            "max_drawdown_pct": mdd_mc, "max_drawdown_peak_date": peak_mc, "max_drawdown_trough_date": trough_mc,
            "longest_underwater_days": uw_mc,
        },
    }
    return results, momentum_series, nifty_series, midcap_series


if __name__ == "__main__":
    r, mom, nif, mid = build()
    with open("results10.json", "w") as f:
        json.dump(r, f)
    print("start", r["start_date"], "end", r["end_date"], "rebalances", r["num_rebalances"])
    for k in ("reconstructed_momentum", "nifty", "midcap"):
        v = r[k]
        print(f"[{k}] net_return={v['net_return_pct']:.1f}% cagr={v['cagr_pct']:.2f}% "
              f"mdd={v['max_drawdown_pct']:.1f}% uw_days={v['longest_underwater_days']}")
    print("\nfirst rebalance:", r["selections_sample"][0]["date"], r["selections_sample"][0]["num_selected"], "selected")
    print("sample tickers:", r["selections_sample"][0]["tickers"][:10])
    print("\nlast rebalance:", r["selections_sample"][-1]["date"], r["selections_sample"][-1]["num_selected"], "selected")

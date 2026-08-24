"""
Sector-momentum rotation — a genuinely different selection process from every
earlier reconstruction (reports 11, 12, 14-18), which all pick a FIXED index
(NIFTY200 / Midcap150 / Smallcap250 / NIFTY500) and then rank stocks WITHIN
it. This flips the order: at every rebalance, first rank NIFTY 500's sectors
by their own average momentum, then take the top 3 momentum stocks from
WHICHEVER sector currently leads. The sector call comes first; the stock
picks are a consequence of it, not the other way round.

Two variants, both compared against the existing top-down NIFTY500 Momentum
10 reconstruction (report 18 / results17.json's "nifty500_10") as the direct
answer to "is bottom-up sector-then-stock momentum different from picking
momentum stocks straight out of one index?":

  - Top1x3  — single leading sector, its top 3 momentum stocks, equal-weighted
              (33.3% each). This is a 3-STOCK PORTFOLIO — the literal ask.
  - Top2x3  — the two leading sectors, top 3 momentum stocks from EACH
              (6 stocks, 16.7% each) — added as a less extreme comparison,
              since a 3-stock book is unusually concentrated.

METHODOLOGY (built from pieces already validated in this project):
  - Universe: NIFTY 500 (same 500-stock universe and price cache as reports
    16-18; see backtest17.load_nifty500_closes()).
  - Sector tags: Yahoo Finance's own present-day classification for each of
    the 500 stocks (Ticker.info['sector'] — 11 sectors, fetched once via
    fetch_sectors.py -> sectors_raw.json). NSE does not publish its own
    official sector taxonomy in a form this project can fetch; Yahoo's GICS-
    like tags are the only sector classification available here.
  - Per-stock momentum score: the IDENTICAL real formula used in every other
    reconstruction in this project (6m and 12m price return, each divided by
    trailing-1-year daily-return volatility, Z-scored cross-sectionally
    across the WHOLE eligible 500-stock universe — not just within a
    sector — then combined as 0.5*Z(6m)+0.5*Z(12m)). This is what NSE's
    momentum indices actually use; nothing new here.
  - Sector momentum score: the SIMPLE (equal-weighted) average of that same
    per-stock Z-score across a sector's eligible members. This is a
    judgment call — there is no official "sector momentum" formula from
    NSE to reuse, since sector rotation isn't a real NSE index methodology.
    Cap-weighting the sector average was considered and rejected: the only
    market-cap figures available in this project are a SINGLE present-day
    snapshot (fetched for the quality-score reports), so cap-weighting
    every historical rebalance with today's market caps would silently
    layer one more look-ahead assumption on top of the sector-tag one that
    already exists. Equal-weighting avoids that extra assumption.
  - Stock picks within the winning sector(s): ranked by the same per-stock
    normalised score used throughout this project, top 3 taken, equal-weighted.
  - Rebalance cadence: June/December — the REAL NIFTY500 Momentum index's
    actual cadence (confirmed via NSE's published methodology, same as
    report 18's NIFTY500 Momentum 10/15), chosen specifically so this can be
    overlaid on that report's series on identical dates.
  - A sector needs >=5 eligible members before it's allowed to be ranked at
    all (an empty or 1-stock "sector" leading the table would be noise, not
    a signal) — comfortably below every real sector's actual size (11-97
    members, printed by fetch_sectors.py).

SAME DISCLOSED APPROXIMATIONS AS EVERY OTHER RECONSTRUCTION IN THIS PROJECT:
  today's fixed NIFTY 500 constituent list applied retroactively
  (survivorship bias); no F&O-eligibility screen; no transaction costs or
  slippage modeled — WORTH FLAGGING MORE HERE than in the fixed-index
  reports, since a 3-stock (or 6-stock) book can turn over completely in one
  rebalance if sector leadership rotates, which is a much higher-turnover
  bet than a 10-30 stock index reshuffling partially.
"""
import json

import numpy as np
import pandas as pd

from backtest10 import fetch, cumret_drawdown, series_to_points, CURRENCY_SYMBOL, rebalance_dates, build_index
from backtest13 import metrics
from backtest17 import load_nifty500_closes

LOOKBACK_12M = 252
LOOKBACK_6M = 126
MIN_ELIGIBLE_TOTAL = 80    # same eligibility floor used for this same 500-stock universe in report 18
MIN_SECTOR_SIZE = 5        # a sector needs at least this many eligible members to be "rankable" at all
TOP_STOCKS_PER_SECTOR = 3
REBALANCE_MONTHS = (6, 12)  # the real NIFTY500 Momentum index's actual cadence

with open("sectors_raw.json") as f:
    _SECTOR_RAW = json.load(f)
TICKER_SECTOR = {t: v.get("sector") for t, v in _SECTOR_RAW.items() if v.get("sector")}


def momentum_scores(closes, t_idx):
    """Per-stock (waz, norm_score) for every eligible stock at row t_idx —
    identical real 6m/12m risk-adjusted, cross-sectionally Z-scored formula
    used throughout this project (see backtest10.select_top30)."""
    if t_idx < LOOKBACK_12M:
        return None, None
    price_t = closes.iloc[t_idx]
    price_t12 = closes.iloc[t_idx - LOOKBACK_12M]
    price_t6 = closes.iloc[t_idx - LOOKBACK_6M]
    eligible = price_t.notna() & price_t12.notna() & price_t6.notna()
    tickers = closes.columns[eligible]
    if len(tickers) < MIN_ELIGIBLE_TOTAL:
        return None, None

    window = closes.iloc[t_idx - LOOKBACK_12M: t_idx + 1][tickers]
    daily_ret = window.pct_change().dropna(how="all")
    vol_1y = daily_ret.std()

    ret_6m = price_t[tickers] / price_t6[tickers] - 1.0
    ret_12m = price_t[tickers] / price_t12[tickers] - 1.0
    ratio_6m = ret_6m / vol_1y
    ratio_12m = ret_12m / vol_1y

    valid = ratio_6m.notna() & ratio_12m.notna() & np.isfinite(ratio_6m) & np.isfinite(ratio_12m)
    ratio_6m, ratio_12m = ratio_6m[valid], ratio_12m[valid]
    if len(ratio_6m) < MIN_ELIGIBLE_TOTAL:
        return None, None

    z6 = (ratio_6m - ratio_6m.mean()) / ratio_6m.std()
    z12 = (ratio_12m - ratio_12m.mean()) / ratio_12m.std()
    waz = 0.5 * z6 + 0.5 * z12
    norm_score = waz.apply(lambda w: 1 + w if w >= 0 else 1 / (1 - w))
    return waz, norm_score


def rank_sectors(waz):
    """Simple average WAZ per sector (sectors with < MIN_SECTOR_SIZE
    eligible members excluded), sorted descending — the strongest-momentum
    sector first."""
    sector_of = pd.Series({t: TICKER_SECTOR.get(t) for t in waz.index})
    df = pd.DataFrame({"waz": waz, "sector": sector_of}).dropna(subset=["sector"])
    grp = df.groupby("sector")["waz"]
    avg = grp.mean()[grp.size() >= MIN_SECTOR_SIZE]
    return avg.sort_values(ascending=False)


def pick_top_stocks(norm_score, sectors, n_per_sector):
    picks = []
    for sec in sectors:
        members = [t for t in norm_score.index if TICKER_SECTOR.get(t) == sec]
        top = norm_score[members].sort_values(ascending=False).head(n_per_sector)
        picks.extend(list(top.index))
    return picks


def build_rotation(closes, top_sectors, n_per_sector=TOP_STOCKS_PER_SECTOR, rebalance_months=REBALANCE_MONTHS):
    dates = closes.index
    rbdates = rebalance_dates(dates, months=rebalance_months)
    date_pos = {d: i for i, d in enumerate(dates)}

    index_level = pd.Series(np.nan, index=dates)
    shares = {}
    selections = []
    started = False
    base_value = 100.0
    prev_tickers = set()

    for i, d in enumerate(dates):
        if d in rbdates:
            t_idx = date_pos[d]
            waz, norm_score = momentum_scores(closes, t_idx)
            if waz is not None:
                sector_ranked = rank_sectors(waz)
                if len(sector_ranked) >= top_sectors:
                    chosen_sectors = list(sector_ranked.index[:top_sectors])
                    selected = pick_top_stocks(norm_score, chosen_sectors, n_per_sector)
                    if len(selected) >= 2:
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
                        overlap = len(prev_tickers & set(selected)) if prev_tickers else None
                        selections.append({
                            "date": d.strftime("%Y-%m-%d"),
                            "sector_scores": {k: round(float(v), 3) for k, v in sector_ranked.head(5).items()},
                            "sectors": chosen_sectors,
                            "tickers": selected,
                            "overlap_with_prev": overlap,
                            "index_value_at_rebalance": float(value_before),
                        })
                        prev_tickers = set(selected)
        if started:
            price_today = closes.iloc[i]
            val = sum(shares.get(tk, 0.0) * price_today.get(tk, 0.0) for tk in shares if pd.notna(price_today.get(tk)))
            index_level.iloc[i] = val

    index_level = index_level.dropna()
    return index_level, selections


def rotation_summary(selections, n_per_sector):
    """Sector win-count distribution + average consecutive-rebalance
    turnover — the "does leadership rotate a lot?" stats for the report."""
    from collections import Counter
    sector_wins = Counter()
    for s in selections:
        for sec in s["sectors"]:
            sector_wins[sec] += 1
    overlaps = [s["overlap_with_prev"] for s in selections if s["overlap_with_prev"] is not None]
    total_slots = n_per_sector * len(selections[0]["sectors"]) if selections else n_per_sector
    avg_overlap_frac = float(np.mean(overlaps)) / total_slots if overlaps else None
    full_turnover_count = sum(1 for o in overlaps if o == 0)
    return {
        "sector_win_counts": dict(sector_wins.most_common()),
        "num_unique_sectors_used": len(sector_wins),
        "avg_ticker_overlap_with_prev_rebalance_pct": round(avg_overlap_frac * 100, 1) if avg_overlap_frac is not None else None,
        "full_turnover_rebalances": full_turnover_count,
        "total_rebalances_after_first": len(overlaps),
    }


def main():
    closes = load_nifty500_closes()
    nifty = fetch("^NSEI")
    midcap_etf = fetch("MID150BEES.NS")
    closes = closes.loc[closes.index.intersection(nifty.index)]

    top1x3_level, top1x3_sel = build_rotation(closes, top_sectors=1, n_per_sector=TOP_STOCKS_PER_SECTOR)
    top2x3_level, top2x3_sel = build_rotation(closes, top_sectors=2, n_per_sector=TOP_STOCKS_PER_SECTOR)

    # top-down benchmark: momentum stocks picked straight from the whole
    # NIFTY 500, no sector step at all — same universe, same cadence as the
    # two rotation variants above, so this is a fair, apples-to-apples line.
    n500_top10_level, n500_top10_sel = build_index(closes, top_n=10, min_eligible=MIN_ELIGIBLE_TOTAL,
                                                     rebalance_months=REBALANCE_MONTHS)

    common = top1x3_level.index.intersection(top2x3_level.index).intersection(n500_top10_level.index)
    start_date, end_date = common[0], common[-1]

    def norm_over(series):
        s = series.loc[common]
        return s / s.iloc[0] * 100.0

    top1x3 = norm_over(top1x3_level)
    top2x3 = norm_over(top2x3_level)
    n500_top10 = norm_over(n500_top10_level)
    nifty_series = nifty.loc[nifty.index.intersection(common), "Close"]
    nifty_series = nifty_series / nifty_series.iloc[0] * 100.0
    midcap_common = common[common.isin(midcap_etf.index)]
    midcap_series = midcap_etf.loc[midcap_common, "Close"]
    midcap_series = midcap_series / midcap_series.iloc[0] * 100.0

    results = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "universe_size": len(closes.columns),
        "num_sectors_used": len(set(TICKER_SECTOR.values())),
        "start_date": start_date.strftime("%Y-%m-%d"), "end_date": end_date.strftime("%Y-%m-%d"),
        "midcap_etf_start": midcap_series.index[0].strftime("%Y-%m-%d") if len(midcap_series) else None,
        "top1x3": {
            "equity_curve": series_to_points(top1x3), **metrics(top1x3_level.loc[common]),
            "num_rebalances": len(top1x3_sel),
            "selections_sample": (top1x3_sel[:3] + top1x3_sel[-3:]) if len(top1x3_sel) > 6 else top1x3_sel,
            **rotation_summary(top1x3_sel, TOP_STOCKS_PER_SECTOR),
        },
        "top2x3": {
            "equity_curve": series_to_points(top2x3), **metrics(top2x3_level.loc[common]),
            "num_rebalances": len(top2x3_sel),
            "selections_sample": (top2x3_sel[:3] + top2x3_sel[-3:]) if len(top2x3_sel) > 6 else top2x3_sel,
            **rotation_summary(top2x3_sel, TOP_STOCKS_PER_SECTOR),
        },
        "nifty500_momentum10": {
            "equity_curve": series_to_points(n500_top10), **metrics(n500_top10_level.loc[common]),
            "num_rebalances": len(n500_top10_sel),
        },
        "nifty": {"equity_curve": series_to_points(nifty_series), **metrics(nifty_series)},
        "midcap_etf": {"equity_curve": series_to_points(midcap_series), **metrics(midcap_series)},
    }
    with open("results18.json", "w") as f:
        json.dump(results, f)

    print("start", start_date.date(), "end", end_date.date())
    for k in ("top1x3", "top2x3", "nifty500_momentum10", "nifty", "midcap_etf"):
        v = results[k]
        print(f"[{k}] net_return={v['net_return_pct']:.1f}% cagr={v['cagr_pct']:.2f}% "
              f"mdd={v['max_drawdown_pct']:.1f}% uw_days={v['longest_underwater_days']}")
    print("\ntop1x3 sector win counts:", results["top1x3"]["sector_win_counts"])
    print("top1x3 avg overlap with prev rebalance:", results["top1x3"]["avg_ticker_overlap_with_prev_rebalance_pct"], "%")
    print("top1x3 full-turnover rebalances:", results["top1x3"]["full_turnover_rebalances"],
          "/", results["top1x3"]["total_rebalances_after_first"])
    print("\ntop2x3 sector win counts:", results["top2x3"]["sector_win_counts"])
    print("\nfirst top1x3 rebalance:", top1x3_sel[0])
    print("\nlast top1x3 rebalance:", top1x3_sel[-1])


if __name__ == "__main__":
    main()

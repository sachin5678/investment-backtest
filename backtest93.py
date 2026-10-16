"""
Midcap150 Momentum 10 + NIFTY 200-EMA regime → gold hedge — report 48's
strategy design, re-engineered as a MomentumScore-style REVIEW RUN: the
same portfolio rule the momentumscore.in "hawda" strategy tests, with the
whole MomentumScore review layer built into its output. One engine, one
window, all of these:

  * FIT% — every eligible stock's 0-100 percentile standing against the
    whole eligible universe at every review (not just "was it picked"),
    and the previous review's rank/fit alongside it (Δ vs last review —
    the "Rank in → out / Fit in → out" columns of MomentumScore's trade
    log, and its ranks table).

  * EXIT RANK 52 — holdings are NOT force-sold at every rebalance into a
    brand-new top-10. A held stock is sold ONLY when its fit rank falls
    below 52 of the ~150 eligible names; the freed slot is refilled with
    the best-ranked non-held stock. Carried stocks keep their original
    shares (never trimmed to equal weight — the same carried-position
    convention as report 31's trade log), so this is genuinely "hold it
    while it still ranks", not "re-shuffle twice a year".

  * BEFORE/AFTER COSTS — the identical run twice: frictionless, and with
    0.1% per side on every leg (MomentumScore's own cost+slippage
    convention, "Before costs / After costs" toggle). Both series ship
    in this file; the trade log is the after-costs one, in real rupees
    from a ₹1,00,000 starting position.

  * TRADE LOG with entry/exit rank & fit, rupees in and out, why-strings
    for both entry and exit, and carried ×n markers.

  * REBALANCES LOG — every review (scheduled, regime exit, regime
    re-entry) with per-action reasons: which stocks carried, which fell
    below the exit rank, which were entered, and at what ranks.

  * RANKS — the latest-close ranking preview: what a review TODAY would
    do (sells for anything below rank 52, buys to refill to 10), with
    each row's Δ vs the last review.

  * ROBUSTNESS — both-halves vs NIFTY (a sound rule should beat the
    benchmark in both halves, not one lucky stretch), plus a DATE-LUCK
    variant: the identical engine rebalanced mid-month (day 15) instead
    of month-end.

  * HEALTH CHECK — the 10 MomentumScore target ranges (share met =
    score/100), computed on full-resolution daily data and the trade log
    (see ms_port/health.py for the two documented tail-risk proxies).

  * TAX — capital-gains estimate over the trade log via ms_port.tax:
    15%/10% → 20%/12.5% régime switch on 23 Jul 2024, ₹1.25L LTCG
    exemption, 4% cess, short/long loss set-off with 8-year carry, and
    s.112A grandfathering using the 31-Jan-2025 FMV read straight off
    this same price data. Plus an after-tax growth curve (each FY's tax
    deducted at that FY's last close).

NOT the same thing as survivorship-free: same universe caveat as every
other Midcap150 report here (today's index membership applied backwards).
Prices are Yahoo Finance closes, forward-filled over single-day halts.
"""
import json
from datetime import datetime

import numpy as np
import pandas as pd

from backtest10 import rebalance_dates, series_to_points, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes, fetch_gold_cleaned
from backtest32 import metrics_only
from ms_port import fit as ms_fit
from ms_port import health as ms_health
from ms_port import robustness as ms_rob
from ms_port import tax as ms_tax

TOP_N = 10
EXIT_RANK = 52          # MomentumScore's default: sell only when rank falls out of top 52
MIN_ELIGIBLE = 30
LOOKBACK_12M = 252
LOOKBACK_6M = 126
EMA_SPAN = 200
COST_PCT_PER_SIDE = 0.001   # 0.1% per side — MomentumScore's own cost+slippage convention
START_CAPITAL = 100_000.0   # ₹1,00,000, the same base MomentumScore's ₹1L → ₹4.43L used
FMV_DATE = "2025-01-31"     # s.112A grandfathering reference date


def select_ranked(closes, t_idx, min_eligible=MIN_ELIGIBLE):
    """The exact 6m/12m risk-adjusted momentum formula every Midcap150
    report here uses (backtest33.select_top_original) — but returning the
    FULL ranked order with scores, so fit percentiles and rank-out
    decisions can be made, not just the top-10 cut."""
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
    ordered = norm_score.sort_values(ascending=False)
    return [(tk, float(sc)) for tk, sc in ordered.items()]


def rank_map_at(closes, t_idx):
    """-> (ordered [(ticker, score)...], {ticker: {rank, fit, score}}) or (None, None)."""
    sel = select_ranked(closes, t_idx)
    if sel is None:
        return None, None
    scores = {tk: sc for tk, sc in sel}
    fits = ms_fit.fit_percentiles(scores)
    rmap = {tk: {"rank": i + 1, "fit": fits[tk], "score": sc} for i, (tk, sc) in enumerate(sel)}
    return sel, rmap


def midmonth_rebalance_dates(dates, months=(6, 12), day=15):
    """The date-luck variant calendar: the FIRST trading day on or after
    the 15th of each rebalance month (vs the repo's usual month-end)."""
    df = pd.Series(dates, index=dates)
    out = []
    for (y, m), grp in df.groupby([dates.year, dates.month]):
        if m in months:
            cands = [d for d in grp if d.day >= day]
            if cands:
                out.append(min(cands))
    return sorted(out)


def run_engine(closes, signal_close, signal_ma, hedge_close, rbdates, cost_pct,
               start_capital=START_CAPITAL):
    """The portfolio loop: report 48's exactly (200-EMA regime on NIFTY,
    100% switch between top-10 momentum stocks and GOLDBEES), plus the
    hysteresis, real-rupee accounting, and logs. Returns a dict."""
    dates = closes.index
    rb_set = set(rbdates)
    index_level = pd.Series(np.nan, index=dates)
    positions = {}      # ticker -> {qty, entry_date, entry_price, invested_gross, rank_in, fit_in, why_in, carried_dates}
    hedge_units = 0.0
    cash = 0.0
    started = False
    state = "hedge"
    events = []
    trades = []
    latest_ranking = None
    latest_ranking_date = None
    hedge_ticker = "GOLDBEES"

    def pv(price_row, hedge_px):
        v = cash
        for tk, p in positions.items():
            px = price_row.get(tk)
            if pd.notna(px):
                v += p["qty"] * px
        if hedge_units and pd.notna(hedge_px):
            v += hedge_units * hedge_px
        return v

    def do_buys(sel, rmap, money, date_s, why_tag, buys):
        """Split `money` equally across sel; books positions + buy rows."""
        per = money / len(sel)
        for tk, _sc in sel:
            px = price_row[tk]
            qty = per * (1 - cost_pct) / px
            positions[tk] = {
                "qty": qty, "entry_date": date_s, "entry_price": float(px),
                "invested_gross": per,
                "rank_in": rmap[tk]["rank"], "fit_in": rmap[tk]["fit"],
                "why_in": f"{why_tag} — rank {rmap[tk]['rank']} of ~{len(rmap)}, fit {rmap[tk]['fit']}%",
                "carried_dates": [],
            }
            buys.append({"ticker": tk.replace(".NS", ""), "rank_in": rmap[tk]["rank"],
                         "fit_in": rmap[tk]["fit"], "amount": round(per, 2)})

    for i, d in enumerate(dates):
        is_rb = d in rb_set
        ma_today = signal_ma.iloc[i]
        raw_invested = bool(signal_close.iloc[i] > ma_today) if pd.notna(ma_today) else False
        price_row = closes.iloc[i]
        hedge_px = hedge_close.iloc[i]
        date_s = d.strftime("%Y-%m-%d")

        if not started:
            if is_rb:
                sel, rmap = rank_map_at(closes, i)
                if sel is not None:
                    started = True
                    latest_ranking, latest_ranking_date = rmap, date_s
                    if raw_invested:
                        state = "invested"
                        buys = []
                        chosen = sel[:TOP_N]
                        do_buys(chosen, rmap, start_capital, date_s, "initial entry", buys)
                        events.append({"date": date_s, "trigger": "initial_entry",
                                       "value_before": start_capital,
                                       "value_after": round(pv(price_row, hedge_px), 2),
                                       "sells": [], "buys": buys, "keeps": [], "cash_left": 0.0,
                                       "holdings_after": [{"ticker": tk.replace(".NS", ""),
                                                           "rank": rmap[tk]["rank"], "fit": rmap[tk]["fit"]}
                                                          for tk, _ in chosen]})
                    else:
                        state = "hedge"
                        hedge_units = start_capital * (1 - cost_pct) / hedge_px
                        events.append({"date": date_s, "trigger": "initial_entry (hedge)",
                                       "value_before": start_capital,
                                       "value_after": round(hedge_units * hedge_px, 2),
                                       "sells": [], "buys": [{"ticker": hedge_ticker, "amount": start_capital}],
                                       "keeps": [], "cash_left": 0.0,
                                       "holdings_after": [{"ticker": hedge_ticker, "note": "regime off at start"}]})
            if started:
                index_level.iloc[i] = pv(price_row, hedge_px)
            continue

        regime_invested = raw_invested if raw_invested != (state == "invested") else (state == "invested")
        value_before = pv(price_row, hedge_px)

        if state == "invested" and not regime_invested:
            # ---- regime exit: everything out, hedge in ----
            sells = []
            for tk in list(positions):
                p = positions.pop(tk)
                px = price_row[tk]
                gross = p["qty"] * px
                net = gross * (1 - cost_pct)
                cash += net
                info = (latest_ranking or {}).get(tk)
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
                    "rank_out": info["rank"] if info else None,
                    "fit_out": info["fit"] if info else None,
                    "why_in": p["why_in"],
                    "why_out": "regime exit — NIFTY 50 closed below its 200-day EMA"
                               + (f" (last known rank {info['rank']})" if info else ""),
                })
                sells.append({"ticker": tk.replace(".NS", ""), "reason": "regime exit",
                              "rank_out": info["rank"] if info else None,
                              "fit_out": info["fit"] if info else None,
                              "proceeds": round(net, 2)})
            hedge_units = cash * (1 - cost_pct) / hedge_px if pd.notna(hedge_px) and hedge_px else 0.0
            cash = 0.0
            state = "hedge"
            events.append({"date": date_s, "trigger": "regime_exit",
                           "value_before": round(value_before, 2),
                           "value_after": round(pv(price_row, hedge_px), 2),
                           "sells": sells, "buys": [], "keeps": [], "cash_left": 0.0,
                           "holdings_after": [{"ticker": hedge_ticker, "note": "regime off"}]})

        elif state == "hedge" and regime_invested:
            # ---- regime re-entry: gold out, fresh top-10 in ----
            cash = hedge_units * hedge_px * (1 - cost_pct) if pd.notna(hedge_px) and hedge_px else 0.0
            hedge_units = 0.0
            sel, rmap = rank_map_at(closes, i)
            if sel is not None:
                latest_ranking, latest_ranking_date = rmap, date_s
                buys = []
                chosen = sel[:TOP_N]
                do_buys(chosen, rmap, cash, date_s, "regime re-entry", buys)
                cash = 0.0
                state = "invested"
                events.append({"date": date_s, "trigger": "regime_reentry",
                               "value_before": round(value_before, 2),
                               "value_after": round(pv(price_row, hedge_px), 2),
                               "sells": [{"ticker": hedge_ticker, "reason": "regime re-entry"}],
                               "buys": buys, "keeps": [], "cash_left": 0.0,
                               "holdings_after": [{"ticker": tk.replace(".NS", ""),
                                                   "rank": rmap[tk]["rank"], "fit": rmap[tk]["fit"]}
                                                  for tk, _ in chosen]})

        elif state == "invested" and regime_invested and is_rb:
            # ---- scheduled review: hysteresis (exit rank 52) + refill ----
            sel, rmap = rank_map_at(closes, i)
            if sel is not None:
                latest_ranking, latest_ranking_date = rmap, date_s
                sells, buys, keeps = [], [], []
                for tk in list(positions):
                    info = rmap.get(tk)
                    if info is None or info["rank"] > EXIT_RANK:
                        p = positions.pop(tk)
                        px = price_row[tk]
                        gross = p["qty"] * px
                        net = gross * (1 - cost_pct)
                        cash += net
                        why = (f"fell to rank {info['rank']} — below the exit rank {EXIT_RANK}"
                               if info else "no longer ranked (insufficient history)")
                        trades.append({
                            "ticker": tk.replace(".NS", ""),
                            "entry_date": p["entry_date"], "entry_price": round(p["entry_price"], 2),
                            "exit_date": date_s, "exit_price": round(float(px), 2),
                            "qty": round(p["qty"], 3),
                            "pct_return": round((net / p["invested_gross"] - 1) * 100, 2),
                            "pnl": round(net - p["invested_gross"], 2),
                            "status": "closed", "carried_in": False,
                            "num_rebalances_held": len(p["carried_dates"]),
                            "carried_dates": p["carried_dates"],
                            "rank_in": p["rank_in"], "fit_in": p["fit_in"],
                            "rank_out": info["rank"] if info else None,
                            "fit_out": info["fit"] if info else None,
                            "why_in": p["why_in"], "why_out": why,
                        })
                        sells.append({"ticker": tk.replace(".NS", ""),
                                      "reason": "exit rank", "rank_out": info["rank"] if info else None,
                                      "fit_out": info["fit"] if info else None,
                                      "proceeds": round(net, 2)})
                    else:
                        positions[tk]["carried_dates"].append(date_s)
                        keeps.append({"ticker": tk.replace(".NS", ""),
                                      "rank": info["rank"], "fit": info["fit"]})
                cash_left = 0.0
                slots = TOP_N - len(positions)
                if slots > 0 and cash > 0:
                    candidates = [(tk, sc) for tk, sc in sel if tk not in positions][:slots]
                    if candidates:
                        buys = []
                        do_buys(candidates, rmap, cash, date_s, "review refill", buys)
                        cash = 0.0
                    else:
                        cash_left = cash
                events.append({"date": date_s, "trigger": "scheduled_rebalance",
                               "value_before": round(value_before, 2),
                               "value_after": round(pv(price_row, hedge_px), 2),
                               "sells": sells, "buys": buys, "keeps": keeps,
                               "cash_left": round(cash_left, 2),
                               "holdings_after": [{"ticker": tk.replace(".NS", ""),
                                                   "rank": rmap[tk]["rank"], "fit": rmap[tk]["fit"]}
                                                  for tk in positions]})

        index_level.iloc[i] = pv(price_row, hedge_px)

    # open positions at the end, marked to the last close
    last_row = closes.iloc[-1]
    last_date_s = dates[-1].strftime("%Y-%m-%d")
    open_trades = []
    for tk, p in positions.items():
        px = last_row.get(tk)
        if pd.notna(px):
            value_net = p["qty"] * px * (1 - cost_pct)
            info = (latest_ranking or {}).get(tk)
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
                "rank_out": info["rank"] if info else None,
                "fit_out": info["fit"] if info else None,
                "why_in": p["why_in"],
                "why_out": f"still held — rank {info['rank']}" if info else "still held",
            })
    trades.extend(open_trades)

    return {
        "series": index_level.dropna(),
        "events": events,
        "trades": trades,
        "latest_ranking": latest_ranking,
        "latest_ranking_date": latest_ranking_date,
        "final_state": state,
        "final_positions": list(positions.keys()),
    }


def build_ranks_preview(closes, held, latest_ranking, latest_ranking_date, dates,
                        regime_on=True, regime_since=None):
    """MomentumScore's ranks table, as of the latest close: the full
    current ranking (top 30 + anything held), each row's Δ vs the last
    review, and the action a review TODAY would take — regime-aware: if
    the 200-EMA filter is currently OFF, a review would stay in the hedge
    and take no stock action at all."""
    sel, rmap = rank_map_at(closes, len(dates) - 1)
    if sel is None:
        return None
    held = set(held)
    # same hysteresis logic as the loop, applied to today's ranks —
    # but only if the regime filter is currently ON; otherwise a review
    # would stay in the hedge and take no action
    sell_tickers = [tk for tk in held if (rmap.get(tk) is None or rmap[tk]["rank"] > EXIT_RANK)] if regime_on else []
    keeps = [tk for tk in held if tk not in set(sell_tickers)] if regime_on else []
    need = TOP_N - len(keeps)
    buy_tickers = [tk for tk, _ in sel if tk not in held][:max(0, need)] if regime_on else []

    rows = []
    shown = [tk for tk, _ in sel[:30] if tk not in held] + [tk for tk, _ in sel if tk in held]
    for tk in shown:
        info = rmap.get(tk)
        if info is None:
            continue
        prev = (latest_ranking or {}).get(tk)
        action = ""
        if not regime_on:
            action = ""
        elif tk in held:
            action = "SELL — fell out of top 52" if info["rank"] > EXIT_RANK else "HOLD"
        elif tk in buy_tickers:
            action = "BUY — refill slot"
        rows.append({
            "ticker": tk.replace(".NS", ""),
            "rank": info["rank"], "fit": info["fit"], "score": round(info["score"], 4),
            "held": tk in held,
            "prev_rank": prev["rank"] if prev else None,
            "prev_fit": prev["fit"] if prev else None,
            "rank_delta": (prev["rank"] - info["rank"]) if prev else None,
            "fit_delta": (info["fit"] - prev["fit"]) if prev else None,
            "action": action,
        })
    rows.sort(key=lambda r: r["rank"])
    # next scheduled rebalance after the last date (June/December month-end)
    y, m = dates[-1].year, dates[-1].month
    nxt = None
    for yy, mm in ((y, 6), (y, 12), (y + 1, 6), (y + 1, 12)):
        if (yy, mm) > (y, m):
            nxt = f"{yy:04d}-{mm:02d}-month-end"
            break
    return {
        "as_of": dates[-1].strftime("%Y-%m-%d"),
        "last_review": latest_ranking_date,
        "next_rebalance": nxt,
        "exit_rank": EXIT_RANK,
        "regime_on": regime_on,
        "regime_since": regime_since,
        "rows": rows,
        "preview": {
            "sells": [tk.replace(".NS", "") for tk in sell_tickers],
            "buys": [tk.replace(".NS", "") for tk in buy_tickers],
            "keeps": len(keeps),
        },
        "note": ("Ranking recomputed at the latest close with the same formula and exit-rank "
                 "rule the engine uses — action column previews what a review on this data "
                 "would do, Δ columns are vs the last scheduled review."
                 + ("" if regime_on else
                    " The 200-day EMA regime filter is currently OFF, so a review today would "
                    f"stay in the gold hedge (since {regime_since}) — no stock actions.")),
    }


def main():
    closes = load_midcap150_closes()
    nifty_df = fetch("^NSEI")
    gold_df = fetch_gold_cleaned()

    nifty = nifty_df["Close"].rename("nifty")
    gold = gold_df["Close"].rename("gold")
    common = closes.index.intersection(nifty.index).intersection(gold.index)
    closes = closes.loc[common]
    nifty = nifty.loc[common].ffill()
    gold = gold.loc[common].ffill()
    dates = closes.index

    ema = nifty.ewm(span=EMA_SPAN, adjust=False).mean()
    rbdates_eom = rebalance_dates(dates, months=(6, 12))
    rbdates_mid = midmonth_rebalance_dates(dates, months=(6, 12), day=15)

    print(f"window: {dates[0].date()} -> {dates[-1].date()} ({len(dates)} days), "
          f"{len(rbdates_eom)} scheduled reviews, {len(closes.columns)} symbols")

    print("running engine — before costs ...")
    run_free = run_engine(closes, nifty, ema, gold, rbdates_eom, cost_pct=0.0)
    print("running engine — after costs (0.1% per side) ...")
    run_cost = run_engine(closes, nifty, ema, gold, rbdates_eom, cost_pct=COST_PCT_PER_SIDE)
    print("running engine — date-luck variant (mid-month reviews, after costs) ...")
    run_mid = run_engine(closes, nifty, ema, gold, rbdates_mid, cost_pct=COST_PCT_PER_SIDE)

    before_costs = metrics_only(run_free["series"], common)
    after_costs = metrics_only(run_cost["series"], common)
    nifty_m = metrics_only(nifty, common)
    gold_m = metrics_only(gold, common)

    # full-resolution points for the review layer (not the downsampled chart series)
    after_full = [[d.strftime("%Y-%m-%d"), float(v)] for d, v in run_cost["series"].items()]
    nifty_full = [[d.strftime("%Y-%m-%d"), float(v)] for d, v in nifty.items()]

    # ---- robustness ----
    halves = ms_rob.halves_check(after_full, nifty_full)
    mid_points = series_to_points(run_mid["series"] / run_mid["series"].iloc[0] * 100.0)
    eom_points = series_to_points(run_cost["series"] / run_cost["series"].iloc[0] * 100.0)
    date_luck = ms_rob.variants_check(nifty_full, [
        {"label": "month-end reviews (day ~31)", "kind": "main", "points": eom_points},
        {"label": "mid-month reviews (day ~15)", "kind": "variant", "points": mid_points},
    ])
    robustness = {"halves": halves, "date_luck": date_luck,
                  "passed_overall": bool(halves and halves["passed_both"] is not None
                                         and halves["passed_both"]
                                         and date_luck["verdict"] == "pass")}

    # ---- health ----
    health = ms_health.health_check(after_full, run_cost["trades"])

    # ---- tax ----
    fmv_idx = closes.index[closes.index <= FMV_DATE]
    fmv_map = {}
    if len(fmv_idx):
        row = closes.loc[fmv_idx[-1]]
        fmv_map = {str(t).replace(".NS", "").upper(): float(v) for t, v in row.items() if v == v}
    closed = [t for t in run_cost["trades"] if t["status"] == "closed"]
    tax_input = [{"ticker": t["ticker"], "entry_date": t["entry_date"], "exit_date": t["exit_date"],
                  "entry_price": t["entry_price"], "exit_price": t["exit_price"], "qty": t["qty"]}
                 for t in closed]
    tax_report = ms_tax.capital_gains_report(tax_input, fmv_by_ticker=fmv_map, fmv_date=FMV_DATE)
    tax_by_fy = {y["fy"]: y["total_tax"] for y in tax_report["years"] if y["total_tax"] > 0}
    after_tax_points, taxes_applied = ms_tax.after_tax_curve(after_full, tax_by_fy)
    at_series = pd.Series([v for _d, v in after_tax_points],
                          index=pd.DatetimeIndex([d for d, _v in after_tax_points]))
    after_tax = metrics_only(at_series, common)
    tax_report["taxes_applied_to_curve"] = taxes_applied
    tax_report["growth_after_tax_pct"] = after_tax["cagr_pct"]
    tax_report["growth_before_tax_pct"] = after_costs["cagr_pct"]

    # ---- ranks preview ----
    last_ev = run_cost["events"][-1] if run_cost["events"] else None
    regime_on = run_cost["final_state"] == "invested"
    regime_since = last_ev["date"] if (last_ev and last_ev["trigger"] in ("regime_exit", "regime_reentry")) else None
    ranks = build_ranks_preview(closes, run_cost["final_positions"],
                                run_cost["latest_ranking"], run_cost["latest_ranking_date"], dates,
                                regime_on=regime_on, regime_since=regime_since)

    # ---- trade stats (matches the TradeLog component's expectations) ----
    def _pcts(rows, status):
        return [t["pct_return"] for t in rows if t["status"] == status]
    closed_pcts = _pcts(run_cost["trades"], "closed")
    wins = [p for p in closed_pcts if p > 0]
    losses = [p for p in closed_pcts if p <= 0]
    trade_stats = {
        "total_trades": len(closed_pcts),
        "win_rate_pct": round(len(wins) / len(closed_pcts) * 100, 1) if closed_pcts else None,
        "avg_win_pct": round(sum(wins) / len(wins), 2) if wins else None,
        "avg_loss_pct": round(sum(losses) / len(losses), 2) if losses else None,
        "avg_rebalances_held": round(sum(t["num_rebalances_held"] for t in closed) / len(closed), 1) if closed else None,
        "total_realized_pnl": round(sum(t["pnl"] for t in closed), 2),
        "total_unrealized_pnl": round(sum(t["pnl"] for t in run_cost["trades"] if t["status"] == "open"), 2),
        "open_positions": sum(1 for t in run_cost["trades"] if t["status"] == "open"),
    }

    out = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "currency_symbol": CURRENCY_SYMBOL,
        "start_date": dates[0].strftime("%Y-%m-%d"),
        "end_date": dates[-1].strftime("%Y-%m-%d"),
        "ema_span": EMA_SPAN,
        "config": {
            "top_n": TOP_N, "exit_rank": EXIT_RANK, "min_eligible": MIN_ELIGIBLE,
            "cost_pct_per_side": COST_PCT_PER_SIDE * 100, "start_capital_inr": START_CAPITAL,
            "rebalance_months": [6, 12], "day_mode": "month-end",
            "held_convention": "carried stocks keep their original shares (report 31 convention)",
        },
        "before_costs": before_costs,
        "after_costs": after_costs,
        "after_tax": after_tax,
        "nifty": nifty_m,
        "gold_benchmark": gold_m,
        "trades": run_cost["trades"],
        "trade_stats": trade_stats,
        "rebalances": run_cost["events"],
        "ranks": ranks,
        "robustness": robustness,
        "health_check": health,
        "tax_report": tax_report,
        "notes": [
            "Same strategy skeleton as report 48 (Midcap150 Momentum 10, NIFTY 50 200-EMA regime, "
            "GOLDBEES hedge) — the changes are the review layer: exit-rank-52 hysteresis instead of "
            "forced re-selection, carried stocks keep their shares (never trimmed), 0.1%/side costs "
            "on every leg, real-rupee trade log from Rs 1,00,000.",
            "Health check: score = share of MomentumScore's 10 target ranges met. Two documented "
            "proxies: 'tail risk' uses the skewness of monthly / per-trade returns (see "
            "ms_port/health.py).",
            "Tax: capital-gains estimate only — 15%/10% for sales before 23 Jul 2024, 20%/12.5% "
            "(exemption Rs 1.25L LTCG) on/after, 4% cess, loss set-off with 8-year carry, s.112A "
            "grandfathering via the 31-Jan-2025 FMV from this same price data.",
            "Universe: today's NIFTY Midcap 150 membership applied to the full history "
            "(survivorship-biased, same caveat as every Midcap150 report here).",
        ],
    }

    with open("results92.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)

    print()
    print(f"before costs : CAGR {before_costs['cagr_pct']:.1f}%  maxDD {before_costs['max_drawdown_pct']:.1f}%")
    print(f"after costs  : CAGR {after_costs['cagr_pct']:.1f}%  maxDD {after_costs['max_drawdown_pct']:.1f}%")
    print(f"after tax    : CAGR {after_tax['cagr_pct']:.1f}%")
    print(f"nifty        : CAGR {nifty_m['cagr_pct']:.1f}%")
    print(f"trades       : {trade_stats['total_trades']} closed, win rate {trade_stats['win_rate_pct']}%, "
          f"realized P&L {CURRENCY_SYMBOL}{trade_stats['total_realized_pnl']:,.0f}")
    print(f"health       : {health['score']} / 100 ({health['checks_met']}/{health['checks_available']} checks)")
    print(f"robustness   : halves both={halves['passed_both']}, date-luck={date_luck['verdict']} "
          f"(eom {eom_points[-1][1]:.0f} vs mid {mid_points[-1][1]:.0f} on 100 base)")
    print(f"tax          : {CURRENCY_SYMBOL}{tax_report['totals']['total_tax']:,.0f} over "
          f"{len(tax_report['years'])} FYs")
    print("results92.json written")


if __name__ == "__main__":
    main()

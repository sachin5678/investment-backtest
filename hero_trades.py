"""Trade-by-trade log for the hero reports (48, 71, 91) — rebuilt from the
SAME event loops the reports already use, never re-derived.

backtest42's builders (build_index_regime_filtered_with_hedge,
build_index_core_satellite) return the index level, a `selections` list
(every buy event: initial entry / scheduled rebalance / regime re-entry) and
a daily `state_log`. A holding's real life, though, is longer than one
selection: a stock that is re-picked at a rebalance is CARRIED (the model
rebalances it back to equal weight but it is the same position, the same
way report 31 merges them), and a regime flip sells everything. This module
walks those two logs day by day and emits one row per continuous holding in
report 31's merged-trade shape, so webapp/src/components/TradeLog.jsx
renders it with the New / Carried / Exited tags it already has.

P&L is exact for the model: every holding's rupee P&L is the sum, over its
rebalance-to-rebalance segments, of (segment allocation x segment price
return), with the segment allocation taken from the strategy's own equity
curve (scaled to the Rs 1,00,000 start the other trade logs use). The
hedge leg (GOLDBEES) appears as a holding too. `check_total` confirms that
summed P&L reproduces the equity curve's gain, which is how a bug here
would show up.

The builders apply no transaction costs (reports 48/71/91 never did), so
neither does this log; report 98's log (ms_builder) is the costed one.
"""
import pandas as pd

START_CAPITAL = 100_000.0
GOLD_NAME = "GOLDBEES (hedge)"


def _d(ts):
    return ts.strftime("%Y-%m-%d")


def reconstruct(series, closes, hedge_close, selections, state_log, off_states,
                stock_weight_on, hedge_weight_on, guard_flat=None):
    """series       the strategy's index-level Series (starts at 100)
    closes       DataFrame of stock closes (same index as the builder used)
    hedge_close  aligned GOLDBEES closes
    selections   builder's selections list
    state_log    builder's [(date, state)] list
    off_states   set of state names that mean "risk-off" (e.g. {"cash"})
    stock_weight_on / hedge_weight_on  target weights while risk-on
    guard_flat   optional boolean Series, True on the days the gold-strength
                 guard held flat cash (position decided at the PRIOR close,
                 report 99's convention) — gold is not held on those days
    Returns (trades, stats).
    """
    scale = START_CAPITAL / 100.0
    sel_by_date = {s["date"]: s["tickers"] for s in selections}
    state_by_date = dict(state_log)

    flat_at_close = None
    if guard_flat is not None:
        # day i earns flat cash if guard_flat[i]; that position was set at
        # close i-1, so the transition happens at the close before.
        gf = guard_flat.reindex(series.index).fillna(False).astype(bool)
        flat_at_close = gf.shift(-1).fillna(False).astype(bool)

    holdings = {}   # key -> dict(entry_date, entry_price, seg_px, seg_alloc, pnl, alloc0, carried)
    trades = []
    picks = []
    prev_sig = None

    def price(key, d):
        if key == GOLD_NAME:
            return float(hedge_close.loc[d])
        return float(closes.loc[d, key + ".NS"])

    def close_out(key, d, status="closed"):
        h = holdings.pop(key)
        px = price(key, d)
        pnl = h["pnl"] + h["seg_alloc"] * (px / h["seg_px"] - 1.0)
        trades.append({
            "ticker": key, "entry_date": h["entry_date"], "entry_price": round(h["entry_price"], 2),
            "exit_date": _d(d) if status == "closed" else None,
            "exit_price": round(px, 2) if status == "closed" else None,
            "pct_return": round((px / h["entry_price"] - 1.0) * 100, 2),
            "alloc": round(h["alloc0"], 2), "pnl": round(pnl, 2),
            "num_rebalances_held": len(h["carried"]), "carried_dates": h["carried"],
            "status": status, "carried_in": False,
        })

    for d in series.index:
        ds = _d(d)
        state = state_by_date.get(d)
        if state is None:
            continue
        is_off = state in off_states
        picked_today = ds in sel_by_date
        if picked_today:
            picks = sel_by_date[ds]

        # --- targets (as weights of total portfolio) at this close ---
        targets = {}
        if not is_off and picks:
            for t in picks:
                targets[t] = stock_weight_on / len(picks)
            if hedge_weight_on > 0:
                targets[GOLD_NAME] = hedge_weight_on
        elif is_off:
            gold_ok = not (flat_at_close is not None and bool(flat_at_close.loc[d]))
            if gold_ok:
                targets[GOLD_NAME] = 1.0
        sig = frozenset(targets)
        if not picked_today and sig == prev_sig:
            continue
        prev_sig = sig

        value = float(series.loc[d]) * scale
        # close holdings that left the target set, carry the ones that stay
        for key in list(holdings):
            if key not in targets:
                close_out(key, d)
        for key, w in targets.items():
            px = price(key, d)
            alloc = value * w
            if key in holdings:
                h = holdings[key]
                h["pnl"] += h["seg_alloc"] * (px / h["seg_px"] - 1.0)
                h["seg_px"], h["seg_alloc"] = px, alloc
                h["carried"].append(ds)
            else:
                holdings[key] = {"entry_date": ds, "entry_price": px, "seg_px": px,
                                 "seg_alloc": alloc, "alloc0": alloc, "pnl": 0.0, "carried": []}

    last = series.index[-1]
    for key in list(holdings):
        close_out(key, last, status="open")

    trades.sort(key=lambda t: (t["entry_date"], t["ticker"]))
    closed = [t for t in trades if t["status"] == "closed"]
    wins = [t["pct_return"] for t in closed if t["pct_return"] > 0]
    losses = [t["pct_return"] for t in closed if t["pct_return"] <= 0]
    stats = {
        "total_positions": len(trades), "closed_positions": len(closed),
        "still_open": len(trades) - len(closed),
        "win_rate_pct": round(len(wins) / len(closed) * 100, 1) if closed else None,
        "avg_win_pct": round(sum(wins) / len(wins), 2) if wins else None,
        "avg_loss_pct": round(sum(losses) / len(losses), 2) if losses else None,
        "avg_rebalances_held": round(sum(t["num_rebalances_held"] for t in closed) / len(closed), 2) if closed else None,
        "longest_held_rebalances": max((t["num_rebalances_held"] for t in trades), default=0),
        "total_realized_pnl": round(sum(t["pnl"] for t in closed), 2),
        "total_unrealized_pnl": round(sum(t["pnl"] for t in trades if t["status"] == "open"), 2),
    }
    return trades, stats


def check_total(series, stats, tol_pct=0.5):
    """Summed holding P&L must equal the equity curve's rupee gain."""
    gain = (float(series.iloc[-1]) - 100.0) * (START_CAPITAL / 100.0)
    got = stats["total_realized_pnl"] + stats["total_unrealized_pnl"]
    ok = abs(got - gain) <= abs(gain) * tol_pct / 100.0
    print(f"  trade-log check: summed P&L {got:,.0f} vs equity-curve gain {gain:,.0f} -> {'OK' if ok else 'MISMATCH'}")
    return ok

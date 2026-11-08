"""Next-open execution builder (CLAUDE.md rule 3).

A signal formed at day T's close (a scheduled rebalance day, or a regime
flip of NIFTY 50 vs its 200-EMA) is filled at day T+1's OPEN: the old
holdings are sold and the new ones bought together at that open, and the
book is marked at T+1's close with the new holdings. The T-close to
T+1-open gap is earned by the OLD position. Signal inputs use data up to T's
close only. Separate from backtest42's close-execution builders so every
published (same-close) number stays reproducible.

use_regime=False -> plain yearly/periodic rebalance, no switch.
use_regime=True  -> 200-EMA switch, risk-off parks 100% in the hedge
                    (confirm_days=1, same as reports 42-48).
"""
import numpy as np
import pandas as pd

MAX_GAP = (0.7, 1.4)   # Open/Close outside this band = bad print -> use Close


def load_opens(closes):
    raw = pd.read_pickle("universe_raw.pkl")
    op = raw.xs("Open", axis=1, level=1).sort_index().reindex(index=closes.index, columns=closes.columns)
    return clean_open(op, closes)


def clean_open(op, cl):
    ratio = op / cl
    bad = op.isna() | (op <= 0) | (ratio < MAX_GAP[0]) | (ratio > MAX_GAP[1])
    return op.where(~bad, cl)


def build_next_open(closes, opens, signal_close, signal_ma, rbdates, select_fn,
                    hedge_close, hedge_open, use_regime=True):
    dates = closes.index
    rb_set = set(rbdates)
    level = pd.Series(np.nan, index=dates)
    shares, hedge_units = {}, 0.0
    state = None            # None=not started, "invested", "hedge"
    pending = None          # ("invest", tickers) | ("hedge", None) decided at prior close
    value = 100.0
    log = []

    for i, d in enumerate(dates):
        c, o = closes.iloc[i], opens.iloc[i]

        # 1) execute what was decided at the prior close, at today's open
        if pending is not None:
            if state == "invested":
                v_open = sum(sh * o[t] for t, sh in shares.items() if pd.notna(o[t]))
            elif state == "hedge":
                v_open = hedge_units * hedge_open.iloc[i]
            else:
                v_open = value
            kind, tickers = pending
            if kind == "invest":
                each = v_open / len(tickers)
                shares = {t: each / o[t] for t in tickers}
                hedge_units, state = 0.0, "invested"
            else:
                shares, hedge_units, state = {}, v_open / hedge_open.iloc[i], "hedge"
            log.append((d, kind, tickers))
            pending = None

        # 2) mark at today's close
        if state == "invested":
            value = sum(sh * c[t] for t, sh in shares.items() if pd.notna(c[t])) or value
        elif state == "hedge":
            value = hedge_units * hedge_close.iloc[i]
        if state is not None:
            level.iloc[i] = value

        # 3) form today's signal (executes at the next open)
        ma = signal_ma.iloc[i]
        raw_on = bool(signal_close.iloc[i] > ma) if pd.notna(ma) else False
        on = raw_on if use_regime else True
        is_rb = d in rb_set
        if state is None:
            if is_rb:
                sel = select_fn(closes, i)
                if sel is not None:
                    pending = ("invest", sel) if on else ("hedge", None)
        elif state == "invested":
            if not on:
                pending = ("hedge", None)
            elif is_rb:
                sel = select_fn(closes, i)
                if sel is not None:
                    pending = ("invest", sel)
        elif state == "hedge":
            if on:
                sel = select_fn(closes, i)
                if sel is not None:
                    pending = ("invest", sel)

    return level.dropna(), log

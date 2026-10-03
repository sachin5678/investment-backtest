"""Wild combinations on report 48's design (200-EMA NIFTY regime
filter, gold in risk-off). All variants hold gold instead of cash;
the stock portfolio only differs in WHEN it gets switched in/out.
"""
import pandas as pd
import numpy as np

from backtest10 import rebalance_dates, fetch, CURRENCY_SYMBOL
from backtest13 import load_midcap150_closes, fetch_gold_cleaned
from backtest32 import metrics_only
from backtest33 import select_top_original, build_index_generic
from backtest42 import build_index_regime_filtered_with_hedge, EMA_SPAN


def run(closes, nifty_close, signal, rbdates, select_fn, hedge_close, start_invested=True):
    """signal(i, state, aux) -> ("invested"|"cash", new_aux):
    aux is a mutable dict the caller's closure uses for latched state
    (confirmation streaks, vol-state latches, etc.)."""
    dates = closes.index
    rb_set = set(rbdates)
    index_level = pd.Series(np.nan, index=dates)
    shares, hedge_units = {}, 0.0
    started, state = False, "invested" if start_invested else "cash"
    aux = {}

    def buy(selected, value_before, price_today):
        return {tk: (value_before / len(selected)) / price_today[tk] for tk in selected}

    for i, d in enumerate(dates):
        is_rb = d in rb_set
        price_today = closes.iloc[i]
        hpt = hedge_close.iloc[i]
        desired, aux = signal(i, state, aux)

        if not started:
            if is_rb:
                selected = select_fn(closes, i)
                if selected is not None:
                    started = True
                    if desired == "invested":
                        state = "invested"
                        shares = buy(selected, 100.0, price_today)
                    else:
                        state = "cash"
                        hedge_units = 100.0 / hpt
            if started:
                val = hedge_units * hpt if state == "cash" else sum(s * price_today.get(t, 0.0) for t, s in shares.items())
                index_level.iloc[i] = val
            continue

        if state == "invested":
            value_before = sum(s * price_today.get(t, 0.0) for t, s in shares.items() if pd.notna(price_today.get(t)))
            if value_before <= 0:
                value_before = index_level.iloc[i - 1]
        else:
            value_before = hedge_units * hpt

        if state == "invested" and desired == "cash":
            state = "cash"; shares = {}
            hedge_units = value_before / hpt
            val = value_before
        elif state == "cash" and desired == "invested":
            selected = select_fn(closes, i)
            if selected is not None:
                shares = buy(selected, value_before, price_today)
                state = "invested"; hedge_units = 0.0
            val = value_before
        elif state == "invested" and desired == "invested" and is_rb:
            selected = select_fn(closes, i)
            if selected is not None:
                shares = buy(selected, value_before, price_today)
            val = sum(s * price_today.get(t, 0.0) for t, s in shares.items() if pd.notna(price_today.get(t)))
        else:
            if state == "invested":
                val = sum(s * price_today.get(t, 0.0) for t, s in shares.items() if pd.notna(price_today.get(t)))
                if val <= 0:
                    val = value_before
            else:
                val = hedge_units * hpt

        index_level.iloc[i] = val

    return index_level.dropna()


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    gold = fetch_gold_cleaned()
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]
    gold_aligned = gold["Close"].reindex(common).ffill().bfill()
    ema200 = nifty_close.ewm(span=200, adjust=False).mean()
    ema100 = nifty_close.ewm(span=100, adjust=False).mean()
    ema50 = nifty_close.ewm(span=50, adjust=False).mean()
    vol20 = nifty_close.pct_change().rolling(20).std() * np.sqrt(252) * 100
    high252 = nifty_close.rolling(252).max()
    stock_ema200 = closes.ewm(span=200, adjust=False).mean()
    rbdates = rebalance_dates(closes.index, months=(6, 12))

    original_series, _ = build_index_generic(closes, rbdates, select_top_original)
    gold_series, _, _ = build_index_regime_filtered_with_hedge(
        closes, nifty_close, ema200, rbdates, select_top_original, gold_aligned)
    common_idx = original_series.index.intersection(gold_series.index)

    variants = {}

    # A. Asymmetric: exit on 100-EMA break, re-enter only on 200-EMA reclaim
    def sig_a(i, state, aux):
        p, m100, m200 = nifty_close.iloc[i], ema100.iloc[i], ema200.iloc[i]
        if state == "invested":
            return ("cash" if p < m100 else "invested"), aux
        return ("invested" if p > m200 else "cash"), aux
    variants["A. exit<100EMA, re-enter>200EMA"] = run(closes, nifty_close, sig_a, rbdates, select_top_original, gold_aligned)

    # B. Both-EMA gate: stocks only when NIFTY > 50 AND > 200 EMA; gold otherwise
    def sig_b(i, state, aux):
        p = nifty_close.iloc[i]
        ok = p > ema50.iloc[i] and p > ema200.iloc[i]
        return ("invested" if ok else "cash"), aux
    variants["B. stocks only above 50&200 EMA"] = run(closes, nifty_close, sig_b, rbdates, select_top_original, gold_aligned)

    # C. Vol regime with hysteresis: gold when 20d ann vol > 20%, stocks when < 15%
    def sig_c(i, state, aux):
        v = vol20.iloc[i]
        if pd.isna(v):
            return ("invested" if state == "invested" else "cash"), aux
        if state == "invested" and v > 20:
            aux["vol_off"] = True
        elif aux.get("vol_off") and v < 15:
            aux["vol_off"] = False
        return ("cash" if aux.get("vol_off") else "invested"), aux
    variants["C. vol>20%->gold, <15%->stocks"] = run(closes, nifty_close, sig_c, rbdates, select_top_original, gold_aligned)

    # D. Drawdown trigger: gold when NIFTY > 8% below its 252d high; stocks when within 3%
    def sig_d(i, state, aux):
        dd = nifty_close.iloc[i] / high252.iloc[i] - 1
        if state == "invested" and dd < -0.08:
            aux["dd_off"] = True
        elif aux.get("dd_off") and dd > -0.03:
            aux["dd_off"] = False
        return ("cash" if aux.get("dd_off") else "invested"), aux
    variants["D. -8%-from-high->gold, -3%->back"] = run(closes, nifty_close, sig_d, rbdates, select_top_original, gold_aligned)

    # E. 3-day confirmation on both sides of 200-EMA
    def sig_e(i, state, aux):
        below = nifty_close.iloc[i] < ema200.iloc[i]
        key = "streak_below" if below else "streak_above"
        other = "streak_above" if below else "streak_below"
        aux[key] = aux.get(key, 0) + 1
        aux[other] = 0
        if aux["streak_below"] >= 3:
            aux["off"] = True
        if aux["streak_above"] >= 3:
            aux["off"] = False
        return ("cash" if aux.get("off") else "invested"), aux
    variants["E. 200EMA, 3-day confirm both sides"] = run(closes, nifty_close, sig_e, rbdates, select_top_original, gold_aligned)

    # F. Breadth entry gate: stocks when NIFTY > 200EMA AND >=40% of Midcap150 names above their 200EMA
    def sig_f(i, state, aux):
        above = nifty_close.iloc[i] > ema200.iloc[i]
        if not above:
            aux["breadth_ok"] = False
            return "cash", aux
        if state == "cash":
            p = closes.iloc[i]; e = stock_ema200.iloc[i]
            frac = ((p > e) & p.notna() & e.notna()).sum() / len(closes.columns)
            aux["breadth_ok"] = bool(frac >= 0.40)
        return ("invested" if aux.get("breadth_ok") else "cash"), aux
    variants["F. 200EMA + 40% breadth entry gate"] = run(closes, nifty_close, sig_f, rbdates, select_top_original, gold_aligned)

    # G. Nested: risk-off -> gold, unless gold itself is below ITS 200-EMA -> cash
    gold_ema200 = gold_aligned.ewm(span=200, adjust=False).mean()
    def sig_g(i, state, aux):
        risk_off = nifty_close.iloc[i] < ema200.iloc[i]
        if not risk_off:
            return "invested", aux
        g_ok = gold_aligned.iloc[i] > gold_ema200.iloc[i]
        aux["cash_mode"] = not g_ok
        return "cash", aux
    # needs the cash_mode to be honored — wrap hedge value in run? simpler: post-scale
    s7 = run(closes, nifty_close, sig_g, rbdates, select_top_original, gold_aligned)
    # patch: in risk-off AND gold<its ema200 periods, hold flat 0% instead of gold return
    ret_g = gold_aligned.pct_change().fillna(0.0)
    mask_cash = (nifty_close < ema200) & (gold_aligned < gold_ema200)
    ret_g_adj = ret_g.mask(mask_cash, 0.0).fillna(0.0)
    base = s7.pct_change().fillna(0.0)
    in_gold = (nifty_close < ema200).reindex(s7.index).fillna(False)
    adj_ret = base.where(~in_gold, ret_g_adj.reindex(s7.index).fillna(0.0))
    variants["G. risk-off gold, but cash if gold<its 200EMA"] = (1 + adj_ret).cumprod() * 100.0

    # H. Momentum card: during risk-off hold gold ONLY if gold's 6m return
    #    beats NIFTY's 6m return, else cash
    g6 = gold_aligned.pct_change(126); n6 = nifty_close.pct_change(126)
    def sig_h(i, state, aux):
        risk_off = nifty_close.iloc[i] < ema200.iloc[i]
        if not risk_off:
            return "invested", aux
        aux["gold_ok"] = bool(g6.iloc[i] > n6.iloc[i])
        return "cash", aux
    s8 = run(closes, nifty_close, sig_h, rbdates, select_top_original, gold_aligned)
    mask_cash_h = (nifty_close < ema200) & (g6 < n6)
    base8 = s8.pct_change().fillna(0.0)
    in_gold8 = (nifty_close < ema200).reindex(s8.index).fillna(False)
    ret_g_adj8 = ret_g.mask(mask_cash_h, 0.0).fillna(0.0)
    adj_ret8 = base8.where(~in_gold8, ret_g_adj8.reindex(s8.index).fillna(0.0))
    variants["H. risk-off gold only if gold 6m > NIFTY 6m"] = (1 + adj_ret8).cumprod() * 100.0

    for name, s in variants.items():
        common_idx = common_idx.intersection(s.index)

    print(f"window {common_idx[0].date()} -> {common_idx[-1].date()}\n")
    for name, s in variants.items():
        m = metrics_only(s, common_idx)
        print(f"{name:40s} CAGR {m['cagr_pct']:.2f}% / DD {m['max_drawdown_pct']:.1f}%")
    m = metrics_only(gold_series, common_idx)
    print(f"{'report 48 (200EMA + gold, standard)':40s} CAGR {m['cagr_pct']:.2f}% / DD {m['max_drawdown_pct']:.1f}%")
    m = metrics_only(original_series, common_idx)
    print(f"{'no filter':40s} CAGR {m['cagr_pct']:.2f}% / DD {m['max_drawdown_pct']:.1f}%")


if __name__ == "__main__":
    main()

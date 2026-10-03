"""Emits the three Opencode-findings series files (results_find_*.json)
in the standard results*.json convention every other report uses, so
the webapp renders them with the normal KPI table + charts."""
import json

import pandas as pd

from backtest10 import rebalance_dates, fetch
from backtest13 import load_midcap150_closes, fetch_gold_cleaned
from backtest32 import metrics_only
from backtest33 import select_top_original, build_index_generic
from backtest42 import build_index_regime_filtered_with_hedge, EMA_SPAN
from dipbuy_experiment import build_with_dipbuy
from overextended_experiment import build as build_overextended
from wild_experiment import run as run_wild

import numpy as np


def main():
    closes = load_midcap150_closes()
    nifty = fetch("^NSEI")
    gold = fetch_gold_cleaned()
    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]
    gold_aligned = gold["Close"].reindex(common).ffill().bfill()
    ema = nifty_close.ewm(span=EMA_SPAN, adjust=False).mean()
    rbdates = rebalance_dates(closes.index, months=(6, 12))

    original_series, _ = build_index_generic(closes, rbdates, select_top_original)
    gold_series, _, _ = build_index_regime_filtered_with_hedge(
        closes, nifty_close, ema, rbdates, select_top_original, gold_aligned)

    def emit(name, series_map):
        common_idx = None
        for s in series_map.values():
            common_idx = s.index if common_idx is None else common_idx.intersection(s.index)
        out = {k: metrics_only(v, common_idx) for k, v in series_map.items()}
        out.update({"generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                    "currency_symbol": "₹"})
        with open(name, "w") as f:
            json.dump(out, f, indent=2)
        print("wrote", name)

    # --- dip-buy ---
    m = {"original_no_filter": original_series, "report48_200ema_gold": gold_series}
    for thr in (0.10, 0.15, 0.20, 0.25):
        s, _, _ = build_with_dipbuy(closes, nifty_close, ema, rbdates, select_top_original, gold_aligned, thr)
        m[f"dipbuy_gap{int(thr*100)}pct"] = s
    emit("results_find_dipbuy.json", m)

    # --- overextended ---
    m = {"original_no_filter": original_series, "report48_200ema_gold": gold_series}
    for over in (0.10, 0.15, 0.20):
        for exit_ in (0.03, 0.05, 0.07):
            s, _, _ = build_overextended(closes, nifty_close, ema, rbdates, select_top_original, gold_aligned, over, exit_)
            m[f"overexit{int(over*100)}_exit{int(exit_*100)}pct"] = s
    emit("results_find_overextended.json", m)

    # --- wild ---
    m = {"original_no_filter": original_series, "report48_200ema_gold": gold_series}
    ema100 = nifty_close.ewm(span=100, adjust=False).mean()
    ema50 = nifty_close.ewm(span=50, adjust=False).mean()
    vol20 = nifty_close.pct_change().rolling(20).std() * np.sqrt(252) * 100
    high252 = nifty_close.rolling(252).max()
    stock_ema200 = closes.ewm(span=200, adjust=False).mean()

    def sig_a(i, state, aux):
        p, m100, m200 = nifty_close.iloc[i], ema100.iloc[i], ema.iloc[i]
        if state == "invested":
            return ("cash" if p < m100 else "invested"), aux
        return ("invested" if p > m200 else "cash"), aux
    m["A_exit100ema_reenter200ema"] = run_wild(closes, nifty_close, sig_a, rbdates, select_top_original, gold_aligned)

    def sig_b(i, state, aux):
        p = nifty_close.iloc[i]
        ok = p > ema50.iloc[i] and p > ema.iloc[i]
        return ("invested" if ok else "cash"), aux
    m["B_above_50_and_200ema"] = run_wild(closes, nifty_close, sig_b, rbdates, select_top_original, gold_aligned)

    def sig_c(i, state, aux):
        v = vol20.iloc[i]
        if pd.isna(v):
            return ("invested" if state == "invested" else "cash"), aux
        if state == "invested" and v > 20:
            aux["vol_off"] = True
        elif aux.get("vol_off") and v < 15:
            aux["vol_off"] = False
        return ("cash" if aux.get("vol_off") else "invested"), aux
    m["C_vol20_15_hysteresis"] = run_wild(closes, nifty_close, sig_c, rbdates, select_top_original, gold_aligned)

    def sig_d(i, state, aux):
        dd = nifty_close.iloc[i] / high252.iloc[i] - 1
        if state == "invested" and dd < -0.08:
            aux["dd_off"] = True
        elif aux.get("dd_off") and dd > -0.03:
            aux["dd_off"] = False
        return ("cash" if aux.get("dd_off") else "invested"), aux
    m["D_drawdown8_3_hysteresis"] = run_wild(closes, nifty_close, sig_d, rbdates, select_top_original, gold_aligned)

    def sig_e(i, state, aux):
        below = nifty_close.iloc[i] < ema.iloc[i]
        key = "streak_below" if below else "streak_above"
        other = "streak_above" if below else "streak_below"
        aux[key] = aux.get(key, 0) + 1
        aux[other] = 0
        if aux["streak_below"] >= 3:
            aux["off"] = True
        if aux["streak_above"] >= 3:
            aux["off"] = False
        return ("cash" if aux.get("off") else "invested"), aux
    m["E_200ema_3day_confirm"] = run_wild(closes, nifty_close, sig_e, rbdates, select_top_original, gold_aligned)

    def sig_f(i, state, aux):
        above = nifty_close.iloc[i] > ema.iloc[i]
        if not above:
            aux["breadth_ok"] = False
            return "cash", aux
        if state == "cash":
            p = closes.iloc[i]; e = stock_ema200.iloc[i]
            frac = ((p > e) & p.notna() & e.notna()).sum() / len(closes.columns)
            aux["breadth_ok"] = bool(frac >= 0.40)
        return ("invested" if aux.get("breadth_ok") else "cash"), aux
    m["F_breadth_40pct_entry_gate"] = run_wild(closes, nifty_close, sig_f, rbdates, select_top_original, gold_aligned)

    gold_ema200 = gold_aligned.ewm(span=200, adjust=False).mean()
    def sig_g(i, state, aux):
        if nifty_close.iloc[i] >= ema.iloc[i]:
            return "invested", aux
        return "cash", aux
    s7 = run_wild(closes, nifty_close, sig_g, rbdates, select_top_original, gold_aligned)
    ret7 = s7.pct_change().fillna(0.0)
    ret_g = gold_aligned.pct_change().fillna(0.0)
    mask_cash = (nifty_close < ema) & (gold_aligned < gold_ema200)
    in_gold = (nifty_close < ema).reindex(s7.index).fillna(False)
    adj_ret = ret7.where(~in_gold, ret_g.mask(mask_cash, 0.0).reindex(s7.index).fillna(0.0))
    m["G_gold_only_when_gold_above_its_200ema"] = (1 + adj_ret).cumprod() * 100.0

    g6 = gold_aligned.pct_change(126); n6 = nifty_close.pct_change(126)
    def sig_h(i, state, aux):
        if nifty_close.iloc[i] >= ema.iloc[i]:
            return "invested", aux
        return "cash", aux
    s8 = run_wild(closes, nifty_close, sig_h, rbdates, select_top_original, gold_aligned)
    ret8 = s8.pct_change().fillna(0.0)
    mask_cash_h = (nifty_close < ema) & (g6 < n6)
    in_gold8 = (nifty_close < ema).reindex(s8.index).fillna(False)
    adj_ret8 = ret8.where(~in_gold8, ret_g.mask(mask_cash_h, 0.0).reindex(s8.index).fillna(0.0))
    m["H_gold_only_when_gold6m_beats_nifty6m"] = (1 + adj_ret8).cumprod() * 100.0

    emit("results_find_wild.json", m)


if __name__ == "__main__":
    main()

"""Report 106 — ATR contraction x the hero (report 98 Max stack A).

Report 104's ATR(14)/ATR(50) filter, isolated from Heikin-Ashi. The question:
does gating entries (or keeping holdings) on volatility contraction improve
the repo's hero?

Run:  py -3 backtest106.py    (writes results105.json)
"""
import json
from datetime import datetime

import numpy as np

import ms_builder
from backtest32 import metrics_only

KEEP_RISING = {"when": "keep", "indicator": "ret_6m", "op": "above", "value": 0}
BASE98 = {"conditions": [KEEP_RISING], "exit_rank": 30}


def cfg98(conditions=None):
    cfg = ms_builder.default_config(**BASE98)
    if conditions is not None:
        cfg["conditions"] = conditions
    return cfg


def cfg93(conditions=None):
    cfg = ms_builder.default_config()
    if conditions is not None:
        cfg["conditions"] = conditions
    return cfg


def buy_atr(op, value):
    return {"when": "buy", "indicator": "atr_ratio", "op": op, "value": value}


def keep_atr(op, value):
    return {"when": "keep", "indicator": "atr_ratio", "op": op, "value": value}


def sharpe_of(series):
    r = series.pct_change().dropna()
    if len(r) < 10 or r.std() == 0:
        return None
    return float(r.mean() / r.std() * np.sqrt(252.0))


def underwater_of(curve):
    out, peak = [], -np.inf
    for d, v in curve:
        peak = max(peak, v)
        out.append([d, round((v / peak - 1.0) * 100.0, 2)])
    return out


def yearly_of(curve):
    last = {}
    for d, v in curve:
        last[d[:4]] = v
    out, prev = {}, curve[0][1]
    for y in sorted(last):
        out[y] = round((last[y] / prev - 1.0) * 100.0, 2)
        prev = last[y]
    return out


def event_stats(run):
    ranks, cash_pct, nhold = [], [], []
    for e in run["events"]:
        if e["trigger"] not in ("scheduled_rebalance", "regime_reentry"):
            continue
        hs = e.get("holdings_after", [])
        rs = [h["rank"] for h in hs if h.get("rank") is not None]
        if rs:
            ranks.append(float(np.mean(rs)))
        nhold.append(len(hs))
        va = e.get("value_after") or 0
        if va:
            cash_pct.append(100.0 * e.get("cash_left", 0) / va)
    return {
        "avg_holdings": round(float(np.mean(nhold)), 2) if nhold else None,
        "avg_rank": round(float(np.mean(ranks)), 1) if ranks else None,
        "avg_cash_pct": round(float(np.mean(cash_pct)), 2) if cash_pct else None,
        "max_cash_pct": round(float(np.max(cash_pct)), 2) if cash_pct else None,
    }


def main():
    print("loading market data ...")
    market = ms_builder.load_market()
    closes = market["closes"]
    dates = closes.index
    common = market["common"]
    print(f"window {dates[0].date()} -> {dates[-1].date()} ({len(dates)} days), "
          f"{len(closes.columns)} symbols")

    print("building ranks + features ...")
    rank_df, fit_df, _score = ms_builder.build_ranks(closes)
    feats = ms_builder.build_features(market)

    # --- diagnostic: how often do momentum names pass each ATR gate?
    rbdates = ms_builder.rebalance_dates_for(cfg98(), dates)
    pass_rates = []
    for label, op, thresh in [("contraction < 0.8", "below", 0.8),
                              ("contraction < 1.0", "below", 1.0),
                              ("expansion > 1.0", "above", 1.0),
                              ("expansion > 1.2", "above", 1.2)]:
        top_rates, all_rates = [], []
        for d in rbdates:
            row = rank_df.loc[d].dropna().sort_values()
            if len(row) < 10:
                continue
            a_top = feats["atr_ratio"].loc[d, row.index[:10]].dropna()
            a_all = feats["atr_ratio"].loc[d, row.index].dropna()
            if len(a_top):
                top_rates.append(((a_top < thresh) if op == "below" else (a_top > thresh)).mean())
            if len(a_all):
                all_rates.append(((a_all < thresh) if op == "below" else (a_all > thresh)).mean())
        pass_rates.append({
            "label": label,
            "top10_pct": round(float(np.mean(top_rates)) * 100.0, 1) if top_rates else None,
            "all_pct": round(float(np.mean(all_rates)) * 100.0, 1) if all_rates else None,
        })
        print(f"  {label:22s} top-10 pass {pass_rates[-1]['top10_pct']:5.1f}%   "
              f"all-ranked pass {pass_rates[-1]['all_pct']:5.1f}%")

    variants = [
        # key, label, group, cfg
        ("hero98", "Hero — report 98 Max stack A", "The hero", cfg98()),

        ("buy05", "Buy ATR<0.5", "Entry gate — contraction",
         cfg98([KEEP_RISING, buy_atr("below", 0.5)])),
        ("buy06", "Buy ATR<0.6", "Entry gate — contraction",
         cfg98([KEEP_RISING, buy_atr("below", 0.6)])),
        ("buy07", "Buy ATR<0.7", "Entry gate — contraction",
         cfg98([KEEP_RISING, buy_atr("below", 0.7)])),
        ("buy08", "Buy ATR<0.8", "Entry gate — contraction",
         cfg98([KEEP_RISING, buy_atr("below", 0.8)])),
        ("buy09", "Buy ATR<0.9", "Entry gate — contraction",
         cfg98([KEEP_RISING, buy_atr("below", 0.9)])),
        ("buy10", "Buy ATR<1.0", "Entry gate — contraction",
         cfg98([KEEP_RISING, buy_atr("below", 1.0)])),
        ("buy11", "Buy ATR<1.1", "Entry gate — contraction",
         cfg98([KEEP_RISING, buy_atr("below", 1.1)])),

        ("buygt10", "Buy ATR>1.0", "Entry gate — expansion",
         cfg98([KEEP_RISING, buy_atr("above", 1.0)])),
        ("buygt12", "Buy ATR>1.2", "Entry gate — expansion",
         cfg98([KEEP_RISING, buy_atr("above", 1.2)])),

        ("keep08", "Keep ATR<0.8", "Review keep — contraction",
         cfg98([KEEP_RISING, keep_atr("below", 0.8)])),
        ("keep10", "Keep ATR<1.0", "Review keep — contraction",
         cfg98([KEEP_RISING, keep_atr("below", 1.0)])),
        ("keep12", "Keep ATR<1.2", "Review keep — contraction",
         cfg98([KEEP_RISING, keep_atr("below", 1.2)])),

        ("buykeep08", "Buy ATR<0.8 + keep ATR<0.8", "Buy + keep",
         cfg98([KEEP_RISING, buy_atr("below", 0.8), keep_atr("below", 0.8)])),
        ("buykeep10", "Buy ATR<1.0 + keep ATR<1.0", "Buy + keep",
         cfg98([KEEP_RISING, buy_atr("below", 1.0), keep_atr("below", 1.0)])),

        ("hero93", "Base hero — report 93 exactly", "Base hero context", cfg93()),
        ("hero93buy08", "Base hero + buy ATR<0.8", "Base hero context",
         cfg93([buy_atr("below", 0.8)])),
        ("hero93buy10", "Base hero + buy ATR<1.0", "Base hero context",
         cfg93([buy_atr("below", 1.0)])),
        ("hero93keep10", "Base hero + keep ATR<1.0", "Base hero context",
         cfg93([keep_atr("below", 1.0)])),
    ]

    out = []
    for key, label, group, cfg in variants:
        print(f"  running {label} ...", flush=True)
        rbd = ms_builder.rebalance_dates_for(cfg, dates)
        run = ms_builder.run_variant(cfg, market, feats, rank_df, fit_df, rbd)
        m = metrics_only(run["series"], common)
        closed = [t for t in run["trades"] if t["status"] == "closed"]
        wins = [t for t in closed if t["pct_return"] > 0]
        curve = m["equity_curve"]
        es = event_stats(run)
        out.append({
            "key": key,
            "label": label,
            "group": group,
            "cagr_pct": round(m["cagr_pct"], 3),
            "net_return_pct": round(m["net_return_pct"], 3),
            "max_drawdown_pct": round(m["max_drawdown_pct"], 3),
            "max_drawdown_peak_date": m["max_drawdown_peak_date"],
            "max_drawdown_trough_date": m["max_drawdown_trough_date"],
            "longest_underwater_days": m["longest_underwater_days"],
            "sharpe": round(sharpe_of(run["series"]), 3),
            "calmar": round(m["cagr_pct"] / abs(m["max_drawdown_pct"]), 3),
            "final_x": round(float(run["series"].iloc[-1] / run["series"].iloc[0]), 3),
            "trades": len(closed),
            "win_pct": round(len(wins) / len(closed) * 100.0, 1) if closed else None,
            "avg_holdings": es["avg_holdings"],
            "avg_rank": es["avg_rank"],
            "avg_cash_pct": es["avg_cash_pct"],
            "max_cash_pct": es["max_cash_pct"],
            "config": ms_builder.describe_config(cfg),
            "equity_curve": curve,
            "underwater": underwater_of(curve),
            "yearly": yearly_of(curve),
        })

    result = {
        "report": 106,
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "start_date": dates[0].strftime("%Y-%m-%d"),
        "end_date": dates[-1].strftime("%Y-%m-%d"),
        "hero": "Report 98 Max stack A — keep-if 6m > 0, exit rank 30, NIFTY 200-EMA + gold",
        "atr_definition": ("ATR(14) / ATR(50) on each stock's high/low/close, simple rolling means "
                           "(report 104's definition); below 1.0 = recent volatility below its "
                           "50-day norm, above 1.0 = expansion."),
        "cost_note": "0.1% cost per side, 0% slippage, fractional units; tax is not modelled.",
        "diagnostics": {
            "review_dates": len(rbdates),
            "pass_rates": pass_rates,
        },
        "variants": {v["label"]: v for v in out},
    }
    with open("results105.json", "w", encoding="utf-8") as f:
        json.dump(ms_builder._json_safe(result), f, indent=1, ensure_ascii=False)
    print(f"\nwrote results105.json ({len(out)} variants)")

    hero = out[0]
    print(f"\nhero: {hero['cagr_pct']:.2f}% CAGR / {hero['max_drawdown_pct']:.2f}% DD / "
          f"Sharpe {hero['sharpe']:.2f} / {hero['trades']} trades")
    for v in out[1:]:
        print(f"  {v['label']:34s} {v['cagr_pct']:6.2f}%  "
              f"{v['cagr_pct'] - hero['cagr_pct']:+6.2f}pp  DD {v['max_drawdown_pct']:6.2f}%  "
              f"Sharpe {v['sharpe']:.2f}  rank {v['avg_rank']}  cash {v['avg_cash_pct']}%")


if __name__ == "__main__":
    main()

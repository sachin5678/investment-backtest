"""Builds 105_ha_x_hero.html from results104.json."""
import html
import json

from svg_charts import COL, area_underwater_chart, line_chart

with open("results104.json", encoding="utf-8") as f:
    R = json.load(f)

TAILWIND_CDN = '<script src="https://cdn.tailwindcss.com"></script>'
PANEL = "bg-[#0F2630] border border-[#1E3A45] rounded-2xl p-6"
PANEL_TIGHT = "bg-[#0F2630] border border-[#1E3A45] rounded-2xl p-5"
MUTED = "text-[#7E97A0] text-[12.5px] leading-snug"
WHAT_THIS_SHOWS = "text-[#9FB4BB] text-[13px] italic mb-3"

PILL_BASE = "inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full whitespace-nowrap"
PILL_POS = PILL_BASE + " bg-[#37F083]/15 text-[#37F083] border border-[#37F083]/40"
PILL_NEG = PILL_BASE + " bg-[#F2643C]/15 text-[#F2643C] border border-[#F2643C]/40"
PILL_ASSUM = PILL_BASE + " bg-[#F2B03C]/15 text-[#F2B03C] border border-[#F2B03C]/40"
PILL_NEUTRAL = PILL_BASE + " bg-[#7E97A0]/15 text-[#7E97A0] border border-[#7E97A0]/40"
KIND_COLOR = {"positive": "#37F083", "negative": "#F2643C", "neutral": "#E6EDF0", "assumption": "#F2B03C"}

GROUP_ORDER = ["The hero", "HA replaces the regime", "HA gates the stock picks",
               "HA as an asymmetric overlay", "Base hero context"]


def pill(text, kind="assumption"):
    cls = {"positive": PILL_POS, "negative": PILL_NEG, "assumption": PILL_ASSUM, "neutral": PILL_NEUTRAL}[kind]
    dot = {"positive": "●", "negative": "●", "assumption": "▲", "neutral": "●"}[kind]
    return f'<span class="{cls}">{dot} {text}</span>'


def esc(s):
    return html.escape(str(s))


def pct(v, decimals=1, signed=True):
    if v is None:
        return "—"
    s = "+" if (signed and v > 0) else ""
    return f"{s}{v:,.{decimals}f}%"


def num(v, decimals=2):
    return "—" if v is None else f"{v:,.{decimals}f}"


def tone(v):
    if v is None:
        return "neutral"
    return "positive" if v > 0 else ("negative" if v < 0 else "neutral")


def base_style():
    return """
    <style>
      html,body{background:#08171E;color:#E6EDF0;font-family:'Inter',ui-sans-serif,system-ui,-apple-system,sans-serif;}
      .mono{font-family:'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,monospace;}
      table.data-table{width:100%;border-collapse:collapse;font-size:13px;}
      table.data-table th{text-align:right;color:#7E97A0;font-weight:600;padding:8px 12px;border-bottom:1px solid #1E3A45;background:#132B36;font-size:11px;letter-spacing:0.03em;text-transform:uppercase;}
      table.data-table th:first-child, table.data-table td:first-child{text-align:left;}
      table.data-table td{text-align:right;padding:7px 12px;border-bottom:1px solid #16303a;white-space:nowrap;transition:background-color 120ms ease;}
      table.data-table tbody tr:nth-child(even) td{background:rgba(255,255,255,0.015);}
      table.data-table tbody tr:hover td{background:rgba(55,240,131,0.06);}
      table.data-table tr.hi td{background:rgba(242,176,60,0.08);}
      table.data-table tr.best td{background:rgba(55,240,131,0.07);}
      table.data-table tr.group td{background:#132B36;color:#9FB4BB;font-size:10.5px;text-transform:uppercase;letter-spacing:0.07em;font-weight:700;padding-top:14px;padding-bottom:8px;border-bottom:1px solid #1E3A45;}
      .kpi-val{font-size:23px;font-weight:700;letter-spacing:-0.01em;}
      tr.real-bench td{color:#9FB4BB;}
    </style>
    """


def kpi_card(label, definition, cols):
    col_html = []
    for col_label, value_str, kind in cols:
        color = KIND_COLOR[kind]
        col_html.append(
            f'<div class="flex-1 min-w-[110px]"><div class="text-[11px] text-[#7E97A0] mb-1 uppercase tracking-wide">{esc(col_label)}</div>'
            f'<div class="kpi-val mono" style="color:{color}">{value_str}</div></div>'
        )
    return f"""
    <div class="{PANEL_TIGHT}">
      <div class="text-[13px] font-semibold text-[#E6EDF0] mb-1">{esc(label)}</div>
      <div class="{MUTED} mb-3">{esc(definition)}</div>
      <div class="flex gap-3 flex-wrap">{''.join(col_html)}</div>
    </div>
    """


def monthly_points(points):
    """Last observation per calendar month — keeps the chart readable
    without changing the shape of a 17-year daily series."""
    last = {}
    for d, v in points:
        last[d[:7]] = [d, v]
    return [last[k] for k in sorted(last)]


def build():
    vals = (list(R["variants"].values()) if isinstance(R["variants"], dict) else R["variants"])
    V = {v["key"]: v for v in vals}
    hero = V["hero98"]
    hero93 = V["hero93"]
    best = max((v for v in vals if v["key"] != "hero98" and v["group"] != "Base hero context"),
               key=lambda v: v["cagr_pct"])
    regime = V["ha_regime"]
    regime_strict = V["ha_regime_strict"]
    buy = V["ha_buy_above"]
    atr = V["ha_buy_atr"]
    keep = V["ha_keep"]
    keep_only = V["ha_keep_only"]
    reentry = V["ha_reentry"]
    early = V["ha_early"]
    half = V["ha_half"]

    d_best = best["cagr_pct"] - hero["cagr_pct"]
    d_regime = regime["cagr_pct"] - hero["cagr_pct"]
    d_atr = atr["cagr_pct"] - hero["cagr_pct"]
    d_early = early["cagr_pct"] - hero["cagr_pct"]
    dd_best = best["max_drawdown_pct"] - hero["max_drawdown_pct"]
    dd_regime = regime["max_drawdown_pct"] - hero["max_drawdown_pct"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Smoothed Heikin-Ashi × the Hero — Does the Indicator Improve the Max Strategy?</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Report 104's double-smoothed HA system bolted onto report 98's Max stack A (Midcap 150 Momentum 10, 200-EMA + gold, keep-if 6m &gt; 0, exit rank 30). Sixteen combinations: HA as the regime, as an entry gate, as a review exit, and as a daily overlay. The answer is no — every version gives up return, and most give up drawdown too.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(R['start_date'])}–{esc(R['end_date'])}<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2643C]">
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          {pill('no combination improves the hero — the least-bad one gives up 1.5pp of CAGR and 1.8pp of drawdown', 'negative')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          The untouched hero compounds at <span class="font-semibold">{pct(hero['cagr_pct'])}</span> with a
          {pct(hero['max_drawdown_pct'], 1, signed=False)} max drawdown, Sharpe {num(hero['sharpe'])} and
          {hero['trades']:,} closed trades. The best HA variant — use HA only as a review-level keep filter —
          returns {pct(best['cagr_pct'])} ({d_best:+.2f}pp) with a {pct(best['max_drawdown_pct'], 1, signed=False)}
          drawdown ({dd_best:+.2f}pp) and Sharpe {num(best['sharpe'])}. Nothing is better on any axis.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The damage scales with how much of the hero the indicator is allowed to touch. Replacing the 200-EMA
          regime with index HA costs {d_regime:+.2f}pp of CAGR and deepens the drawdown by {abs(dd_regime):.2f}pp.
          An HA entry gate costs {buy['cagr_pct'] - hero['cagr_pct']:+.2f}pp and deepens the drawdown by
          {abs(buy['max_drawdown_pct'] - hero['max_drawdown_pct']):.2f}pp. Adding the ATR contraction filter costs
          {d_atr:+.2f}pp. A daily HA early-exit overlay makes {early['trades']:,} trades instead of {hero['trades']:,}
          and costs {d_early:+.2f}pp.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("Return", "CAGR over the identical 2009–2026 window; 0.1% cost per side.",
                 [("Hero 98", pct(hero["cagr_pct"]), "positive"),
                  (f"Best HA — {best['label'].split('—')[0].strip()}", pct(best["cagr_pct"], signed=False), "negative"),
                  ("Delta", f"{d_best:+.2f}pp", "negative"),
                  ("Regime swap", pct(regime["cagr_pct"], signed=False), "negative")]),
        kpi_card("Drawdown", "Largest peak-to-trough decline over the identical window.",
                 [("Hero 98", pct(hero["max_drawdown_pct"], 1, signed=False), "positive"),
                  ("Best HA", pct(best["max_drawdown_pct"], 1, signed=False), "negative"),
                  ("HA regime", pct(regime["max_drawdown_pct"], 1, signed=False), "negative"),
                  ("HA + ATR", pct(atr["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("Risk-adjusted and turnover", "Sharpe uses daily returns; trades are closed round trips.",
                 [("Hero Sharpe", num(hero["sharpe"]), "positive"),
                  ("Best HA Sharpe", num(best["sharpe"]), "negative"),
                  ("Hero trades", f"{hero['trades']:,}", "neutral"),
                  ("Early-exit trades", f"{early['trades']:,}", "negative")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-1 gap-4 mt-6">{"".join(kpis)}</div>'

    # ---- full matrix ----
    rows_html = []
    for group in GROUP_ORDER:
        rows_html.append(f'<tr class="group"><td colspan="8">{esc(group)}</td></tr>')
        for v in [x for x in vals if x["group"] == group]:
            cls = []
            if v["key"] == "hero98":
                cls.append("hi")
            if v["key"] == best["key"]:
                cls.append("best")
            klass = f' class="{" ".join(cls)}"' if cls else ""
            delta = v["cagr_pct"] - hero["cagr_pct"]
            delta_s = "—" if v["key"] == "hero98" else f"{delta:+.2f}pp"
            rows_html.append(
                f'<tr{klass}><td>{esc(v["label"])}</td>'
                f'<td><strong>{pct(v["cagr_pct"])}</strong></td>'
                f'<td style="color:{"#37F083" if delta > 0 else ("#F2643C" if delta < 0 else "#7E97A0")}">{delta_s}</td>'
                f'<td>{pct(v["max_drawdown_pct"], 1, signed=False)}</td>'
                f'<td>{num(v["sharpe"])}</td>'
                f'<td>{v["trades"]:,}</td>'
                f'<td>{pct(v["win_pct"], 1, signed=False)}</td>'
                f'<td>{v["regime_exits"]:,}</td></tr>'
            )

    matrix = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">The full matrix — sixteen ways to combine them</h3>
        {pill('hero row in amber; least-bad HA row in green', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — each row changes one layer of the hero: the market regime, the stock gate at a review, or a daily overlay. The hero is the top row; every HA row is measured against it. Δ is CAGR versus the hero.</p>
      <div class="overflow-x-auto">
      <table class="data-table">
        <thead><tr><th>Variant</th><th>CAGR</th><th>Δ vs hero</th><th>Max DD</th><th>Sharpe</th><th>Trades</th><th>Win rate</th><th>Regime exits</th></tr></thead>
        <tbody>{''.join(rows_html)}</tbody>
      </table>
      </div>
      <p class="{MUTED} mt-3">All rows: midcap150, Jun/Dec reviews, top 10, 0.1% cost per side, 0% slippage, fractional units, gold park when the regime is off. Tax is not modelled in this lab; the HA variants trade more, so adding it would widen the gap, not close it.</p>
    </div>
    """

    # ---- charts ----
    eq_series = [
        {"name": "Hero 98 — Max stack A", "color": COL["positive"], "points": monthly_points(hero["equity_curve"])},
        {"name": f"Best HA — {best['label']}", "color": COL["assumption"], "points": monthly_points(best["equity_curve"])},
        {"name": "HA replaces the 200-EMA", "color": COL["muted"], "points": monthly_points(regime["equity_curve"])},
        {"name": "HA buy + ATR < 0.8", "color": COL["negative"], "points": monthly_points(atr["equity_curve"])},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=430, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_105")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — the hero vs the three HA designs</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the hero ends at {num(hero['final_x'], 0)}×; the best HA variant at {num(best['final_x'], 0)}×; the regime swap at {num(regime['final_x'], 0)}×; the ATR-filtered entry at {num(atr['final_x'], 0)}×. The gap opens early and never closes: HA is not adding a timing edge, it is removing exposure to the names that compound.</p>
      <div class="flex items-center mb-2">{eq_legend}</div>
      {eq_svg}
    </div>
    """

    dd_series = [
        {"name": "Hero 98 — Max stack A", "color": COL["positive"], "points": monthly_points(hero["underwater"])},
        {"name": "HA replaces the 200-EMA", "color": COL["muted"], "points": monthly_points(regime["underwater"])},
        {"name": f"Best HA — {best['label']}", "color": COL["assumption"], "points": monthly_points(best["underwater"])},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=230, chart_id="dd_105")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown — the HA versions do not even win here</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the regime swap (grey) is deeper and stays underwater longer than the hero (green). The least-bad HA variant (amber) is also slightly deeper. The one thing HA was supposed to add — faster risk-off — is exactly what the slow 200-EMA already does better.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    # ---- why ----
    why = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Why every combination loses</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the failure is structural, not a tuning problem. Four mechanisms explain the whole table.</p>
      <ol class="list-decimal pl-5 space-y-3 text-[13.5px] text-[#C9D6DA] leading-relaxed">
        <li><strong class="text-[#E6EDF0]">Frequency mismatch.</strong> The hero decides twice a year on 6- and 12-month momentum. A smoothed 10-day HA candle flips in days. At a June or December review, the HA colour is close to noise relative to the signal that picked the stock; gating a 6-month pick on a 10-day state removes strong names without adding information. The best HA variant still gives up {abs(d_best):.2f}pp.</li>
        <li><strong class="text-[#E6EDF0]">The ATR contraction filter is the most destructive.</strong> Momentum leaders are volatile by construction. Requiring ATR(14)/ATR(50) &lt; 0.8 selects the quiet names inside the momentum top 10: CAGR collapses to {pct(atr['cagr_pct'])} and the drawdown deepens to {pct(atr['max_drawdown_pct'], 1, signed=False)}. Report 104 found ATR useful as an entry-timing filter for a broad HA stock system; it is not a stock-selection filter for a concentrated momentum portfolio.</li>
        <li><strong class="text-[#E6EDF0]">A faster regime is not a better regime.</strong> Index HA raises regime exits from {hero['regime_exits']} to {regime['regime_exits']} and cuts CAGR by {abs(d_regime):.2f}pp; the strict version (green plus close above the HA open) is worse still — {regime_strict['regime_exits']} exits and {pct(regime_strict['cagr_pct'])} CAGR. The 200-EMA's slowness is a feature: it ignores bear-market rallies instead of trading them.</li>
        <li><strong class="text-[#E6EDF0]">Daily HA exits are a cost machine.</strong> The early-exit overlay makes {early['trades']:,} trades versus {hero['trades']:,}; the half-de-risk version makes {half['trades']:,}. At 0.1% per side the friction alone compounds to a double-digit drag, and the timing benefit never covers it. The re-entry gate is the mildest overlay tested, and it still costs {abs(reentry['cagr_pct'] - hero['cagr_pct']):.2f}pp with a deeper drawdown.</li>
      </ol>
    </div>
    """

    # ---- what it does not say ----
    honest = f"""
    <div class="{PANEL} mt-6 border-l-4 border-l-[#F2B03C]">
      <div class="flex items-center gap-2 mb-3 flex-wrap">
        {pill('this is a statement about the combination, not about the indicator', 'assumption')}
      </div>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        HA is not a bad indicator. Report 104 shows the standalone system on the same Midcap 150 cache beating an
        equal-weight basket over 2016–2026: {pct(27.8, signed=False)} CAGR versus {pct(20.6, signed=False)}, with a
        {pct(32.6, signed=False)} drawdown versus {pct(40.8, signed=False)}, Sharpe 1.57 versus 1.19. That edge is real but 2020-dependent
        (ex-2020 it lags the basket), and it comes from selecting and timing individual stocks out of a broad
        universe — a different job from overlaying a concentrated 10-stock, twice-a-year momentum book.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        The hero is also not fragile. It survives every overlay tested; the worst still compounds at
        {pct(atr['cagr_pct'])}. The point is that the untouched hero is better, not that the combination blows up.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        Caveats: Midcap 150 is today's constituent list applied backwards, so all absolute CAGRs are
        survivorship-inflated; this lab does not model tax; and the window is 2009–2026. Those caveats apply to
        every row, so the ranking is robust even though the absolute numbers are optimistic.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mt-3">
        <strong class="text-[#E6EDF0]">Scope.</strong> This lab tests the HA signal as a market regime, a stock
        gate at the review, and a daily index overlay. It does not bolt the standalone system's per-stock 12% stop
        and next-open red-flip exit onto the hero: the engine's daily sell rule parks proceeds until the next
        review, so that test would be dominated by a mechanical cash drag. The review-level HA keep filter is the
        closest fair test, and it already gives up {abs(d_best):.2f}pp. A per-stock stop is a separate risk rule,
        not the HA signal, and deserves its own lab.
      </p>
    </div>
    """

    bottom = f"""
    <div class="px-10 py-6">
      <div class="{PANEL} border-2 border-[#37F083]">
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          {pill('keep them separate — the hero stays the hero, HA stays report 104', 'positive')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          If you want HA exposure, run it as a separate sleeve with its own capital, not as a filter on the
          momentum book. The two systems have different horizons, different turnover and different jobs; combining
          them at the same decision point subtracts from both.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          For the hero, report 98's Max stack A remains the best configuration in this repo. For HA, report 104 is
          the implementation to use. The correct combination is a portfolio of the two strategies, not an overlay
          of one on the other.
        </p>
      </div>
    </div>
    """

    method = f"""
    <div class="{PANEL_TIGHT} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Method and reproduction</h3>
      <p class="{MUTED} mb-2">Hero: report 98 Max stack A — midcap150, top 10, Jun/Dec reviews, keep-if 6m &gt; 0, exit rank 30, NIFTY 50 200-EMA regime with 100% GOLDBEES park, 0.1% cost per side.</p>
      <p class="{MUTED} mb-2">HA: report 104's smoothed Heikin-Ashi — EMA(10) applied twice to O/H/L/C; green when HA close &gt; HA open; strict adds price &gt; HA open; ATR contraction is ATR(14)/ATR(50) &lt; 0.8. Index HA uses the same definition on NIFTY 50.</p>
      <p class="{MUTED} mb-3">Every variant runs through the same <span class="mono">ms_builder.py</span> engine used by reports 93–98; the hero regression gate is re-run after the HA additions and still reproduces report 93 exactly. Window {esc(R['start_date'])}–{esc(R['end_date'])}.</p>
      <pre class="mono text-[12px] text-[#C9D6DA] bg-[#08171E] border border-[#1E3A45] rounded-xl p-4 overflow-x-auto">py -3 backtest105.py      # writes results104.json
py -3 build_html105.py    # writes 105_ha_x_hero.html
py -3 check_builder_regression.py   # hero must still match report 93</pre>
    </div>
    """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>105 — Smoothed Heikin-Ashi × the Hero</title>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="min-h-screen">
{header}
{lead}
<div class="px-10">{kpi_grid}</div>
<div class="px-10">{matrix}{eq_panel}{dd_panel}{why}{honest}<div class="py-6">{method}</div></div>
{bottom}
</body>
</html>"""


if __name__ == "__main__":
    out = "105_ha_x_hero.html"
    with open(out, "w", encoding="utf-8") as f:
        f.write(build())
    print(f"wrote {out}")

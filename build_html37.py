"""Builds 37_midcap_momentum10_frontloaded_weights.html from
results36.json. Same self-contained contract, smooth Catmull-Rom charts,
dark palette as every other report."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results36.json") as f:
    R = json.load(f)

TAILWIND_CDN = '<script src="https://cdn.tailwindcss.com"></script>'
PANEL = "bg-[#0F2630] border border-[#1E3A45] rounded-2xl p-6"
PANEL_TIGHT = "bg-[#0F2630] border border-[#1E3A45] rounded-2xl p-5"
MUTED = "text-[#7E97A0] text-[12.5px] leading-snug"
WHAT_THIS_SHOWS = "text-[#9FB4BB] text-[13px] italic mb-3"

PILL_BASE = "inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full whitespace-nowrap"
PILL_POS = PILL_BASE + " bg-[#37F083]/15 text-[#37F083] border border-[#37F083]/40"
PILL_NEG = PILL_BASE + " bg-[#F2643C]/15 text-[#F2643C] border border-[#F2643C]/40"
PILL_ASSUM = PILL_BASE + ' bg-[#F2B03C]/15 text-[#F2B03C] border border-[#F2B03C]/40'
PILL_NEUTRAL = PILL_BASE + " bg-[#7E97A0]/15 text-[#7E97A0] border border-[#7E97A0]/40"
KIND_COLOR = {"positive": "#37F083", "negative": "#F2643C", "neutral": "#E6EDF0", "assumption": "#F2B03C"}
ACCENT_2 = "#8B5CF6"


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


def win_loss_kind(v):
    if v is None:
        return "neutral"
    return "positive" if v > 0 else ("negative" if v < 0 else "neutral")


def base_style():
    return """
    <style>
      html,body{background:#08171E;color:#E6EDF0;font-family:'Inter',ui-sans-serif,system-ui,-apple-system,sans-serif;}
      .mono{font-family:'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,monospace;}
      table.data-table{width:100%;border-collapse:collapse;font-size:13px;}
      table.data-table th{text-align:right;color:#7E97A0;font-weight:600;padding:8px 12px;border-bottom:1px solid #1E3A45;position:sticky;top:0;background:#132B36;font-size:11px;letter-spacing:0.03em;text-transform:uppercase;}
      table.data-table th:first-child, table.data-table td:first-child{text-align:left;}
      table.data-table td{text-align:right;padding:7px 12px;border-bottom:1px solid #16303a;white-space:nowrap;transition:background-color 120ms ease;}
      table.data-table tbody tr:nth-child(even) td{background:rgba(255,255,255,0.015);}
      table.data-table tbody tr:hover td{background:rgba(55,240,131,0.06);}
      .kpi-val{font-size:24px;font-weight:700;letter-spacing:-0.01em;}
      tr.real-bench td{color:#9FB4BB;}
    </style>
    """


def kpi_card(label, definition, cols):
    col_html = []
    for col_label, value_str, kind in cols:
        color = KIND_COLOR[kind]
        col_html.append(
            f'<div class="flex-1 min-w-[120px]"><div class="text-[11px] text-[#7E97A0] mb-1 uppercase tracking-wide">{esc(col_label)}</div>'
            f'<div class="kpi-val mono" style="color:{color}">{value_str}</div></div>'
        )
    return f"""
    <div class="{PANEL_TIGHT}">
      <div class="text-[13px] font-semibold text-[#E6EDF0] mb-1">{esc(label)}</div>
      <div class="{MUTED} mb-3">{definition}</div>
      <div class="flex gap-4 flex-wrap">{''.join(col_html)}</div>
    </div>
    """


def build():
    orig, fl, nif = R["original"], R["frontloaded"], R["nifty"]
    w = R["weights"]
    sym = R["currency_symbol"]

    cagr_gap = orig["cagr_pct"] - fl["cagr_pct"]
    dd_improvement = fl["max_drawdown_pct"] - orig["max_drawdown_pct"]  # positive = shallower

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap Momentum 10 — Front-Loaded 3m/6m/12m Weighted Momentum</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Same top-10, equal-weight, June/December strategy — but the momentum score now blends THREE windows (3-month, 6-month, 12-month risk-adjusted return) instead of two, weighted {w['w3m']:.0f}%/{w['w6m']:.0f}%/{w['w12m']:.0f}% toward the most recent window instead of the original's equal 50/50 split between 6m and 12m.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(R['start_date'])}–{esc(R['end_date'])} · {R['num_rebalances']} rebalances<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2B03C]">
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          {pill(f"{R['avg_overlap_pct']:.1f}% average pick overlap with the original", 'neutral')}
          {pill('a genuine risk/return trade-off, not a straight downgrade', 'assumption')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Unlike most other variants tested in this comparison series, front-loading recent momentum doesn't just move CAGR and drawdown in the
          same direction — it trades one for the other. CAGR comes in at {pct(fl['cagr_pct'])} versus the original's {pct(orig['cagr_pct'])}
          ({pct(cagr_gap,1,signed=False)} points lower), but max drawdown is actually SHALLOWER at
          {pct(fl['max_drawdown_pct'],1,signed=False)} versus {pct(orig['max_drawdown_pct'],1,signed=False)}
          ({pct(dd_improvement,1,signed=False)} points better).
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The mechanism is intuitive: weighting the most recent 3 months at 50% makes the score react faster to a deteriorating trend (cutting
          exposure to a stock that's started rolling over sooner than a 12-month-anchored score would), which cushions the worst drawdowns a
          little — but it also means the score can chase a short-lived 3-month spike that later fades, giving up some of the longer-horizon
          trend-persistence edge the equal-weighted 6m/12m blend was capturing. Whether that trade-off is worth it depends on how much you value
          a shallower drawdown against a lower total return — this report doesn't declare a winner, just shows the trade honestly.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR", "Compound annual growth rate, identical window for all three.",
                  [("Original (50/50 6m/12m)", pct(orig["cagr_pct"]), win_loss_kind(orig["cagr_pct"])),
                   (f"Front-loaded ({w['w3m']:.0f}/{w['w6m']:.0f}/{w['w12m']:.0f})", pct(fl["cagr_pct"]), win_loss_kind(fl["cagr_pct"])),
                   ("NIFTY 50", pct(nif["cagr_pct"]), win_loss_kind(nif["cagr_pct"]))]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline over the same window.",
                  [("Original (50/50 6m/12m)", pct(orig["max_drawdown_pct"], 1, signed=False), "negative"),
                   (f"Front-loaded ({w['w3m']:.0f}/{w['w6m']:.0f}/{w['w12m']:.0f})", pct(fl["max_drawdown_pct"], 1, signed=False), "positive"),
                   ("NIFTY 50", pct(nif["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("Net return", f"{esc(R['start_date'])} to {esc(R['end_date'])}, base 100.",
                  [("Original (50/50 6m/12m)", pct(orig["net_return_pct"]), win_loss_kind(orig["net_return_pct"])),
                   ("Front-loaded", pct(fl["net_return_pct"]), win_loss_kind(fl["net_return_pct"]))]),
        kpi_card("How different are the actual picks", "Average % of each rebalance's top 10 that's the SAME stock under both formulas.",
                  [("Avg overlap", f"{R['avg_overlap_pct']:.1f}%", "assumption"),
                   ("Rebalances compared", f"{R['num_overlap_rebalances']}", "neutral")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, v, cls=""):
        c = f' class="{cls}"' if cls else ""
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(v['net_return_pct'])}</td><td>{pct(v['cagr_pct'])}</td>
        <td>{pct(v['max_drawdown_pct'],1,signed=False)}</td><td>{v['longest_underwater_days']:,}d</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">All three, side by side</h3>
        {pill('grey row = real benchmark, not a reconstruction', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — both formulas against the real NIFTY 50 index, over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("Original formula (equal-weighted 6m/12m)", orig)}
          {row(f"Front-loaded formula ({w['w3m']:.0f}% 3m / {w['w6m']:.0f}% 6m / {w['w12m']:.0f}% 12m)", fl)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "Original (equal-weighted)", "color": COL["positive"], "points": orig["equity_curve"]},
        {"name": "Front-loaded (50/30/20)", "color": ACCENT_2, "points": fl["equity_curve"], "dash": True},
        {"name": "NIFTY 50", "color": COL["text"], "points": nif["equity_curve"], "dash": True},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_37")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how {sym}100 invested at the start of the window grew under each formula, linear axis, not log-scaled. The two momentum lines track closely, with the original pulling modestly ahead over the full 18 years.</p>
      <div class="flex items-center mb-2">{eq_legend}</div>
      {eq_svg}
    </div>
    """

    def dd_points(equity):
        out, peak = [], None
        for d, v in equity:
            peak = v if peak is None else max(peak, v)
            out.append([d, (v / peak - 1.0) * 100.0])
        return out

    dd_series = [
        {"name": "Original (equal-weighted)", "color": COL["positive"], "points": dd_points(orig["equity_curve"])},
        {"name": "Front-loaded (50/30/20)", "color": ACCENT_2, "points": dd_points(fl["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=220, chart_id="dd_37")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the front-loaded formula's drawdown ({pct(fl['max_drawdown_pct'],1,signed=False)}) is visibly shallower than the original's ({pct(orig['max_drawdown_pct'],1,signed=False)}) at multiple points — the faster-reacting recent-momentum weighting genuinely does cushion some drawdowns, not just on average.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    def sel_row(s):
        return f"""<tr><td>{esc(s['date'])}</td><td style="text-align:left">{esc(', '.join(s['tickers']))}</td></tr>"""

    selections_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Sample rebalances — same dates, partly different picks</h3>
        {pill('first 3 and last 3 of ' + str(R['num_rebalances']) + ' shown for each', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the actual top-10 selected by each formula at the same rebalance dates. With {R['avg_overlap_pct']:.1f}% average overlap, expect roughly half of each row to differ.</p>
      <div class="mb-4">
        <div class="text-[13px] font-semibold text-[#C9D6DA] mb-2">Original formula (equal-weighted 6m/12m)</div>
        <table class="data-table"><thead><tr><th>Date</th><th style="text-align:left">Top 10 selected</th></tr></thead>
        <tbody>{''.join(sel_row(s) for s in R['original']['selections_sample'])}</tbody></table>
      </div>
      <div>
        <div class="text-[13px] font-semibold text-[#C9D6DA] mb-2">Front-loaded formula (50/30/20)</div>
        <table class="data-table"><thead><tr><th>Date</th><th style="text-align:left">Top 10 selected</th></tr></thead>
        <tbody>{''.join(sel_row(s) for s in R['frontloaded']['selections_sample'])}</tbody></table>
      </div>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why this one is a genuine trade-off, not a clean win or loss</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Every other variant in this comparison series (reports 33, 34, 36) moved CAGR and max drawdown in the SAME direction — better or worse
        on both, or a near-tie on both. This one splits: {pct(cagr_gap,1,signed=False)} points lower CAGR, but
        {pct(dd_improvement,1,signed=False)} points shallower drawdown. That's exactly what you'd expect from making the score react faster to
        recent price action: a 3-month-heavy score notices a stock rolling over sooner than a formula anchored more to the past 12 months, so it
        drops that stock from the top 10 a bit earlier in a real decline — cushioning the worst drawdowns — but it also means the score gives
        real weight to short 3-month moves that sometimes reverse before the 6- and 12-month windows would have confirmed the trend, costing some
        of the longer-run compounding.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        Neither number is "wrong" — this is the standard responsiveness-vs-persistence trade-off in momentum investing, showing up cleanly in a
        real backtest instead of just as a theoretical concern. Whether {pct(cagr_gap,1,signed=False)} points of CAGR is worth
        {pct(dd_improvement,1,signed=False)} points of shallower drawdown is a preference call this report doesn't make on your behalf.
      </p>
    </div>
    """

    limitations = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2">
        <h3 class="text-base font-bold text-[#E6EDF0]">Limitations</h3>
        {pill("read before trusting any number above", "assumption")}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every simplification behind this backtest.</p>
      <ul class="text-[13px] text-[#C9D6DA] list-disc pl-5 leading-relaxed">
        <li class="mb-1.5">Only ONE weighting scheme ({w['w3m']:.0f}%/{w['w6m']:.0f}%/{w['w12m']:.0f}%) was tested — the user-specified weights, not a search over alternatives; a different split (e.g. 40/40/20, or 60/25/15) could land anywhere between the original and this result, or outside that range entirely.</li>
        <li class="mb-1.5">All three windows still divide by the SAME trailing-1-year volatility as the risk-adjustment denominator — a genuinely "3-month-native" version might use 3-month volatility for the 3-month leg instead, which was not tested here.</li>
        <li class="mb-1.5">Today's fixed NIFTY Midcap 150 constituent list is applied retroactively across the whole window for both formulas equally (survivorship bias) — same disclosed approximation as every other reconstruction here.</li>
        <li class="mb-1.5">Zero transaction costs, slippage, or taxes modeled — same as reports 11-19/24-36's frictionless numbers (see report 32 for what real Kotak Neo charges do to a similar strategy).</li>
        <li class="mb-1.5">Equal weighting (not free-float market-cap x momentum score) and no F&O-eligibility screen, same as every other reconstruction in this project.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modeled for any holding. This is a single, fixed 18-year historical path — a choppier or trendier market regime could shift this specific trade-off in either direction.</li>
      </ul>
    </div>
    """

    body = f"""
    {header}
    {lead_disclosure}
    <div class="px-10 py-6">
      {kpi_grid}
      {full_table}
      {eq_panel}
      {dd_panel}
      {selections_panel}
      {honesty_note}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Midcap Momentum 10 — Front-Loaded 3m/6m/12m Weighted Momentum</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("37_midcap_momentum10_frontloaded_weights.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 37_midcap_momentum10_frontloaded_weights.html")

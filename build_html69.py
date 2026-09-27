"""Builds 69_smallcap250_momentum10_smooth_exposure_hedged.html from results68.json."""
import json
import html
from svg_charts import line_chart, COL

with open("results68.json") as f:
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
HEDGE_COLORS = {"cash": "#7E97A0", "gold": "#F2B03C", "liquid": "#6AE4FF"}
HEDGE_LABELS = {"cash": "Cash (0%)", "gold": "Gold (GOLDBEES.NS)", "liquid": "Liquid fund (assumed 6% p.a.)"}


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
      tr.highlight td{background:rgba(55,240,131,0.06);}
    </style>
    """


def kpi_card(label, definition, cols):
    col_html = []
    for col_label, value_str, kind in cols:
        color = KIND_COLOR[kind]
        col_html.append(
            f'<div class="flex-1 min-w-[130px]"><div class="text-[11px] text-[#7E97A0] mb-1 uppercase tracking-wide">{esc(col_label)}</div>'
            f'<div class="kpi-val mono" style="color:{color}">{value_str}</div></div>'
        )
    return f"""
    <div class="{PANEL_TIGHT}">
      <div class="text-[13px] font-semibold text-[#E6EDF0] mb-1">{esc(label)}</div>
      <div class="{MUTED} mb-3">{definition}</div>
      <div class="flex gap-3 flex-wrap">{''.join(col_html)}</div>
    </div>
    """


def build():
    orig, nif, gb = R["original"], R["nifty"], R["gold_benchmark"]
    bands = R["bands"]
    by_band = {b["band_pct"]: b for b in bands}
    b15 = by_band[15.0]
    sym = R["currency_symbol"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Smallcap250 Momentum 10 — Smooth Exposure, Combined With Gold and a Liquid Fund</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Report 68 combined the smooth exposure ramp with gold and a liquid-fund yield assumption on Midcap150, where gold won outright. This applies the identical mechanics to report 16/29's Smallcap250 Momentum 10 config — and finds a genuine trade-off instead.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(R['start_date'])}–{esc(R['end_date'])}<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2B03C]">
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          {pill('gold wins on CAGR but LOSES on drawdown here — the opposite of Midcap150', 'assumption')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          At the 15% band, gold gives the best CAGR of the three sleeves — <span class="font-semibold">{pct(b15['gold']['cagr_pct'])}</span>
          vs. {pct(b15['cash']['cagr_pct'])} (cash) and {pct(b15['liquid']['cagr_pct'])} (liquid fund) — but its drawdown is
          the WORST of the three: <span class="font-semibold">{pct(b15['gold']['max_drawdown_pct'],1,signed=False)}</span>
          vs. {pct(b15['cash']['max_drawdown_pct'],1,signed=False)} (cash) and {pct(b15['liquid']['max_drawdown_pct'],1,signed=False)}
          (liquid fund). Unlike Midcap150 (report 68), where gold was a clean upgrade on both axes, here it's a genuine trade-off.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The liquid-fund assumption is the cleanest performer here: it slightly beats cash on CAGR while ALSO giving the
          shallowest drawdown of all three sleeves — the safest, least eventful choice, not the highest-conviction one.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR at the 15% band", "Compound annual growth rate, identical window for all three sleeve choices.",
                  [("Cash (0%)", pct(b15["cash"]["cagr_pct"]), "neutral"),
                   ("Liquid fund (assumed 6%)", pct(b15["liquid"]["cagr_pct"]), "positive"),
                   ("Gold (GOLDBEES.NS)", pct(b15["gold"]["cagr_pct"]), "positive"),
                   ("No filter (100% always)", pct(orig["cagr_pct"]), "neutral")]),
        kpi_card("Max drawdown at the 15% band", "Largest peak-to-trough decline, identical window for all three sleeve choices.",
                  [("Cash (0%)", pct(b15["cash"]["max_drawdown_pct"], 1, signed=False), "neutral"),
                   ("Liquid fund (assumed 6%)", pct(b15["liquid"]["max_drawdown_pct"], 1, signed=False), "positive"),
                   ("Gold (GOLDBEES.NS)", pct(b15["gold"]["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("No filter (100% always)", pct(orig["max_drawdown_pct"], 1, signed=False), "negative")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-1 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, cagr, dd, net, cls="", highlight=False):
        c = f' class="{cls} highlight"' if highlight else (f' class="{cls}"' if cls else "")
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(net)}</td><td>{pct(cagr)}</td><td>{pct(dd,1,signed=False)}</td></tr>"""

    full_table_rows = []
    for b in bands:
        for key in ("cash", "liquid", "gold"):
            v = b[key]
            full_table_rows.append(row(f"{b['band_pct']:.0f}% band — {HEDGE_LABELS[key]}", v["cagr_pct"], v["max_drawdown_pct"], v["net_return_pct"], highlight=(b["band_pct"] == 15.0 and key == "liquid")))

    full_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Every band × every sleeve, side by side</h3>
        {pill('highlighted row = liquid fund at the 15% band, the most consistent result here', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — all nine combinations of band width and de-risked-sleeve choice, over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window. Window is shorter than reports 66's because GOLDBEES.NS's history starts mid-2010.</p>
      <table class="data-table">
        <thead><tr><th>Design</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th></tr></thead>
        <tbody>
          <tr><td>No filter (100% always)</td><td>{pct(orig['net_return_pct'])}</td><td>{pct(orig['cagr_pct'])}</td><td>{pct(orig['max_drawdown_pct'],1,signed=False)}</td></tr>
          {''.join(full_table_rows)}
          <tr class="real-bench"><td>NIFTY 50 (real index)</td><td>{pct(nif['net_return_pct'])}</td><td>{pct(nif['cagr_pct'])}</td><td>{pct(nif['max_drawdown_pct'],1,signed=False)}</td></tr>
          <tr class="real-bench"><td>GOLDBEES.NS, buy &amp; hold (real ETF)</td><td>{pct(gb['net_return_pct'])}</td><td>{pct(gb['cagr_pct'])}</td><td>{pct(gb['max_drawdown_pct'],1,signed=False)}</td></tr>
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "No filter", "color": COL["muted"], "points": orig["equity_curve"], "dash": True},
        {"name": "15% band — Cash", "color": HEDGE_COLORS["cash"], "points": b15["cash"]["equity_curve"], "dash": True},
        {"name": "15% band — Liquid fund", "color": HEDGE_COLORS["liquid"], "points": b15["liquid"]["equity_curve"]},
        {"name": "15% band — Gold", "color": HEDGE_COLORS["gold"], "points": b15["gold"]["equity_curve"]},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=440, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_69")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — 15% band, {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how {sym}100 invested at the start of the window grew under each de-risked-sleeve choice, linear axis, not log-scaled, all at the same 15% band width.</p>
      <div class="flex items-center mb-2 flex-wrap">{eq_legend}</div>
      {eq_svg}
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why gold's edge flips into a trade-off here</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Smallcap250 Momentum 10's own unfiltered drawdown ({pct(orig['max_drawdown_pct'],1,signed=False)}) is the deepest
        universe tested in this project — and its worst stretches don't perfectly line up with gold's own calmest periods.
        Where Midcap150's crashes and gold's own quiet patches happened to overlap well (report 68), here gold's price
        apparently had enough of its OWN volatility DURING Smallcap250's worst drawdown windows to add to the pain rather
        than cushion it, even while still delivering the best average annual return of the three sleeves.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        This is a useful reminder that "gold as a crisis hedge" is a historical tendency, not a guarantee, and it can vary
        by which specific downturns a given strategy's own worst periods happen to coincide with — reports 68-70 together
        show gold winning cleanly on two universes (Midcap150, NIFTY100) and trading off on this one.
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
        <li class="mb-1.5">The liquid-fund sleeve is a MODELED ASSUMPTION (flat {R['assumed_liquid_yield_pct']:.0f}% p.a.), not real market data — see report 68's data caveat. Real yields varied roughly 3%-9% across this window.</li>
        <li class="mb-1.5">GOLDBEES.NS's history only starts mid-2010, so this report's window excludes the 2008-2009 global financial crisis.</li>
        <li class="mb-1.5">This is a SIMPLIFIED implementation: exposure scales the ALREADY-COMPUTED fully-invested strategy's own daily returns, not a re-simulation of actual partial share purchases.</li>
        <li class="mb-1.5">Zero transaction costs on continuously adjusting the stock/hedge split.</li>
        <li class="mb-1.5">No official "Smallcap250 Momentum 10" index exists — the June/December cadence is a borrowed convention. Today's fixed constituent list is applied retroactively (survivorship bias). This is a single, fixed 18-year historical path.</li>
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
      {honesty_note}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Smallcap250 Momentum 10 — Smooth Exposure, Hedged</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("69_smallcap250_momentum10_smooth_exposure_hedged.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 69_smallcap250_momentum10_smooth_exposure_hedged.html")

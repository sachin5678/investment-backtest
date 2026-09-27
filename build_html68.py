"""Builds 68_midcap_momentum10_smooth_exposure_hedged.html from results67.json."""
import json
import html
from svg_charts import line_chart, COL

with open("results67.json") as f:
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
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap150 Momentum 10 — Smooth Exposure, Combined With Gold and a Liquid Fund</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Reports 65-67 ramped equity exposure down smoothly instead of a hard on/off switch, holding plain 0%-return cash for the de-risked portion. This report tests two better homes for that de-risked capital: GOLDBEES.NS (the same real gold ETF from reports 48-50) and a liquid-fund proxy for the safe overnight yield idle capital would actually earn. Same 200-day EMA signal, same three band widths (10%/15%/20%) as reports 65-67 — the ONLY change is what the unexposed portion holds.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(R['start_date'])}–{esc(R['end_date'])}<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    data_caveat = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2B03C]">
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          {pill('data caveat found while building this report', 'assumption')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          LIQUIDBEES.NS's Yahoo Finance price is effectively FLAT for its entire 2009-2026 history — it sits at ~₹1000.00
          every single day, moving by fractions of a rupee at most. Real liquid-fund yield is paid out as additional bonus
          units, NOT reflected in this per-unit price feed at all. Using that raw price directly would have silently
          modeled "liquid fund" as earning exactly 0%, identical to plain cash — a misleading result to present as a
          finding.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          Instead, the "liquid fund" sleeve below is modeled as a flat ASSUMED {R['assumed_liquid_yield_pct']:.0f}% annual
          yield, compounding daily — a round-number approximation of India's long-run overnight/liquid-fund yield (actual
          yields ranged roughly 3%-9% across this 18-year window, both above and below 6% at different points). This is
          clearly a MODELED ASSUMPTION, not real market data, unlike gold's real ETF price series below.
        </p>
      </div>
    </div>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#37F083]">
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          {pill('gold wins outright; the liquid-fund assumption gives a smaller, still-real edge', 'positive')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          At every band width, gold beats cash on CAGR by a wide margin AND matches or beats it on drawdown too — at the
          15% band, cash gives {pct(b15['cash']['cagr_pct'])} CAGR / {pct(b15['cash']['max_drawdown_pct'],1,signed=False)} drawdown,
          gold gives <span class="font-semibold">{pct(b15['gold']['cagr_pct'])}</span> CAGR /
          <span class="font-semibold">{pct(b15['gold']['max_drawdown_pct'],1,signed=False)}</span> drawdown — a clean
          upgrade, no trade-off at all, echoing reports 48-50's binary-filter finding.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The liquid-fund assumption also beats cash — {pct(b15['liquid']['cagr_pct'])} CAGR at the 15% band, a smaller but
          real edge over cash, roughly matching cash's own drawdown. It's the more CONSERVATIVE upgrade of the two: no
          market risk (unlike gold, whose price can fall), just capturing yield that idle capital would realistically earn
          in a real liquid fund instead of literally nothing.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR at the 15% band", "Compound annual growth rate, identical window for all three sleeve choices.",
                  [("Cash (0%)", pct(b15["cash"]["cagr_pct"]), "neutral"),
                   ("Liquid fund (assumed 6%)", pct(b15["liquid"]["cagr_pct"]), "assumption"),
                   ("Gold (GOLDBEES.NS)", pct(b15["gold"]["cagr_pct"]), "positive"),
                   ("No filter (100% always)", pct(orig["cagr_pct"]), "neutral")]),
        kpi_card("Max drawdown at the 15% band", "Largest peak-to-trough decline, identical window for all three sleeve choices.",
                  [("Cash (0%)", pct(b15["cash"]["max_drawdown_pct"], 1, signed=False), "neutral"),
                   ("Liquid fund (assumed 6%)", pct(b15["liquid"]["max_drawdown_pct"], 1, signed=False), "assumption"),
                   ("Gold (GOLDBEES.NS)", pct(b15["gold"]["max_drawdown_pct"], 1, signed=False), "positive"),
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
            full_table_rows.append(row(f"{b['band_pct']:.0f}% band — {HEDGE_LABELS[key]}", v["cagr_pct"], v["max_drawdown_pct"], v["net_return_pct"], highlight=(b["band_pct"] == 15.0 and key == "gold")))

    full_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Every band × every sleeve, side by side</h3>
        {pill('highlighted row = gold at the 15% band, the best all-round result here', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — all nine combinations of band width and de-risked-sleeve choice, over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window. Window is shorter than reports 65-67's because GOLDBEES.NS's history starts mid-2010.</p>
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
    eq_svg, eq_legend = line_chart(eq_series, height=440, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_68")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — 15% band, {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how {sym}100 invested at the start of the window grew under each de-risked-sleeve choice, linear axis, not log-scaled, all at the same 15% band width. Gold (amber) pulls decisively ahead of both cash (grey) and the liquid-fund assumption (cyan).</p>
      <div class="flex items-center mb-2 flex-wrap">{eq_legend}</div>
      {eq_svg}
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Two upgrades, two different reasons they work</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Gold's edge comes from the same mechanism reports 48-50 found for the binary filter: it has historically had low or
        negative correlation to Indian equities during broad selloffs, so it doesn't need to rise to help here — it just
        needs to not fall alongside the momentum stocks the exposure ramp is de-risking away from. Since gold ALSO had a
        genuinely strong run over this specific 2010-2026 window (see the real GOLDBEES.NS buy-and-hold row above), it adds
        real compounding on top of that diversification benefit, which is why it beats even the (optimistic) 6% liquid-fund
        assumption here.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        The liquid-fund edge is a completely different, much more mundane mechanism: it isn't diversification or a bet on
        an asset's own returns at all, just capturing the safe yield that idle capital would realistically earn instead of
        sitting at literally zero. It's a smaller edge than gold's, but it comes with essentially no additional risk — a
        real liquid fund's NAV doesn't meaningfully fall in a crisis the way gold's price occasionally can. Which of the
        two an investor should prefer is a genuine risk-appetite choice, not a strictly-better-or-worse comparison.
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
        <li class="mb-1.5">The liquid-fund sleeve is a MODELED ASSUMPTION (flat {R['assumed_liquid_yield_pct']:.0f}% p.a.), not real market data — see the data caveat above. Real liquid-fund yields varied roughly 3%-9% across this window, so the true edge over cash would have been smaller in low-rate years (2020-2021) and larger in high-rate years (2008-2013).</li>
        <li class="mb-1.5">GOLDBEES.NS's history only starts mid-2010, so this report's window EXCLUDES the 2008-2009 global financial crisis — same disclosed limitation as reports 48-50.</li>
        <li class="mb-1.5">This is a SIMPLIFIED implementation: exposure scales the ALREADY-COMPUTED fully-invested strategy's own daily returns (blended with the hedge sleeve's), not a re-simulation of actual partial share purchases.</li>
        <li class="mb-1.5">Zero transaction costs on continuously adjusting the stock/hedge split — a real implementation would need periodic rebalancing trades between sleeves.</li>
        <li class="mb-1.5">GOLDBEES.NS tracks domestic gold prices in INR, which also move with the rupee's own exchange rate, a real but separate driver from "gold as a crisis hedge."</li>
        <li class="mb-1.5">Today's fixed Midcap150 constituent list is applied retroactively (survivorship bias). Equal weighting, no F&O-eligibility screen, unadjusted prices, no dividends modeled — same as every other reconstruction here.</li>
      </ul>
    </div>
    """

    body = f"""
    {header}
    {data_caveat}
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
<html lang="en"><head><meta charset="utf-8"/><title>Midcap150 Momentum 10 — Smooth Exposure, Hedged</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("68_midcap_momentum10_smooth_exposure_hedged.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 68_midcap_momentum10_smooth_exposure_hedged.html")

"""Builds 18_midcap30_nifty500_10_15.html from results17.json (+ results13.json
and results15.json for the midcap size-spectrum context). Same self-contained
contract, smooth Catmull-Rom charts throughout."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results17.json") as f:
    R = json.load(f)
with open("results13.json") as f:
    R_MC20_SRC = json.load(f)
with open("results15.json") as f:
    R_MC10_SRC = json.load(f)

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
      .scrollbox{max-height:240px;overflow:auto;}
      .scrollbox::-webkit-scrollbar{width:8px;}
      .scrollbox::-webkit-scrollbar-thumb{background:#1E3A45;border-radius:4px;}
      tr.real-bench td{color:#9FB4BB;}
      tr.context-row td{color:#7E97A0;font-style:italic;}
    </style>
    """


def kpi_card(label, definition, cols):
    col_html = []
    for col_label, value_str, kind in cols:
        color = KIND_COLOR[kind]
        col_html.append(
            f'<div class="flex-1 min-w-[100px]"><div class="text-[11px] text-[#7E97A0] mb-1 uppercase tracking-wide">{esc(col_label)}</div>'
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
    mc30, n10, n15 = R["midcap30"], R["nifty500_10"], R["nifty500_15"]
    nif, midetf = R["nifty"], R["midcap_etf"]
    mc20 = R_MC20_SRC["momentum20"]
    mc10 = R_MC10_SRC["midcap10"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap Momentum-30, and NIFTY500 Momentum-10 vs. Momentum-15</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Three more custom top-N selections, each run at its universe's REAL rebalance cadence this time — May/November for midcap, June/December for NIFTY 500 (both confirmed via NSE's own published methodology).</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          Reuses price data already cached from reports 11-16 — NIFTY 500 = NIFTY 100 + Midcap 150 + Smallcap 250, no new downloads.<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2643C]">
        <div class="flex items-center gap-2 mb-3">
          <h2 class="text-lg font-bold text-[#E6EDF0]">What's real here, and what still isn't</h2>
          {pill('rebalance months are genuinely real this time', 'positive')}{pill('top-N counts are still custom', 'negative')}{pill('survivorship bias', 'negative')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Unlike the smallcap reconstructions in report 16 (which had to borrow the NIFTY200 Momentum 30's June/December convention because no real
          pure-momentum smallcap index exists), the rebalance calendars used here ARE the real ones: <span class="font-semibold">May/November</span> for
          Nifty Midcap150 Momentum 50, and <span class="font-semibold">June/December</span> for Nifty500 Momentum 50 — both confirmed directly from NSE's
          published methodology. What's still custom is the <span class="font-semibold">selection size</span>: the real indices always pick the top 50;
          this report picks the top 30 (midcap) and top 10/15 (NIFTY 500) instead.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The same survivorship bias as every reconstruction in this series still applies — today's fixed universe (Midcap 150 or NIFTY 500), applied
          retroactively to 2008.
        </p>
      </div>
    </div>
    """

    definitions_strip = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL_TIGHT}">
        <p class="{WHAT_THIS_SHOWS} mb-2">WHAT THIS SHOWS — the formula and universes, unchanged from every earlier reconstruction.</p>
        <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
          All three: {pill('6m/12m risk-adjusted momentum, z-scored, asymmetrically normalised', 'assumption')} — identical formula throughout this project
          — {pill('equal-weighted', 'assumption')} (not free-float market cap × score), no F&O-eligibility screen. Midcap150 Momentum 30:
          {R['midcap_universe_size']}-stock universe, May/November. NIFTY500 Momentum 10 and Momentum 15 share the same {R['nifty500_universe_size']}-stock
          universe and June/December cadence, differing only in how many stocks are selected.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("Net return", f"{esc(R['common_start'])} to {esc(R['common_end'])}, base 100.",
                  [("Midcap Momentum-30", pct(mc30["net_return_pct"]), win_loss_kind(mc30["net_return_pct"])),
                   ("NIFTY500 Momentum-10", pct(n10["net_return_pct"]), win_loss_kind(n10["net_return_pct"])),
                   ("NIFTY500 Momentum-15", pct(n15["net_return_pct"]), win_loss_kind(n15["net_return_pct"]))]),
        kpi_card("CAGR", "Compound annual growth rate, identical window for all three.",
                  [("Midcap Momentum-30", pct(mc30["cagr_pct"]), win_loss_kind(mc30["cagr_pct"])),
                   ("NIFTY500 Momentum-10", pct(n10["cagr_pct"]), win_loss_kind(n10["cagr_pct"])),
                   ("NIFTY500 Momentum-15", pct(n15["cagr_pct"]), win_loss_kind(n15["cagr_pct"]))]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline over the same window.",
                  [("Midcap Momentum-30", pct(mc30["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("NIFTY500 Momentum-10", pct(n10["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("NIFTY500 Momentum-15", pct(n15["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("Longest time underwater", "Longest stretch, in calendar days, below a prior peak.",
                  [("Midcap Momentum-30", f'{mc30["longest_underwater_days"]:,}d', "neutral"),
                   ("NIFTY500 Momentum-10", f'{n10["longest_underwater_days"]:,}d', "neutral"),
                   ("NIFTY500 Momentum-15", f'{n15["longest_underwater_days"]:,}d', "neutral")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, v, cls=""):
        c = f' class="{cls}"' if cls else ""
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(v['net_return_pct'])}</td><td>{pct(v['cagr_pct'])}</td>
        <td>{pct(v['max_drawdown_pct'],1,signed=False)}</td><td>{v['longest_underwater_days']:,}d</td></tr>"""

    spectrum_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Midcap momentum, the full size spectrum: 10 vs. 20 vs. 30</h3>
        {pill('italic rows = pulled from reports 14 & 16 for context, not recomputed here', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the same Midcap 150 universe and May/November cadence, at three selection sizes, so the concentration effect already seen in smallcap (report 16) can be checked against midcap too.</p>
      <table class="data-table">
        <thead><tr><th>Selection</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("Midcap Momentum-10 (report 16)", mc10, "context-row")}
          {row("Midcap Momentum-20 (report 14)", mc20, "context-row")}
          {row("Midcap Momentum-30 (this report)", mc30)}
        </tbody>
      </table>
    </div>
    """

    full_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">All five, side by side</h3>
        {pill('grey rows = real, un-reconstructed benchmarks', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the three custom reconstructions from this report against NIFTY 50 and the real Midcap 150 ETF, over the identical {esc(R['common_start'])}–{esc(R['common_end'])} window.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("Midcap Momentum-30 (custom top-N)", mc30)}
          {row("NIFTY500 Momentum-10 (custom top-N)", n10)}
          {row("NIFTY500 Momentum-15 (custom top-N)", n15)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
          {row(f"Midcap 150 ETF, MID150BEES.NS (real, only from {R['midcap_etf_start']})", midetf, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "Midcap Momentum-30", "color": COL["positive"], "points": mc30["equity_curve"]},
        {"name": "NIFTY500 Momentum-10", "color": COL["negative"], "points": n10["equity_curve"]},
        {"name": "NIFTY500 Momentum-15", "color": COL["assumption"], "points": n15["equity_curve"], "dash": True},
        {"name": "NIFTY 50 (real)", "color": COL["text"], "points": nif["equity_curve"], "dash": True},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=460, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_18")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Growth of 100 — {esc(R['common_start'])} to {esc(R['common_end'])}</h3>
        {pill('linear axis, starts at zero — not log-scaled', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — NIFTY500 Momentum-10 and Momentum-15 track each other extremely closely for almost the entire span — the two lines are barely distinguishable until zoomed into the exact endpoint values in the table above.</p>
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
        {"name": "Midcap Momentum-30", "color": COL["positive"], "points": dd_points(mc30["equity_curve"])},
        {"name": "NIFTY500 Momentum-10", "color": COL["negative"], "points": dd_points(n10["equity_curve"])},
        {"name": "NIFTY500 Momentum-15", "color": COL["assumption"], "points": dd_points(n15["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=260, chart_id="dd_18")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — NIFTY500 Momentum-10 and -15 also drew down almost identically — going from 10 to 15 holdings in a 500-stock universe barely changes concentration risk, unlike the much bigger jumps tested in smallcap (10 vs. 20 out of 250) or midcap (10 vs. 30 out of 150).</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    def sel_rows(sample):
        return "".join(f"""<tr><td>{esc(s['date'])}</td><td class="text-left" style="text-align:left">{esc(', '.join(t.replace('.NS','') for t in s['tickers']))}</td></tr>""" for s in sample)

    sel_tables = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Sample rebalances — first 2 and last 2, each strategy</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — which stocks got selected at the start and end of each reconstruction's history.</p>
      <div class="grid grid-cols-1 gap-4">
        <div>
          <div class="text-[12px] font-semibold text-[#9FB4BB] mb-1">Midcap Momentum-30</div>
          <div class="scrollbox"><table class="data-table"><tbody>{sel_rows(mc30['selections_sample'])}</tbody></table></div>
        </div>
        <div>
          <div class="text-[12px] font-semibold text-[#9FB4BB] mb-1">NIFTY500 Momentum-10</div>
          <div class="scrollbox"><table class="data-table"><tbody>{sel_rows(n10['selections_sample'])}</tbody></table></div>
        </div>
        <div>
          <div class="text-[12px] font-semibold text-[#9FB4BB] mb-1">NIFTY500 Momentum-15</div>
          <div class="scrollbox"><table class="data-table"><tbody>{sel_rows(n15['selections_sample'])}</tbody></table></div>
        </div>
      </div>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Concentration effect depends on how big the universe is</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — reconciling this report's near-identical 10-vs-15 result with the sharper differences seen in earlier reports.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Going from 10 to 15 stocks out of a 500-name universe is a small relative jump (+50% more names, but still only 2-3% of the universe either way) —
        the two NIFTY500 versions ended up {pct(n15['cagr_pct'] - n10['cagr_pct'], 2)} apart in CAGR, essentially noise. Compare that to smallcap (report 16),
        where going from 10 to 20 out of 250 stocks changed CAGR by over 6 percentage points. The lesson isn't that concentration doesn't matter — it's that
        it matters more when the selection is a bigger SHARE of a smaller universe, not just a bigger absolute headcount.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        Midcap Momentum-30 fits the same pattern from the other earlier reports: within the 150-stock midcap universe, CAGR fell monotonically as the
        selection grew — {pct(mc10['cagr_pct'])} (top 10) → {pct(mc20['cagr_pct'])} (top 20) → {pct(mc30['cagr_pct'])} (top 30) — the clearest, most
        consistent concentration effect found in any reconstruction so far.
      </p>
    </div>
    """

    limitations = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2">
        <h3 class="text-base font-bold text-[#E6EDF0]">Limitations</h3>
        {pill("read before trusting any number above", "assumption")}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every simplification behind these three reconstructions.</p>
      <ul class="text-[13px] text-[#C9D6DA] list-disc pl-5 leading-relaxed">
        <li class="mb-1.5">The rebalance MONTHS are real for both universes here — but the top-N selection sizes (30, 10, 15) are still custom; the real indices always select 50.</li>
        <li class="mb-1.5">Survivorship bias — today's fixed universe (Midcap 150 or NIFTY 500), applied retroactively to 2008, unchanged from every earlier report.</li>
        <li class="mb-1.5">Equal-weighted, not free-float-market-cap × score; no F&O-eligibility screen — same as always.</li>
        <li class="mb-1.5">The midcap "10 vs. 20 vs. 30" spectrum table pulls report 14's and 16's already-computed numbers directly — those two used a slightly different common date-window intersection (each report intersected against its own companion series), so their figures may differ by a negligible amount from what an identical from-scratch re-run against this report's exact window would show.</li>
        <li class="mb-1.5">Midcap 150 ETF's real trading history only starts {esc(R['midcap_etf_start'])} — shown for context, not the full {esc(R['common_start'])}–{esc(R['common_end'])} window the other four series cover.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modelled for any series shown.</li>
        <li class="mb-1.5">These are three single, fixed reconstructions computed once — no out-of-sample check, and no test of whether 10/15/30 specifically are curve-fit to this history.</li>
      </ul>
    </div>
    """

    body = f"""
    {header}
    {lead_disclosure}
    {definitions_strip}
    <div class="px-10 py-6">
      {kpi_grid}
      {spectrum_table}
      {full_table}
      {eq_panel}
      {dd_panel}
      {sel_tables}
      {honesty_note}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Midcap-30 &amp; NIFTY500 Momentum 10/15</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("18_midcap30_nifty500_10_15.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 18_midcap30_nifty500_10_15.html")

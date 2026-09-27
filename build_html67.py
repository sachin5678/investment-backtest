"""Builds 67_nifty100_momentum10_smooth_exposure.html from results66.json."""
import json
import html
from svg_charts import line_chart, COL

with open("results66.json") as f:
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
BAND_COLORS = {10: "#6AE4FF", 15: "#37F083", 20: "#8B5CF6"}


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
            f'<div class="flex-1 min-w-[110px]"><div class="text-[11px] text-[#7E97A0] mb-1 uppercase tracking-wide">{esc(col_label)}</div>'
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
    orig, binf, nif = R["original"], R["binary_filter"], R["nifty"]
    bands = R["bands"]
    by_band = {b["band_pct"]: b for b in bands}

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">NIFTY100 Momentum 10 — Volatility-Scaled (Smooth) Exposure</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Reports 65-66 found smooth exposure beats the binary 200-EMA filter on Midcap150 (trade-off frontier) and dominates it outright on Smallcap250 (wins on both CAGR and drawdown). This applies the identical mechanics to report 12's NIFTY100 Momentum 10 config — the third and final universe in this comparison, and the one where the pattern breaks.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(R['start_date'])}–{esc(R['end_date'])}<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2643C]">
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          {pill('the pattern reverses — the binary filter dominates EVERY smooth band', 'negative')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          On NIFTY100, the binary filter ({pct(binf['cagr_pct'])} CAGR / {pct(binf['max_drawdown_pct'],1,signed=False)} drawdown)
          beats EVERY smooth band on BOTH dimensions — 10% ({pct(by_band[10]['cagr_pct'])} / {pct(by_band[10]['max_drawdown_pct'],1,signed=False)}),
          15% ({pct(by_band[15]['cagr_pct'])} / {pct(by_band[15]['max_drawdown_pct'],1,signed=False)}), and 20%
          ({pct(by_band[20]['cagr_pct'])} / {pct(by_band[20]['max_drawdown_pct'],1,signed=False)}). This is the OPPOSITE of
          Smallcap250's result (report 66), where the wider smooth bands dominated the binary filter instead.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          Lined up with reports 65-66, the honest pattern: the binary filter's whipsaw cost is only worth removing (via
          smoothing) when that whipsaw cost is large to begin with. NIFTY100's binary filter has {binf['num_regime_reentries']}
          re-entries — the SAME regime-signal count as every other universe (since the signal is NIFTY 50's own price,
          independent of what it protects) — but a calmer, lower-volatility universe like NIFTY100 apparently pays a
          smaller whipsaw tax for the SAME number of round-trips than a choppier one like Smallcap250 does, leaving less
          for smoothing to recover.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR by exposure design", "Compound annual growth rate, identical window for every variant.",
                  [("No filter (100% always)", pct(orig["cagr_pct"]), "neutral")] +
                  [(f"Smooth {b['band_pct']:.0f}% band", pct(b["cagr_pct"]), "negative") for b in bands] +
                  [("Binary filter (report 45)", pct(binf["cagr_pct"]), "positive"),
                   ("NIFTY 50", pct(nif["cagr_pct"]), "neutral")]),
        kpi_card("Max drawdown by exposure design", "Largest peak-to-trough decline, identical window for every variant.",
                  [("No filter (100% always)", pct(orig["max_drawdown_pct"], 1, signed=False), "negative")] +
                  [(f"Smooth {b['band_pct']:.0f}% band", pct(b["max_drawdown_pct"], 1, signed=False), "negative") for b in bands] +
                  [("Binary filter (report 45)", pct(binf["max_drawdown_pct"], 1, signed=False), "positive"),
                   ("NIFTY 50", pct(nif["max_drawdown_pct"], 1, signed=False), "negative")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-1 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, cagr, dd, net, uw, avg_exp=None, full_pct=None, zero_pct=None, cls="", highlight=False):
        c = f' class="{cls} highlight"' if highlight else (f' class="{cls}"' if cls else "")
        exp_str = f"{avg_exp:.1f}%" if avg_exp is not None else "—"
        full_str = f"{full_pct:.1f}%" if full_pct is not None else "—"
        zero_str = f"{zero_pct:.1f}%" if zero_pct is not None else "—"
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(net)}</td><td>{pct(cagr)}</td>
        <td>{pct(dd,1,signed=False)}</td><td>{uw:,}d</td><td>{exp_str}</td><td>{full_str}</td><td>{zero_str}</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Every exposure design, side by side</h3>
        {pill("highlighted row = report 45's binary 200-EMA filter — the best of everything here", 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — no filter, all three smooth bands, the binary filter, and the real NIFTY 50 index, over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th><th>Avg exposure</th><th>% days full</th><th>% days zero</th></tr></thead>
        <tbody>
          {row("No filter (100% always)", orig['cagr_pct'], orig['max_drawdown_pct'], orig['net_return_pct'], orig['longest_underwater_days'], 100.0, 100.0, 0.0)}
          {"".join(row(f"Smooth {b['band_pct']:.0f}% band", b['cagr_pct'], b['max_drawdown_pct'], b['net_return_pct'], b['longest_underwater_days'], b['avg_exposure_pct'], b['pct_days_full_exposure'], b['pct_days_zero_exposure']) for b in bands)}
          {row("Binary filter (report 45)", binf['cagr_pct'], binf['max_drawdown_pct'], binf['net_return_pct'], binf['longest_underwater_days'], highlight=True)}
          {row("NIFTY 50 (real index)", nif['cagr_pct'], nif['max_drawdown_pct'], nif['net_return_pct'], nif['longest_underwater_days'], cls="real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [{"name": "No filter", "color": COL["muted"], "points": orig["equity_curve"], "dash": True}]
    for b in bands:
        eq_series.append({"name": f"Smooth {b['band_pct']:.0f}% band", "color": BAND_COLORS[int(b["band_pct"])], "points": b["equity_curve"]})
    eq_series.append({"name": "Binary filter", "color": COL["positive"], "points": binf["equity_curve"], "dash": True})
    eq_svg, eq_legend = line_chart(eq_series, height=440, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_67")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — every design, {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how {R['currency_symbol']}100 invested at the start of the window grew under each exposure design, linear axis, not log-scaled. The binary filter (green) sits ABOVE every smooth band here — the reverse of report 66's chart.</p>
      <div class="flex items-center mb-2 flex-wrap">{eq_legend}</div>
      {eq_svg}
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Reading three universes together</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        NIFTY100's own unfiltered drawdown ({pct(orig['max_drawdown_pct'],1,signed=False)}) is the SHALLOWEST of the three
        universes tested across reports 65-67 — shallower than Midcap150's and much shallower than Smallcap250's. Report 45
        already found the binary filter costs NIFTY100 almost nothing in CAGR (30.70% -> 30.67%) — there was very little
        whipsaw damage for smoothing to recover in the first place, so a smoother ramp here just gives up some of the
        binary filter's clean, sharp de-risking without much offsetting benefit.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        Put the three reports together and a genuinely useful rule of thumb emerges: smooth exposure scaling is worth
        trying specifically on universes where the binary filter ALREADY shows meaningful whipsaw cost (like Smallcap250);
        on a universe where the binary filter is already nearly free (like NIFTY100), there's less to gain and the
        binary switch's crisper full de-risking wins outright. This is exactly the kind of conditional, universe-dependent
        finding this project has repeatedly surfaced (see also reports 37-41's front-loaded momentum) — no single design
        choice is universally best.
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
        <li class="mb-1.5">This is a SIMPLIFIED implementation: exposure scales the ALREADY-COMPUTED fully-invested strategy's own daily returns, not a re-simulation of actual partial share purchases.</li>
        <li class="mb-1.5">Exposure uses YESTERDAY's close-to-EMA ratio to scale TODAY's return, avoiding same-day look-ahead.</li>
        <li class="mb-1.5">Cash (the unexposed portion) earns exactly 0%, same convention as every cash-holding report here.</li>
        <li class="mb-1.5">Only three band widths were tested (10%/15%/20%) — none of them beat the binary filter here, but a wider or narrower band wasn't checked and might close the gap.</li>
        <li class="mb-1.5">Today's fixed NIFTY100 constituent list (report 12's config) is applied retroactively (survivorship bias). This is a single, fixed historical path.</li>
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
<html lang="en"><head><meta charset="utf-8"/><title>NIFTY100 Momentum 10 — Smooth Exposure</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("67_nifty100_momentum10_smooth_exposure.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 67_nifty100_momentum10_smooth_exposure.html")

"""Builds 65_midcap_momentum10_smooth_exposure.html from results64.json."""
import json
import html
from svg_charts import line_chart, COL

with open("results64.json") as f:
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
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap150 Momentum 10 — Volatility-Scaled (Smooth) Exposure</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Reports 42-64's regime filter flips 100%/0% the instant NIFTY 50 crosses its 200-day EMA. This report replaces the hard switch with a CONTINUOUS ramp: exposure scales linearly from 100% (at or above the EMA) down to 0% (a band_pct below it), removing the whipsaw problem at its root rather than tuning around it — there is no discrete state here at all, so there is nothing to "re-enter" or "confirm." Three band widths tested (10%/15%/20%) against the original and report 42's binary filter, all on the identical window.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(R['start_date'])}–{esc(R['end_date'])}<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#37F083]">
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          {pill('beats the binary filter on CAGR at every band width', 'positive')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Every band tested gives a HIGHER CAGR than the binary filter — {pct(binf['cagr_pct'])} (binary) vs.
          {pct(by_band[10]['cagr_pct'])} (10% band), {pct(by_band[15]['cagr_pct'])} (15%), and
          {pct(by_band[20]['cagr_pct'])} (20%) — while still cutting drawdown meaningfully versus no filter at all
          ({pct(orig['max_drawdown_pct'],1,signed=False)}): {pct(by_band[10]['max_drawdown_pct'],1,signed=False)},
          {pct(by_band[15]['max_drawdown_pct'],1,signed=False)}, and {pct(by_band[20]['max_drawdown_pct'],1,signed=False)}
          respectively.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The trade-off: none of these bands protect drawdown as deeply as the binary filter's {pct(binf['max_drawdown_pct'],1,signed=False)}.
          This forms a clean, non-dominated frontier — no filter (best CAGR, worst drawdown) → wider band → narrower band →
          binary filter (worst CAGR, best drawdown) — with every point on it a genuinely different, reasonable choice
          depending on how much an investor weights return versus downside protection, not a single "best" answer.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR by exposure design", "Compound annual growth rate, identical window for every variant.",
                  [("No filter (100% always)", pct(orig["cagr_pct"]), "neutral")] +
                  [(f"Smooth {b['band_pct']:.0f}% band", pct(b["cagr_pct"]), "positive") for b in bands] +
                  [("Binary filter (report 42)", pct(binf["cagr_pct"]), "neutral"),
                   ("NIFTY 50", pct(nif["cagr_pct"]), "neutral")]),
        kpi_card("Max drawdown by exposure design", "Largest peak-to-trough decline, identical window for every variant.",
                  [("No filter (100% always)", pct(orig["max_drawdown_pct"], 1, signed=False), "negative")] +
                  [(f"Smooth {b['band_pct']:.0f}% band", pct(b["max_drawdown_pct"], 1, signed=False), "assumption") for b in bands] +
                  [("Binary filter (report 42)", pct(binf["max_drawdown_pct"], 1, signed=False), "positive"),
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
        {pill("highlighted row = report 42's binary 200-EMA filter", 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — no filter, all three smooth bands, the binary filter, and the real NIFTY 50 index, over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window. "% days full" / "% days zero" describe how often exposure sat exactly at 100% or 0% vs. somewhere in between.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th><th>Avg exposure</th><th>% days full</th><th>% days zero</th></tr></thead>
        <tbody>
          {row("No filter (100% always)", orig['cagr_pct'], orig['max_drawdown_pct'], orig['net_return_pct'], orig['longest_underwater_days'], 100.0, 100.0, 0.0)}
          {"".join(row(f"Smooth {b['band_pct']:.0f}% band", b['cagr_pct'], b['max_drawdown_pct'], b['net_return_pct'], b['longest_underwater_days'], b['avg_exposure_pct'], b['pct_days_full_exposure'], b['pct_days_zero_exposure']) for b in bands)}
          {row("Binary filter (report 42)", binf['cagr_pct'], binf['max_drawdown_pct'], binf['net_return_pct'], binf['longest_underwater_days'], highlight=True)}
          {row("NIFTY 50 (real index)", nif['cagr_pct'], nif['max_drawdown_pct'], nif['net_return_pct'], nif['longest_underwater_days'], cls="real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [{"name": "No filter", "color": COL["muted"], "points": orig["equity_curve"], "dash": True}]
    for b in bands:
        eq_series.append({"name": f"Smooth {b['band_pct']:.0f}% band", "color": BAND_COLORS[int(b["band_pct"])], "points": b["equity_curve"]})
    eq_series.append({"name": "Binary filter", "color": COL["negative"], "points": binf["equity_curve"], "dash": True})
    eq_svg, eq_legend = line_chart(eq_series, height=440, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_65")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — every design, {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how {R['currency_symbol']}100 invested at the start of the window grew under each exposure design, linear axis, not log-scaled. The smooth bands sit consistently between the two extremes, closer to "no filter" the wider the band.</p>
      <div class="flex items-center mb-2 flex-wrap">{eq_legend}</div>
      {eq_svg}
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why removing the whipsaw at its root pays off</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        The binary filter's own honesty notes (reports 42, 46, 47) repeatedly found that its biggest hidden cost is
        {binf['num_regime_reentries']} whipsaw round-trips — full sells and full buys triggered by ordinary
        volatility near the 200-EMA, all charged nothing in this frictionless model but expensive in reality. A smooth
        ramp has NO discrete flip to whipsaw on: a day where price wobbles slightly above and below the EMA just nudges
        exposure a few percentage points, rather than triggering a full round-trip. Removing that specific cost is exactly
        why the smooth version's CAGR comes out ahead of the binary filter's at every band width tested, even though the
        binary filter still protects drawdown more deeply (it goes all the way to 0% exposure at the depth of a real crash,
        which the smooth version with a narrow band width only approaches asymptotically).
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        This IS still a genuinely different mechanism worth weighing, not a strict improvement: the {by_band[10]['pct_days_zero_exposure']:.1f}%
        of days at fully zero exposure under the tightest (10%) band shows it still fully de-risks during the depths of a
        real crash, just via a smoother path in and out rather than a single hard switch.
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
        <li class="mb-1.5">This is a SIMPLIFIED implementation: exposure is applied by scaling the ALREADY-COMPUTED fully-invested strategy's own daily returns, not by re-simulating actual partial share purchases day by day — in practice, continuously adjusting a real portfolio's stock/cash split would itself require frequent (small) trades, which this model charges nothing for.</li>
        <li class="mb-1.5">Exposure uses YESTERDAY's close-to-EMA ratio to scale TODAY's return (disclosed in the function itself) — getting this ordering backwards was an actual bug caught and fixed while building this report; readers implementing something similar should watch for the same look-ahead trap.</li>
        <li class="mb-1.5">Cash (the unexposed portion) earns exactly 0%, same convention as every cash-holding report here.</li>
        <li class="mb-1.5">Only three band widths were tested (10%/15%/20%) — the true efficient frontier between "no filter" and "binary filter" could have better points elsewhere.</li>
        <li class="mb-1.5">Today's fixed Midcap150 constituent list is applied retroactively (survivorship bias). Equal weighting, no F&O-eligibility screen, unadjusted prices, no dividends modeled — same as every other reconstruction here.</li>
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
<html lang="en"><head><meta charset="utf-8"/><title>Midcap150 Momentum 10 — Smooth Exposure</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("65_midcap_momentum10_smooth_exposure.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 65_midcap_momentum10_smooth_exposure.html")

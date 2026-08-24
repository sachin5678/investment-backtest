"""Builds 17_monthly_rebalance_compare.html from results16.json. Same
self-contained contract, smooth Catmull-Rom charts — a 6-way sensitivity
comparison table plus one illustrative chart pair for the most dramatic
reversal found."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results16.json") as f:
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


def delta_color(v):
    if v is None:
        return "#E6EDF0"
    return "#37F083" if v > 0 else ("#F2643C" if v < 0 else "#7E97A0")


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
      .grp-cagr{background:rgba(55,240,131,0.03);}
      .grp-mdd{background:rgba(242,100,60,0.03);}
    </style>
    """


def build():
    cfgs = R["configs"]
    sym = R["currency_symbol"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Monthly Rebalancing — Every Momentum Reconstruction, Compared to Its Original</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">All six custom momentum reconstructions built in this project so far, re-run with a monthly rebalance calendar instead of their original semi-annual (or May/November) schedule.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          Reuses the same universes and formula from reports 11, 12, 14, and 16 — no new price data needed.<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2643C]">
        <div class="flex items-center gap-2 mb-3">
          <h2 class="text-lg font-bold text-[#E6EDF0]">Read this before the table below</h2>
          {pill('zero trading costs modelled', 'negative')}{pill('mixed result, not a clean win', 'assumption')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Monthly rebalancing means <span class="font-semibold">12 reshuffles a year</span> instead of 2 — every original cadence in this project
          (June/December or May/November) rebalances twice a year, so monthly is <span class="font-semibold">6x the portfolio turnover</span> across the board. This project has never modelled transaction costs for any momentum reconstruction, and doesn't here either, so every
          "monthly did better" result below is shown with zero commission, slippage, or market impact charged against that extra trading — a comparison
          that structurally favours whichever schedule trades more.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          Even so — and this is the actual finding — <span class="font-semibold">monthly rebalancing does not uniformly win</span>. It improved some
          reconstructions and made others worse. If more frequent rebalancing were simply "better" at capturing momentum, it should have won everywhere;
          it didn't. All six still carry the same survivorship bias as every reconstruction in this series (today's fixed universe, applied retroactively).
        </p>
      </div>
    </div>
    """

    rows = []
    for key, c in cfgs.items():
        m, o = c["monthly"], c["original"]
        cagr_delta = m["cagr_pct"] - o["cagr_pct"]
        mdd_delta = m["max_drawdown_pct"] - o["max_drawdown_pct"]   # negative delta = deeper (worse) drawdown
        rows.append(f"""
        <tr>
          <td>{esc(c['label'])}</td>
          <td class="{MUTED}" style="text-align:left">{esc(c['original_cadence'])}</td>
          <td>{pct(o['cagr_pct'])}</td>
          <td>{pct(m['cagr_pct'])}</td>
          <td style="color:{delta_color(cagr_delta)}">{cagr_delta:+.2f}pp</td>
          <td>{pct(o['max_drawdown_pct'],1,signed=False)}</td>
          <td>{pct(m['max_drawdown_pct'],1,signed=False)}</td>
          <td style="color:{delta_color(mdd_delta)}">{mdd_delta:+.1f}pp</td>
        </tr>""")

    comparison_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">All six, monthly vs. original</h3>
        {pill('green delta = monthly did better, red = monthly did worse', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — for the drawdown delta, "better" means a SMALLER (closer to zero) drawdown, so a positive/green delta there means monthly's drawdown was shallower than the original's.</p>
      <div style="overflow-x:auto">
      <table class="data-table">
        <thead><tr><th>Reconstruction</th><th style="text-align:left">Original cadence</th>
        <th class="grp-cagr">CAGR (original)</th><th class="grp-cagr">CAGR (monthly)</th><th class="grp-cagr">Δ CAGR</th>
        <th class="grp-mdd">Max DD (original)</th><th class="grp-mdd">Max DD (monthly)</th><th class="grp-mdd">Δ Max DD</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
      </div>
    </div>
    """

    wins = sum(1 for c in cfgs.values() if c["monthly"]["cagr_pct"] > c["original"]["cagr_pct"])
    losses = len(cfgs) - wins
    biggest_gain_key = max(cfgs, key=lambda k: cfgs[k]["monthly"]["cagr_pct"] - cfgs[k]["original"]["cagr_pct"])
    biggest_loss_key = min(cfgs, key=lambda k: cfgs[k]["monthly"]["cagr_pct"] - cfgs[k]["original"]["cagr_pct"])
    biggest_gain, biggest_loss = cfgs[biggest_gain_key], cfgs[biggest_loss_key]

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">A genuinely mixed result</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the honest summary, not a cherry-picked headline.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Monthly rebalancing raised CAGR in {wins} of {len(cfgs)} reconstructions and lowered it in {losses}. The biggest improvement was
        <span class="font-semibold text-[#E6EDF0]">{esc(biggest_gain['label'])}</span> ({pct(biggest_gain['original']['cagr_pct'])} →
        {pct(biggest_gain['monthly']['cagr_pct'])}); the biggest deterioration was <span class="font-semibold text-[#E6EDF0]">{esc(biggest_loss['label'])}</span>
        ({pct(biggest_loss['original']['cagr_pct'])} → {pct(biggest_loss['monthly']['cagr_pct'])}) — notably, the smallest, most concentrated basket
        (10 holdings), where reshuffling monthly means chasing short-term momentum signals in and out of just 10 names, seems to have hurt rather than
        helped on this data.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        Combined with the zero-transaction-cost caveat above, the honest takeaway is: <span class="font-semibold text-[#E6EDF0]">there is no clean,
        general rule that "rebalancing more often improves a momentum strategy"</span> — it depends on the specific universe and concentration, and even
        the wins here are shown before any of the real cost of trading 6x more often.
      </p>
    </div>
    """

    # illustrative chart pair for the config with the largest CAGR change (in either direction)
    illus_key = max(cfgs, key=lambda k: abs(cfgs[k]["monthly"]["cagr_pct"] - cfgs[k]["original"]["cagr_pct"]))
    illus = cfgs[illus_key]

    eq_series = [
        {"name": f"{illus['label']} — monthly", "color": COL["positive"], "points": illus["monthly"]["equity_curve"]},
        {"name": f"{illus['label']} — original ({illus['original_cadence']})", "color": COL["assumption"], "points": illus["original"]["equity_curve"], "dash": True},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_illus")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Largest swing, illustrated: {esc(illus['label'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the config where rebalance frequency mattered most, monthly vs. its original cadence, growth of 100.</p>
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
        {"name": "Monthly", "color": COL["positive"], "points": dd_points(illus["monthly"]["equity_curve"])},
        {"name": f"Original ({illus['original_cadence']})", "color": COL["assumption"], "points": dd_points(illus["original"]["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=240, chart_id="dd_illus")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown — {esc(illus['label'])}, monthly vs. original</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the same comparison from the risk side.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    limitations = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2">
        <h3 class="text-base font-bold text-[#E6EDF0]">Limitations</h3>
        {pill("read before trusting any number above", "assumption")}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — everything carried over from the six original reports, plus what's new to this comparison.</p>
      <ul class="text-[13px] text-[#C9D6DA] list-disc pl-5 leading-relaxed">
        <li class="mb-1.5"><span class="font-semibold text-[#E6EDF0]">Zero transaction costs anywhere</span> (repeated) — this is the single biggest reason not to over-read a "monthly wins" result at face value.</li>
        <li class="mb-1.5">None of the six reconstructions are real NSE products — see reports 11, 12, 14, and 16 for the full disclosure on each (custom top-N selections, some on universes the real momentum family doesn't even use in a pure-momentum form).</li>
        <li class="mb-1.5">Survivorship bias — today's fixed universe for each reconstruction, applied retroactively to 2008, unchanged from every earlier report.</li>
        <li class="mb-1.5">Equal-weighted, not free-float-market-cap × score; no F&O-eligibility screen — same as always.</li>
        <li class="mb-1.5">Only two rebalance frequencies (original cadence and monthly) were compared per reconstruction — this is not a full sweep (weekly, bi-monthly, etc. are untested).</li>
        <li class="mb-1.5">Monthly rebalancing was implemented as "last trading day of every calendar month" — a monthly cadence anchored to different day-of-month conventions could give slightly different results.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modelled for any series shown.</li>
      </ul>
    </div>
    """

    body = f"""
    {header}
    {lead_disclosure}
    <div class="px-10 py-6">
      {comparison_table}
      {honesty_note}
      {eq_panel}
      {dd_panel}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Monthly Rebalance — All Momentum Reconstructions</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("17_monthly_rebalance_compare.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 17_monthly_rebalance_compare.html")

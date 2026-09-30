"""Builds 87_midcap150_report48_blended_calendars.html from results86.json."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results86.json") as f:
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

MONTH_LABEL = {"june_dec": "June / December (report 48)", "july_jan": "July / January", "aug_feb": "August / February",
               "sept_mar": "September / March", "oct_apr": "October / April", "nov_may": "November / May"}


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
      tr.blended td{background:rgba(106,228,255,0.06);}
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
    blended = R["blended"]
    best, worst, safest = R["best_calendar"], R["worst_calendar"], R["safest_calendar"]
    june_dec = R["june_dec"]
    nif, gb = R["nifty"], R["gold_benchmark"]
    span = R["ema_span"]
    labels = list(R["month_names"].values())
    sleeves = {lbl: R[f"sleeve_{lbl}"] for lbl in labels}

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap150 Momentum 10 — Report 48, Blending All Six Rebalance Calendars</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Report 85 could only compare the six semi-annual rebalance calendars one at a time — picking a winner meant guessing in advance which two months would turn out best. This report asks what happens if you don't pick: split capital equally (1/6 each) across ALL SIX calendars — June/December, July/January, August/February, September/March, October/April, November/May — as six independently-compounding sleeves of the same {span}-day EMA + gold design, then combine them into one blended portfolio.</p>
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
          {pill("the blend beats report 48's own June/December on CAGR, while staying close to its drawdown", "positive")}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          The blended portfolio returns <span class="font-semibold">{pct(blended['cagr_pct'])}</span> CAGR with a
          <span class="font-semibold">{pct(blended['max_drawdown_pct'],1,signed=False)}</span> drawdown — better CAGR than
          report 48's own June/December calendar ({pct(june_dec['cagr_pct'])}), for only
          {blended['max_drawdown_pct']-june_dec['max_drawdown_pct']:.1f} percentage points more drawdown
          ({pct(june_dec['max_drawdown_pct'],1,signed=False)}). It lands almost exactly in the MIDDLE of the six individual
          calendars' CAGR range ({pct(worst['cagr_pct'])} to {pct(best['cagr_pct'])}) — expected for an equal-weight
          average — but its drawdown is the SECOND-BEST of all seven options shown here (six single calendars plus the
          blend), only just behind June/December's own.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The practical value: you never had to know in advance that June/December would turn out to have the best
          drawdown, or that July/January would have the best CAGR. Blending all six gets most of the benefit of picking
          well, without having to actually guess — a real diversification effect, not a coincidence of these particular
          six numbers.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR — blended vs. individual calendars", "Equal-weight (1/6 each) blend of all six calendars vs. picking just one.",
                  [("Blended, all 6", pct(blended["cagr_pct"]), win_loss_kind(blended["cagr_pct"])),
                   ("June/Dec (report 48)", pct(june_dec["cagr_pct"]), "neutral"),
                   (f"Best single ({MONTH_LABEL[best['label']].split(' (')[0]})", pct(best["cagr_pct"]), "neutral"),
                   (f"Worst single ({MONTH_LABEL[worst['label']].split(' (')[0]})", pct(worst["cagr_pct"]), "neutral")]),
        kpi_card("Max drawdown — blended vs. individual calendars", "Largest peak-to-trough decline, identical window for every series.",
                  [("Blended, all 6", pct(blended["max_drawdown_pct"], 1, signed=False), "positive"),
                   ("June/Dec (report 48)", pct(june_dec["max_drawdown_pct"], 1, signed=False), "neutral"),
                   (f"Safest single ({MONTH_LABEL[safest['label']].split(' (')[0]})", pct(safest["max_drawdown_pct"], 1, signed=False), "neutral"),
                   (f"Worst-DD single ({MONTH_LABEL[best['label']].split(' (')[0]})", pct(best["max_drawdown_pct"], 1, signed=False), "neutral")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-1 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, v, cls=""):
        c = f' class="{cls}"' if cls else ""
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(v['net_return_pct'])}</td><td>{pct(v['cagr_pct'])}</td>
        <td>{pct(v['max_drawdown_pct'],1,signed=False)}</td><td>{v['longest_underwater_days']:,}d</td></tr>"""

    sleeve_rows = "".join(row(MONTH_LABEL[lbl], sleeves[lbl]) for lbl in labels)
    full_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">All seven, side by side</h3>
        {pill('highlighted row = the blend; grey rows = real benchmarks', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every series over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {sleeve_rows}
          {row("Blended — all 6 calendars, 1/6 each", blended, "blended")}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
          {row("GOLDBEES.NS, buy & hold (real ETF)", gb, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    palette = [COL["muted"], COL["muted"], COL["muted"], COL["muted"], COL["muted"], COL["muted"]]
    eq_series = [{"name": MONTH_LABEL[lbl].split(" (")[0], "color": palette[i], "points": sleeves[lbl]["equity_curve"], "dash": True}
                 for i, lbl in enumerate(labels)]
    eq_series.append({"name": "Blended — all 6 calendars", "color": COL["positive"], "points": blended["equity_curve"]})
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_87")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the six individual calendars (dashed, muted) fan out around the solid blended line, which sits in the middle of them almost throughout.</p>
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

    dd_series = [{"name": MONTH_LABEL[lbl].split(" (")[0], "color": palette[i], "points": dd_points(sleeves[lbl]["equity_curve"]), "dash": True}
                 for i, lbl in enumerate(labels)]
    dd_series.append({"name": "Blended — all 6 calendars", "color": COL["positive"], "points": dd_points(blended["equity_curve"])})
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=220, chart_id="dd_87")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the blended line's worst points are shallower than most of the six individual calendars' — averaging smooths out the specific dates where any one calendar happened to get caught badly positioned.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    mechanism_note = f"""
    <div class="{PANEL} mt-6 border-[#6AE4FF]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why blending shallows the drawdown without giving up CAGR</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Each calendar's own worst drawdown happens on ITS OWN specific rebalance dates — whichever ten stocks a given
        calendar happened to be holding right as a bad stretch hit. Since the six calendars' rebalance dates are spread
        roughly a month apart from each other, they're rarely all badly positioned on the exact same day. Blending means
        the portfolio's WORST day is an average across six sleeves that don't all bottom out simultaneously — some
        calendars will have already refreshed into fresher picks by the time others are still holding stale ones,
        smoothing the combined trough shallower than most of the individual lines.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        CAGR, being an average of six numbers that are all comfortably positive and fairly close together
        ({pct(worst['cagr_pct'])} to {pct(best['cagr_pct'])}), simply lands near the middle — averaging doesn't cost much
        on the upside because none of the six individual calendars is dramatically better or worse than the others to
        begin with. The combination of "averages out to close to the middle on CAGR" and "smooths out the specific worst
        day on drawdown" is what makes blending land favorably here — a portfolio that never has to bet everything on one
        specific two-month pair.
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
        <li class="mb-1.5">Each sleeve is rebased to 100 at the SAME common start date before averaging — a real
        implementation would need to actually split capital 1/6 at inception and let each sleeve compound independently
        from there, which is exactly what this simulates, but real-world onboarding into an already-running strategy
        would need its own entry-timing decision this report doesn't address.</li>
        <li class="mb-1.5">This roughly TRIPLES the number of distinct rebalance events across the year compared to any
        single calendar (six calendars × 2 dates each = up to 12 refresh dates/year across the whole blended portfolio,
        vs. 2/year for a single calendar) — zero transaction costs are assumed throughout, same disclosed omission as
        every other reconstruction here, but a real blended version would trade meaningfully more often.</li>
        <li class="mb-1.5">Only these specific six calendars (report 25's original set) were blended — a different
        selection or weighting of calendars (e.g. weighting the historically safer ones more heavily) wasn't tested.</li>
        <li class="mb-1.5">Today's fixed Midcap150 constituent list is applied retroactively across the whole window
        (survivorship bias). Equal weighting within each sleeve, no F&O-eligibility screen, unadjusted prices, no
        dividends modeled — same as every other reconstruction here.</li>
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
      {mechanism_note}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Midcap150 Momentum 10 — Blended Rebalance Calendars</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("87_midcap150_report48_blended_calendars.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 87_midcap150_report48_blended_calendars.html")

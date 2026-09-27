"""Builds 75_midcap150_quality10_rebalanced.html from results74.json."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results74.json") as f:
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
    quality, momentum, nif = R["quality"], R["momentum_flagship"], R["nifty"]
    sym = R["currency_symbol"]
    top_n = R["top_n"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap150 Quality {top_n} — A Real Rebalanced Backtest, Not a Snapshot</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">The Midcap150 counterpart to report 74's NIFTY500 Quality 50 — same real NSE Quality formula, same rebalance mechanics and same data-availability limits, applied to this project's flagship Midcap150 universe (10 out of 150 stocks — proportionally close to 50 out of 500).</p>
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
          {pill('quality-10 lost money outright in this window — the momentum flagship did not', 'negative')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Over the same ~14-month stretch (see report 74's data-availability disclosure — only two real fundamentals
          snapshots exist in this cache, so this is one rebalance event, not an 18-year track record), the Midcap150
          Quality-{top_n} basket returned <span class="font-semibold">{pct(quality['net_return_pct'])}</span> — a real loss —
          while the Midcap150 Momentum-10 flagship returned <span class="font-semibold">{pct(momentum['net_return_pct'])}</span>
          and even NIFTY 50 itself came in at {pct(nif['net_return_pct'])}. Quality was the worst of the three here, by a wide
          margin, and its drawdown ({pct(quality['max_drawdown_pct'],1,signed=False)}) was also the deepest of the three.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          This is a genuinely unflattering result for quality investing over this specific window, reported exactly as
          computed — a concentrated 10-stock basket (vs. 50 on NIFTY500) has much more idiosyncratic risk than a broader
          quality basket, and one bad stretch for a couple of names in a 10-stock portfolio can dominate the whole
          result. See the honesty note below for why this single data point shouldn't be read as "quality doesn't work."
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR (short window — see report 74's disclosure)", "Annualized, but over only ~14 months — treat with real caution.",
                  [(f"Quality-{top_n}", pct(quality["cagr_pct"]), win_loss_kind(quality["cagr_pct"])),
                   ("Momentum-10 flagship", pct(momentum["cagr_pct"]), win_loss_kind(momentum["cagr_pct"])),
                   ("NIFTY 50", pct(nif["cagr_pct"]), "neutral")]),
        kpi_card("Net return over this window", "The more honest number for a window this short.",
                  [(f"Quality-{top_n}", pct(quality["net_return_pct"]), win_loss_kind(quality["net_return_pct"])),
                   ("Momentum-10 flagship", pct(momentum["net_return_pct"]), win_loss_kind(momentum["net_return_pct"])),
                   ("NIFTY 50", pct(nif["net_return_pct"]), "neutral")]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline, identical window for every series.",
                  [(f"Quality-{top_n}", pct(quality["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Momentum-10 flagship", pct(momentum["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("NIFTY 50", pct(nif["max_drawdown_pct"], 1, signed=False), "negative")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-1 gap-4 mt-6">{"".join(kpis)}</div>'

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
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every series over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window. The momentum flagship's own real June/December-rebalanced series is SLICED to this window, not rebuilt.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row(f"Midcap150 Quality {top_n} (this report)", quality)}
          {row("Midcap150 Momentum 10 flagship (sliced to same window)", momentum)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": f"Quality-{top_n}", "color": COL["negative"], "points": quality["equity_curve"]},
        {"name": "Momentum-10 flagship", "color": COL["positive"], "points": momentum["equity_curve"], "dash": True},
        {"name": "NIFTY 50", "color": COL["muted"], "points": nif["equity_curve"], "dash": True},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=380, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_75")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how {sym}100 invested at the start of this short window grew under each strategy, linear axis, not log-scaled.</p>
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
        {"name": f"Quality-{top_n}", "color": COL["negative"], "points": dd_points(quality["equity_curve"])},
        {"name": "Momentum-10 flagship", "color": COL["positive"], "points": dd_points(momentum["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=200, chart_id="dd_75")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — quality-{top_n}'s drawdown is both deeper AND longer-lasting than the momentum flagship's over this same stretch.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    sched_rows = "".join(
        f"<tr><td>FY ending {esc(u['fiscal_year_end'])}</td><td>{esc(u['rebalance_date'])}</td>"
        f"<td>{u['eligible_count']}</td><td>{u['basket_size']}</td></tr>"
        for u in R["rebalance_schedule"]
    )
    sel_rows = "".join(
        f"<tr><td>{esc(s['date'])}</td><td class='text-left'>{esc(', '.join(s['tickers']))}</td></tr>"
        for s in quality["selections_sample"]
    )
    mechanism_note = f"""
    <div class="{PANEL} mt-6 border-[#6AE4FF]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">The two real rebalances</h3>{pill('mechanism', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — exactly which fundamentals snapshot fed each rebalance, and how many Midcap150 stocks were actually scoreable at that point.</p>
      <table class="data-table mb-4">
        <thead><tr><th>Fundamentals from</th><th>Portfolio formed</th><th>Eligible stocks</th><th>Basket size</th></tr></thead>
        <tbody>{sched_rows}</tbody>
      </table>
      <p class="{WHAT_THIS_SHOWS} mb-1">Full basket at each rebalance</p>
      <table class="data-table">
        <thead><tr><th>Date</th><th class="text-left">Tickers</th></tr></thead>
        <tbody>{sel_rows}</tbody>
      </table>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why this isn't a strong test of "quality" as a factor</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the honest limits of what one rebalance event, on a 10-stock basket, can tell you.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Every momentum report in this project earns its credibility from surviving MANY market regimes across 18 years.
        This report has exactly one ~14-month window, one rebalance event, and only 10 stocks — small enough that one or
        two names having a bad stretch can dominate the whole basket's return, independent of whether "quality" as a
        factor is sound. The formula also only had 2-3 years of trailing annual data to average over at this point
        (see quality_pit.py's docstring) — a much noisier ROE/D-E/EPS-growth-variability estimate than a mature index
        with a decade of history to average across.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        This report exists to show what a REAL, point-in-time-correct rebalance looks like with the fundamentals data
        actually available — not to make a claim about whether quality investing works on Indian midcaps. A single bad
        (or good) stretch for a concentrated basket is one data point, not a verdict.
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
        <li class="mb-1.5">Only TWO rebalance dates exist in this data cache — this is a ~14-month test, not an 18-year one.
        See report 74's disclosure panel for exactly why.</li>
        <li class="mb-1.5">Only 10 stocks — much more concentrated (and idiosyncratic-risk-exposed) than report 74's 50-stock
        NIFTY500 Quality basket.</li>
        <li class="mb-1.5">The 2-calendar-month reporting lag is an assumption, not a measured company-by-company disclosure
        date.</li>
        <li class="mb-1.5">Equal weighting (not free-float-market-cap x quality-score weighted, the real index's own
        methodology) — same disclosed simplification report 13 used.</li>
        <li class="mb-1.5">Today's fixed Midcap150 constituent list is applied retroactively (survivorship bias) — same as
        every other reconstruction here. A ticker with usable fundamentals but no price yet on the rebalance date is
        excluded from that rebalance's eligible pool, same as momentum's own price-eligibility filters.</li>
        <li class="mb-1.5">Zero transaction costs, no dividends modeled, unadjusted prices — same as every other
        reconstruction here.</li>
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
      {honesty_note}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Midcap150 Quality {top_n}</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("75_midcap150_quality10_rebalanced.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 75_midcap150_quality10_rebalanced.html")

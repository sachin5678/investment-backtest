"""Builds 86_midcap150_report48_midmonth_rebalance.html from results85.json."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results85.json") as f:
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
    oe, om = R["original_month_end"], R["original_mid_month"]
    fe, fm = R["filtered_month_end"], R["filtered_mid_month"]
    nif, gb = R["nifty"], R["gold_benchmark"]
    span = R["ema_span"]
    target_day = R["target_day"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap150 Momentum 10 — Report 48, Month-End vs. Mid-Month Rebalance</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Report 48's exact design — the {span}-day EMA regime filter, gold instead of cash — rebalanced on the trading day closest to the {target_day}th of June/December instead of the LAST trading day of June/December. Same two months, same continuous daily {span}-EMA regime signal — only WHICH DAY within each month the top-10 picks get refreshed on changes. A different axis from report 85 (which months) and reports 76/77 (how often).</p>
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
          {pill('mid-month rebalancing helps the PLAIN strategy but hurts the gold-hedged hero design', 'assumption')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Without the regime filter, moving to the {target_day}th improves BOTH numbers: CAGR {pct(oe['cagr_pct'])} →
          <span class="font-semibold">{pct(om['cagr_pct'])}</span>, drawdown {pct(oe['max_drawdown_pct'],1,signed=False)} →
          <span class="font-semibold">{pct(om['max_drawdown_pct'],1,signed=False)}</span>. With the 200-EMA + gold filter
          layered on, the SAME change goes the other way: CAGR {pct(fe['cagr_pct'])} →
          <span class="font-semibold">{pct(fm['cagr_pct'])}</span>, drawdown {pct(fe['max_drawdown_pct'],1,signed=False)} →
          <span class="font-semibold">{pct(fm['max_drawdown_pct'],1,signed=False)}</span> — worse on both counts.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          Reported honestly rather than explained away: this project doesn't have a confirmed mechanism for why the SAME
          day-of-month shift helps one version and hurts the other. A plausible but UNVERIFIED hypothesis — Indian
          markets have real month-end flows (F&O expiry is the last Thursday of the month, mutual fund NAV-related
          activity clusters around month-end) that could interact differently with a portfolio that's sometimes 100% in
          gold than one that's always 100% in stocks — but this report doesn't test that hypothesis directly, so it
          should be read as a real, disclosed pattern in this data, not a mechanism this project has actually confirmed.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR — month-end vs. mid-month", "Compound annual growth rate, identical window for every series.",
                  [("No filter, month-end", pct(oe["cagr_pct"]), win_loss_kind(oe["cagr_pct"])),
                   ("No filter, mid-month", pct(om["cagr_pct"]), win_loss_kind(om["cagr_pct"])),
                   ("200-EMA+gold, month-end (report 48)", pct(fe["cagr_pct"]), win_loss_kind(fe["cagr_pct"])),
                   ("200-EMA+gold, mid-month", pct(fm["cagr_pct"]), win_loss_kind(fm["cagr_pct"]))]),
        kpi_card("Max drawdown — month-end vs. mid-month", "Largest peak-to-trough decline, identical window for every series.",
                  [("No filter, month-end", pct(oe["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("No filter, mid-month", pct(om["max_drawdown_pct"], 1, signed=False), "positive"),
                   ("200-EMA+gold, month-end (report 48)", pct(fe["max_drawdown_pct"], 1, signed=False), "positive"),
                   ("200-EMA+gold, mid-month", pct(fm["max_drawdown_pct"], 1, signed=False), "negative")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-1 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, v, cls=""):
        c = f' class="{cls}"' if cls else ""
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(v['net_return_pct'])}</td><td>{pct(v['cagr_pct'])}</td>
        <td>{pct(v['max_drawdown_pct'],1,signed=False)}</td><td>{v['longest_underwater_days']:,}d</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">All six, side by side</h3>
        {pill('grey rows = real benchmarks, not reconstructions', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every series over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("No filter — rebalance month-end", oe)}
          {row(f"No filter — rebalance ~{target_day}th of month", om)}
          {row("200-EMA + gold — rebalance month-end (report 48)", fe)}
          {row(f"200-EMA + gold — rebalance ~{target_day}th of month", fm)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
          {row("GOLDBEES.NS, buy & hold (real ETF)", gb, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "No filter, month-end", "color": COL["muted"], "points": oe["equity_curve"], "dash": True},
        {"name": "200-EMA+gold, month-end (report 48)", "color": COL["positive"], "points": fe["equity_curve"]},
        {"name": "200-EMA+gold, mid-month", "color": COL["negative"], "points": fm["equity_curve"]},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_86")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how ₹100 invested at the start of the window grew under each version, linear axis, not log-scaled.</p>
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
        {"name": "200-EMA+gold, month-end (report 48)", "color": COL["positive"], "points": dd_points(fe["equity_curve"])},
        {"name": "200-EMA+gold, mid-month", "color": COL["negative"], "points": dd_points(fm["equity_curve"])},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=220, chart_id="dd_86")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison — gold-hedged variants only</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — month-end's line sits shallower than mid-month's for most of the window.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">A genuine open question, not a settled mechanism</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — what this report can and can't tell you.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Every other rebalance-timing report in this project (76, 77, 85) found a consistent DIRECTION of effect — wider
        EMA spans hurt, faster stock-refresh sometimes helps and sometimes hurts depending on the underlying signal's own
        speed, different month-pairs shift the result by a couple of points either way. This report is different: the
        SAME change (month-end → mid-month) helps the unfiltered strategy and hurts the filtered one. That's not a
        contradiction in the data — it's a real signal that whatever is driving the day-of-month effect interacts with
        the regime filter itself, not just with the stock-picking formula alone.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        This report does not identify that interaction — it only documents that it exists. Isolating the actual cause
        would need a dedicated test (e.g. comparing day-of-month effects specifically DURING gold-hedge periods vs.
        DURING invested periods), which is a real follow-up, not something to guess at here.
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
        <li class="mb-1.5">Only ONE mid-month target (the {target_day}th) was tested against month-end — this doesn't map
        the full curve of possible days within the month, or confirm the {target_day}th specifically is unusual rather
        than any non-month-end day behaving similarly.</li>
        <li class="mb-1.5">The proposed month-end-flow hypothesis (F&O expiry, NAV-related activity) is explicitly
        UNVERIFIED — offered as a plausible direction for a follow-up, not a confirmed explanation.</li>
        <li class="mb-1.5">Zero transaction costs on any regime switch or scheduled rebalance — same disclosed omission
        as every other reconstruction here.</li>
        <li class="mb-1.5">Today's fixed Midcap150 constituent list is applied retroactively across the whole window
        (survivorship bias). Equal weighting, no F&O-eligibility screen, unadjusted prices, no dividends modeled — same
        as every other reconstruction here.</li>
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
      {honesty_note}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Midcap150 Momentum 10 — Month-End vs Mid-Month</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("86_midcap150_report48_midmonth_rebalance.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 86_midcap150_report48_midmonth_rebalance.html")

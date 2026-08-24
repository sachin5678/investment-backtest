"""Builds 09_sip_day_of_month.html from results8.json. Same self-contained
contract, smooth Catmull-Rom charts, honesty rules."""
import json
import html
import pandas as pd
from svg_charts import line_chart, area_underwater_chart, COL

with open("results8.json") as f:
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


def money(v, symbol, decimals=0):
    if v is None:
        return "—"
    sign = "-" if v < 0 else ""
    return f"{sign}{symbol}{abs(v):,.{decimals}f}"


def pct(v, decimals=1, signed=True):
    if v is None:
        return "—"
    s = "+" if (signed and v > 0) else ""
    return f"{s}{v:,.{decimals}f}%"


def win_loss_kind(v):
    if v is None:
        return "neutral"
    return "positive" if v > 0 else ("negative" if v < 0 else "neutral")


def weekly_resample(points):
    out = []
    last_week = None
    for d, v in points:
        wk = pd.Timestamp(d).to_period("W")
        if wk != last_week:
            out.append([d, v])
            last_week = wk
        else:
            out[-1] = [d, v]
    return out


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
      .scrollbox{max-height:320px;overflow:auto;}
      .scrollbox::-webkit-scrollbar{width:8px;}
      .scrollbox::-webkit-scrollbar-thumb{background:#1E3A45;border-radius:4px;}
      .kpi-val{font-size:26px;font-weight:700;letter-spacing:-0.01em;}
      .rank-1{background:rgba(55,240,131,0.08);}
    </style>
    """


def kpi_card(label, definition, cols):
    col_html = []
    for col_label, value_str, kind in cols:
        color = KIND_COLOR[kind]
        col_html.append(
            f'<div class="flex-1"><div class="text-[11px] text-[#7E97A0] mb-1 uppercase tracking-wide">{esc(col_label)}</div>'
            f'<div class="kpi-val mono" style="color:{color}">{value_str}</div></div>'
        )
    return f"""
    <div class="{PANEL_TIGHT}">
      <div class="text-[13px] font-semibold text-[#E6EDF0] mb-1">{esc(label)}</div>
      <div class="{MUTED} mb-3">{definition}</div>
      <div class="flex gap-4">{''.join(col_html)}</div>
    </div>
    """


LABELS = {"1st": "1st of month", "10th": "10th of month", "20th": "20th of month", "last": "Last day of month"}
COLORS = {"1st": COL["positive"], "10th": COL["negative"], "20th": COL["assumption"], "last": COL["text"]}


def build():
    sym = R["currency_symbol"]
    variants = {k: v["frictionless"] for k, v in R["day_variants"].items()}
    ranked = sorted(variants.items(), key=lambda kv: kv[1]["xirr_pct"], reverse=True)
    winner_key, winner = ranked[0]
    loser_key, loser = ranked[-1]
    spread = winner["xirr_pct"] - loser["xirr_pct"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Does the SIP Date Matter? — 1st vs 10th vs 20th vs Last Day</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Same ₹1,000/month into midcap, no overlay of any kind — only the calendar day of the month the SIP runs on changes.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          Data: daily OHLC price data — midcap {esc(R['midcap_ticker'])}<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    definitions_strip = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL_TIGHT}">
        <p class="{WHAT_THIS_SHOWS} mb-2">WHAT THIS SHOWS — plain-English recap: this isolates ONE variable, the day of the month, holding everything else fixed.</p>
        <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
          Four identical vanilla SIPs — ₹1,000/month into midcap, {esc(R['start_date'])} to {esc(R['end_date'])}, no dip overlay, no lump sums — that differ only in
          which calendar day each month's contribution lands on: the {pill('first trading day of the month', 'assumption')}, the
          {pill('first trading day on/after the 10th', 'assumption')}, the {pill('first trading day on/after the 20th', 'assumption')}, or the
          {pill('last trading day of the month', 'assumption')}. Each fills at that day's own close.
        </p>
      </div>
    </div>
    """

    kpis = []
    for key in ["1st", "10th", "20th", "last"]:
        v = variants[key]
        is_winner = key == winner_key
        kpis.append(kpi_card(
            f"{LABELS[key]}{' — highest XIRR' if is_winner else ''}",
            f"Final value {money(v['final_value'], sym)} on {money(v['total_invested'], sym)} invested ({v['num_contributions']} contributions).",
            [("XIRR", pct(v['xirr_pct'], 2), "positive" if is_winner else "neutral"),
             ("Max drawdown", pct(v['max_drawdown_pct'], 1, signed=False), "negative"),
             ("Net gain %", pct(v['net_gain_pct'], 1), "neutral")],
        ))
    kpi_grid = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(kpis)}</div>'

    rank_rows = "".join(f"""
    <tr{' class="rank-1"' if i == 0 else ''}>
      <td>{i+1}</td><td>{esc(LABELS[k])}</td><td>{money(v['final_value'], sym)}</td>
      <td>{pct(v['xirr_pct'], 3)}</td><td>{pct(v['net_gain_pct'], 2)}</td><td>{pct(v['max_drawdown_pct'], 1, signed=False)}</td>
    </tr>""" for i, (k, v) in enumerate(ranked))
    rank_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Ranked by XIRR</h3>
        {pill(f'spread top-to-bottom: {spread:.2f} percentage points', 'assumption')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — {esc(LABELS[winner_key])} comes out on top on this data, but by a margin this narrow, "on top" mostly means "happened to land on slightly better prices," not a reliable, repeatable edge — see the honesty note below.</p>
      <table class="data-table">
        <thead><tr><th>Rank</th><th>SIP day</th><th>Final value</th><th>XIRR</th><th>Net gain %</th><th>Max drawdown</th></tr></thead>
        <tbody>{rank_rows}</tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": LABELS[k], "color": COLORS[k], "points": weekly_resample(variants[k]["value_curve"]),
         "dash": k in ("10th", "20th")}
        for k in ["1st", "10th", "20th", "last"]
    ]
    eq_svg, eq_legend = line_chart(eq_series, y_prefix=sym, height=460, value_fmt=lambda v: f"{v:,.0f}",
                                    chart_id="eq_day", smooth=True)
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Portfolio value over time — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
        {pill('smoothed curve through real weekly values', 'assumption')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — all four lines are essentially on top of each other for the whole 7.5-year span; you cannot visually tell them apart until you zoom into the final numbers.</p>
      <div class="flex items-center mb-2">{eq_legend}</div>
      {eq_svg}
      <div class="{MUTED} mt-2">Curve is drawn through one real data point per calendar week connected with a smooth curve — every plotted value is a genuine historical value. KPI figures above use the full daily series.</div>
    </div>
    """

    def dd_points(value, invested):
        i = {d: val for d, val in invested}
        out, peak = [], None
        for d, val in value:
            ratio = val / i[d] if i[d] else 1.0
            peak = ratio if peak is None else max(peak, ratio)
            out.append([d, (ratio / peak - 1.0) * 100.0])
        return out

    dd_series = [
        {"name": LABELS[k], "color": COLORS[k], "points": weekly_resample(dd_points(variants[k]["value_curve"], variants[k]["invested_curve"])),
         "dash": k in ("10th", "20th")}
        for k in ["1st", "10th", "20th", "last"]
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=260, chart_id="dd_day", smooth=True)
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison (value ÷ invested, not raw value)</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the four lines are indistinguishable in shape; the day of the month has no visible effect on how deep the worst paper loss got.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Where will you get the most returns? Practically, it doesn't matter which day you pick</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the direct answer to "where will we get most returns," stated plainly rather than dressed up.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        {esc(LABELS[winner_key])} produced the highest XIRR ({pct(winner['xirr_pct'], 2)}) and {esc(LABELS[loser_key])} the lowest ({pct(loser['xirr_pct'], 2)}) — a gap of only
        <span class="font-semibold text-[#E6EDF0]">{spread:.2f} percentage points</span> across four otherwise-identical SIPs run for 7.5 years. Compare that to the ~11-point
        gap from choosing midcap over NIFTY (report 5) or the ~0.7-point gap from a genuinely different overlay rule (double SIP on drawdown, report 7) — this is roughly
        an order of magnitude smaller than either.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        This spread is best read as <span class="font-semibold text-[#E6EDF0]">timing noise, not a repeatable edge</span> — which day "wins" reflects which specific
        daily closing prices each schedule happened to land on over this one 7.5-year path in this one market. There's no economic mechanism (unlike, say, a real
        dip-buying overlay) that would make the 1st, 10th, 20th, or last day of the month structurally better or worse in the future. If you have to pick one,
        pick whichever date is operationally easiest for you (e.g. matches your salary credit date) rather than optimising for a difference this small.
      </p>
    </div>
    """

    limitations = f"""
    <div class="{PANEL} border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2">
        <h3 class="text-base font-bold text-[#E6EDF0]">Limitations</h3>
        {pill("read before trusting any number above", "assumption")}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the concrete ways this backtest can mislead you if taken at face value.</p>
      <ul class="text-[13px] text-[#C9D6DA] list-disc pl-5 leading-relaxed">
        <li class="mb-1.5">This tests ONE historical price path ({esc(R['start_date'])}–{esc(R['end_date'])}) — the ranking above is not guaranteed to repeat, and given how small the spread is, it's more likely to reshuffle than to persist on a different date range.</li>
        <li class="mb-1.5">"10th" and "20th" resolve to the first trading day ON OR AFTER that calendar date (since SIPs can't run on weekends/holidays) — a stricter "nearest trading day" rule could shift a date by a day or two in either direction and change results at this margin.</li>
        <li class="mb-1.5">Only midcap was tested here; NIFTY 50 or another instrument could show a different (though probably similarly small) day-of-month effect.</li>
        <li class="mb-1.5">The cost-loaded variant (0.05% commission + 1 tick slippage) is computed in the underlying data but not shown separately above, since it moves every variant by an almost identical, negligible amount and doesn't change the ranking.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modelled.</li>
        <li class="mb-1.5">Drawdown and longest-underwater are computed on (value ÷ invested), not raw ₹ — the same methodology as every SIP report in this series.</li>
      </ul>
    </div>
    """

    body = f"""
    {header}
    {definitions_strip}
    <div class="px-10 py-6">
      {kpi_grid}
      {rank_table}
      {eq_panel}
      {dd_panel}
      {honesty_note}
      <div class="mt-6">{limitations}</div>
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>SIP Day of Month — NIFTY Midcap 150</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("09_sip_day_of_month.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 09_sip_day_of_month.html")

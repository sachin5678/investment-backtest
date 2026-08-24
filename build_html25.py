"""Builds 25_midcap_momentum10_rebalance_offsets.html from results24.json.
Same self-contained contract, smooth Catmull-Rom charts, dark palette as
every other report. Equity chart uses a log10-transformed y-axis (values
converted back for axis labels via value_fmt) since 18 years of ~40% CAGR
compounding pushes net returns into the tens of thousands of percent,
which would flatten every curve into an unreadable hockey-stick on a
linear axis."""
import json
import math
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results24.json") as f:
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

OFFSET_COLOR = {
    "jan_jul": "#F2643C", "feb_aug": "#F2B03C", "mar_sep": "#37F083",
    "apr_oct": "#6AE4FF", "may_nov": "#8B5CF6", "jun_dec": "#E6EDF0",
}
ORDER = ["jan_jul", "feb_aug", "mar_sep", "apr_oct", "may_nov", "jun_dec"]


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
      tr.normal-row td{color:#E6EDF0;font-weight:600;}
    </style>
    """


def kpi_card(label, definition, cols):
    col_html = []
    for col_label, value_str, kind in cols:
        color = KIND_COLOR[kind]
        col_html.append(
            f'<div class="flex-1 min-w-[120px]"><div class="text-[11px] text-[#7E97A0] mb-1 uppercase tracking-wide">{esc(col_label)}</div>'
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
    cfgs = R["configs"]
    sym = R["currency_symbol"]
    normal = cfgs["jun_dec"]

    by_cagr = sorted(cfgs.items(), key=lambda kv: kv[1]["cagr_pct"], reverse=True)
    best_key, best = by_cagr[0]
    worst_key, worst = by_cagr[-1]
    by_dd = sorted(cfgs.items(), key=lambda kv: kv[1]["max_drawdown_pct"], reverse=True)
    shallowest_key, shallowest = by_dd[0]
    deepest_key, deepest = by_dd[-1]

    cagr_spread = best["cagr_pct"] - worst["cagr_pct"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap Momentum 10 — Every Semi-Annual Rebalance Offset, Compared</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">The exact same strategy, only the calendar shifts: Jan/Jul, Feb/Aug, Mar/Sep, Apr/Oct, May/Nov, and the "normal" Jun/Dec used everywhere else in this project — same universe, same top-10/equal-weight/6m-12m-momentum formula, same 2008-2026 window.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(normal['start_date'])}–{esc(normal['end_date'])} · {normal['num_rebalances']} rebalances each<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2643C]">
        <div class="flex items-center gap-2 mb-3">
          <h2 class="text-lg font-bold text-[#E6EDF0]">The question, and the honest result up front</h2>
          {pill(f"{cagr_spread:.1f}pp CAGR spread across all 6 offsets", 'neutral')}
          {pill('the "normal" Jun/Dec offset is mid-pack, not best or worst', 'assumption')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Every report in this project that uses Midcap150 Momentum 10 checks momentum, and rebalances, every June and December — a convention
          borrowed from the real NIFTY200 Momentum index's own schedule, not something specifically chosen because it works best for THIS
          strategy. Since momentum is measured 6 and 12 months back from the rebalance date, moving that date to a different month pair genuinely
          changes which stocks get picked at every single rebalance, not just when the reshuffle happens.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          Across all six possible offsets, CAGR ranges from <span class="font-semibold">{pct(worst['cagr_pct'])}</span> ({worst['label']}) to
          <span class="font-semibold">{pct(best['cagr_pct'])}</span> ({best['label']}) — a {cagr_spread:.1f} percentage-point spread — while max
          drawdown ranges from <span class="font-semibold">{pct(shallowest['max_drawdown_pct'],1,signed=False)}</span> ({shallowest['label']}) to
          <span class="font-semibold">{pct(deepest['max_drawdown_pct'],1,signed=False)}</span> ({deepest['label']}). The "normal" Jun/Dec offset
          this project has used all along ({pct(normal['cagr_pct'])} / {pct(normal['max_drawdown_pct'],1,signed=False)}) lands
          <span class="font-semibold">squarely in the middle</span> of that range on both dimensions — not the best case, not the worst, which is
          the honest, reassuring reading: the strategy's edge doesn't appear to hinge on having picked a lucky rebalance month.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR range across all 6 offsets", "Best and worst of the six month-pairs tested.",
                  [(f"Best: {best['label']}", pct(best["cagr_pct"]), "positive"),
                   (f"Worst: {worst['label']}", pct(worst["cagr_pct"]), "negative"),
                   (f"Normal (Jun/Dec)", pct(normal["cagr_pct"]), "neutral")]),
        kpi_card("Max drawdown range across all 6 offsets", "Shallowest and deepest of the six month-pairs tested.",
                  [(f"Shallowest: {shallowest['label']}", pct(shallowest["max_drawdown_pct"], 1, signed=False), "positive"),
                   (f"Deepest: {deepest['label']}", pct(deepest["max_drawdown_pct"], 1, signed=False), "negative"),
                   (f"Normal (Jun/Dec)", pct(normal["max_drawdown_pct"], 1, signed=False), "neutral")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(key):
        c = cfgs[key]
        cls = "normal-row" if c["is_normal"] else ""
        cls_attr = f' class="{cls}"' if cls else ""
        tag = ' <span class="text-[10px] text-[#7E97A0]">(used everywhere else in this project)</span>' if c["is_normal"] else ""
        return f"""<tr{cls_attr}><td>{esc(c['label'])}{tag}</td><td>{pct(c['net_return_pct'])}</td><td>{pct(c['cagr_pct'])}</td>
        <td>{pct(c['max_drawdown_pct'],1,signed=False)}</td><td>{c['longest_underwater_days']:,}d</td><td>{c['num_rebalances']}</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">All six offsets, side by side</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — identical strategy, identical {esc(normal['start_date'])}–{esc(normal['end_date'])} window, only the rebalance month-pair changes. Bold row is the "normal" Jun/Dec convention used in every other report.</p>
      <table class="data-table">
        <thead><tr><th>Rebalance months</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th><th>Rebalances</th></tr></thead>
        <tbody>{''.join(row(k) for k in ORDER)}</tbody>
      </table>
    </div>
    """

    def log_points(points):
        return [[d, math.log10(v)] for d, v in points]

    eq_series = [
        {"name": cfgs[k]["label"] + (" (normal)" if cfgs[k]["is_normal"] else ""),
         "color": OFFSET_COLOR[k], "points": log_points(cfgs[k]["equity_curve"]),
         "dash": not cfgs[k]["is_normal"]}
        for k in ORDER
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=460, force_zero=False,
                                     value_fmt=lambda v: f"{10**v:,.0f}", chart_id="eq_25")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Growth of 100 — {esc(normal['start_date'])} to {esc(normal['end_date'])}</h3>
        {pill('log10 y-axis — labels show real values, not log values', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — all six offsets compound at a broadly similar rate for most of the window (that's why a log axis is used — on a linear axis, 18 years of ~40% compounding would flatten every curve into an indistinguishable hockey-stick). The solid white line is the "normal" Jun/Dec convention.</p>
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
        {"name": cfgs[k]["label"] + (" (normal)" if cfgs[k]["is_normal"] else ""),
         "color": OFFSET_COLOR[k], "points": dd_points(cfgs[k]["equity_curve"]),
         "dash": not cfgs[k]["is_normal"]}
        for k in ORDER
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=260, chart_id="dd_25")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — all six offsets drew down hard in the same real crashes (2008-09, 2020 COVID) since they all hold overlapping stocks in a correlated universe — the differences between them are in the DEPTH of each crash, not in whether one avoided it.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why the offset matters less than you might expect</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Each offset checks the same 6-month/12-month risk-adjusted momentum formula on 36 different dates spread 6 months apart across the same
        18-year history — different SPECIFIC dates, but similar SEASONAL coverage: over 18 years, every offset ends up rebalancing through
        roughly the same mix of bull runs, corrections, and recoveries, just measured from a different monthly starting point each time. That's
        the statistical reason the six results cluster in a relatively narrow {cagr_spread:.1f}-point CAGR band rather than diverging wildly —
        the underlying momentum signal in Indian midcaps over this period was real and persistent enough to show up regardless of which specific
        month it's sampled from.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        That said, {cagr_spread:.1f} percentage points of CAGR compounded over 18 years is NOT a trivial difference in final wealth — it is the
        gap between {best['label']}'s {pct(best['net_return_pct'])} and {worst['label']}'s {pct(worst['net_return_pct'])} net return over the
        identical window. Some of that gap is likely genuine (certain months may happen to catch momentum inflection points slightly earlier or
        later than others), and some of it is noise from a single 18-year historical path — with only 36 rebalances per offset, this is not a
        large enough sample to say with confidence that {best['label']} is a permanently better calendar choice, only that it happened to be
        over this specific history.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        The practical takeaway: the "normal" Jun/Dec convention this project has used throughout was a reasonable, defensible choice (it borrows
        the real NIFTY200 Momentum index's actual schedule) — and this report confirms it was not an accidentally-lucky or accidentally-unlucky
        pick relative to the five alternatives, landing near the middle of the pack on both return and drawdown.
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
        <li class="mb-1.5">Today's fixed NIFTY Midcap 150 constituent list is applied retroactively across the whole window for all six offsets equally (survivorship bias) — same disclosed approximation as every other reconstruction in this project.</li>
        <li class="mb-1.5">Only 36 rebalances per offset over 18 years — six separate 36-point samples is not a large basis for concluding any one offset is structurally superior; see the honesty note above.</li>
        <li class="mb-1.5">Zero transaction costs, slippage, or taxes modeled for any of the six offsets equally — this doesn't favor one offset over another, but understates the real-world cost of all of them.</li>
        <li class="mb-1.5">Equal weighting (not free-float market-cap x momentum score) and no F&O-eligibility screen, same as every other reconstruction here.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modeled for any holding.</li>
        <li class="mb-1.5">This is a single, fixed 2008-2026 historical path — a different 18-year window could rank these six offsets in a completely different order.</li>
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
<html lang="en"><head><meta charset="utf-8"/><title>Midcap Momentum 10 — Rebalance Offsets Compared</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("25_midcap_momentum10_rebalance_offsets.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 25_midcap_momentum10_rebalance_offsets.html")

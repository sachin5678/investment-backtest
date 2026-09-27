"""Builds 38_midcap_momentum10_frontloaded_two_splits.html from
results37.json. Same self-contained contract, smooth Catmull-Rom charts,
dark palette as every other report."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results37.json") as f:
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
COLOR_5030 = "#8B5CF6"
COLOR_4035 = "#6AE4FF"


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
    orig, fl5030, fl4035, nif = R["original"], R["fl_50_30_20"], R["fl_40_35_25"], R["nifty"]
    sym = R["currency_symbol"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap Momentum 10 — Front-Loaded Weighting, Two Splits Compared</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Report 37 tested a 50%/30%/20% front-loaded 3m/6m/12m blend and found a genuine risk/return trade-off vs. the original equal-weighted formula. This report adds a gentler 40%/35%/25% split to see whether the trade-off scales smoothly or behaves differently.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(R['start_date'])}–{esc(R['end_date'])} · {R['num_rebalances']} rebalances<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2B03C]">
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          {pill('the trade-off does NOT scale smoothly between the two splits', 'assumption')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          A naive guess would be that a gentler front-load (40/35/25, closer to equal weighting) lands somewhere BETWEEN the original and the
          50/30/20 split on both CAGR and drawdown — a smooth dial. That's not what happened. 40/35/25 actually edges out 50/30/20 slightly on
          CAGR ({pct(fl4035['cagr_pct'])} vs. {pct(fl5030['cagr_pct'])}) — but gives back almost the ENTIRE drawdown improvement
          ({pct(fl4035['max_drawdown_pct'],1,signed=False)}, nearly back to the original's {pct(orig['max_drawdown_pct'],1,signed=False)}, vs.
          50/30/20's shallower {pct(fl5030['max_drawdown_pct'],1,signed=False)}).
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          In other words: 50/30/20 turns out to be the better risk-adjusted choice of the two front-loaded splits tested here — not because it
          has the highest CAGR (it doesn't, by a whisker), but because it gets almost all of its drawdown protection from a smaller CAGR
          sacrifice than 40/35/25 does. See the honesty note below for why "more front-loading = smoothly more responsive" isn't quite the right
          mental model.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR", "Compound annual growth rate, identical window for all four.",
                  [("Original (equal-weighted)", pct(orig["cagr_pct"]), win_loss_kind(orig["cagr_pct"])),
                   ("50/30/20 (report 37)", pct(fl5030["cagr_pct"]), win_loss_kind(fl5030["cagr_pct"])),
                   ("40/35/25 (new)", pct(fl4035["cagr_pct"]), win_loss_kind(fl4035["cagr_pct"])),
                   ("NIFTY 50", pct(nif["cagr_pct"]), win_loss_kind(nif["cagr_pct"]))]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline over the same window.",
                  [("Original (equal-weighted)", pct(orig["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("50/30/20 (report 37)", pct(fl5030["max_drawdown_pct"], 1, signed=False), "positive"),
                   ("40/35/25 (new)", pct(fl4035["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("NIFTY 50", pct(nif["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("Net return", f"{esc(R['start_date'])} to {esc(R['end_date'])}, base 100.",
                  [("Original", pct(orig["net_return_pct"]), win_loss_kind(orig["net_return_pct"])),
                   ("50/30/20", pct(fl5030["net_return_pct"]), win_loss_kind(fl5030["net_return_pct"])),
                   ("40/35/25", pct(fl4035["net_return_pct"]), win_loss_kind(fl4035["net_return_pct"]))]),
        kpi_card("Pick overlap with the original", "Average % of each rebalance's top 10 that's the SAME stock as the original formula.",
                  [("50/30/20", f"{fl5030['avg_overlap_pct']:.1f}%", "assumption"),
                   ("40/35/25", f"{fl4035['avg_overlap_pct']:.1f}%", "assumption")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, v, cls=""):
        c = f' class="{cls}"' if cls else ""
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(v['net_return_pct'])}</td><td>{pct(v['cagr_pct'])}</td>
        <td>{pct(v['max_drawdown_pct'],1,signed=False)}</td><td>{v['longest_underwater_days']:,}d</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">All four, side by side</h3>
        {pill('grey row = real benchmark, not a reconstruction', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the original formula, both front-loaded splits, and the real NIFTY 50 index, over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("Original formula (equal-weighted 6m/12m)", orig)}
          {row("Front-loaded 50/30/20 (report 37)", fl5030)}
          {row("Front-loaded 40/35/25 (new)", fl4035)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "Original (equal-weighted)", "color": COL["positive"], "points": orig["equity_curve"]},
        {"name": "50/30/20", "color": COLOR_5030, "points": fl5030["equity_curve"], "dash": True},
        {"name": "40/35/25", "color": COLOR_4035, "points": fl4035["equity_curve"], "dash": True},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=440, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_38")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how {sym}100 invested at the start of the window grew under each weighting, linear axis, not log-scaled. All three momentum lines track closely.</p>
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
        {"name": "Original (equal-weighted)", "color": COL["positive"], "points": dd_points(orig["equity_curve"])},
        {"name": "50/30/20", "color": COLOR_5030, "points": dd_points(fl5030["equity_curve"]), "dash": True},
        {"name": "40/35/25", "color": COLOR_4035, "points": dd_points(fl4035["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=260, chart_id="dd_38")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — 50/30/20 (violet) sits visibly shallower than both the original (green) and 40/35/25 (cyan) at multiple points — 40/35/25 tracks close to the original's own drawdown depth, not a smooth midpoint between the two.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why the effect isn't a smooth dial</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Cross-sectional Z-scoring and the top-10 cutoff mean the final stock SELECTION only changes when the weighting shift is large enough to
        flip which stocks cross the 10th-place threshold on a given rebalance date — small weight changes can leave many rebalances' top 10
        completely unchanged, while a specific threshold crossing at just the right weighting can flip several names at once. That's a
        discontinuous, not continuous, relationship between the weighting parameter and the actual portfolio — which is exactly why moving from
        50/30/20 to 40/35/25 recovered pick overlap with the original ({fl5030['avg_overlap_pct']:.1f}% → {fl4035['avg_overlap_pct']:.1f}%) without
        moving CAGR and drawdown in the smooth, proportional way you might expect from a "gentler" version of the same idea.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        The practical takeaway: if the goal is genuinely to reduce drawdown with the smallest possible CAGR sacrifice, 50/30/20 is the better of
        these two tested splits — not 40/35/25, even though 40/35/25 looks "closer to the original" on paper. A finer grid search across many
        weight combinations (not done here) would be needed to find whether an even better trade-off exists between them, or outside this range
        entirely.
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
        <li class="mb-1.5">Only these two specific splits were tested, not a systematic grid search — the true "best" weighting for either CAGR or drawdown alone, or any particular trade-off preference, could sit anywhere else on the weight simplex.</li>
        <li class="mb-1.5">All three windows still divide by the SAME trailing-1-year volatility as the risk-adjustment denominator, same simplification disclosed in report 37.</li>
        <li class="mb-1.5">Today's fixed NIFTY Midcap 150 constituent list is applied retroactively across the whole window for all three formulas equally (survivorship bias) — same disclosed approximation as every other reconstruction here.</li>
        <li class="mb-1.5">Zero transaction costs, slippage, or taxes modeled — same as reports 11-19/24-37's frictionless numbers (see report 32 for what real Kotak Neo charges do to a similar strategy).</li>
        <li class="mb-1.5">Equal weighting (not free-float market-cap x momentum score) and no F&O-eligibility screen, same as every other reconstruction in this project.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modeled for any holding. This is a single, fixed 18-year historical path — a different window could rank these weightings differently.</li>
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
<html lang="en"><head><meta charset="utf-8"/><title>Midcap Momentum 10 — Front-Loaded Weighting, Two Splits</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("38_midcap_momentum10_frontloaded_two_splits.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 38_midcap_momentum10_frontloaded_two_splits.html")

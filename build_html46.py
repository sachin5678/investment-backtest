"""Builds 46_midcap_momentum10_ema_span_sensitivity.html from
results45.json. Same self-contained contract as reports 42-45."""
import json
import html
from svg_charts import line_chart, COL

with open("results45.json") as f:
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
SPAN_COLORS = {100: "#6AE4FF", 150: "#8B5CF6", 200: "#37F083", 250: "#F2B03C"}


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
    orig, nif = R["original"], R["nifty"]
    spans = R["spans"]
    by_span = {s["span"]: s for s in spans}
    sym = R["currency_symbol"]

    best_dd = max(spans, key=lambda s: s["max_drawdown_pct"])   # least negative = shallowest drawdown
    best_cagr = max(spans, key=lambda s: s["cagr_pct"])

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap150 Momentum 10 — EMA-Span Sensitivity for the Regime Filter</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Report 42 picked 200 trading days for the EMA span without testing alternatives. This report runs the IDENTICAL cash/invested filter mechanics with four different spans — {', '.join(str(s) for s in R['spans_tested'])} trading days — to see whether 200 was actually a good choice, and how a wider or narrower span trades off drawdown protection against whipsaw.</p>
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
          {pill("NOT a smooth dial — wider isn't always better", 'assumption')}
          {pill(f"{best_dd['span']}-day gave the shallowest drawdown ({pct(best_dd['max_drawdown_pct'],1,signed=False)})", 'positive')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Shrinking the span from 200 to 150 to 100 days makes the filter progressively MORE protective — drawdown improves from
          {pct(by_span[200]['max_drawdown_pct'],1,signed=False)} (200-day) to {pct(by_span[150]['max_drawdown_pct'],1,signed=False)} (150-day)
          to {pct(by_span[100]['max_drawdown_pct'],1,signed=False)} (100-day) — but at the cost of far more whipsaw:
          {by_span[200]['num_regime_reentries']} re-entries at 200 days climbs to {by_span[150]['num_regime_reentries']} at 150 days and
          {by_span[100]['num_regime_reentries']} at 100 days.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          Going WIDER than 200, to 250 days, does NOT continue any clean trend — it's the worst span tested on BOTH dimensions
          at once: CAGR falls to {pct(by_span[250]['cagr_pct'])} (worse than 200-day's {pct(by_span[200]['cagr_pct'])}) AND drawdown
          gets deeper, {pct(by_span[250]['max_drawdown_pct'],1,signed=False)} vs. 200-day's {pct(by_span[200]['max_drawdown_pct'],1,signed=False)} —
          despite triggering the FEWEST re-entries of any span tested. A slower signal isn't automatically a better one; it can just
          mean late exits and late re-entries that miss both the protection and the recovery.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR by span", "Compound annual growth rate, identical window for every span.",
                  [("No filter", pct(orig["cagr_pct"]), "neutral")] +
                  [(f"{s['span']}-day EMA", pct(s["cagr_pct"]), "positive" if s["span"] == best_cagr["span"] else "neutral") for s in spans] +
                  [("NIFTY 50", pct(nif["cagr_pct"]), "neutral")]),
        kpi_card("Max drawdown by span", "Largest peak-to-trough decline, identical window for every span.",
                  [("No filter", pct(orig["max_drawdown_pct"], 1, signed=False), "negative")] +
                  [(f"{s['span']}-day EMA", pct(s["max_drawdown_pct"], 1, signed=False), "positive" if s["span"] == best_dd["span"] else "neutral") for s in spans] +
                  [("NIFTY 50", pct(nif["max_drawdown_pct"], 1, signed=False), "negative")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-1 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, cagr, dd, net, uw, reentries=None, cash_pct=None, cls="", highlight=False):
        c = f' class="{cls} highlight"' if highlight else (f' class="{cls}"' if cls else "")
        reentries_str = f"{reentries}" if reentries is not None else "—"
        cash_str = f"{cash_pct:.1f}%" if cash_pct is not None else "—"
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(net)}</td><td>{pct(cagr)}</td>
        <td>{pct(dd,1,signed=False)}</td><td>{uw:,}d</td><td>{cash_str}</td><td>{reentries_str}</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">All four spans, side by side</h3>
        {pill("highlighted row = report 42's original 200-day choice", 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every EMA span tested against the unfiltered strategy and the real NIFTY 50 index, over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th><th>Time in cash</th><th>Re-entries</th></tr></thead>
        <tbody>
          {row("No filter (always invested)", orig['cagr_pct'], orig['max_drawdown_pct'], orig['net_return_pct'], orig['longest_underwater_days'])}
          {"".join(row(f"{s['span']}-day EMA regime filter", s['cagr_pct'], s['max_drawdown_pct'], s['net_return_pct'], s['longest_underwater_days'], s['num_regime_reentries'], s['pct_time_in_cash'], highlight=(s['span']==200)) for s in spans)}
          {row("NIFTY 50 (real index)", nif['cagr_pct'], nif['max_drawdown_pct'], nif['net_return_pct'], nif['longest_underwater_days'], cls="real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [{"name": "No filter", "color": COL["muted"], "points": orig["equity_curve"], "dash": True}]
    for s in spans:
        eq_series.append({"name": f"{s['span']}-day EMA", "color": SPAN_COLORS[s["span"]], "points": s["equity_curve"]})
    eq_svg, eq_legend = line_chart(eq_series, height=440, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_46")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — every span, {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how {sym}100 invested at the start of the window grew under each EMA span, linear axis, not log-scaled. The 250-day line (amber) visibly lags the tighter spans through the window's steepest recoveries.</p>
      <div class="flex items-center mb-2 flex-wrap">{eq_legend}</div>
      {eq_svg}
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Reading the trade-off correctly</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        A shorter EMA span tracks price more closely, so it reacts to a downturn sooner — which is why 100-day gives the
        shallowest drawdown of any span tested ({pct(best_dd['max_drawdown_pct'],1,signed=False)}). The cost is that a
        closely-tracking average also crosses back and forth more often during ordinary volatility that ISN'T a real trend
        change, which is why 100-day also has by far the most re-entries ({by_span[100]['num_regime_reentries']} vs. 200-day's
        {by_span[200]['num_regime_reentries']}) — nearly {by_span[100]['num_regime_reentries'] / by_span[200]['num_regime_reentries']:.1f}x
        the whipsaw, and this backtest still charges nothing for any of them.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        250-day's poor showing on BOTH axes is the more surprising result: it has the FEWEST re-entries
        ({by_span[250]['num_regime_reentries']}) of any span, confirming it really is the "calmest" signal — but calmness alone
        didn't help here. A slow-moving average exits late into declines (giving back more before the filter reacts) and
        re-enters late into recoveries (missing more of the bounce), and in this specific 18-year path that combination cost
        both CAGR and drawdown protection relative to 200-day. This is a genuine finding about THIS historical window, not a
        general law that "wider is worse" — a different window could rank these four spans differently.
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
        <li class="mb-1.5">Zero transaction costs on ANY regime switch across all four spans — the shorter spans in particular would look meaningfully worse once realistic per-trade costs are included, given how much more often they switch.</li>
        <li class="mb-1.5">Cash earns exactly 0% while any span is out of the market, same convention as reports 03, 42-45.</li>
        <li class="mb-1.5">Only four spans were tested (100/150/200/250) — the true optimum, if one exists, could sit between or outside these points; this is a coarse sensitivity check, not an exhaustive search.</li>
        <li class="mb-1.5">Only ONE historical window (2008-2026) is tested — report 46's "250 is worse than 200" finding is specific to this path and is not guaranteed to hold in a different period. See report 47 for a different kind of whipsaw fix (a confirmation delay) applied to the 200-day span specifically.</li>
        <li class="mb-1.5">Today's fixed Midcap150 constituent list is applied retroactively across the whole window (survivorship bias). Equal weighting, no F&O-eligibility screen, unadjusted prices, no dividends modeled — same as every other reconstruction here.</li>
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
<html lang="en"><head><meta charset="utf-8"/><title>Midcap150 Momentum 10 — EMA-Span Sensitivity</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("46_midcap_momentum10_ema_span_sensitivity.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 46_midcap_momentum10_ema_span_sensitivity.html")

"""Builds 63_smallcap250_momentum10_absolute_momentum_gate.html from results62.json."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results62.json") as f:
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
    orig, gated, nif = R["original"], R["gated"], R["nifty"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Smallcap250 Momentum 10 — Absolute Momentum Gate</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Report 62 tested the classic dual-momentum absolute-return gate on Midcap150 — the gate barely fired and cost a little CAGR for no drawdown benefit. This applies the identical gate to report 16/29's Smallcap250 Momentum 10 config.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(R['start_date'])}–{esc(R['end_date'])} · {R['num_rebalances']} rebalances<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2643C]">
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          {pill('same non-event, but a bigger CAGR cost this time', 'negative')}
          {pill(f"only {R['num_partial_fill_rebalances']} of {R['num_rebalances']} rebalances ever had an unfilled slot", 'neutral')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Drawdown is again IDENTICAL to the original ({pct(orig['max_drawdown_pct'],1,signed=False)} either way), but the
          CAGR cost is larger than Midcap150's: {pct(orig['cagr_pct'])} to <span class="font-semibold">{pct(gated['cagr_pct'])}</span>.
          The gate still only fired in {R['num_partial_fill_rebalances']} of {R['num_rebalances']} rebalances, averaging
          {R['avg_slots_filled']} of 10 slots filled.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The mechanism is the same as report 62 — relative and absolute momentum mostly agree — but smallcap stocks are
          more volatile, so the FEW positions the gate does exclude are likely names with larger swings, and losing access
          to even one or two big winners in a 10-stock portfolio has a bigger relative impact on CAGR than in a calmer
          universe.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR", "Compound annual growth rate, identical window for both.",
                  [("No gate (original)", pct(orig["cagr_pct"]), win_loss_kind(orig["cagr_pct"])),
                   ("Absolute momentum gate", pct(gated["cagr_pct"]), win_loss_kind(gated["cagr_pct"])),
                   ("NIFTY 50", pct(nif["cagr_pct"]), "neutral")]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline over the same window.",
                  [("No gate (original)", pct(orig["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Absolute momentum gate", pct(gated["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("NIFTY 50", pct(nif["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("How often does the gate actually bite", "Rebalances where at least one slot went unfilled.",
                  [("Partial-fill rebalances", f"{R['num_partial_fill_rebalances']} / {R['num_rebalances']}", "assumption"),
                   ("Avg slots filled", f"{R['avg_slots_filled']} / 10", "assumption")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, v, cls=""):
        c = f' class="{cls}"' if cls else ""
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(v['net_return_pct'])}</td><td>{pct(v['cagr_pct'])}</td>
        <td>{pct(v['max_drawdown_pct'],1,signed=False)}</td><td>{v['longest_underwater_days']:,}d</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Both versions, side by side</h3>
        {pill('grey row = real benchmark, not a reconstruction', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the gated and ungated Smallcap250 Momentum 10 formulas against the real NIFTY 50 index, over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("Smallcap250 Momentum 10 — no gate (original)", orig)}
          {row("Smallcap250 Momentum 10 — absolute momentum gate", gated)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "No gate (original)", "color": COL["positive"], "points": orig["equity_curve"]},
        {"name": "Absolute momentum gate", "color": COL["negative"], "points": gated["equity_curve"], "dash": True},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_63")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how {R['currency_symbol']}100 invested at the start of the window grew under each version, linear axis, not log-scaled.</p>
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
        {"name": "No gate (original)", "color": COL["positive"], "points": dd_points(orig["equity_curve"])},
        {"name": "Absolute momentum gate", "color": COL["negative"], "points": dd_points(gated["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=220, chart_id="dd_63")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the two drawdown paths are IDENTICAL ({pct(orig['max_drawdown_pct'],1,signed=False)} both).</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">A bigger cost for the same non-result</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        As in report 62, the gate hardly ever fires — relative top-10 status and positive absolute 12-month return are
        highly correlated in a normal market. But when it DOES exclude a name here, that name is drawn from a more volatile
        universe, so its would-have-been contribution to the portfolio (positive or negative) tends to be larger in
        magnitude. Since the gate specifically fires only in the AFTERMATH of a crash — precisely when a genuine V-shaped
        recovery candidate might otherwise be excluded for still showing a negative 12-month return even as it's about to
        rip higher — a bigger CAGR cost for smallcaps (which tend to have sharper V-shaped recoveries than midcaps) is a
        plausible explanation, though this report can't isolate that from other noise with only one real crash in the data.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        The drawdown result is unchanged from report 62's finding: the gate doesn't touch the specific stretch where the
        worst decline happens, because by the time the crash is UNDERWAY, the top-10 by relative score is typically still
        absolute-positive (the crash hasn't lasted 12 months yet).
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
        <li class="mb-1.5">The gate is checked only at scheduled June/December rebalances — a stock that qualifies at entry but turns absolute-negative mid-period is still held until the next rebalance.</li>
        <li class="mb-1.5">Only a 12-month absolute-return threshold (> 0%) was tested — a different lookback window or buffer could behave differently.</li>
        <li class="mb-1.5">Unfilled slots sit in cash at 0% return, same convention as every cash-holding report here.</li>
        <li class="mb-1.5">Zero transaction costs, slippage, or taxes modeled — same as every other reconstruction in this project.</li>
        <li class="mb-1.5">No official "Smallcap250 Momentum 10" index exists — the June/December cadence is a borrowed convention. This is a single, fixed 18-year historical path with only one truly severe crash (2008) to test the gate against.</li>
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
<html lang="en"><head><meta charset="utf-8"/><title>Smallcap250 Momentum 10 — Absolute Momentum Gate</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("63_smallcap250_momentum10_absolute_momentum_gate.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 63_smallcap250_momentum10_absolute_momentum_gate.html")

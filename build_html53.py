"""Builds 53_nifty100_momentum10_invvol_weighting.html from results52.json."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results52.json") as f:
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
    equal, invvol, nif = R["equal"], R["invvol"], R["nifty"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">NIFTY100 Momentum 10 — Inverse-Volatility Position Sizing</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Reports 51-52 tested weighting each top-10 pick inversely to its own trailing 1-year volatility on Midcap150 and Smallcap250. This applies the identical mechanics to report 12's NIFTY100 Momentum 10 config — the lowest-volatility universe in this comparison, where reformulations have previously behaved differently from the broader ones (report 41's front-loading actively backfired here).</p>
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
          {pill('still a modest trade-off, not a breakdown like report 41', 'assumption')}
          {pill(f"{R['avg_overlap_pct']:.1f}% average pick overlap (same tickers, different weights)", 'neutral')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          On NIFTY100, inverse-vol weighting costs CAGR — {pct(equal['cagr_pct'])} to
          <span class="font-semibold">{pct(invvol['cagr_pct'])}</span> — for a modest drawdown improvement:
          {pct(equal['max_drawdown_pct'],1,signed=False)} to <span class="font-semibold">{pct(invvol['max_drawdown_pct'],1,signed=False)}</span>.
          Unlike report 41's front-loaded-momentum test — where NIFTY100 was the ONE universe where the reformulation actively
          backfired on BOTH dimensions — this weighting change behaves the same way here as it does on Midcap150 and
          Smallcap250: a real but modest trade-off, not a breakdown.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          That's consistent with this project's emerging pattern: changes that touch WHICH stocks get selected (like
          front-loading) are the ones sensitive to universe breadth; changes that only touch position SIZING or WHEN the
          strategy is invested (like this report, or the 200-EMA filter) behave consistently across universes.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR", "Compound annual growth rate, identical window for both weighting schemes.",
                  [("Equal-weight (original)", pct(equal["cagr_pct"]), win_loss_kind(equal["cagr_pct"])),
                   ("Inverse-vol weight", pct(invvol["cagr_pct"]), win_loss_kind(invvol["cagr_pct"])),
                   ("NIFTY 50", pct(nif["cagr_pct"]), "neutral")]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline over the same window.",
                  [("Equal-weight (original)", pct(equal["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Inverse-vol weight", pct(invvol["max_drawdown_pct"], 1, signed=False), "positive"),
                   ("NIFTY 50", pct(nif["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("Net return", f"{esc(R['start_date'])} to {esc(R['end_date'])}, base 100.",
                  [("Equal-weight", pct(equal["net_return_pct"]), win_loss_kind(equal["net_return_pct"])),
                   ("Inverse-vol", pct(invvol["net_return_pct"]), win_loss_kind(invvol["net_return_pct"]))]),
    ]
    kpi_grid = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, v, cls=""):
        c = f' class="{cls}"' if cls else ""
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(v['net_return_pct'])}</td><td>{pct(v['cagr_pct'])}</td>
        <td>{pct(v['max_drawdown_pct'],1,signed=False)}</td><td>{v['longest_underwater_days']:,}d</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Both weighting schemes, side by side</h3>
        {pill('grey row = real benchmark, not a reconstruction', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — equal-weight and inverse-vol weighted NIFTY100 Momentum 10 against the real NIFTY 50 index, over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("NIFTY100 Momentum 10 — equal-weight (original)", equal)}
          {row("NIFTY100 Momentum 10 — inverse-vol weight", invvol)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "Equal-weight (original)", "color": COL["negative"], "points": equal["equity_curve"]},
        {"name": "Inverse-vol weight", "color": COL["positive"], "points": invvol["equity_curve"], "dash": True},
        {"name": "NIFTY 50", "color": COL["text"], "points": nif["equity_curve"], "dash": True},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_53")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how {R['currency_symbol']}100 invested at the start of the window grew under each weighting scheme, linear axis, not log-scaled.</p>
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
        {"name": "Equal-weight (original)", "color": COL["negative"], "points": dd_points(equal["equity_curve"])},
        {"name": "Inverse-vol weight", "color": COL["positive"], "points": dd_points(invvol["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=220, chart_id="dd_53")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — inverse-vol weighting's drawdown improvement ({pct(equal['max_drawdown_pct'],1,signed=False)} to {pct(invvol['max_drawdown_pct'],1,signed=False)}).</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    def weight_row(s):
        w = s.get("weights_pct", {})
        parts = ", ".join(f"{t} ({w.get(t, '—')}%)" for t in s["tickers"])
        return f"""<tr><td>{esc(s['date'])}</td><td style="text-align:left">{esc(parts)}</td></tr>"""

    weights_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Sample rebalances — inverse-vol weights actually assigned</h3>
        {pill('first 3 and last 3 of ' + str(R['num_rebalances']) + ' shown', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the SAME top-10 picks as the equal-weight version, but with each one's actual capital allocation.</p>
      <table class="data-table"><thead><tr><th>Date</th><th style="text-align:left">Ticker (weight %)</th></tr></thead>
      <tbody>{''.join(weight_row(s) for s in R['invvol']['selections_sample'])}</tbody></table>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">A weighting change, not a selection change</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Report 41 found front-loaded momentum weighting broke down specifically on NIFTY100 because a narrower universe gave
        the reformulated SELECTION formula fewer genuinely-strong alternatives to fall back on. Inverse-vol weighting never
        touches selection — the picks here are IDENTICAL to the equal-weight version, only their dollar allocation differs —
        so there's no "fewer candidates" failure mode to trigger. That's exactly why this change performs consistently across
        all three universes (reports 51-53) while front-loading did not.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        Like reports 51-52, most of this strategy's largest drawdowns come from broad market declines that hit every stock in
        the top 10 together — a within-portfolio reweighting can only do so much about that. Compare to report 45's 200-EMA
        filter on this same NIFTY100 universe, which sidesteps entire downturns rather than reweighting within them.
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
        <li class="mb-1.5">Weights are recomputed fresh at EVERY rebalance from a 1-year trailing window — a short, unusual volatility spike right before a rebalance date could distort a stock's weight for the following 6 months.</li>
        <li class="mb-1.5">No cap or floor on individual weights (see the sample weights table above).</li>
        <li class="mb-1.5">Zero transaction costs, slippage, or taxes modeled — same as every other reconstruction in this project.</li>
        <li class="mb-1.5">Only inverse-1-year-volatility weighting was tested — a different lookback or weighting rule could produce a different trade-off.</li>
        <li class="mb-1.5">Today's fixed NIFTY100 constituent list (report 12's config) is applied retroactively (survivorship bias). This is a single, fixed 18-year historical path.</li>
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
      {weights_panel}
      {honesty_note}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>NIFTY100 Momentum 10 — Inverse-Vol Weighting</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("53_nifty100_momentum10_invvol_weighting.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 53_nifty100_momentum10_invvol_weighting.html")

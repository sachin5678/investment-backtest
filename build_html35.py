"""Builds 35_midcap_momentum10_bottom10_reversal.html from results34.json.
Same self-contained contract, smooth Catmull-Rom charts, dark palette as
every other report."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results34.json") as f:
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
    top, bottom, nif = R["top"], R["bottom"], R["nifty"]
    sym = R["currency_symbol"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap Momentum 10 — Bottom-10 Reversal Sanity Check</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Not a formula refinement — a discipline check. Exact same score as the original formula, but this report deliberately buys the WORST 10 stocks by that score each rebalance instead of the best 10. If momentum is real, bottom-10 should reliably lose to top-10.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(R['start_date'])}–{esc(R['end_date'])} · {R['num_rebalances']} rebalances<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#37F083]">
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          {pill('momentum passes the sanity check', 'positive')}
          {pill(f"{R['total_overlap_names']} shared names across all rebalances (harness sanity check)", 'neutral')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Every other formula variant in this project tweaks one piece of the momentum score and checks whether the result changes sensibly.
          This one is different in kind: it asks whether the score is capturing something real at all. Bottom-10 uses the EXACT same 6m/12m
          risk-adjusted, cross-sectionally Z-scored score as the original — the only change is selecting the lowest-ranked 10 names instead of
          the highest-ranked 10.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The result: bottom-10 clearly loses. CAGR {pct(bottom['cagr_pct'])} vs. top-10's {pct(top['cagr_pct'])}, and a much deeper max drawdown
          ({pct(bottom['max_drawdown_pct'],1,signed=False)} vs. {pct(top['max_drawdown_pct'],1,signed=False)}). That's real evidence the score is
          doing genuine work, not noise a different random seed would just as easily reverse — see the honesty note below for one important
          caveat: bottom-10 still beat NIFTY 50 itself, which is worth understanding correctly rather than over-reading.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR", "Compound annual growth rate, identical window for all three.",
                  [("Top-10 (momentum)", pct(top["cagr_pct"]), win_loss_kind(top["cagr_pct"])),
                   ("Bottom-10 (reversal)", pct(bottom["cagr_pct"]), win_loss_kind(bottom["cagr_pct"])),
                   ("NIFTY 50", pct(nif["cagr_pct"]), win_loss_kind(nif["cagr_pct"]))]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline over the same window.",
                  [("Top-10 (momentum)", pct(top["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Bottom-10 (reversal)", pct(bottom["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("NIFTY 50", pct(nif["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("Net return", f"{esc(R['start_date'])} to {esc(R['end_date'])}, base 100.",
                  [("Top-10 (momentum)", pct(top["net_return_pct"]), win_loss_kind(top["net_return_pct"])),
                   ("Bottom-10 (reversal)", pct(bottom["net_return_pct"]), win_loss_kind(bottom["net_return_pct"]))]),
        kpi_card("Harness sanity check", "Best-10 and worst-10 of the same ranked list should never overlap.",
                  [("Shared names, all rebalances", f"{R['total_overlap_names']}", "positive" if R['total_overlap_names'] == 0 else "negative")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(kpis)}</div>'

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
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the momentum strategy and its deliberate inversion against the real NIFTY 50 index, over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("Top-10 (the actual momentum strategy)", top)}
          {row("Bottom-10 (deliberate reversal)", bottom)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "Top-10 (momentum)", "color": COL["positive"], "points": top["equity_curve"]},
        {"name": "Bottom-10 (reversal)", "color": COL["negative"], "points": bottom["equity_curve"]},
        {"name": "NIFTY 50", "color": COL["text"], "points": nif["equity_curve"], "dash": True},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_35")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how {sym}100 invested at the start of the window grew under each selection — top-10 (green) pulls decisively ahead of bottom-10 (red) for almost the entire 18-year window, not just at the end.</p>
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
        {"name": "Top-10 (momentum)", "color": COL["positive"], "points": dd_points(top["equity_curve"])},
        {"name": "Bottom-10 (reversal)", "color": COL["negative"], "points": dd_points(bottom["equity_curve"])},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=220, chart_id="dd_35")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — bottom-10's drawdown ({pct(bottom['max_drawdown_pct'],1,signed=False)}) is far deeper than top-10's ({pct(top['max_drawdown_pct'],1,signed=False)}) — the worst-ranked names by this exact score really did fall harder, not just compound slower.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    def sel_row(s):
        return f"""<tr><td>{esc(s['date'])}</td><td style="text-align:left">{esc(', '.join(s['tickers']))}</td></tr>"""

    selections_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Sample rebalances — opposite ends of the same ranked list</h3>
        {pill('first 3 and last 3 of ' + str(R['num_rebalances']) + ' shown for each', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the actual top-10 and bottom-10 picks at the same rebalance dates, by construction always disjoint sets from the same day's ranked list.</p>
      <div class="mb-4">
        <div class="text-[13px] font-semibold text-[#C9D6DA] mb-2">Top-10 (momentum)</div>
        <table class="data-table"><thead><tr><th>Date</th><th style="text-align:left">Top 10 selected</th></tr></thead>
        <tbody>{''.join(sel_row(s) for s in R['top']['selections_sample'])}</tbody></table>
      </div>
      <div>
        <div class="text-[13px] font-semibold text-[#C9D6DA] mb-2">Bottom-10 (reversal)</div>
        <table class="data-table"><thead><tr><th>Date</th><th style="text-align:left">Bottom 10 selected</th></tr></thead>
        <tbody>{''.join(sel_row(s) for s in R['bottom']['selections_sample'])}</tbody></table>
      </div>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">What this does and doesn't prove</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        The clean gap between top-10 and bottom-10 — both {pct(top['cagr_pct'] - bottom['cagr_pct'],1,signed=False)} points of CAGR and a much
        deeper drawdown for bottom-10 — is exactly what a genuine momentum effect should produce, and is good evidence that the score used
        throughout reports 11-19/24-34 is capturing something real about these stocks, not noise from an arbitrarily lucky simulation.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        One important thing this does NOT show: that bottom-10 is a bad strategy in absolute terms. Bottom-10 still compounded at
        {pct(bottom['cagr_pct'])} — comfortably ahead of NIFTY 50's own {pct(nif['cagr_pct'])} — despite being the deliberately worst-ranked
        names in the universe by this score. That's most plausibly explained by the general midcap risk premium over this specific 18-year
        window (even the WORST midcap picks by this measure benefited from midcaps broadly outperforming large caps over most of 2008-2026, per
        every other midcap-vs-NIFTY comparison in this project), not by any skill in this bottom-ranking. Don't read "bottom-10 beat the
        index" as "reversal also works" — it's a reminder that a rising-universe backdrop can flatter even a strategy's designed-to-fail control
        group.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        This result also does not validate every OTHER variant tested in this project's momentum family (reports 25, 27, 30, 33, 34) — it only
        confirms that the underlying score, at its two extremes, behaves the way a real momentum effect should. Each of those other reports still
        needs to be judged on its own comparison to the original, which is exactly what they each do.
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
        <li class="mb-1.5">Today's fixed NIFTY Midcap 150 constituent list is applied retroactively across the whole window for both selections equally (survivorship bias) — same disclosed approximation as every other reconstruction here.</li>
        <li class="mb-1.5">Zero transaction costs, slippage, or taxes modeled — same as reports 11-19/24-34's frictionless numbers (see report 32 for what real Kotak Neo charges do to a similar strategy).</li>
        <li class="mb-1.5">Equal weighting (not free-float market-cap x momentum score) and no F&O-eligibility screen, same as every other reconstruction in this project.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modeled for any holding. This is a single, fixed 18-year historical path — a window with less of a general midcap-over-largecap tailwind could show bottom-10 losing to NIFTY 50 too, unlike here.</li>
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
      {selections_panel}
      {honesty_note}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Midcap Momentum 10 — Bottom-10 Reversal Sanity Check</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("35_midcap_momentum10_bottom10_reversal.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 35_midcap_momentum10_bottom10_reversal.html")

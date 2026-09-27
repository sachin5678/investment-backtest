"""Builds 47_midcap_momentum10_confirmation_delay_sensitivity.html from
results46.json. Same self-contained contract as reports 42-46."""
import json
import html
from svg_charts import line_chart, COL

with open("results46.json") as f:
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
VARIANT_COLORS = {1: "#37F083", 3: "#6AE4FF", 5: "#8B5CF6", 10: "#F2B03C"}


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
    variants = R["variants"]
    by_cd = {v["confirm_days"]: v for v in variants}

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap150 Momentum 10 — Confirmation-Delay Sensitivity for the Regime Filter</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Report 42's biggest disclosed weakness: 69 regime re-entries over 18 years, almost 2x its own scheduled rebalance count, all free of transaction costs in that model. This report tests the user's whipsaw-reduction idea directly — require NIFTY 50's signal to disagree with the current state for {', '.join(str(c) for c in R['confirm_days_tested'][1:])} CONSECUTIVE trading days (not just 1) before the filter actually switches — same 200-day EMA, same Midcap150 Momentum 10 formula throughout.</p>
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
          {pill('fewer whipsaws, but NOT a free improvement', 'negative')}
          {pill(f"re-entries fall from {by_cd[1]['num_regime_reentries']} to {by_cd[10]['num_regime_reentries']} (1-day vs. 10-day confirmation)", 'positive')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Requiring confirmation works exactly as intended on whipsaw: re-entries drop steadily as the delay grows —
          {by_cd[1]['num_regime_reentries']} (1-day, report 42's original) → {by_cd[3]['num_regime_reentries']} (3-day) →
          {by_cd[5]['num_regime_reentries']} (5-day) → {by_cd[10]['num_regime_reentries']} (10-day).
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          But CAGR falls steadily too — {pct(by_cd[1]['cagr_pct'])} → {pct(by_cd[3]['cagr_pct'])} → {pct(by_cd[5]['cagr_pct'])} →
          {pct(by_cd[10]['cagr_pct'])} — and drawdown does NOT reliably improve to compensate: 3-day confirmation is actually WORSE on
          drawdown ({pct(by_cd[3]['max_drawdown_pct'],1,signed=False)}) than the immediate 1-day switch
          ({pct(by_cd[1]['max_drawdown_pct'],1,signed=False)}), before 10-day finally edges it out slightly
          ({pct(by_cd[10]['max_drawdown_pct'],1,signed=False)}) at a much larger CAGR cost. In this historical window, the
          immediate-switch version from report 42 is the best risk-adjusted choice of the four tested — the whipsaw-reduction
          idea reduces trading activity as intended, but doesn't pay for itself here.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR by confirmation delay", "Compound annual growth rate, identical window for every variant.",
                  [("No filter", pct(orig["cagr_pct"]), "neutral")] +
                  [(f"{v['confirm_days']}-day confirm", pct(v["cagr_pct"]), "positive" if v["confirm_days"] == 1 else "neutral") for v in variants] +
                  [("NIFTY 50", pct(nif["cagr_pct"]), "neutral")]),
        kpi_card("Max drawdown by confirmation delay", "Largest peak-to-trough decline, identical window for every variant.",
                  [("No filter", pct(orig["max_drawdown_pct"], 1, signed=False), "negative")] +
                  [(f"{v['confirm_days']}-day confirm", pct(v["max_drawdown_pct"], 1, signed=False), "neutral") for v in variants] +
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
        <h3 class="text-base font-bold text-[#E6EDF0]">All four confirmation delays, side by side</h3>
        {pill("highlighted row = report 42's original immediate-switch (1-day)", 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every confirmation delay tested against the unfiltered strategy and the real NIFTY 50 index, over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window. Same 200-day EMA span throughout.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th><th>Time in cash</th><th>Re-entries</th></tr></thead>
        <tbody>
          {row("No filter (always invested)", orig['cagr_pct'], orig['max_drawdown_pct'], orig['net_return_pct'], orig['longest_underwater_days'])}
          {"".join(row(f"{v['confirm_days']}-day confirmation", v['cagr_pct'], v['max_drawdown_pct'], v['net_return_pct'], v['longest_underwater_days'], v['num_regime_reentries'], v['pct_time_in_cash'], highlight=(v['confirm_days']==1)) for v in variants)}
          {row("NIFTY 50 (real index)", nif['cagr_pct'], nif['max_drawdown_pct'], nif['net_return_pct'], nif['longest_underwater_days'], cls="real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [{"name": "No filter", "color": COL["muted"], "points": orig["equity_curve"], "dash": True}]
    for v in variants:
        eq_series.append({"name": f"{v['confirm_days']}-day confirm", "color": VARIANT_COLORS[v["confirm_days"]], "points": v["equity_curve"]})
    eq_svg, eq_legend = line_chart(eq_series, height=440, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_47")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — every confirmation delay, {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how {R['currency_symbol']}100 invested at the start of the window grew under each confirmation delay, linear axis, not log-scaled. Longer delays (purple, amber) visibly fall further behind — confirmation costs real return, it doesn't just filter noise for free.</p>
      <div class="flex items-center mb-2 flex-wrap">{eq_legend}</div>
      {eq_svg}
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why "wait for confirmation" isn't a free whipsaw fix</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        A confirmation delay works by definition: it ignores single-day or short-lived crossings of the EMA, so it only acts on
        moves that persist. That's exactly why re-entries fall so sharply ({by_cd[1]['num_regime_reentries']} → {by_cd[10]['num_regime_reentries']}
        from 1-day to 10-day). The problem is that a REAL trend change also starts as a single day that has to persist before it's
        "confirmed" — so every extra day of confirmation is also an extra day of being on the wrong side of a genuine move, both
        entering AND exiting. Over 18 years, those extra wrong-side days added up to more lost CAGR than the avoided whipsaws saved,
        which is the honest reason the immediate 1-day switch — the version this project already tested in report 42 — comes out
        ahead of every slower alternative tried here.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        This does NOT mean confirmation delays are a bad idea in general — a different EMA span, a different confirmation
        window, or a different market history could rank these differently, and a real trader who cares specifically about
        NOT paying commissions on {by_cd[1]['num_regime_reentries']} round-trips might still prefer a slower, cheaper-to-run
        variant even at this CAGR cost. What this report shows is that "add a confirmation delay" is a REAL trade-off to be made
        deliberately, not a strictly-better refinement of report 42's filter.
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
        <li class="mb-1.5">Zero transaction costs on ANY regime switch across all four variants — the shorter-delay variants would look relatively BETTER once realistic per-trade costs are included, since they're being compared here on a frictionless basis that ignores their own whipsaw cost.</li>
        <li class="mb-1.5">Cash earns exactly 0% while any variant is out of the market, same convention as reports 03, 42-46.</li>
        <li class="mb-1.5">Only one EMA span (200 trading days, report 42's choice) was tested with confirmation delays — see report 46 for span sensitivity WITHOUT a confirmation delay; the two haven't been tested in combination.</li>
        <li class="mb-1.5">Only four confirmation delays were tested (1/3/5/10 days) — the true optimum, if one exists, could sit between or outside these points.</li>
        <li class="mb-1.5">Only ONE historical window (2008-2026) is tested — this ranking is specific to this path and is not guaranteed to hold in a different period.</li>
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
<html lang="en"><head><meta charset="utf-8"/><title>Midcap150 Momentum 10 — Confirmation-Delay Sensitivity</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("47_midcap_momentum10_confirmation_delay_sensitivity.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 47_midcap_momentum10_confirmation_delay_sensitivity.html")

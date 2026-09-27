"""Builds 60_smallcap250_momentum10_asymmetric_ema.html from results59.json."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results59.json") as f:
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
    orig, sym, asym, nif = R["original"], R["symmetric"], R["asymmetric"], R["nifty"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Smallcap250 Momentum 10 — Asymmetric EMA Regime Filter</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Report 59 tested exiting on the slow 200-day EMA but re-entering on a faster {R['reentry_ema_span']}-day EMA, on Midcap150 — a clean loss. This applies the identical mechanics to report 16/29's Smallcap250 Momentum 10 config, to see whether the idea fares any better on a second universe.</p>
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
          {pill('the same failure mode as Midcap150 (report 59)', 'negative')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          On Smallcap250, CAGR is roughly flat — {pct(sym['cagr_pct'])} (symmetric) to <span class="font-semibold">{pct(asym['cagr_pct'])}</span>
          (asymmetric) — but drawdown gets meaningfully WORSE: {pct(sym['max_drawdown_pct'],1,signed=False)} to
          <span class="font-semibold">{pct(asym['max_drawdown_pct'],1,signed=False)}</span>, and re-entries again more than
          double, {sym['num_regime_reentries']} to {asym['num_regime_reentries']}.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          Same mechanism as report 59: a faster re-entry signal catches false starts during a still-declining market, and the
          slow 200-day exit signal doesn't react quickly enough to cut the resulting extra exposure short.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR", "Compound annual growth rate, identical window for all three.",
                  [("No filter", pct(orig["cagr_pct"]), win_loss_kind(orig["cagr_pct"])),
                   ("Symmetric 200/200", pct(sym["cagr_pct"]), win_loss_kind(sym["cagr_pct"])),
                   (f"Asymmetric 200/{R['reentry_ema_span']}", pct(asym["cagr_pct"]), win_loss_kind(asym["cagr_pct"])),
                   ("NIFTY 50", pct(nif["cagr_pct"]), "neutral")]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline over the same window.",
                  [("No filter", pct(orig["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Symmetric 200/200", pct(sym["max_drawdown_pct"], 1, signed=False), "positive"),
                   (f"Asymmetric 200/{R['reentry_ema_span']}", pct(asym["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("NIFTY 50", pct(nif["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("How active is each filter", "Time in cash and re-entries for each design.",
                  [("Symmetric: time in cash", f"{sym['pct_time_in_cash']:.1f}%", "assumption"),
                   ("Symmetric: re-entries", f"{sym['num_regime_reentries']}", "assumption"),
                   ("Asymmetric: time in cash", f"{asym['pct_time_in_cash']:.1f}%", "assumption"),
                   ("Asymmetric: re-entries", f"{asym['num_regime_reentries']}", "negative")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-1 gap-4 mt-6">{"".join(kpis)}</div>'

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
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every series over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("Smallcap250 Momentum 10 — no filter", orig)}
          {row("Smallcap250 Momentum 10 — symmetric 200/200 (report 44)", sym)}
          {row(f"Smallcap250 Momentum 10 — asymmetric 200/{R['reentry_ema_span']}", asym)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "No filter", "color": COL["muted"], "points": orig["equity_curve"], "dash": True},
        {"name": "Symmetric 200/200", "color": COL["positive"], "points": sym["equity_curve"]},
        {"name": f"Asymmetric 200/{R['reentry_ema_span']}", "color": COL["negative"], "points": asym["equity_curve"]},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_60")
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
        {"name": "Symmetric 200/200", "color": COL["positive"], "points": dd_points(sym["equity_curve"])},
        {"name": f"Asymmetric 200/{R['reentry_ema_span']}", "color": COL["negative"], "points": dd_points(asym["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=220, chart_id="dd_60")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the asymmetric version's drawdown ({pct(asym['max_drawdown_pct'],1,signed=False)}) is deeper than the symmetric version's ({pct(sym['max_drawdown_pct'],1,signed=False)}).</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">A second universe, the same false-start problem</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Same explanation as report 59: the {R['reentry_ema_span']}-day EMA is choppy enough to flag "recovery" on moves that
        turn out to be temporary bounces within a still-declining market, and the slow 200-day exit signal doesn't cut that
        exposure short quickly enough to avoid the follow-through decline. Smallcap stocks, being typically MORE volatile
        than midcaps, would be expected to produce even MORE false starts from a fast signal — consistent with re-entries
        again more than doubling here.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        Two universes now agree: pairing a fast re-entry signal with a slow exit signal doesn't get "the best of both speeds"
        — it imports the fast signal's false-positive rate into an otherwise slow, reliable filter.
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
        <li class="mb-1.5">Only ONE re-entry span ({R['reentry_ema_span']} days) was tested — a less aggressive choice might behave differently.</li>
        <li class="mb-1.5">Zero transaction costs on ANY regime switch — with {asym['num_regime_reentries']} re-entries, this omission matters even more here.</li>
        <li class="mb-1.5">Cash earns exactly 0% while out of the market, same convention as every regime-filter report here.</li>
        <li class="mb-1.5">No official "Smallcap250 Momentum 10" index exists — the June/December cadence is a borrowed convention. Today's fixed constituent list is applied retroactively (survivorship bias). This is a single, fixed 18-year historical path.</li>
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
<html lang="en"><head><meta charset="utf-8"/><title>Smallcap250 Momentum 10 — Asymmetric EMA Filter</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("60_smallcap250_momentum10_asymmetric_ema.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 60_smallcap250_momentum10_asymmetric_ema.html")

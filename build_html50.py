"""Builds 50_nifty100_momentum10_gold_vs_cash.html from results49.json."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results49.json") as f:
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
    orig, cash, gold, nif, gb = R["original"], R["cash_filtered"], R["gold_filtered"], R["nifty"], R["gold_benchmark"]
    sym = R["currency_symbol"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">NIFTY100 Momentum 10 — Gold Instead of Cash During the 200-EMA Filter</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Reports 48-49 tested holding GOLDBEES.NS instead of cash during the 200-day-EMA filter's risk-off periods on Midcap150 and Smallcap250. This applies the identical mechanics to NIFTY100 Momentum 10 — the third and final universe in this comparison. GOLDBEES.NS only has price history from mid-2010, so ALL series here are recomputed fresh on this shorter, common window, not re-quoted from report 45's longer window.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(R['start_date'])}–{esc(R['end_date'])}<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#37F083]">
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          {pill('three for three — gold beats cash on every universe tested', 'positive')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          On NIFTY100 too, gold beats cash on CAGR — {pct(cash['cagr_pct'])} to
          <span class="font-semibold">{pct(gold['cagr_pct'])}</span> — while max drawdown stays essentially unchanged:
          {pct(cash['max_drawdown_pct'],1,signed=False)} (cash) vs. {pct(gold['max_drawdown_pct'],1,signed=False)} (gold).
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          Across Midcap150 (report 48), Smallcap250 (report 49), and NIFTY100 here, "gold instead of cash" is a consistent,
          clean improvement — unlike the front-loaded-momentum reformulation (reports 37-41), which flipped sign by universe,
          this change works the same way everywhere because it doesn't touch stock selection at all, only what's held while
          the regime filter is in its risk-off state.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR", "Compound annual growth rate, identical (gold-constrained) window for every series.",
                  [("No filter", pct(orig["cagr_pct"]), win_loss_kind(orig["cagr_pct"])),
                   ("200-EMA + cash", pct(cash["cagr_pct"]), win_loss_kind(cash["cagr_pct"])),
                   ("200-EMA + gold", pct(gold["cagr_pct"]), win_loss_kind(gold["cagr_pct"])),
                   ("NIFTY 50", pct(nif["cagr_pct"]), "neutral")]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline, identical window for every series.",
                  [("No filter", pct(orig["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("200-EMA + cash", pct(cash["max_drawdown_pct"], 1, signed=False), "positive"),
                   ("200-EMA + gold", pct(gold["max_drawdown_pct"], 1, signed=False), "positive"),
                   ("NIFTY 50", pct(nif["max_drawdown_pct"], 1, signed=False), "negative")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-1 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, v, cls=""):
        c = f' class="{cls}"' if cls else ""
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(v['net_return_pct'])}</td><td>{pct(v['cagr_pct'])}</td>
        <td>{pct(v['max_drawdown_pct'],1,signed=False)}</td><td>{v['longest_underwater_days']:,}d</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">All five, side by side</h3>
        {pill('grey rows = real benchmarks, not reconstructions', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every series over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("NIFTY100 Momentum 10 — no filter", orig)}
          {row("NIFTY100 Momentum 10 — 200-EMA + cash", cash)}
          {row("NIFTY100 Momentum 10 — 200-EMA + gold", gold)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
          {row("GOLDBEES.NS, buy & hold (real ETF)", gb, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "No filter", "color": COL["muted"], "points": orig["equity_curve"], "dash": True},
        {"name": "200-EMA + cash", "color": COL["negative"], "points": cash["equity_curve"]},
        {"name": "200-EMA + gold", "color": COL["positive"], "points": gold["equity_curve"]},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_50")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how {sym}100 invested at the start of the window grew under each version, linear axis, not log-scaled.</p>
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
        {"name": "200-EMA + cash", "color": COL["negative"], "points": dd_points(cash["equity_curve"])},
        {"name": "200-EMA + gold", "color": COL["positive"], "points": dd_points(gold["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=220, chart_id="dd_50")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — cash and gold give nearly identical drawdown protection ({pct(cash['max_drawdown_pct'],1,signed=False)} vs. {pct(gold['max_drawdown_pct'],1,signed=False)}).</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Three for three — a change that doesn't depend on universe</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        "Gold instead of cash" changes what the strategy holds during ~a quarter of trading days (whenever the NIFTY-50-driven
        filter is risk-off) but never touches which stocks get picked the rest of the time. Since gold's low correlation to
        Indian equities during broad selloffs doesn't depend on whether the underlying strategy trades large caps, midcaps, or
        smallcaps, this change works the same way on all three universes tested — reports 48-50 all show the same shape of
        result: meaningfully higher CAGR, essentially unchanged drawdown.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        The same caveat applies everywhere: this window (2010-2026) excludes the 2008 GFC, and gold CAN fall alongside
        equities during a genuine liquidity crunch — this is a consistently good result across three universes on ONE
        historical period, not a guarantee gold always helps.
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
        <li class="mb-1.5">GOLDBEES.NS's history only starts mid-2010, excluding the 2008-2009 global financial crisis.</li>
        <li class="mb-1.5">Zero transaction costs on ANY regime switch (into or out of gold) — same disclosed omission as reports 42-49.</li>
        <li class="mb-1.5">GOLDBEES.NS tracks domestic gold prices in INR, which also move with the rupee's own exchange rate.</li>
        <li class="mb-1.5">Only ONE EMA span (200 days) and immediate-switch (no confirmation delay) were tested here.</li>
        <li class="mb-1.5">Today's fixed NIFTY100 constituent list (report 12's config) is applied retroactively (survivorship bias). Equal weighting, no F&O-eligibility screen, unadjusted prices, no dividends modeled — same as every other reconstruction here.</li>
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
<html lang="en"><head><meta charset="utf-8"/><title>NIFTY100 Momentum 10 — Gold vs. Cash</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("50_nifty100_momentum10_gold_vs_cash.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 50_nifty100_momentum10_gold_vs_cash.html")

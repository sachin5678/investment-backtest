"""Builds 73_midcap150_momentum50.html from results72.json."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results72.json") as f:
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
    top10, top50, nif = R["top10"], R["top50"], R["nifty"]
    sym = R["currency_symbol"]
    n_base, n_wide = R["top_n_base"], R["top_n_wide"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap150 Momentum {n_wide} — A Much Wider Basket, Same Formula</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Every other report in this project's flagship line picks the top {n_base} out of Midcap150 by momentum score. This report changes exactly one thing — top_n from {n_base} to {n_wide}, roughly a third of the entire 150-stock universe — using the identical formula, price history, and June/December rebalance schedule, to see what a much broader basket does to CAGR and drawdown.</p>
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
          {pill('a wider basket loses on BOTH CAGR and drawdown here', 'negative')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Widening the basket from top-{n_base} to top-{n_wide} cuts CAGR from <span class="font-semibold">{pct(top10['cagr_pct'])}</span> to
          <span class="font-semibold">{pct(top50['cagr_pct'])}</span> — and drawdown gets slightly WORSE too, not better:
          {pct(top10['max_drawdown_pct'],1,signed=False)} (top-{n_base}) vs. {pct(top50['max_drawdown_pct'],1,signed=False)} (top-{n_wide}).
          There's no diversification trade-off to point to here — this isn't "lower return, lower risk," it's lower return with no
          risk benefit at all.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The likely reason: momentum's edge comes specifically from the STRONGEST-ranked names — diluting the portfolio with
          names ranked 11th to 50th (weaker momentum scores, by definition) pulls in stocks the formula itself considers less
          attractive, without actually smoothing out the concentrated portfolio's stock-specific risk enough to show up in max
          drawdown.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR", "Compound annual growth rate, identical window for every series.",
                  [(f"Top-{n_base}", pct(top10["cagr_pct"]), win_loss_kind(top10["cagr_pct"])),
                   (f"Top-{n_wide}", pct(top50["cagr_pct"]), win_loss_kind(top50["cagr_pct"])),
                   ("NIFTY 50", pct(nif["cagr_pct"]), "neutral")]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline, identical window for every series.",
                  [(f"Top-{n_base}", pct(top10["max_drawdown_pct"], 1, signed=False), "positive"),
                   (f"Top-{n_wide}", pct(top50["max_drawdown_pct"], 1, signed=False), "negative"),
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
        <h3 class="text-base font-bold text-[#E6EDF0]">All three, side by side</h3>
        {pill('grey row = real benchmark, not a reconstruction', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every series over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window, {R['num_rebalances']} rebalances.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row(f"Midcap150 Momentum {n_base} (the flagship top-{n_base})", top10)}
          {row(f"Midcap150 Momentum {n_wide} (this report's top-{n_wide})", top50)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": f"Top-{n_base}", "color": COL["positive"], "points": top10["equity_curve"]},
        {"name": f"Top-{n_wide}", "color": COL["negative"], "points": top50["equity_curve"]},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_73")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how {sym}100 invested at the start of the window grew under each basket size, linear axis, not log-scaled.</p>
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
        {"name": f"Top-{n_base}", "color": COL["positive"], "points": dd_points(top10["equity_curve"])},
        {"name": f"Top-{n_wide}", "color": COL["negative"], "points": dd_points(top50["equity_curve"])},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=220, chart_id="dd_73")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the wider basket doesn't meaningfully shallow any dip; if anything it's very slightly deeper.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    mechanism_note = f"""
    <div class="{PANEL} mt-6 border-[#6AE4FF]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">How the basket behaves</h3>{pill('mechanism', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the plumbing behind the headline numbers.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        The top-{n_wide} basket held exactly {R['min_basket_size']} names at every one of the {R['num_rebalances']} rebalances —
        the eligible pool (stocks with a full 12-month price history on that date) never dropped below {n_wide} even at the very
        start of the window, so the basket was never forced smaller than intended. And because both baskets are drawn from the
        SAME momentum ranking on the same date, the top-{n_base} picks are always a strict subset of the top-{n_wide} basket by
        construction (100% overlap, every rebalance) — not a finding, just how the two are related.
      </p>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why concentration wins here</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Momentum investing's entire premise is that recent relative strength predicts near-term future strength — which means
        the formula's OWN ranking is claiming stock #1 is a better bet than stock #50. Concentrating in the top-{n_base} takes
        that claim at face value; diversifying out to top-{n_wide} means holding 40 more names the formula itself ranks weaker,
        which should mechanically drag CAGR toward the broader index's own return — consistent with what happened here
        ({pct(top50['cagr_pct'])}, well below top-{n_base}'s {pct(top10['cagr_pct'])} but still well above NIFTY 50's {pct(nif['cagr_pct'])}).
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        The surprising part is that drawdown didn't improve at all despite the extra breadth — a broader basket is usually
        expected to smooth out single-stock blowups. That it didn't here suggests Midcap150's worst drawdowns in this window
        were broad, market-wide moves (most stocks falling together) rather than a few concentrated single-name disasters that
        diversification would have diluted.
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
        <li class="mb-1.5">Only ONE alternative basket size (50) was tested against the flagship top-10 — this doesn't map out the
        full CAGR/drawdown curve across every basket size between 10 and 150 (that would need several more runs, e.g. 20/30/75).</li>
        <li class="mb-1.5">Equal weighting within the basket (each of the 50 names gets 2% at every rebalance) — a cap-weighted or
        score-weighted top-50 could behave differently, since it would still overweight the strongest-ranked names within the
        broader basket.</li>
        <li class="mb-1.5">Zero transaction costs — same disclosed omission as every other reconstruction here; a 50-name
        portfolio also has 5x as many individual buy/sell legs per rebalance as the top-10 version, so real-world costs would
        scale up correspondingly, not stay flat.</li>
        <li class="mb-1.5">Today's fixed Midcap150 constituent list is applied retroactively across the whole window (survivorship
        bias). No F&O-eligibility screen, unadjusted prices, no dividends modeled — same as every other reconstruction here.</li>
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
      {mechanism_note}
      {honesty_note}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Midcap150 Momentum 50</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("73_midcap150_momentum50.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 73_midcap150_momentum50.html")

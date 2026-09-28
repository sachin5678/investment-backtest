"""Builds 77_midcap150_report48_rebalance_cadence.html from results76.json."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results76.json") as f:
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
    orig, semi, yearly, m4 = R["original"], R["ema200_gold_semiannual"], R["ema200_gold_yearly"], R["ema200_gold_4monthly"]
    nif, gb = R["nifty"], R["gold_benchmark"]
    sym = R["currency_symbol"]
    span = R["ema_span"]
    nrb = R["num_rebalances"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap150 Momentum 10 — Report 48's Own Design, Rebalanced Every 4 Months</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Report 76 found that a MORE frequent stock-selection refresh shallowed drawdown on a 400-day-EMA design, without beating its CAGR. This report asks whether that same benefit shows up on the actual hero design — report 48's own {span}-day EMA regime filter + gold — or whether it was specific to the 400-day EMA's slower-reacting signal. Same continuous/daily {span}-EMA regime check throughout; only the top-10 stock-selection cadence changes between the three variants below.</p>
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
          {pill("report 76's benefit does NOT transfer to the hero design — more frequent rebalancing hurts here", 'negative')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          On the {span}-day EMA — this project's actual best Midcap150 CAGR/drawdown combination — the semi-annual cadence report
          48 already uses is essentially the BEST of the three: CAGR <span class="font-semibold">{pct(semi['cagr_pct'])}</span> and
          drawdown <span class="font-semibold">{pct(semi['max_drawdown_pct'],1,signed=False)}</span>. Yearly comes in almost
          identical ({pct(yearly['cagr_pct'])} / {pct(yearly['max_drawdown_pct'],1,signed=False)}). Every 4 months is clearly
          WORSE on both counts — {pct(m4['cagr_pct'])} CAGR (barely above the unfiltered {pct(orig['cagr_pct'])} baseline) and a
          slightly deeper {pct(m4['max_drawdown_pct'],1,signed=False)} drawdown.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          This directly contradicts report 76's finding on the 400-day EMA, where every-4-months clearly shallowed the drawdown.
          The likely reason: the 400-day EMA's regime signal reacts so slowly that the held stock basket had genuinely gone stale
          by the time report 76's semi-annual cadence refreshed it, so a faster refresh had real staleness to fix. The 200-day EMA
          reacts quickly enough that this staleness barely exists — refreshing the basket more often here mostly just adds
          transaction churn and rotates OUT of stocks before their momentum has actually faded, at a real CAGR cost, without a
          comparable amount of "already gone stale" upside to recover.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR — rebalance cadence, report 48's own 200-EMA", "Compound annual growth rate, identical window for every series.",
                  [("No filter", pct(orig["cagr_pct"]), win_loss_kind(orig["cagr_pct"])),
                   ("Semi-annual (report 48)", pct(semi["cagr_pct"]), win_loss_kind(semi["cagr_pct"])),
                   ("Yearly", pct(yearly["cagr_pct"]), win_loss_kind(yearly["cagr_pct"])),
                   ("Every 4 months", pct(m4["cagr_pct"]), win_loss_kind(m4["cagr_pct"]))]),
        kpi_card("Max drawdown — rebalance cadence, report 48's own 200-EMA", "Largest peak-to-trough decline, identical window for every series.",
                  [("No filter", pct(orig["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Semi-annual (report 48)", pct(semi["max_drawdown_pct"], 1, signed=False), "positive"),
                   ("Yearly", pct(yearly["max_drawdown_pct"], 1, signed=False), "positive"),
                   ("Every 4 months", pct(m4["max_drawdown_pct"], 1, signed=False), "negative")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-1 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, v, cls=""):
        c = f' class="{cls}"' if cls else ""
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(v['net_return_pct'])}</td><td>{pct(v['cagr_pct'])}</td>
        <td>{pct(v['max_drawdown_pct'],1,signed=False)}</td><td>{v['longest_underwater_days']:,}d</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">All six, side by side</h3>
        {pill('grey rows = real benchmarks, not reconstructions', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every series over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("Midcap150 Momentum 10 — no filter", orig)}
          {row(f"{span}-day EMA + gold, semi-annual (report 48)", semi)}
          {row(f"{span}-day EMA + gold, yearly", yearly)}
          {row(f"{span}-day EMA + gold, every 4 months", m4)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
          {row("GOLDBEES.NS, buy & hold (real ETF)", gb, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "No filter", "color": COL["muted"], "points": orig["equity_curve"], "dash": True},
        {"name": "Semi-annual (report 48)", "color": COL["positive"], "points": semi["equity_curve"]},
        {"name": "Yearly", "color": "#8B5CF6", "points": yearly["equity_curve"]},
        {"name": "Every 4 months", "color": COL["negative"], "points": m4["equity_curve"]},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_77")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how {sym}100 invested at the start of the window grew under each cadence, linear axis, not log-scaled. Semi-annual and yearly track each other closely; every-4-months visibly lags both.</p>
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
        {"name": "Semi-annual (report 48)", "color": COL["positive"], "points": dd_points(semi["equity_curve"])},
        {"name": "Yearly", "color": "#8B5CF6", "points": dd_points(yearly["equity_curve"])},
        {"name": "Every 4 months", "color": COL["negative"], "points": dd_points(m4["equity_curve"])},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=220, chart_id="dd_77")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — unlike report 76's 400-day-EMA test, more frequent rebalancing does NOT shallow the drawdown here — the three lines sit close together, with every-4-months if anything the worst.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    mechanism_note = f"""
    <div class="{PANEL} mt-6 border-[#6AE4FF]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">What actually changes between the three cadences</h3>{pill('mechanism', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the regime filter's OWN switch timing (into/out of gold) is identical in all three; only the top-10 stock-selection refresh rate differs.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        Semi-annual rebalances the momentum picks {nrb['semiannual']} times across this window (June and December); yearly
        rebalances {nrb['yearly']} times (June only); every-4-months rebalances {nrb['4monthly']} times (February, June,
        October) — identical cadence definitions to report 76, applied here to the {span}-day EMA instead of 400. All three
        share the exact same regime signal, checked daily against NIFTY 50's own close; a switch into or out of gold happens
        on the same dates in every version. The ONLY difference is which specific 10 stocks are held during each "on" stretch.
      </p>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why report 76's benefit doesn't carry over</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        A more frequent rebalance only helps when the existing cadence is letting the basket go genuinely stale between
        refreshes. Report 76's 400-day EMA is slow enough that this staleness was real — refreshing more often gave the
        strategy real, recoverable value. Report 48's {span}-day EMA reacts fast enough, and its semi-annual cadence is
        already close enough to "fresh," that there's little staleness left to fix. What's left when you rebalance more
        often anyway is mostly the downside of turnover: exiting stocks whose momentum hasn't actually faded yet, on a
        schedule driven by the calendar rather than by any real signal that the basket needs refreshing.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        The practical takeaway: "rebalance more often" is not a universal fix — whether it helps depends on how slow (and
        therefore how prone to staleness) the underlying signal already is. On report 48's own well-tuned design, the
        existing semi-annual cadence already looks close to right.
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
        <li class="mb-1.5">Only THREE rebalance cadences were tested, all anchored to keep June as a shared month — a genuinely
        different calendar (e.g. March/July/November) or a non-4-month spacing (e.g. quarterly) could behave differently.</li>
        <li class="mb-1.5">Zero transaction costs on any regime switch or scheduled rebalance — same disclosed omission as
        every other reconstruction here; the every-4-months cadence also trades 50% more often per year than semi-annual,
        so real-world costs would scale up correspondingly and make its already-worse CAGR look worse still.</li>
        <li class="mb-1.5">Today's fixed Midcap150 constituent list is applied retroactively across the whole window
        (survivorship bias). Equal weighting, no F&O-eligibility screen, unadjusted prices, no dividends modeled — same as
        every other reconstruction here.</li>
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
<html lang="en"><head><meta charset="utf-8"/><title>Midcap150 Momentum 10 — Report 48, Rebalance Cadence</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("77_midcap150_report48_rebalance_cadence.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 77_midcap150_report48_rebalance_cadence.html")

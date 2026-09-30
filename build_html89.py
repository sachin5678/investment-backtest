"""Builds 89_midcap150_report48_slippage.html from results88.json."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results88.json") as f:
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
    fric, cost = R["frictionless"], R["cost_loaded"]
    nif, gb = R["nifty"], R["gold_benchmark"]
    span = R["ema_span"]
    slip = R["slippage_pct"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap150 Momentum 10 — Report 48 With {slip:.1f}% Slippage</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Report 48's exact design — the {span}-day EMA regime filter, gold instead of cash — with a real trading cost applied for the first time: every buy fills {slip:.1f}% ABOVE the modeled price, every sell fills {slip:.1f}% BELOW it. Every transition in this design (a regime exit, a regime re-entry, or the scheduled semi-annual refresh) is really a two-leg trade — sell whatever's currently held, buy whatever it's moving into — so slippage is charged on BOTH legs, every time. Zero transaction costs has been a disclosed simplification in every report here so far, including report 48 itself; this tests how much of the reported edge survives once a real cost is actually charged.</p>
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
          {pill(f'{slip:.1f}% slippage costs {fric["cagr_pct"]-cost["cagr_pct"]:.2f} points of CAGR and makes the drawdown worse too', 'negative')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          CAGR drops from {pct(fric['cagr_pct'])} to <span class="font-semibold">{pct(cost['cagr_pct'])}</span> — a real,
          meaningful cost, not a rounding error. Max drawdown gets WORSE too, not just CAGR:
          {pct(fric['max_drawdown_pct'],1,signed=False)} frictionless vs.
          <span class="font-semibold">{pct(cost['max_drawdown_pct'],1,signed=False)}</span> with slippage — every regime
          switch INTO gold during a crash now sells stocks at a worse price and buys gold at a worse price too, right
          when the strategy can least afford it.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The design still comfortably beats NIFTY 50 ({pct(nif['cagr_pct'])}) even after this cost — but {slip:.1f}%
          slippage, a small-sounding number, adds up over {R['num_selection_events']} separate buy/sell events across 18
          years into a genuinely large compounding drag. This is the single biggest gap between a "backtest number" and
          a "number you could actually expect to live with" that this project has shown for report 48 so far.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card(f"CAGR — frictionless vs. {slip:.1f}% slippage", "Compound annual growth rate, identical window for every series.",
                  [("Frictionless (report 48)", pct(fric["cagr_pct"]), win_loss_kind(fric["cagr_pct"])),
                   (f"{slip:.1f}% slippage, both sides", pct(cost["cagr_pct"]), win_loss_kind(cost["cagr_pct"])),
                   ("NIFTY 50", pct(nif["cagr_pct"]), "neutral")]),
        kpi_card(f"Max drawdown — frictionless vs. {slip:.1f}% slippage", "Largest peak-to-trough decline, identical window for every series.",
                  [("Frictionless (report 48)", pct(fric["max_drawdown_pct"], 1, signed=False), "positive"),
                   (f"{slip:.1f}% slippage, both sides", pct(cost["max_drawdown_pct"], 1, signed=False), "negative"),
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
        <h3 class="text-base font-bold text-[#E6EDF0]">All four, side by side</h3>
        {pill('grey rows = real benchmarks, not reconstructions', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every series over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("200-EMA + gold — frictionless (report 48)", fric)}
          {row(f"200-EMA + gold — {slip:.1f}% slippage, both sides", cost)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
          {row("GOLDBEES.NS, buy & hold (real ETF)", gb, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "Frictionless (report 48)", "color": COL["positive"], "points": fric["equity_curve"]},
        {"name": f"{slip:.1f}% slippage, both sides", "color": COL["negative"], "points": cost["equity_curve"]},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_89")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how ₹100 invested at the start of the window grew under each version, linear axis, not log-scaled. The gap between the two lines widens visibly as the trading costs compound over 18 years.</p>
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
        {"name": "Frictionless (report 48)", "color": COL["positive"], "points": dd_points(fric["equity_curve"])},
        {"name": f"{slip:.1f}% slippage, both sides", "color": COL["negative"], "points": dd_points(cost["equity_curve"])},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=220, chart_id="dd_89")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the slippage-loaded line dips visibly deeper at the same points the frictionless line does — every regime switch during a crash now costs extra, exactly when the strategy is already under stress.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    mechanism_note = f"""
    <div class="{PANEL} mt-6 border-[#6AE4FF]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">How much trading this design actually does</h3>{pill('mechanism', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every buy/sell event over the full window, each one now paying slippage on both legs.</p>
      <p class="text-13.5px] text-[#C9D6DA] leading-relaxed">
        <span class="font-semibold text-[#E6EDF0]">{R['num_selection_events']}</span> total selection/switch events across
        18 years — every scheduled semi-annual refresh AND every regime switch into or out of gold, each one a full
        sell-the-old / buy-the-new round trip. That's roughly
        <span class="font-semibold text-[#E6EDF0]">{R['num_stock_buy_legs']}</span> individual stock buy/sell legs alone
        (10 stocks × every stock-side event), before counting the gold-side legs on top. At {slip:.1f}% per side, that
        adds up to a real, compounding drag — not a rounding error, and not something a "just ignore costs" backtest can
        responsibly claim doesn't matter.
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
        <li class="mb-1.5">Every scheduled rebalance sells the ENTIRE old top-10 basket and buys the ENTIRE new one, even
        for a stock that happens to stay in the top-10 across consecutive rebalances — a real broker/fund would usually
        net out an unchanged position rather than sell-and-rebuy it, so this modestly OVERSTATES the true slippage cost
        for names that persist across rebalances.</li>
        <li class="mb-1.5">Only slippage is modeled here — no separate brokerage commission, STT, stamp duty, or GST on
        brokerage, all of which are real additional costs on top of this in India. This report is not the full
        real-world cost picture, just the slippage piece of it in isolation.</li>
        <li class="mb-1.5">{slip:.1f}% is a flat assumption applied uniformly to every trade, regardless of order size or
        how liquid a specific midcap stock was on that specific day — real slippage varies name to name and can be
        considerably worse for less liquid names during a stressed market, exactly when this strategy is most likely to
        be trading (a regime switch).</li>
        <li class="mb-1.5">Today's fixed Midcap150 constituent list is applied retroactively across the whole window
        (survivorship bias). Equal weighting, no F&O-eligibility screen, unadjusted prices, no dividends modeled — same
        as every other reconstruction here.</li>
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
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Midcap150 Momentum 10 — Report 48 With Slippage</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("89_midcap150_report48_slippage.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 89_midcap150_report48_slippage.html")

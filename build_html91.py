"""Builds 91_midcap150_gold_strength_guard.html from results90.json."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results90.json") as f:
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
      tr.mostly-flat td{color:#F2B03C;}
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
    orig, r48, guard = R["original"], R["report48_standard"], R["gold_strength_guard"]
    nif, gb = R["nifty"], R["gold_benchmark"]
    span, lookback = R["ema_span"], R["gold_lookback_days"]
    blocks = R["cash_block_breakdown"]
    flat_days, total_cash_days = R["days_guard_moved_to_flat"], R["total_cash_regime_days"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap150 Momentum 10 — Gold-Strength Guard on Report 48</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Report 48's exact design, with one change: during a risk-off period (NIFTY below its {span}-day EMA), the hedge sleeve holds gold ONLY while gold itself passes two checks — its own {lookback}-day (~6-month) return beats NIFTY's {lookback}-day return, AND that return is positive. Whenever either check fails, the hedge sleeve sits in flat 0%-return cash instead of gold for that day. This guard never adds leverage or a third asset — it only ever replaces gold with cash — so any improvement has to come from avoiding gold's own bad stretches, not from gold earning something better.</p>
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
          {pill(f'{guard["cagr_pct"]-r48["cagr_pct"]:.1f} points of extra CAGR, AND a shallower drawdown', 'positive')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          CAGR rises from {pct(r48['cagr_pct'])} (report 48, unconditional gold) to <span class="font-semibold">{pct(guard['cagr_pct'])}</span>
          with the guard — and max drawdown improves too, from {pct(r48['max_drawdown_pct'],1,signed=False)} to
          <span class="font-semibold">{pct(guard['max_drawdown_pct'],1,signed=False)}</span>. This is a genuine two-sided
          improvement, not a return bought with extra risk.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The mechanism moved <span class="font-semibold">{flat_days} of {total_cash_days}</span> regime-off days from gold
          into flat cash. The cash-block breakdown below shows exactly which historical periods those days came from —
          and it is NOT the periods an earlier, less careful pass through this idea assumed.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR — no guard vs. gold-strength guard", "Compound annual growth rate, identical window for every series.",
                  [("Report 48 (gold, no guard)", pct(r48["cagr_pct"]), win_loss_kind(r48["cagr_pct"])),
                   ("Gold-strength guard", pct(guard["cagr_pct"]), win_loss_kind(guard["cagr_pct"])),
                   ("NIFTY 50", pct(nif["cagr_pct"]), "neutral")]),
        kpi_card("Max drawdown — no guard vs. gold-strength guard", "Largest peak-to-trough decline, identical window for every series.",
                  [("Report 48 (gold, no guard)", pct(r48["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Gold-strength guard", pct(guard["max_drawdown_pct"], 1, signed=False), "positive"),
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
          {row("No filter (plain momentum)", orig)}
          {row(f"{span}-EMA regime filter + gold (report 48)", r48)}
          {row("+ gold-strength guard", guard)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
          {row("GOLDBEES.NS, buy & hold (real ETF)", gb, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "Report 48 (gold, no guard)", "color": COL["muted"], "points": r48["equity_curve"]},
        {"name": "Gold-strength guard", "color": COL["positive"], "points": guard["equity_curve"]},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_91")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how ₹100 invested at the start of the window grew under each version, linear axis, not log-scaled.</p>
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
        {"name": "Report 48 (gold, no guard)", "color": COL["muted"], "points": dd_points(r48["equity_curve"])},
        {"name": "Gold-strength guard", "color": COL["positive"], "points": dd_points(guard["equity_curve"])},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=220, chart_id="dd_91")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the guarded line recovers from several episodes noticeably shallower than the unconditional-gold line.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    block_rows = []
    for b in blocks:
        cls = ' class="mostly-flat"' if b["mostly"] == "flat" else ""
        block_rows.append(f"""<tr{cls}><td>{esc(b['start'])} → {esc(b['end'])}</td><td>{b['days']}d</td>
        <td>{b['gold_days']}d</td><td>{b['flat_days']}d</td><td>{esc(b['mostly'].upper())}</td></tr>""")

    mechanism_note = f"""
    <div class="{PANEL} mt-6 border-[#6AE4FF]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Which historical periods actually drove this — the concentration check</h3>{pill('the honest part', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every regime-off (cash-eligible) period of 10+ days, and whether the guard spent most of it in gold or flat cash. This is the single clearest way to see whether the improvement is a broad, repeatable effect or a lucky bet on one or two episodes.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-4">
        An earlier, less careful pass at this idea assumed the guard's benefit came from dodging gold's well-known 2013
        taper-tantrum selloff and its 2021–22 correction. The breakdown below shows that's <span class="font-semibold text-[#F2643C]">not</span>
        what actually happened: during 2013-07-30→2013-09-06 the guard stayed <span class="font-semibold">mostly in gold</span>
        (15 of 27 days), and during 2022-05-04→2022-07-19 it stayed in gold <span class="font-semibold">every single day</span>
        (55 of 55). The real flat-cash concentration is in 2015–16 and late 2016/early 2017, plus
        {R['days_in_short_blips']} days scattered across many short
        (under 10-day) regime whipsaws too brief to list individually below. Only
        <span class="font-semibold">{R['num_cash_blocks_mostly_flat']} of {R['num_cash_blocks']}</span> listed blocks were
        mostly flat — most of the guard's {R['days_guard_moved_to_flat']} flat-cash days are spread thinly across many
        otherwise-gold periods, not concentrated in one or two decisive bets.
      </p>
      <table class="data-table">
        <thead><tr><th>Regime-off period</th><th>Length</th><th>Gold days</th><th>Flat days</th><th>Mostly</th></tr></thead>
        <tbody>{''.join(block_rows)}</tbody>
      </table>
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
        <li class="mb-1.5">Zero transaction costs on the extra gold↔cash switches this guard introduces beyond report 48's
        own switching. Report 89 found even 0.1% slippage costs report 48 itself ~2.6 points of CAGR — this guard adds
        MORE switch events than report 48 alone, and has not been cost-tested. The real improvement, after costs, is
        almost certainly smaller than the headline number above.</li>
        <li class="mb-1.5">The guard's "beats NIFTY" and "is positive" checks both use the same {lookback}-day lookback —
        this specific window wasn't tuned or compared against other lookback lengths here; a different window could
        move the result in either direction.</li>
        <li class="mb-1.5">Flat cash earns literally 0% here, same convention as report 48's own cash-based variants —
        a liquid fund or short-term debt instrument (reports 68/69/70 assumed ~6%) would likely improve this further,
        untested in this report.</li>
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
<html lang="en"><head><meta charset="utf-8"/><title>Midcap150 Momentum 10 — Gold-Strength Guard</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("91_midcap150_gold_strength_guard.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 91_midcap150_gold_strength_guard.html")

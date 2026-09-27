"""Builds 76_midcap150_ema400_gold_rebalance_cadence.html from results75.json."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results75.json") as f:
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
    orig, e200, e400, e400y, e4004m = (R["original"], R["ema200_gold"], R["ema400_gold"],
                                        R["ema400_gold_yearly"], R["ema400_gold_4monthly"])
    nif, gb = R["nifty"], R["gold_benchmark"]
    sym = R["currency_symbol"]
    base_span, wide_span = R["ema_span_base"], R["ema_span_wide"]
    nrb = R["num_rebalances"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap150 Momentum 10 — Report 48 Replicated with a {wide_span}-Day EMA</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Report 48's exact design — binary regime filter, gold instead of cash — replicated with a {wide_span}-day EMA instead of {base_span}, considerably wider than reports 46/47's own 100-250 span-sensitivity test (which already found 250 was the WORST span tested there, for the cash version). Part two holds this {wide_span}-day EMA fixed and instead varies how often the top-10 momentum picks themselves get refreshed — semi-annual (June/December, this project's usual cadence), yearly, and every 4 months — while the regime check itself stays continuous/daily throughout.</p>
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
          {pill(f'{wide_span}-day EMA loses to {base_span}-day on both CAGR and drawdown, gold or not', 'negative')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Widening the EMA from {base_span} to {wide_span} days drops CAGR from {pct(e200['cagr_pct'])} to
          <span class="font-semibold">{pct(e400['cagr_pct'])}</span> and makes the drawdown WORSE too — {pct(e200['max_drawdown_pct'],1,signed=False)}
          vs. <span class="font-semibold">{pct(e400['max_drawdown_pct'],1,signed=False)}</span> — the same "wider isn't better" pattern
          reports 46/47 already found for the cash version, now confirmed to hold with gold as the hedge asset too. A slower-moving
          {wide_span}-day average reacts to a real trend change later in both directions: later into the hedge on the way down, and
          later back into momentum on the way up, missing more of the recovery.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          On rebalance cadence (holding the {wide_span}-day EMA fixed): yearly is the worst of the three on both CAGR
          ({pct(e400y['cagr_pct'])}) and drawdown ({pct(e400y['max_drawdown_pct'],1,signed=False)}) — refreshing the momentum picks
          less often means holding a stale, aging portfolio through more of each holding period. Every-4-months
          ({pct(e4004m['cagr_pct'])} CAGR, {pct(e4004m['max_drawdown_pct'],1,signed=False)} drawdown) doesn't beat the semi-annual
          baseline's CAGR, but its drawdown lands closer to gold's own {pct(gb['max_drawdown_pct'],1,signed=False)} — refreshing the
          basket more often gives the strategy more chances to rotate out of names that have already peaked.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card(f"CAGR — EMA span ({base_span} vs {wide_span}, same semi-annual cadence)", "Compound annual growth rate, identical window for every series.",
                  [("No filter", pct(orig["cagr_pct"]), win_loss_kind(orig["cagr_pct"])),
                   (f"{base_span}-EMA + gold", pct(e200["cagr_pct"]), win_loss_kind(e200["cagr_pct"])),
                   (f"{wide_span}-EMA + gold", pct(e400["cagr_pct"]), win_loss_kind(e400["cagr_pct"])),
                   ("NIFTY 50", pct(nif["cagr_pct"]), "neutral")]),
        kpi_card(f"Max drawdown — EMA span ({base_span} vs {wide_span})", "Largest peak-to-trough decline, identical window for every series.",
                  [("No filter", pct(orig["max_drawdown_pct"], 1, signed=False), "negative"),
                   (f"{base_span}-EMA + gold", pct(e200["max_drawdown_pct"], 1, signed=False), "positive"),
                   (f"{wide_span}-EMA + gold", pct(e400["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("NIFTY 50", pct(nif["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card(f"CAGR — rebalance cadence ({wide_span}-day EMA fixed)", "Compound annual growth rate, identical window for every series.",
                  [("Semi-annual", pct(e400["cagr_pct"]), win_loss_kind(e400["cagr_pct"])),
                   ("Yearly", pct(e400y["cagr_pct"]), win_loss_kind(e400y["cagr_pct"])),
                   ("Every 4 months", pct(e4004m["cagr_pct"]), win_loss_kind(e4004m["cagr_pct"]))]),
        kpi_card(f"Max drawdown — rebalance cadence ({wide_span}-day EMA fixed)", "Largest peak-to-trough decline, identical window for every series.",
                  [("Semi-annual", pct(e400["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Yearly", pct(e400y["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Every 4 months", pct(e4004m["max_drawdown_pct"], 1, signed=False), "positive")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-1 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, v, cls=""):
        c = f' class="{cls}"' if cls else ""
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(v['net_return_pct'])}</td><td>{pct(v['cagr_pct'])}</td>
        <td>{pct(v['max_drawdown_pct'],1,signed=False)}</td><td>{v['longest_underwater_days']:,}d</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">All seven, side by side</h3>
        {pill('grey rows = real benchmarks, not reconstructions', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every series over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window (the latest start date among all five reconstructions, since different rebalance cadences take different lengths of time to first become valid).</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("Midcap150 Momentum 10 — no filter", orig)}
          {row(f"{base_span}-day EMA + gold, semi-annual (report 48)", e200)}
          {row(f"{wide_span}-day EMA + gold, semi-annual", e400)}
          {row(f"{wide_span}-day EMA + gold, yearly", e400y)}
          {row(f"{wide_span}-day EMA + gold, every 4 months", e4004m)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
          {row("GOLDBEES.NS, buy & hold (real ETF)", gb, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "No filter", "color": COL["muted"], "points": orig["equity_curve"], "dash": True},
        {"name": f"{base_span}-EMA + gold", "color": COL["assumption"], "points": e200["equity_curve"], "dash": True},
        {"name": f"{wide_span}-EMA + gold, semi-annual", "color": COL["positive"], "points": e400["equity_curve"]},
        {"name": f"{wide_span}-EMA + gold, yearly", "color": COL["negative"], "points": e400y["equity_curve"]},
        {"name": f"{wide_span}-EMA + gold, 4-monthly", "color": "#8B5CF6", "points": e4004m["equity_curve"]},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_76")
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
        {"name": f"{wide_span}-EMA + gold, semi-annual", "color": COL["positive"], "points": dd_points(e400["equity_curve"])},
        {"name": f"{wide_span}-EMA + gold, yearly", "color": COL["negative"], "points": dd_points(e400y["equity_curve"])},
        {"name": f"{wide_span}-EMA + gold, 4-monthly", "color": "#8B5CF6", "points": dd_points(e4004m["equity_curve"])},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=220, chart_id="dd_76")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison — rebalance cadence, {wide_span}-day EMA fixed</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — more frequent stock-selection refreshes visibly shallow the drawdown, even though the regime-switch timing itself (into/out of gold) is identical across all three — only which stocks are held while "on" differs.</p>
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
        October). All three share the same {wide_span}-day EMA continuously checked against NIFTY 50's own close every
        single day — a regime switch into or out of gold happens on exactly the same dates regardless of which cadence is
        running. The ONLY thing that differs is which specific 10 stocks are held during each "on" stretch, and how stale
        that basket is allowed to get before being refreshed.
      </p>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why a wider EMA and a slower rebalance cadence both hurt the same way</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        A {wide_span}-day EMA and a yearly rebalance are both, in different ways, a "slower to react" design — the EMA reacts
        slower to a genuine regime change, and a yearly refresh reacts slower to the momentum picks themselves going stale.
        Both cost CAGR and drawdown here for the same underlying reason: momentum's edge decays as a stock's own recent
        strength ages, and anything that holds the SAME 10 stocks or the SAME hedge/invested state for longer than
        necessary gives up more of that edge before the next chance to correct course.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        The 4-monthly result is the interesting exception: it doesn't beat semi-annual on CAGR, but its drawdown is
        noticeably shallower — refreshing the basket more often gives the strategy more OPPORTUNITIES to rotate away from
        names that have already turned down, even while the regime filter's own gold/momentum switch timing is unchanged.
        That's a genuinely different lever from the EMA span itself, and it's the one place in this report where "more
        frequent" clearly helped rather than hurt.
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
        <li class="mb-1.5">Only ONE wide span ({wide_span} days) was tested against the {base_span}-day baseline — this doesn't map
        the full CAGR/drawdown curve between 250 (reports 46/47's widest cash test) and {wide_span} days.</li>
        <li class="mb-1.5">Only THREE rebalance cadences were tested, all anchored to keep June as a shared month — a genuinely
        different calendar (e.g. March/July/November) could behave differently even at the same 4-month spacing.</li>
        <li class="mb-1.5">Zero transaction costs on any regime switch or scheduled rebalance — same disclosed omission as
        every other reconstruction here; the 4-monthly cadence also trades 50% more often per year than semi-annual, so
        real-world costs would scale up correspondingly, not stay flat.</li>
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
<html lang="en"><head><meta charset="utf-8"/><title>Midcap150 Momentum 10 — {wide_span}-Day EMA + Gold</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("76_midcap150_ema400_gold_rebalance_cadence.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 76_midcap150_ema400_gold_rebalance_cadence.html")

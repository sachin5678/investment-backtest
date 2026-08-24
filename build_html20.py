"""Builds 20_momentum_gold_catch_blend.html from results19.json. Same
self-contained contract, smooth Catmull-Rom charts, plus one new panel not
used elsewhere: the full trigger -> recovery event timeline (only 5 cycles
total, so every one of them is shown, not a sample)."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results19.json") as f:
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
ACCENT_2 = "#8B5CF6"   # 4th chart hue, needed because this report features 4 series at once


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
      tr.trig-row td{color:#F2643C;}
      tr.rec-row td{color:#37F083;}
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
    cb, static, periodic = R["catch_blend"], R["static_50_50_no_rebalance"], R["periodic_50_50_rebalance"]
    mom, gold, nif = R["midcap_momentum10"], R["gold"], R["nifty"]
    sym = R["currency_symbol"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Momentum + Gold, With a Drawdown Catch</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">50/50 Midcap150 Momentum-10 + gold — but a 20% drawdown in the momentum leg sells all the gold into momentum, held until a full recovery, then reset back to 50/50.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(R['start_date'])}–{esc(R['end_date'])} · {R['num_triggers']} trigger cycles<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2643C]">
        <div class="flex items-center gap-2 mb-3">
          <h2 class="text-lg font-bold text-[#E6EDF0]">The rule, and the honest result up front</h2>
          {pill('reduces drawdown vs. pure momentum', 'positive')}{pill('underperforms just leaving it alone', 'negative')}{pill('5 trigger cycles in 17.6 years', 'neutral')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Start 50% Midcap150 Momentum-10 / 50% gold. The moment the momentum leg falls 20% below its OWN running peak, sell 100% of the gold and put
          it all into momentum — an all-in lump sum funded by the diversification cushion. Stay 100% momentum until it makes a brand-new all-time high
          (fully recovers), then reset to exactly 50/50 and repeat. This happened <span class="font-semibold">{R['num_triggers']} times</span> over
          {esc(R['start_date'])}–{esc(R['end_date'])}, averaging <span class="font-semibold">{R['avg_days_to_recover']:.0f} days</span> to recover
          each time.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The catch does what it's designed to do on the risk side — shallower drawdown than holding pure momentum alone. But on return, it
          <span class="font-semibold">underperforms simply buying 50/50 once and never touching it again</span> ({pct(cb['cagr_pct'])} CAGR vs.
          {pct(static['cagr_pct'])}) — and it even underperforms a plain CALENDAR-rebalanced 50/50 blend on drawdown ({pct(cb['max_drawdown_pct'],1,signed=False)}
          vs. {pct(periodic['max_drawdown_pct'],1,signed=False)}). Repeatedly resetting back to 50/50 after each recovery turns out to cap the compounding
          of the far-faster-growing momentum leg more than the "buy the dip" timing helps — see the honesty note below for the mechanism.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("Net return", f"{esc(R['start_date'])} to {esc(R['end_date'])}, base 100.",
                  [("Catch blend (this idea)", pct(cb["net_return_pct"]), win_loss_kind(cb["net_return_pct"])),
                   ("Static 50/50, never touched", pct(static["net_return_pct"]), win_loss_kind(static["net_return_pct"])),
                   ("Periodic 50/50 rebalance", pct(periodic["net_return_pct"]), win_loss_kind(periodic["net_return_pct"]))]),
        kpi_card("CAGR", "Compound annual growth rate, identical window for all three.",
                  [("Catch blend (this idea)", pct(cb["cagr_pct"]), win_loss_kind(cb["cagr_pct"])),
                   ("Static 50/50, never touched", pct(static["cagr_pct"]), win_loss_kind(static["cagr_pct"])),
                   ("Periodic 50/50 rebalance", pct(periodic["cagr_pct"]), win_loss_kind(periodic["cagr_pct"]))]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline over the same window.",
                  [("Catch blend (this idea)", pct(cb["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Static 50/50, never touched", pct(static["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Periodic 50/50 rebalance", pct(periodic["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("Longest time underwater", "Longest stretch, in calendar days, below a prior peak.",
                  [("Catch blend (this idea)", f'{cb["longest_underwater_days"]:,}d', "neutral"),
                   ("Static 50/50, never touched", f'{static["longest_underwater_days"]:,}d', "neutral"),
                   ("Periodic 50/50 rebalance", f'{periodic["longest_underwater_days"]:,}d', "neutral")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, v, cls=""):
        c = f' class="{cls}"' if cls else ""
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(v['net_return_pct'])}</td><td>{pct(v['cagr_pct'])}</td>
        <td>{pct(v['max_drawdown_pct'],1,signed=False)}</td><td>{v['longest_underwater_days']:,}d</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">All six, side by side</h3>
        {pill('grey rows = single-asset reference lines, not blends', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the three 50/50-style portfolios (this catch, static buy-and-hold, and plain periodic rebalancing) against their two underlying single assets and NIFTY 50, over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("Catch blend — the drawdown rule (this idea)", cb)}
          {row("Static 50/50, bought once, never touched", static)}
          {row("Periodic 50/50, rebalanced every June/December", periodic)}
          {row("Midcap150 Momentum-10 alone (100%)", mom, "real-bench")}
          {row("Gold alone, GOLDBEES.NS (100%)", gold, "real-bench")}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "Catch blend (this idea)", "color": COL["negative"], "points": cb["equity_curve"]},
        {"name": "Static 50/50, never touched", "color": COL["positive"], "points": static["equity_curve"]},
        {"name": "Periodic 50/50 rebalance", "color": ACCENT_2, "points": periodic["equity_curve"], "dash": True},
        {"name": "Midcap150 Momentum-10 alone", "color": COL["text"], "points": mom["equity_curve"], "dash": True},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=460, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_20")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
        {pill('linear axis, starts at zero — not log-scaled', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — static (green) and pure momentum (dashed white) pull furthest ahead; the catch (red) and periodic rebalance (dashed violet) both sit visibly below them for almost the whole window, not just at the end.</p>
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
        {"name": "Catch blend (this idea)", "color": COL["negative"], "points": dd_points(cb["equity_curve"])},
        {"name": "Static 50/50, never touched", "color": COL["positive"], "points": dd_points(static["equity_curve"])},
        {"name": "Periodic 50/50 rebalance", "color": ACCENT_2, "points": dd_points(periodic["equity_curve"]), "dash": True},
        {"name": "Midcap150 Momentum-10 alone", "color": COL["text"], "points": dd_points(mom["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=260, chart_id="dd_20")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the catch's drawdown ({pct(cb['max_drawdown_pct'],1,signed=False)}) is shallower than pure momentum's ({pct(mom['max_drawdown_pct'],1,signed=False)}) — the rule does cushion the worst of it. But periodic rebalancing, with no drawdown-timing at all, cushions it even more ({pct(periodic['max_drawdown_pct'],1,signed=False)}), just by regularly trimming the winner and topping up the laggard.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    def event_rows(events):
        rows = []
        for e in events:
            if e["event"] == "trigger_all_in":
                rows.append(f"""<tr class="trig-row"><td>{esc(e['date'])}</td><td>All-in trigger</td>
                <td>Momentum at {pct(e['momentum_drawdown_pct'],2,signed=False)} from its own peak — gold fully sold into momentum</td>
                <td>{sym}{e['portfolio_value']:,.1f}</td></tr>""")
            else:
                rows.append(f"""<tr class="rec-row"><td>{esc(e['date'])}</td><td>Recovery — reset to 50/50</td>
                <td>Momentum made a new all-time high after {e['days_since_trigger']} days concentrated — split back to 50/50</td>
                <td>{sym}{e['portfolio_value']:,.1f}</td></tr>""")
        return "".join(rows)

    still_in = R["currently_in_concentrated_state"]
    status_pill = pill('still 100% momentum as of the last data point', 'assumption') if still_in else pill('back to 50/50 as of the last data point', 'positive')

    timeline_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Every trigger → recovery cycle, in full</h3>
        {status_pill}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — all {R['num_triggers']} times the rule fired, over the full {esc(R['start_date'])}–{esc(R['end_date'])} window — small enough to show every cycle, not a sample. Average time spent 100%-in-momentum before recovering: {R['avg_days_to_recover']:.0f} days.</p>
      <div style="overflow-x:auto">
      <table class="data-table">
        <thead><tr><th>Date</th><th style="text-align:left">Event</th><th style="text-align:left">Detail</th><th>Portfolio value</th></tr></thead>
        <tbody>{event_rows(R['events'])}</tbody>
      </table>
      </div>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why "buying the dip" here still lost to doing nothing</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Over {esc(R['start_date'])}–{esc(R['end_date'])}, momentum alone compounded at {pct(mom['cagr_pct'])} a year versus gold's {pct(gold['cagr_pct'])} —
        momentum grew roughly {mom['net_return_pct']/100:,.0f}x versus gold's {gold['net_return_pct']/100:,.0f}x over the full window. A 50/50 split that is
        NEVER rebalanced naturally drifts to be almost entirely momentum within a few years, simply because the faster-compounding asset dominates the mix —
        that drift is exactly what "static, never touched" is capturing, and it's a large share of why it wins.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        The catch rule does the opposite at every single cycle: the moment momentum recovers from a dip, it forcibly resets the mix back to 50/50 —
        selling down exactly the asset that was about to keep compounding fastest, and buying back into gold, right as momentum turns UP again. Each of the
        {R['num_triggers']} reset points is a small, repeated tax on the momentum leg's own compounding, paid in exchange for a real but partial reduction
        in how deep the worst drawdown gets.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        That trade-off shows up exactly as expected: the catch's max drawdown ({pct(cb['max_drawdown_pct'],1,signed=False)}) is shallower than pure
        momentum's ({pct(mom['max_drawdown_pct'],1,signed=False)}) — the rule does work as risk management. It just isn't a free lunch: plain periodic
        rebalancing, with no drawdown-timing logic at all, achieves an even shallower drawdown ({pct(periodic['max_drawdown_pct'],1,signed=False)}) for a
        similar return give-up, suggesting the discipline of rebalancing itself — not the specific -20%/new-high timing rule — is doing most of the risk
        reduction here.
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
        <li class="mb-1.5">Midcap150 Momentum 10 is reused exactly as built in report 16 — today's fixed Midcap 150 constituent list applied retroactively (survivorship bias), equal-weighted top 10, June/December rebalance (borrowed from the NIFTY200 Momentum convention, not the real Midcap150 Momentum index's own May/November cadence).</li>
        <li class="mb-1.5">Only ONE drawdown threshold (-20%) and ONE exit condition (a full new all-time high) were tested — a shallower/deeper trigger, or a partial-recovery exit (e.g. "halfway back"), are untested alternatives that could change this result in either direction.</li>
        <li class="mb-1.5">Zero transaction costs, slippage, or taxes modeled on any of the reallocation events (5 triggers + 5 resets = 10 trades total) — a much smaller concern here than report 19's sector rotation, given how few trades this rule generates, but still not zero in practice.</li>
        <li class="mb-1.5">As of the last data point, the rule is back in its normal 50/50 state (not mid-drawdown) — see the pill above the trigger timeline; this wasn't cherry-picked, it's simply where the 2025-01-28 → 2025-12-23 cycle happened to land relative to today's date.</li>
        <li class="mb-1.5">The "periodic 50/50 rebalance" comparison line reuses report 14's exact blending mechanics (backtest13.blend_50_50) but on the Momentum-10 leg instead of report 14's Momentum-20 — it is NOT report 14's own number restated, it's freshly computed here for a fair, matched comparison.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modelled for gold, momentum, or NIFTY 50.</li>
        <li class="mb-1.5">This is a single, fixed historical path — 5 trigger events is not a large sample to judge a timing rule's reliability by; a different 17.6-year window could show a very different trigger count and outcome.</li>
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
      {timeline_panel}
      {honesty_note}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Momentum + Gold, With a Drawdown Catch</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("20_momentum_gold_catch_blend.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 20_momentum_gold_catch_blend.html")

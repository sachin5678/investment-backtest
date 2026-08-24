"""Builds 30_midcap_momentum10_breakeven_lock.html from results29.json.
Same self-contained contract, smooth Catmull-Rom charts, dark palette as
every other report."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results29.json") as f:
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
      tr.lock-row td{color:#F2B03C;}
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
    orig, lock = R["original"], R["breakeven_lock"]
    ts = R["trade_stats"]
    sym = R["currency_symbol"]
    arm_pct = R["profit_arm_pct"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap Momentum 10 — No Stop-Loss, Just a Breakeven Profit-Lock</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Same exact selection/weighting as reports 11-19, 24, 25, 27 — no downside stop at all. Instead: once a position has run up {arm_pct:.0f}% from entry, arm a protective exit at cost — if it falls all the way back to breakeven before the next rebalance, exit immediately at 0%, rather than riding it down further or waiting.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(R['start_date'])}–{esc(R['end_date'])} · {ts['total_positions']} total positions<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#37F083]">
        <div class="flex items-center gap-2 mb-3">
          {pill(f"only {ts['breakeven_lock_pct_of_positions']}% of positions ever triggered the rule", 'neutral')}
          {pill('near-neutral impact — a much smaller effect than either stop-loss threshold', 'positive')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          This rule only ever fires for a position that BOTH ran up {arm_pct:.0f}%+ from entry AND later gave essentially all of that gain back
          before the next rebalance — a much narrower trigger condition than report 27's fixed-percentage-loss stops. Over
          {esc(R['start_date'])}–{esc(R['end_date'])}, that happened to just <span class="font-semibold">{ts['breakeven_lock_exits']} of
          {ts['total_positions']} positions</span> ({ts['breakeven_lock_pct_of_positions']}%) — versus 15%'s 43.3% and 30%'s 12.5% of positions
          affected in report 27.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The result is correspondingly small: CAGR barely moves, from <span class="font-semibold">{pct(orig['cagr_pct'])}</span> (original) to
          <span class="font-semibold">{pct(lock['cagr_pct'])}</span> (with the lock) — a {pct(orig['cagr_pct']-lock['cagr_pct'],1,signed=False)}
          point difference, far smaller than either of report 27's stop-loss variants — and max drawdown is essentially unchanged
          ({pct(orig['max_drawdown_pct'],1,signed=False)} vs. {pct(lock['max_drawdown_pct'],1,signed=False)}). This rule locks in exactly what
          it's designed to: guaranteeing a big winner can never fully round-trip back to a loss, without materially touching the strategy's
          overall risk/return profile.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR", "Compound annual growth rate, identical window.",
                  [("Original (no exit rule)", pct(orig["cagr_pct"]), win_loss_kind(orig["cagr_pct"])),
                   (f"Breakeven-lock at +{arm_pct:.0f}%", pct(lock["cagr_pct"]), win_loss_kind(lock["cagr_pct"]))]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline over the same window.",
                  [("Original (no exit rule)", pct(orig["max_drawdown_pct"], 1, signed=False), "negative"),
                   (f"Breakeven-lock at +{arm_pct:.0f}%", pct(lock["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("Net return", f"{esc(R['start_date'])} to {esc(R['end_date'])}, base 100.",
                  [("Original (no exit rule)", pct(orig["net_return_pct"]), win_loss_kind(orig["net_return_pct"])),
                   (f"Breakeven-lock at +{arm_pct:.0f}%", pct(lock["net_return_pct"]), win_loss_kind(lock["net_return_pct"]))]),
        kpi_card("Position outcomes", "How every position taken over 18 years actually ended, with the lock rule active.",
                  [("Breakeven-locked", f"{ts['breakeven_lock_exits']} ({ts['breakeven_lock_pct_of_positions']}%)", "assumption"),
                   ("Rode to rebalance", f"{ts['rebalance_exits']}", "positive"),
                   ("Still open", f"{ts['still_open']}", "neutral")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, v, cls=""):
        c = f' class="{cls}"' if cls else ""
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(v['net_return_pct'])}</td><td>{pct(v['cagr_pct'])}</td>
        <td>{pct(v['max_drawdown_pct'],1,signed=False)}</td><td>{v['longest_underwater_days']:,}d</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Original vs. breakeven profit-lock</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the exact same strategy, identical {esc(R['start_date'])}–{esc(R['end_date'])} window, only the exit rule changes.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("Original — no exit rule, hold to rebalance", orig)}
          {row(f"With breakeven-lock at +{arm_pct:.0f}%", lock)}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "Original (no exit rule)", "color": COL["positive"], "points": orig["equity_curve"]},
        {"name": f"Breakeven-lock at +{arm_pct:.0f}%", "color": COL["assumption"], "points": lock["equity_curve"], "dash": True},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=460, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_30")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the two lines track each other almost exactly for the full 18-year window — visually near-indistinguishable, unlike report 27's stop-loss variants which diverge sharply.</p>
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
        {"name": "Original (no exit rule)", "color": COL["positive"], "points": dd_points(orig["equity_curve"])},
        {"name": f"Breakeven-lock at +{arm_pct:.0f}%", "color": COL["assumption"], "points": dd_points(lock["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=260, chart_id="dd_30")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the two drawdown lines sit almost exactly on top of each other — the breakeven-lock rule is simply too rare an event ({ts['breakeven_lock_pct_of_positions']}% of positions) to move the portfolio's overall drawdown profile.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    def trade_row(t):
        return f"""<tr class="lock-row"><td>{esc(t['ticker'])}</td><td>{esc(t['entry_date'])}</td><td>{sym}{t['entry_price']:,.2f}</td>
        <td>{esc(t['exit_date'])}</td><td>{sym}{t['exit_price']:,.2f}</td><td>{pct(t['pct_return'])}</td></tr>"""

    sample = R["breakeven_lock_trades_sample"]
    sample_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Every position the breakeven-lock actually caught</h3>
        {pill(f"all {ts['breakeven_lock_exits']} shown — small enough for a full list", 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every position that ran up {arm_pct:.0f}%+ at some point, then fell all the way back to its own entry price before the next rebalance. Returns cluster right around 0% — a small negative from occasional gap-through fills, not from the rule itself.</p>
      <div style="overflow-x:auto">
      <table class="data-table">
        <thead><tr><th style="text-align:left">Stock</th><th>Bought</th><th>Buy price</th><th>Locked out</th><th>Exit price</th><th>Return</th></tr></thead>
        <tbody>{''.join(trade_row(t) for t in sample)}</tbody>
      </table>
      </div>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why this rule barely moves the needle</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Report 27's stop-losses fire on a SINGLE condition (price falls X% from entry) — easy to trigger, which is why 43.3% of positions got
        caught at a 15% stop. This rule requires TWO conditions in sequence: the position must first prove it can run up {arm_pct:.0f}%, and
        THEN give essentially all of that entire gain back before the next rebalance. Most positions that reach +{arm_pct:.0f}% either keep
        running (never re-test entry) or pull back only partially — a full round-trip all the way to breakeven is a narrow, specific pattern,
        which is exactly why it only happened {ts['breakeven_lock_exits']} times in {ts['total_positions']} positions across 18 years.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        What this rule DOES guarantee, on the {ts['breakeven_lock_exits']} times it fired, is that a position which was once a big winner can
        never turn into an outright loss on the way back down — the average locked-out return was {pct(ts['avg_breakeven_lock_return'])}, almost
        exactly breakeven by construction. Whether those specific {ts['breakeven_lock_exits']} positions would have ended up positive or negative
        by the ACTUAL next rebalance (had the rule not intervened) isn't shown here — that counterfactual wasn't computed — but given how few
        positions are affected, either way the portfolio-level impact was always going to be small.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        The practical takeaway: this is a genuinely different kind of rule than a stop-loss — it protects a specific outcome (never letting a
        confirmed winner become a loser) rather than capping downside broadly, and it costs almost nothing to add because it so rarely fires.
        It is not a substitute for a stop-loss if the goal is limiting how much any single position can lose — for that, report 27's 30%
        threshold remains the better-tested option.
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
        <li class="mb-1.5">Today's fixed NIFTY Midcap 150 constituent list is applied retroactively across the whole window (survivorship bias) — same disclosed approximation as every other reconstruction here.</li>
        <li class="mb-1.5">Arming uses the day's intraday HIGH and the breakeven trigger uses the day's intraday LOW — a position that spikes to +30% and crashes back to entry within the SAME trading day is deliberately NOT caught (arming only takes effect starting the next day's check), a conservative choice since the data can't confirm which happened first within that one day.</li>
        <li class="mb-1.5">The counterfactual — what the {ts['breakeven_lock_exits']} locked-out positions would have actually returned by the real next rebalance had this rule not existed — was not computed; only the actual rule's effect on the portfolio's overall equity curve is shown.</li>
        <li class="mb-1.5">Only ONE arming threshold (+{arm_pct:.0f}%) was tested — a lower threshold would arm more positions (and likely trigger more often); a higher one, fewer.</li>
        <li class="mb-1.5">Zero transaction costs, slippage, or taxes are modeled — the extra {ts['breakeven_lock_exits']} trades this rule generates beyond the original strategy's {ts['rebalance_exits']} would carry a small real-world cost not reflected here.</li>
        <li class="mb-1.5">Equal weighting (not free-float market-cap x momentum score) and no F&O-eligibility screen, same as every other reconstruction in this project.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modeled for any holding. This is a single, fixed 18-year historical path.</li>
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
      {sample_panel}
      {honesty_note}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Midcap Momentum 10 — Breakeven Profit-Lock</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("30_midcap_momentum10_breakeven_lock.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 30_midcap_momentum10_breakeven_lock.html")

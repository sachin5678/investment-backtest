"""Builds 07_double_sip.html from results6.json (+ results4.json, results5.json
for the cross-strategy comparison). Same self-contained contract, smooth
Catmull-Rom charts, honesty rules."""
import json
import html
import pandas as pd
from svg_charts import line_chart, area_underwater_chart, COL

with open("results6.json") as f:
    R = json.load(f)
with open("results4.json") as f:
    R_DIP = json.load(f)
with open("results5.json") as f:
    R_REC = json.load(f)

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


def money(v, symbol, decimals=0):
    if v is None:
        return "—"
    sign = "-" if v < 0 else ""
    return f"{sign}{symbol}{abs(v):,.{decimals}f}"


def pct(v, decimals=1, signed=True):
    if v is None:
        return "—"
    s = "+" if (signed and v > 0) else ""
    return f"{s}{v:,.{decimals}f}%"


def win_loss_kind(v):
    if v is None:
        return "neutral"
    return "positive" if v > 0 else ("negative" if v < 0 else "neutral")


def weekly_resample(points):
    out = []
    last_week = None
    for d, v in points:
        wk = pd.Timestamp(d).to_period("W")
        if wk != last_week:
            out.append([d, v])
            last_week = wk
        else:
            out[-1] = [d, v]
    return out


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
      .scrollbox{max-height:320px;overflow:auto;}
      .scrollbox::-webkit-scrollbar{width:8px;}
      .scrollbox::-webkit-scrollbar-thumb{background:#1E3A45;border-radius:4px;}
      .kpi-val{font-size:26px;font-weight:700;letter-spacing:-0.01em;}
      tr.in-progress td{color:#F2B03C;}
    </style>
    """


def kpi_card(label, definition, cols):
    col_html = []
    for col_label, value_str, kind in cols:
        color = KIND_COLOR[kind]
        col_html.append(
            f'<div class="flex-1"><div class="text-[11px] text-[#7E97A0] mb-1 uppercase tracking-wide">{esc(col_label)}</div>'
            f'<div class="kpi-val mono" style="color:{color}">{value_str}</div></div>'
        )
    return f"""
    <div class="{PANEL_TIGHT}">
      <div class="text-[13px] font-semibold text-[#E6EDF0] mb-1">{esc(label)}</div>
      <div class="{MUTED} mb-3">{definition}</div>
      <div class="flex gap-4">{''.join(col_html)}</div>
    </div>
    """


def build():
    sym = R["currency_symbol"]
    strat_f = R["portfolios"]["strategy"]["frictionless"]
    strat_c = R["portfolios"]["strategy"]["cost_loaded"]
    van_m_f = R["portfolios"]["vanilla_midcap"]["frictionless"]
    van_n = R["portfolios"]["vanilla_nifty"]["frictionless"]
    dip_f = R_DIP["portfolios"]["strategy"]["frictionless"]
    rec_f = R_REC["portfolios"]["strategy"]["frictionless"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">SIP That Doubles During a Drawdown — NIFTY Midcap 150</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">₹1,000/month into midcap, always — except every month the SIP date falls while midcap is more than 15% below its all-time high, that month's contribution doubles to ₹2,000. Reverts to ₹1,000 once midcap sets a new all-time high.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          Data: Yahoo Finance daily OHLC via yfinance — midcap {esc(R['midcap_ticker'])}, NIFTY ^NSEI<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    definitions_strip = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL_TIGHT}">
        <p class="{WHAT_THIS_SHOWS} mb-2">WHAT THIS SHOWS — plain-English recap of the rule. This is different from the last two reports: it's not a one-off lump sum, it's the recurring SIP itself changing size for as long as a drawdown lasts.</p>
        <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
          Every month's ₹1,000 SIP, on the first trading day, still goes into midcap at that day's close. But the moment midcap's close first falls to
          {pill('15% below its all-time high', 'assumption')}, the strategy "arms" — and every SIP date that falls while still armed contributes
          <span class="font-semibold text-[#E6EDF0]">₹2,000 instead of ₹1,000</span>. It disarms — back to ₹1,000 — only once midcap closes back at or above
          that same pre-drop all-time high (the same hysteresis rule used in the last two reports, so a partial bounce that doesn't reach a new high
          doesn't reset it early).
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("Total invested (out of pocket)",
                  f"Sum of every SIP contribution — {strat_f['num_doubled_months']} of {strat_f['num_contributions']} months were doubled.",
                  [("Frictionless", money(strat_f["total_invested"], sym), "neutral"),
                   ("Cost-loaded", money(strat_c["total_invested"], sym), "neutral")]),
        kpi_card("Final portfolio value",
                  f"Market value of all units held as of {esc(R['end_date'])}.",
                  [("Frictionless", money(strat_f["final_value"], sym), "positive"),
                   ("Cost-loaded", money(strat_c["final_value"], sym), "positive")]),
        kpi_card("Net gain",
                  "Final value minus total invested, in ₹ and as a simple (non-annualised) % of what was put in.",
                  [("Frictionless", f'{money(strat_f["net_gain"], sym)} ({pct(strat_f["net_gain_pct"])})', "positive"),
                   ("Cost-loaded", f'{money(strat_c["net_gain"], sym)} ({pct(strat_c["net_gain_pct"])})', "positive")]),
        kpi_card("XIRR (annualised, money-weighted return)",
                  "The annual rate that makes the present value of every contribution, plus the final value, net to zero — comparable across different cash-flow schedules.",
                  [("Frictionless", pct(strat_f["xirr_pct"]), win_loss_kind(strat_f["xirr_pct"])),
                   ("Cost-loaded", pct(strat_c["xirr_pct"]), win_loss_kind(strat_c["xirr_pct"]))]),
        kpi_card("Drawdown episodes / doubled months",
                  "How many separate ≥15%-drawdown episodes occurred, and how many total SIP dates fell while armed.",
                  [("Both variants", f'{len(strat_f["episodes"])} episodes · {strat_f["num_doubled_months"]} doubled months', "assumption")]),
        kpi_card("Max drawdown (on value ÷ invested)",
                  f"Peak-to-trough decline of (portfolio value ÷ cumulative amount invested) — the same honest, growing-account-aware methodology as the last two reports. Occurred {esc(strat_f['max_drawdown_peak_date'])} → {esc(strat_f['max_drawdown_trough_date'])}.",
                  [("Frictionless", pct(strat_f["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Cost-loaded", pct(strat_c["max_drawdown_pct"], 1, signed=False), "negative")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(kpis)}</div>'

    def cmp_card(label, definition, values):
        cols = "".join(
            f'<div class="flex-1"><div class="text-[11px] text-[#7E97A0] mb-1 uppercase tracking-wide">{esc(n)}</div>'
            f'<div class="kpi-val mono" style="color:{KIND_COLOR[k]}">{v}</div></div>'
            for n, v, k in values
        )
        return f"""
        <div class="{PANEL_TIGHT}">
          <div class="text-[13px] font-semibold text-[#E6EDF0] mb-1">{esc(label)}</div>
          <div class="{MUTED} mb-3">{definition}</div>
          <div class="flex gap-4">{cols}</div>
        </div>
        """

    cmp_cards = [
        cmp_card("Total invested", "Different by design — this strategy adds an extra ₹1,000 on every doubled month.",
                  [("Double-SIP strategy", money(strat_f["total_invested"], sym), "neutral"),
                   ("Dip lump sums (report 5)", money(dip_f["total_invested"], sym), "neutral"),
                   ("Confirmed-recovery lump sum (report 6)", money(rec_f["total_invested"], sym), "neutral"),
                   ("Vanilla SIP, midcap", money(van_m_f["total_invested"], sym), "neutral")]),
        cmp_card("Final value", f"As of {esc(R['end_date'])}.",
                  [("Double-SIP strategy", money(strat_f["final_value"], sym), "positive"),
                   ("Dip lump sums (report 5)", money(dip_f["final_value"], sym), "positive"),
                   ("Confirmed-recovery lump sum (report 6)", money(rec_f["final_value"], sym), "positive"),
                   ("Vanilla SIP, midcap", money(van_m_f["final_value"], sym), "positive")]),
        cmp_card("XIRR — the fair comparison", "Annualised, money-weighted — comparable despite the different amounts and timings.",
                  [("Double-SIP strategy", pct(strat_f["xirr_pct"]), win_loss_kind(strat_f["xirr_pct"])),
                   ("Dip lump sums (report 5)", pct(dip_f["xirr_pct"]), win_loss_kind(dip_f["xirr_pct"])),
                   ("Confirmed-recovery lump sum (report 6)", pct(rec_f["xirr_pct"]), win_loss_kind(rec_f["xirr_pct"])),
                   ("Vanilla SIP, midcap", pct(van_m_f["xirr_pct"]), win_loss_kind(van_m_f["xirr_pct"]))]),
        cmp_card("Max drawdown (value ÷ invested)", "Smaller (closer to 0%) is a shallower worst-case paper loss relative to money put in so far.",
                  [("Double-SIP strategy", pct(strat_f["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Dip lump sums (report 5)", pct(dip_f["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Confirmed-recovery lump sum (report 6)", pct(rec_f["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Vanilla SIP, midcap", pct(van_m_f["max_drawdown_pct"], 1, signed=False), "negative")]),
    ]
    cmp_grid = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(cmp_cards)}</div>'

    eq_series = [
        {"name": "Double-SIP strategy — value", "color": COL["positive"], "points": weekly_resample(strat_f["value_curve"])},
        {"name": "Dip lump sums (report 5)", "color": COL["assumption"], "points": weekly_resample(dip_f["value_curve"]), "dash": True},
        {"name": "Vanilla SIP, midcap", "color": COL["text"], "points": weekly_resample(van_m_f["value_curve"])},
        {"name": "Vanilla SIP, NIFTY", "color": COL["negative"], "points": weekly_resample(van_n["value_curve"]), "dash": True},
    ]
    eq_svg, eq_legend = line_chart(eq_series, y_prefix=sym, height=460, value_fmt=lambda v: f"{v:,.0f}",
                                    chart_id="eq_double", smooth=True)
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Portfolio value over time — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
        {pill('smoothed curve through real weekly values', 'assumption')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the double-SIP strategy (green) pulls slightly ahead of both the dip-lump-sum strategy (amber) and vanilla SIP (white) by the end, from spreading extra money across every month of each drawdown rather than a couple of one-off lump sums.</p>
      <div class="flex items-center mb-2">{eq_legend}</div>
      {eq_svg}
      <div class="{MUTED} mt-2">Curve is drawn through one real data point per calendar week connected with a smooth curve — every plotted value is a genuine historical value. KPI figures above use the full daily series.</div>
    </div>
    """

    def dd_points(value, invested):
        i = {d: val for d, val in invested}
        out, peak = [], None
        for d, val in value:
            ratio = val / i[d] if i[d] else 1.0
            peak = ratio if peak is None else max(peak, ratio)
            out.append([d, (ratio / peak - 1.0) * 100.0])
        return out

    dd_series = [
        {"name": "Double-SIP strategy", "color": COL["positive"], "points": weekly_resample(dd_points(strat_f["value_curve"], strat_f["invested_curve"]))},
        {"name": "Dip lump sums (report 5)", "color": COL["assumption"], "points": weekly_resample(dd_points(dip_f["value_curve"], dip_f["invested_curve"])), "dash": True},
        {"name": "Vanilla SIP, midcap", "color": COL["text"], "points": weekly_resample(dd_points(van_m_f["value_curve"], van_m_f["invested_curve"])), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=260, chart_id="dd_double", smooth=True)
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison (value ÷ invested, not raw value)</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the double-SIP strategy's worst dip sits right on top of vanilla SIP's, unlike the dip-lump-sum strategy's deeper trough — spreading extra contributions across many months, rather than concentrating them in one or two big lump sums right near the bottom, avoids adding a large new stake at the single most fragile moment.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    rows = "".join(f"""
    <tr{' class="in-progress"' if e['end'] is None else ''}>
      <td>{esc(e['start'])}</td><td>{esc(e['end']) if e['end'] else 'still open as of ' + esc(R['end_date'])}</td>
      <td>{e['months_doubled']}</td><td>{money(e['months_doubled']*1000, sym, 0)}</td>
    </tr>""" for e in strat_f["episodes"])
    episodes_table = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Every drawdown episode</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the {len(strat_f['episodes'])} times midcap fell more than 15% below its all-time high, how many SIP dates fell while armed, and how much extra that added, frictionless variant.</p>
      <div class="scrollbox">
      <table class="data-table">
        <thead><tr><th>Armed (first ≥15% close)</th><th>Disarmed (new ATH)</th><th>Months doubled</th><th>Extra invested</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
      </div>
    </div>
    """

    xirr_gap_double = strat_f['xirr_pct'] - van_m_f['xirr_pct']
    xirr_gap_dip = dip_f['xirr_pct'] - van_m_f['xirr_pct']
    xirr_gap_rec = rec_f['xirr_pct'] - van_m_f['xirr_pct']
    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Three ways to time extra money into midcap — how they actually compare</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — across all three overlays tried on this exact data, which idea actually delivered the best trade-off?</p>
      <div class="scrollbox">
      <table class="data-table mb-3">
        <thead><tr><th>Overlay idea</th><th>Extra invested</th><th>XIRR vs. vanilla SIP</th><th>Max drawdown</th></tr></thead>
        <tbody>
          <tr><td>Double the SIP through every month of a ≥15% drawdown (this report)</td><td>{money(strat_f['total_invested']-van_m_f['total_invested'], sym)}</td>
              <td style="color:#37F083">{xirr_gap_double:+.2f}pp</td><td>{pct(strat_f['max_drawdown_pct'],1,signed=False)}</td></tr>
          <tr><td>Lump sums at -10%/-20% dip crossings (report 5)</td><td>{money(dip_f['total_invested']-van_m_f['total_invested'], sym)}</td>
              <td style="color:#37F083">{xirr_gap_dip:+.2f}pp</td><td>{pct(dip_f['max_drawdown_pct'],1,signed=False)}</td></tr>
          <tr><td>One lump sum on confirmed recovery to new ATH (report 6)</td><td>{money(rec_f['total_invested']-van_m_f['total_invested'], sym)}</td>
              <td style="color:#37F083">{xirr_gap_rec:+.2f}pp</td><td>{pct(rec_f['max_drawdown_pct'],1,signed=False)}</td></tr>
        </tbody>
      </table>
      </div>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        On this specific {esc(R['start_date'])}–{esc(R['end_date'])} window, <span class="font-semibold text-[#E6EDF0]">doubling the SIP through the whole drawdown
        did the most</span> — the best XIRR improvement of the three, using less extra capital than the dip-lump-sum approach, and without deepening the
        drawdown at all (unchanged from vanilla). That's a genuinely better-looking result than the last two reports found, but it rests on the same
        three correction episodes (2020, 2022, 2025) as all three — it is not three independent trials, and a fourth, differently-shaped correction could
        easily rank these differently.
      </p>
    </div>
    """

    limitations = f"""
    <div class="{PANEL} border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2">
        <h3 class="text-base font-bold text-[#E6EDF0]">Limitations</h3>
        {pill("read before trusting any number above", "assumption")}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the concrete ways this backtest can mislead you if taken at face value.</p>
      <ul class="text-[13px] text-[#C9D6DA] list-disc pl-5 leading-relaxed">
        <li class="mb-1.5">Only {len(strat_f['episodes'])} drawdown episodes exist in this data — the "best of three" ranking above is not a statistically meaningful comparison, just what happened to occur on this one historical path.</li>
        <li class="mb-1.5">The disarm-on-new-ATH hysteresis was not specified by you — it's carried over from the last two reports for consistency and for the same reason (avoiding rapid on/off flickering around the -15% line).</li>
        <li class="mb-1.5">The midcap ETF's Yahoo history starts {esc(R['start_date'])}, so — as in the last two reports — the 2008 and 2011 crashes are entirely absent.</li>
        <li class="mb-1.5">The monthly SIP date is assumed to be the first trading day of each calendar month; the doubled/normal amount is decided by the state as of that same day's close.</li>
        <li class="mb-1.5">The NIFTY 50 vanilla-SIP benchmark is frictionless only; the midcap portfolios are shown in both cost variants.</li>
        <li class="mb-1.5">The cost-loaded variant models only a flat 0.05% commission and a fixed one-tick slippage per contribution — no bid-ask spread widening, no market impact, no India-specific transaction taxes, no ETF tracking error vs. the actual NIFTY Midcap 150 index.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modelled anywhere in this report.</li>
        <li class="mb-1.5">Drawdown and longest-underwater are computed on (value ÷ invested), not raw ₹ — the same deliberate methodology as the last two reports.</li>
        <li class="mb-1.5">This is a single, fixed rule tested once over one specific historical window — there is no out-of-sample test and no check for whether "15% / double" happen to be curve-fit to this particular history.</li>
      </ul>
    </div>
    """

    body = f"""
    {header}
    {definitions_strip}
    <div class="px-10 py-6">
      {kpi_grid}
      <h2 class="text-lg font-bold text-[#E6EDF0] mt-8 mb-1">Strategy vs. vanilla-SIP benchmarks and the last two overlays</h2>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — same monthly contribution dates throughout: does doubling the SIP through a drawdown beat vanilla SIP-ing, and how does it stack up against the last two reports' lump-sum ideas?</p>
      {cmp_grid}
      {eq_panel}
      {dd_panel}
      {episodes_table}
      {honesty_note}
      <div class="mt-6">{limitations}</div>
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Double SIP During Drawdown — NIFTY Midcap 150</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("07_double_sip.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 07_double_sip.html")

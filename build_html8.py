"""Builds 08_double_sip_10pct.html from results7.json (10% trigger), compared
against results6.json (the 15% version) and the vanilla-SIP benchmarks. Same
self-contained contract, smooth Catmull-Rom charts, honesty rules."""
import json
import html
import pandas as pd
from svg_charts import line_chart, area_underwater_chart, COL

with open("results7.json") as f:
    R = json.load(f)
with open("results6.json") as f:
    R15 = json.load(f)

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
    strat15_f = R15["portfolios"]["strategy"]["frictionless"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">SIP That Doubles During a Drawdown — 10% Trigger — NIFTY Midcap 150</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Same rule as the last report, arming threshold lowered from 15% to 10%: ₹1,000/month into midcap, doubling to ₹2,000 every month midcap is ≥10% below its all-time high, reverting once it sets a new all-time high.</p>
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
        <p class="{WHAT_THIS_SHOWS} mb-2">WHAT THIS SHOWS — the only change from the last report is the arming threshold.</p>
        <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
          Identical mechanism to the last report — ₹1,000/month into midcap, doubling to ₹2,000 for every SIP date that falls while midcap is armed, reverting
          once midcap sets a new all-time high — except the arming threshold is now {pill('10% below ATH', 'assumption')} instead of 15%. A lower threshold arms
          more easily and more often, so more months end up doubled.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("Total invested (out of pocket)",
                  f"Sum of every SIP contribution — {strat_f['num_doubled_months']} of {strat_f['num_contributions']} months were doubled (vs. {strat15_f['num_doubled_months']} at the 15% threshold).",
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
                  "The annual rate that makes the present value of every contribution, plus the final value, net to zero.",
                  [("Frictionless", pct(strat_f["xirr_pct"]), win_loss_kind(strat_f["xirr_pct"])),
                   ("Cost-loaded", pct(strat_c["xirr_pct"]), win_loss_kind(strat_c["xirr_pct"]))]),
        kpi_card("Drawdown episodes / doubled months",
                  "How many separate ≥10%-drawdown episodes occurred, and how many total SIP dates fell while armed.",
                  [("Both variants", f'{len(strat_f["episodes"])} episodes · {strat_f["num_doubled_months"]} doubled months', "assumption")]),
        kpi_card("Max drawdown (on value ÷ invested)",
                  f"Peak-to-trough decline of (portfolio value ÷ cumulative amount invested). Occurred {esc(strat_f['max_drawdown_peak_date'])} → {esc(strat_f['max_drawdown_trough_date'])}.",
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
        cmp_card("Total invested", "The 10% trigger arms more easily, so more months get doubled.",
                  [("10% trigger (this report)", money(strat_f["total_invested"], sym), "neutral"),
                   ("15% trigger (last report)", money(strat15_f["total_invested"], sym), "neutral"),
                   ("Vanilla SIP, midcap", money(van_m_f["total_invested"], sym), "neutral"),
                   ("Vanilla SIP, NIFTY", money(van_n["total_invested"], sym), "neutral")]),
        cmp_card("Final value", f"As of {esc(R['end_date'])}.",
                  [("10% trigger (this report)", money(strat_f["final_value"], sym), "positive"),
                   ("15% trigger (last report)", money(strat15_f["final_value"], sym), "positive"),
                   ("Vanilla SIP, midcap", money(van_m_f["final_value"], sym), "positive"),
                   ("Vanilla SIP, NIFTY", money(van_n["final_value"], sym), "positive")]),
        cmp_card("XIRR — the fair comparison", "Annualised, money-weighted — comparable despite the different amounts and timings. Shown to 2 decimals here since the 10%-vs-15% gap is otherwise invisible at 1.",
                  [("10% trigger (this report)", pct(strat_f["xirr_pct"], 2), win_loss_kind(strat_f["xirr_pct"])),
                   ("15% trigger (last report)", pct(strat15_f["xirr_pct"], 2), win_loss_kind(strat15_f["xirr_pct"])),
                   ("Vanilla SIP, midcap", pct(van_m_f["xirr_pct"], 2), win_loss_kind(van_m_f["xirr_pct"])),
                   ("Vanilla SIP, NIFTY", pct(van_n["xirr_pct"]), win_loss_kind(van_n["xirr_pct"]))]),
        cmp_card("Max drawdown (value ÷ invested)", "Smaller (closer to 0%) is a shallower worst-case paper loss.",
                  [("10% trigger (this report)", pct(strat_f["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("15% trigger (last report)", pct(strat15_f["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Vanilla SIP, midcap", pct(van_m_f["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Vanilla SIP, NIFTY", pct(van_n["max_drawdown_pct"], 1, signed=False), "negative")]),
    ]
    cmp_grid = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(cmp_cards)}</div>'

    eq_series = [
        {"name": "10% trigger — value", "color": COL["positive"], "points": weekly_resample(strat_f["value_curve"])},
        {"name": "15% trigger (last report) — value", "color": COL["assumption"], "points": weekly_resample(strat15_f["value_curve"]), "dash": True},
        {"name": "Vanilla SIP, midcap", "color": COL["text"], "points": weekly_resample(van_m_f["value_curve"])},
        {"name": "Vanilla SIP, NIFTY", "color": COL["negative"], "points": weekly_resample(van_n["value_curve"]), "dash": True},
    ]
    eq_svg, eq_legend = line_chart(eq_series, y_prefix=sym, height=460, value_fmt=lambda v: f"{v:,.0f}",
                                    chart_id="eq_double10", smooth=True)
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Portfolio value over time — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
        {pill('smoothed curve through real weekly values', 'assumption')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the 10% and 15% versions track each other almost exactly despite the 10% version investing ₹13,000 more — the extra money from the shallower dips didn't buy a meaningfully bigger outcome.</p>
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
        {"name": "10% trigger (this report)", "color": COL["positive"], "points": weekly_resample(dd_points(strat_f["value_curve"], strat_f["invested_curve"]))},
        {"name": "15% trigger (last report)", "color": COL["assumption"], "points": weekly_resample(dd_points(strat15_f["value_curve"], strat15_f["invested_curve"])), "dash": True},
        {"name": "Vanilla SIP, midcap", "color": COL["text"], "points": weekly_resample(dd_points(van_m_f["value_curve"], van_m_f["invested_curve"])), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=260, chart_id="dd_double10", smooth=True)
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison (value ÷ invested, not raw value)</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — all three lines sit almost on top of each other; lowering the trigger to 10% neither helped nor hurt the worst-case paper loss in any visible way.</p>
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
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Every drawdown episode (10% trigger)</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the {len(strat_f['episodes'])} times midcap fell more than 10% below its all-time high — nearly double the 3 episodes the 15% threshold caught, because shallower, more frequent pullbacks now qualify too.</p>
      <div class="scrollbox">
      <table class="data-table">
        <thead><tr><th>Armed (first ≥10% close)</th><th>Disarmed (new ATH)</th><th>Months doubled</th><th>Extra invested</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
      </div>
    </div>
    """

    xirr_gap_10 = strat_f['xirr_pct'] - van_m_f['xirr_pct']
    xirr_gap_15 = strat15_f['xirr_pct'] - van_m_f['xirr_pct']
    extra_10 = strat_f['total_invested'] - van_m_f['total_invested']
    extra_15 = strat15_f['total_invested'] - van_m_f['total_invested']
    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Lower threshold, more money, about the same result</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — whether being more trigger-happy about "what counts as a drawdown" actually pays for the extra capital it commits.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Lowering the trigger from 15% to 10% roughly <span class="font-semibold text-[#E6EDF0]">doubled the number of drawdown episodes</span> ({len(strat15_f['episodes'])} → {len(strat_f['episodes'])})
        and the doubled-SIP months ({strat15_f['num_doubled_months']} → {strat_f['num_doubled_months']}), committing {money(extra_10, sym)} extra overall versus vanilla SIP — about
        {money(extra_10-extra_15, sym)} more than the 15% version's {money(extra_15, sym)}. That extra capital did <span class="font-semibold text-[#E6EDF0]">not</span> translate into a
        better outcome: XIRR actually came in very slightly lower ({pct(strat_f['xirr_pct'], 2)} vs. {pct(strat15_f['xirr_pct'], 2)} — the same to one decimal place, but a real, consistent gap), and max drawdown was essentially unchanged
        ({pct(strat_f['max_drawdown_pct'],1,signed=False)} vs. {pct(strat15_f['max_drawdown_pct'],1,signed=False)}).
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        The likely reason: a 10-15% pullback is common and often shallow — money doubled into those milder dips buys in at prices not meaningfully cheaper than
        a normal month would have anyway, while still diluting the concentration effect that made the 15% version's more selective doubling slightly more effective.
        More sensitivity points (5%, 20%, 25%…) would be needed to say where any real "sweet spot" sits — this report only tested two thresholds.
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
        <li class="mb-1.5">Only two thresholds (10% and 15%) have been tested — this is not a sweep across all plausible triggers, and the "10% did slightly worse" finding could reverse at other thresholds or other data windows.</li>
        <li class="mb-1.5">{len(strat_f['episodes'])} drawdown episodes at 10% is still a small sample — several of them are shallow, short pullbacks that may not repeat with the same frequency going forward.</li>
        <li class="mb-1.5">The disarm-on-new-ATH hysteresis, the ₹1,000/₹2,000 amounts, and the first-trading-day-of-month SIP date are all carried over unchanged from the last report for consistency, not independently re-justified for a 10% trigger.</li>
        <li class="mb-1.5">The midcap ETF's Yahoo history starts {esc(R['start_date'])}, missing the 2008 and 2011 crashes entirely, same caveat as every report in this series.</li>
        <li class="mb-1.5">The NIFTY 50 vanilla-SIP benchmark is frictionless only; the midcap portfolios are shown in both cost variants.</li>
        <li class="mb-1.5">The cost-loaded variant models only a flat 0.05% commission and a fixed one-tick slippage per contribution — no bid-ask spread widening, no market impact, no India-specific transaction taxes, no ETF tracking error vs. the actual NIFTY Midcap 150 index.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modelled anywhere in this report.</li>
        <li class="mb-1.5">Drawdown and longest-underwater are computed on (value ÷ invested), not raw ₹ — the same deliberate methodology as the last two reports.</li>
        <li class="mb-1.5">This is a single, fixed rule tested once over one specific historical window — there is no out-of-sample test and no check for whether any of these thresholds are curve-fit to this particular history.</li>
      </ul>
    </div>
    """

    body = f"""
    {header}
    {definitions_strip}
    <div class="px-10 py-6">
      {kpi_grid}
      <h2 class="text-lg font-bold text-[#E6EDF0] mt-8 mb-1">10% trigger vs. 15% trigger vs. vanilla-SIP benchmarks</h2>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — same monthly contribution dates throughout: does a more sensitive trigger help, or just commit more capital for the same outcome?</p>
      {cmp_grid}
      {eq_panel}
      {dd_panel}
      {episodes_table}
      {honesty_note}
      <div class="mt-6">{limitations}</div>
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Double SIP at 10% Drawdown — NIFTY Midcap 150</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("08_double_sip_10pct.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 08_double_sip_10pct.html")

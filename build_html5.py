"""Builds 05_sip_dip_overlay.html from results4.json. Same self-contained
contract as the earlier reports, with SMOOTH (Catmull-Rom curve) charts over
weekly-resampled real data points, per the user's request."""
import json
import html
import pandas as pd
from svg_charts import line_chart, area_underwater_chart, COL

with open("results4.json") as f:
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
    """Keep one REAL data point per calendar week (the last trading day seen
    that week) — this is what makes the smooth curve readable instead of
    tracing every daily wiggle, without inventing any synthetic averages."""
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
    van_m_c = R["portfolios"]["vanilla_midcap"]["cost_loaded"]
    van_n = R["portfolios"]["vanilla_nifty"]["frictionless"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">SIP + Tiered Dip Lump-Sums — NIFTY Midcap 150</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">₹1,000/month into midcap, always. +₹5,000 lump sum when midcap closes 10% below its own all-time high; +₹10,000 more when it closes 20% below. Compared against two vanilla-SIP benchmarks.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          Data: daily OHLC price data — midcap {esc(R['midcap_ticker'])}, NIFTY ^NSEI<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    definitions_strip = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL_TIGHT}">
        <p class="{WHAT_THIS_SHOWS} mb-2">WHAT THIS SHOWS — plain-English recap of the rule, and one judgment call flagged up front.</p>
        <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-2">
          ₹1,000 is invested every month, on the first trading day, into midcap — filled at that day's own close (a scheduled contribution, not a reactive signal).
          Separately, midcap's own <span class="font-semibold text-[#E6EDF0]">all-time high</span> (its running record closing level, since {esc(R['start_date'])}) is
          tracked continuously. If midcap's close ever falls to {pill("10% below that ATH", "assumption")}, an extra ₹5,000 is invested (filled at the next day's open);
          if it falls to {pill("20% below", "assumption")}, a further ₹10,000 is invested on top. Both tiers can fire in the same decline if it's steep enough.
        </p>
        <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
          {pill('Judgment call', 'assumption')} — the instruction didn't say how often a tier can re-fire. Tested literally (any day the close is ≤10% below ATH), midcap's
          price wobbled across that exact line <span class="font-semibold text-[#E6EDF0]">23 separate times in barely two months</span> in mid-2019 alone — each would trigger
          another ₹5,000. That's almost certainly not the intent, so this report only lets a tier fire again after midcap has set a genuinely <span class="font-semibold text-[#E6EDF0]">new</span>
          all-time high since it last fired — turning that into a sensible 6 tier-1 and 3 tier-2 events across {esc(R['start_date'])}–{esc(R['end_date'])}. Flagged again in Limitations.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("Total invested (out of pocket)",
                  "Sum of every SIP and lump-sum contribution — the strategy invests more in total than the vanilla benchmarks because of the extra dip lump sums.",
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
                  "The standard way to compare returns across cash-flow streams of different sizes and timings — the annual rate that makes the present value of every contribution, plus the final value, net to zero.",
                  [("Frictionless", pct(strat_f["xirr_pct"]), win_loss_kind(strat_f["xirr_pct"])),
                   ("Cost-loaded", pct(strat_c["xirr_pct"]), win_loss_kind(strat_c["xirr_pct"]))]),
        kpi_card("Tier-1 / Tier-2 lump sums fired",
                  "How many times the -10% and -20% triggers actually fired (after the new-ATH-required reset described above).",
                  [("Both variants", f'{sum(1 for e in strat_f["tier_events"] if e["tier_pct"]==10)} × ₹5,000 · {sum(1 for e in strat_f["tier_events"] if e["tier_pct"]==20)} × ₹10,000', "assumption")]),
        kpi_card("Max drawdown (on value ÷ invested)",
                  f"NOT a drawdown on raw ₹ value — raw value drifts up simply because more money keeps arriving. This is the peak-to-trough decline of (portfolio value ÷ cumulative amount invested), the honest way to see the paper-loss experience of a growing contribution account. Occurred {esc(strat_f['max_drawdown_peak_date'])} → {esc(strat_f['max_drawdown_trough_date'])}.",
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
        cmp_card("Total invested", "Different by design — the strategy adds lump sums the benchmarks never make.",
                  [("Strategy", money(strat_f["total_invested"], sym), "neutral"),
                   ("Vanilla SIP, midcap", money(van_m_f["total_invested"], sym), "neutral"),
                   ("Vanilla SIP, NIFTY", money(van_n["total_invested"], sym), "neutral")]),
        cmp_card("Final value", f"As of {esc(R['end_date'])}.",
                  [("Strategy", money(strat_f["final_value"], sym), "positive"),
                   ("Vanilla SIP, midcap", money(van_m_f["final_value"], sym), "positive"),
                   ("Vanilla SIP, NIFTY", money(van_n["final_value"], sym), "positive")]),
        cmp_card("XIRR — the fair comparison", "Annualised, money-weighted — comparable despite the different amounts and timings above.",
                  [("Strategy", pct(strat_f["xirr_pct"]), win_loss_kind(strat_f["xirr_pct"])),
                   ("Vanilla SIP, midcap", pct(van_m_f["xirr_pct"]), win_loss_kind(van_m_f["xirr_pct"])),
                   ("Vanilla SIP, NIFTY", pct(van_n["xirr_pct"]), win_loss_kind(van_n["xirr_pct"]))]),
        cmp_card("Max drawdown (value ÷ invested)", "Smaller (closer to 0%) is a shallower worst-case paper loss relative to money put in so far.",
                  [("Strategy", pct(strat_f["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Vanilla SIP, midcap", pct(van_m_f["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Vanilla SIP, NIFTY", pct(van_n["max_drawdown_pct"], 1, signed=False), "negative")]),
    ]
    cmp_grid = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(cmp_cards)}</div>'

    # smooth equity value chart (weekly-resampled real points, Catmull-Rom curve)
    eq_series = [
        {"name": "Strategy — value (frictionless)", "color": COL["positive"], "points": weekly_resample(strat_f["value_curve"])},
        {"name": "Vanilla SIP, midcap — value", "color": COL["text"], "points": weekly_resample(van_m_f["value_curve"])},
        {"name": "Vanilla SIP, NIFTY — value", "color": COL["negative"], "points": weekly_resample(van_n["value_curve"]), "dash": True},
        {"name": "Strategy — total invested", "color": COL["assumption"], "points": weekly_resample(strat_f["invested_curve"]), "dash": True},
    ]
    eq_svg, eq_legend = line_chart(eq_series, y_prefix=sym, height=460, value_fmt=lambda v: f"{v:,.0f}",
                                    chart_id="eq_sip", smooth=True)
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Portfolio value over time — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
        {pill('smoothed curve through real weekly values — see note below', 'assumption')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — market value of each portfolio, plus the strategy's own cumulative amount invested (dashed amber) so you can see how much of the ending value is your own money versus market gains.</p>
      <div class="flex items-center mb-2">{eq_legend}</div>
      {eq_svg}
      <div class="{MUTED} mt-2">Curve is drawn through one real data point per calendar week (not a synthetic average) connected with a smooth curve, as requested — every plotted value is a genuine historical value, just rendered with curved rather than jagged straight-line segments. KPI figures above are computed on the full daily series.</div>
    </div>
    """

    def dd_points(value, invested):
        v = {d: val for d, val in value}
        i = {d: val for d, val in invested}
        out, peak = [], None
        for d, val in value:
            ratio = val / i[d] if i[d] else 1.0
            peak = ratio if peak is None else max(peak, ratio)
            out.append([d, (ratio / peak - 1.0) * 100.0])
        return out

    dd_series = [
        {"name": "Strategy", "color": COL["positive"], "points": weekly_resample(dd_points(strat_f["value_curve"], strat_f["invested_curve"]))},
        {"name": "Vanilla SIP, midcap", "color": COL["text"], "points": weekly_resample(dd_points(van_m_f["value_curve"], van_m_f["invested_curve"])), "dash": True},
        {"name": "Vanilla SIP, NIFTY", "color": COL["negative"], "points": weekly_resample(dd_points(van_n["value_curve"], van_n["invested_curve"])), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=260, chart_id="dd_sip", smooth=True)
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison (value ÷ invested, not raw value)</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how far each portfolio's value fell below its own best-ever ratio to money invested; note the strategy's dips are not shallower than the vanilla SIP's — pouring extra money in as things fall can deepen the ratio's dip before it recovers.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    rows = "".join(f"""
    <tr>
      <td>{esc(e['signal_date'])}</td><td>{esc(e['fill_date'])}</td><td>-{e['tier_pct']:.0f}%</td>
      <td>{money(e['amount'], sym, 0)}</td><td>{money(e['fill_price'], sym, 2)}</td>
    </tr>""" for e in strat_f["tier_events"])
    events_table = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Every tiered lump-sum event</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — all 9 dip lump sums that actually fired, frictionless variant (cost-loaded fill prices differ by a few paise from slippage/commission and are omitted here for brevity).</p>
      <div class="scrollbox">
      <table class="data-table">
        <thead><tr><th>Signal date (close ≤ threshold)</th><th>Filled</th><th>Tier</th><th>Amount</th><th>Fill price</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
      </div>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Read this before concluding "the dip overlay works"</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — what the tactical overlay actually bought you, versus what simply choosing midcap over NIFTY bought you.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        The tactical dip overlay improved XIRR from {pct(van_m_f['xirr_pct'])} (vanilla midcap SIP) to {pct(strat_f['xirr_pct'])} (strategy) — about
        <span class="font-semibold text-[#E6EDF0]">+{strat_f['xirr_pct']-van_m_f['xirr_pct']:.1f} percentage points</span> a year, from only 9 lump-sum events across {esc(R['start_date'])}–{esc(R['end_date'])}.
        Compare that to the gap from simply choosing midcap over NIFTY 50 in the first place: {pct(van_n['xirr_pct'])} vs. {pct(van_m_f['xirr_pct'])} — a
        <span class="font-semibold text-[#E6EDF0]">~{van_m_f['xirr_pct']-van_n['xirr_pct']:.0f} percentage-point</span> difference. The asset-class choice mattered far more than the tactical overlay did.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        The overlay also did not reduce risk: the strategy's worst drawdown ({pct(strat_f['max_drawdown_pct'], 1, signed=False)}) is slightly deeper than the vanilla midcap
        SIP's ({pct(van_m_f['max_drawdown_pct'], 1, signed=False)}) — putting extra money in as a crash deepens increases your stake right when the ratio of value-to-invested
        is at its most fragile, the same pattern seen in the "Flight to Midcap" report. And with only 9 lump-sum events total (6 at -10%, 3 at -20%), this is a very small
        sample to generalise from either way.
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
        <li class="mb-1.5"><span class="font-semibold text-[#E6EDF0]">The "requires a new ATH to re-fire" rule was not specified by you</span> — it was added because the literal rule fires 23 times in two months on ordinary price noise. A tier that instead re-arms after any partial recovery, or one throttled to "once per calendar year," would produce a different number and timing of lump sums.</li>
        <li class="mb-1.5">Only 9 lump-sum events exist in this data (6 at -10%, 3 at -20%) — far too few to treat the overlay's apparent edge as statistically meaningful.</li>
        <li class="mb-1.5">The midcap ETF's available price history starts {esc(R['start_date'])}, so this backtest — like the last report — entirely misses the 2008 and 2011 crashes; it spans one pandemic crash, one rate-hike correction, and a couple of smaller wobbles.</li>
        <li class="mb-1.5">The monthly SIP date is assumed to be the first trading day of each calendar month — a different fixed date (5th, 15th, last day) would shift results slightly.</li>
        <li class="mb-1.5">XIRR is solved numerically by bisection over a -99.9%-to-+2000% annual rate range; it can fail to find a root for a pathological cash-flow pattern, though none occurred here.</li>
        <li class="mb-1.5">The NIFTY 50 vanilla-SIP benchmark is frictionless only (no commission/slippage modelled), to keep scope reasonable — the midcap portfolios are shown in both variants.</li>
        <li class="mb-1.5">The cost-loaded variant models only a flat 0.05% commission and a fixed one-tick slippage per contribution — no bid-ask spread widening, no market impact, no India-specific transaction taxes (STT, stamp duty, GST on brokerage), no ETF tracking error vs. the actual NIFTY Midcap 150 index.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modelled anywhere in this report.</li>
        <li class="mb-1.5">Drawdown and longest-underwater are computed on (value ÷ invested), not raw ₹ — a deliberate, disclosed methodology choice, not the same figure you'd get from a naive drawdown calculation on the raw value curve.</li>
        <li class="mb-1.5">This is a single, fixed rule tested once over one specific historical window — there is no out-of-sample test and no check for whether ₹1,000/10%/20% happen to be curve-fit to this particular history.</li>
      </ul>
    </div>
    """

    body = f"""
    {header}
    {definitions_strip}
    <div class="px-10 py-6">
      {kpi_grid}
      <h2 class="text-lg font-bold text-[#E6EDF0] mt-8 mb-1">Strategy vs. two vanilla-SIP benchmarks</h2>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — same monthly contribution dates throughout: does the tactical dip overlay help, and how much of any gain is really just "midcap vs. NIFTY" rather than the overlay itself?</p>
      {cmp_grid}
      {eq_panel}
      {dd_panel}
      {events_table}
      {honesty_note}
      <div class="mt-6">{limitations}</div>
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>SIP + Dip Overlay — NIFTY Midcap 150</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("05_sip_dip_overlay.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 05_sip_dip_overlay.html")

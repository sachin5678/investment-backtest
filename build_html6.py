"""Builds 06_breakout_recovery.html from results5.json (+ results4.json for
the bonus comparison against the dip-buying overlay strategy). Same
self-contained contract, smooth Catmull-Rom charts, honesty rules."""
import json
import html
import pandas as pd
from svg_charts import line_chart, area_underwater_chart, COL

with open("results5.json") as f:
    R = json.load(f)
with open("results4.json") as f:
    R_DIP = json.load(f)

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
    dip_f = R_DIP["portfolios"]["strategy"]["frictionless"]   # last report's dip-buying overlay, for comparison

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">SIP + "Buy the Confirmed Recovery" — NIFTY Midcap 150</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">₹1,000/month into midcap, always. +₹5,000 lump sum only once midcap has fallen ≥15% from its all-time high AND then closed back above that same high.</p>
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
        <p class="{WHAT_THIS_SHOWS} mb-2">WHAT THIS SHOWS — plain-English recap of the rule, which is the mirror image of the last report.</p>
        <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-2">
          ₹1,000 still goes into midcap on the first trading day of every month, filled at that day's close. Separately: once midcap's close has fallen
          {pill("15% below its all-time high", "assumption")} at any point, the strategy "arms" and waits. The extra ₹5,000 fires the moment midcap's close
          {pill("breaks back above that same pre-drop ATH", "assumption")} — filled at the next day's open, a reactive signal like every other trigger in this
          project. Unlike the last report, this buys confirmed strength <span class="font-semibold text-[#E6EDF0]">after</span> a correction has fully round-tripped,
          not the dip itself. After firing, it disarms — a fresh ≥15% drawdown from the new high is required before it can fire again.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("Total invested (out of pocket)",
                  "Sum of every SIP and lump-sum contribution.",
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
        kpi_card("Confirmed-recovery lump sums fired",
                  "How many times a ≥15% drawdown was actually followed by a full round trip back to a new all-time high.",
                  [("Both variants", f'{len(strat_f["events"])} × ₹5,000 = {money(len(strat_f["events"])*5000, sym)}', "assumption")]),
        kpi_card("Max drawdown (on value ÷ invested)",
                  f"Peak-to-trough decline of (portfolio value ÷ cumulative amount invested) — the honest way to see paper-loss for a growing contribution account, not a naive drawdown on raw ₹ value. Occurred {esc(strat_f['max_drawdown_peak_date'])} → {esc(strat_f['max_drawdown_trough_date'])}.",
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
        cmp_card("Total invested", "The recovery strategy invests only slightly more than vanilla (3 lump sums vs. the dip strategy's 9).",
                  [("Recovery strategy", money(strat_f["total_invested"], sym), "neutral"),
                   ("Dip strategy (last report)", money(dip_f["total_invested"], sym), "neutral"),
                   ("Vanilla SIP, midcap", money(van_m_f["total_invested"], sym), "neutral"),
                   ("Vanilla SIP, NIFTY", money(van_n["total_invested"], sym), "neutral")]),
        cmp_card("Final value", f"As of {esc(R['end_date'])}.",
                  [("Recovery strategy", money(strat_f["final_value"], sym), "positive"),
                   ("Dip strategy (last report)", money(dip_f["final_value"], sym), "positive"),
                   ("Vanilla SIP, midcap", money(van_m_f["final_value"], sym), "positive"),
                   ("Vanilla SIP, NIFTY", money(van_n["final_value"], sym), "positive")]),
        cmp_card("XIRR — the fair comparison", "Annualised, money-weighted — comparable despite the different amounts and timings.",
                  [("Recovery strategy", pct(strat_f["xirr_pct"]), win_loss_kind(strat_f["xirr_pct"])),
                   ("Dip strategy (last report)", pct(dip_f["xirr_pct"]), win_loss_kind(dip_f["xirr_pct"])),
                   ("Vanilla SIP, midcap", pct(van_m_f["xirr_pct"]), win_loss_kind(van_m_f["xirr_pct"])),
                   ("Vanilla SIP, NIFTY", pct(van_n["xirr_pct"]), win_loss_kind(van_n["xirr_pct"]))]),
        cmp_card("Max drawdown (value ÷ invested)", "Smaller (closer to 0%) is a shallower worst-case paper loss relative to money put in so far.",
                  [("Recovery strategy", pct(strat_f["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Dip strategy (last report)", pct(dip_f["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Vanilla SIP, midcap", pct(van_m_f["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Vanilla SIP, NIFTY", pct(van_n["max_drawdown_pct"], 1, signed=False), "negative")]),
    ]
    cmp_grid = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(cmp_cards)}</div>'

    eq_series = [
        {"name": "Recovery strategy — value", "color": COL["positive"], "points": weekly_resample(strat_f["value_curve"])},
        {"name": "Dip strategy (last report) — value", "color": COL["assumption"], "points": weekly_resample(dip_f["value_curve"]), "dash": True},
        {"name": "Vanilla SIP, midcap — value", "color": COL["text"], "points": weekly_resample(van_m_f["value_curve"])},
        {"name": "Vanilla SIP, NIFTY — value", "color": COL["negative"], "points": weekly_resample(van_n["value_curve"]), "dash": True},
    ]
    eq_svg, eq_legend = line_chart(eq_series, y_prefix=sym, height=460, value_fmt=lambda v: f"{v:,.0f}",
                                    chart_id="eq_rec", smooth=True)
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Portfolio value over time — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
        {pill('smoothed curve through real weekly values', 'assumption')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the recovery strategy (green) tracks the vanilla midcap SIP (white) almost exactly — the ₹15,000 in extra lump sums barely moves the line, unlike the dip strategy's more visible lift.</p>
      <div class="flex items-center mb-2">{eq_legend}</div>
      {eq_svg}
      <div class="{MUTED} mt-2">Curve is drawn through one real data point per calendar week connected with a smooth curve — every plotted value is a genuine historical value, just rendered with curved rather than jagged straight-line segments. KPI figures above use the full daily series.</div>
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
        {"name": "Recovery strategy", "color": COL["positive"], "points": weekly_resample(dd_points(strat_f["value_curve"], strat_f["invested_curve"]))},
        {"name": "Dip strategy (last report)", "color": COL["assumption"], "points": weekly_resample(dd_points(dip_f["value_curve"], dip_f["invested_curve"])), "dash": True},
        {"name": "Vanilla SIP, midcap", "color": COL["text"], "points": weekly_resample(dd_points(van_m_f["value_curve"], van_m_f["invested_curve"])), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=260, chart_id="dd_rec", smooth=True)
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison (value ÷ invested, not raw value)</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — because this strategy only adds money AFTER a full recovery (never mid-crash), its drawdown line sits on top of the vanilla SIP's almost exactly — unlike the dip strategy, which deepened its own worst drawdown by buying in while things were still falling.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    rows = "".join(f"""
    <tr>
      <td>{esc(e['signal_date'])}</td><td>{esc(e['fill_date'])}</td><td>{money(5000, sym, 0)}</td><td>{money(e['fill_price'], sym, 2)}</td>
    </tr>""" for e in strat_f["events"])
    events_table = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Every confirmed-recovery event</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — all {len(strat_f['events'])} times a ≥15% drawdown fully round-tripped back to a new all-time high, frictionless variant.</p>
      <div class="scrollbox">
      <table class="data-table">
        <thead><tr><th>Breakout close (signal)</th><th>Filled</th><th>Amount</th><th>Fill price</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
      </div>
    </div>
    """

    xirr_gap_recovery = strat_f['xirr_pct'] - van_m_f['xirr_pct']
    xirr_gap_dip = dip_f['xirr_pct'] - van_m_f['xirr_pct']
    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Buying the dip vs. buying the confirmed recovery</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the direct comparison you're likely asking for: which timing idea actually did more with the same ₹1,000/month base?</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Buying the confirmed recovery added {money(len(strat_f['events'])*5000, sym)} across {len(strat_f['events'])} lump sums and moved XIRR from {pct(van_m_f['xirr_pct'])}
        (vanilla midcap SIP) to {pct(strat_f['xirr_pct'])} — a gain of only <span class="font-semibold text-[#E6EDF0]">{xirr_gap_recovery:+.2f} percentage points</span> a year.
        The dip-buying overlay from the last report added three times as much extra money (₹60,000 across 9 lump sums) and moved XIRR by
        <span class="font-semibold text-[#E6EDF0]">{xirr_gap_dip:+.2f} percentage points</span> — over 10× the improvement, for roughly 4× the extra capital.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        The trade-off: this strategy's max drawdown ({pct(strat_f['max_drawdown_pct'], 1, signed=False)}) is identical to plain vanilla SIP-ing, because it never adds money while
        the market is still falling — it only ever buys in after the fact. The dip strategy took on a slightly deeper drawdown ({pct(dip_f['max_drawdown_pct'], 1, signed=False)})
        in exchange for its bigger return gain. Whether that trade-off is worth it is a judgment call this report can't make for you — but on this specific
        {esc(R['start_date'])}–{esc(R['end_date'])} data, buying the dip did more than buying the confirmed recovery, on both counts.
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
        <li class="mb-1.5">Only {len(strat_f['events'])} confirmed-recovery events exist in this data — far too few to treat this overlay's near-zero edge over vanilla SIP as a settled conclusion either way.</li>
        <li class="mb-1.5">The "disarm after firing, re-arm only after a fresh ≥15% drawdown" rule was not specified by you — it's the natural mirror of the reset rule used in the last report, applied here for the same reason (to stop repeated firing on ordinary noise near the old high).</li>
        <li class="mb-1.5">The midcap ETF's Yahoo history starts {esc(R['start_date'])}, so — as in the last two reports — the 2008 and 2011 crashes are entirely absent; this backtest spans essentially three correction-recovery cycles (2020, 2022, 2025).</li>
        <li class="mb-1.5">The monthly SIP date is assumed to be the first trading day of each calendar month.</li>
        <li class="mb-1.5">The NIFTY 50 vanilla-SIP benchmark is frictionless only; the midcap portfolios are shown in both cost variants.</li>
        <li class="mb-1.5">The cost-loaded variant models only a flat 0.05% commission and a fixed one-tick slippage per contribution — no bid-ask spread widening, no market impact, no India-specific transaction taxes, no ETF tracking error vs. the actual NIFTY Midcap 150 index.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modelled anywhere in this report.</li>
        <li class="mb-1.5">Drawdown and longest-underwater are computed on (value ÷ invested), not raw ₹ — the same deliberate methodology as the last report, not a naive drawdown on the raw value curve.</li>
        <li class="mb-1.5">This is a single, fixed rule tested once over one specific historical window — there is no out-of-sample test and no check for whether "15% / ₹5,000" happen to be curve-fit to this particular history.</li>
      </ul>
    </div>
    """

    body = f"""
    {header}
    {definitions_strip}
    <div class="px-10 py-6">
      {kpi_grid}
      <h2 class="text-lg font-bold text-[#E6EDF0] mt-8 mb-1">Strategy vs. vanilla-SIP benchmarks and the dip-buying overlay</h2>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — same monthly contribution dates throughout: does buying strength after a confirmed recovery help, and how does it stack up against buying the dip itself (last report)?</p>
      {cmp_grid}
      {eq_panel}
      {dd_panel}
      {events_table}
      {honesty_note}
      <div class="mt-6">{limitations}</div>
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>SIP + Confirmed Recovery — NIFTY Midcap 150</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("06_breakout_recovery.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 06_breakout_recovery.html")

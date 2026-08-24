"""Builds 04_midcap_rotation.html from results3.json. Same self-contained
contract as the earlier reports: Tailwind Play CDN, inline SVG charts
(svg_charts.py), no chart/backtesting libraries, dark palette, honesty rules."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results3.json") as f:
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
      .scrollbox{max-height:340px;overflow:auto;}
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


def dd_points(points):
    out, peak = [], None
    for d, v in points:
        peak = v if peak is None else max(peak, v)
        out.append([d, (v / peak - 1.0) * 100.0])
    return out


def build():
    sym = R["currency_symbol"]
    fr = R["variants"]["frictionless"]
    cl = R["variants"]["cost_loaded"]
    bh_n = R["benchmark_nifty"]
    bh_m = R["benchmark_midcap"]
    sf, sc = fr["stats"], cl["stats"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Flight to Midcap — NIFTY 50 / Midcap 150 Rotation</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Hold NIFTY 50 by default. When NIFTY closes 15% below its all-time high, move 100% into midcap for exactly one year, then rotate back to NIFTY. Repeats.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          Data: Yahoo Finance daily OHLC via yfinance — NIFTY ^NSEI, midcap {esc(R['midcap_ticker'])}<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    definitions_strip = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL_TIGHT}">
        <p class="{WHAT_THIS_SHOWS} mb-2">WHAT THIS SHOWS — plain-English recap of the rule being tested.</p>
        <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
          The account defaults to <span class="font-semibold text-[#E6EDF0]">100% NIFTY 50</span> — unlike the two prior reports, it is never sitting in cash.
          <span class="font-semibold text-[#E6EDF0]">ATH</span> (all-time high) is NIFTY's own running record closing level, tracked continuously since
          {esc(R['nifty_data_start'])} — it only ever rises or holds flat, never resets. Whenever NIFTY's close falls to
          {pill("15% below that ATH", "assumption")}, the account sells all of its NIFTY and buys midcap instead (filled at the next day's open),
          confirmed in chat as the {pill("NIFTY Midcap 150 tracking ETF, " + esc(R['midcap_ticker']), "assumption")}. It then holds midcap for
          {pill("exactly 365 calendar days", "assumption")}, at which point it's a scheduled, known-in-advance event — modelled as switching back to
          NIFTY at that day's own close, not the next open. Only after that rotation back does the account start watching for the next -15% signal again
          — starting the following trading day. Because midcap data on Yahoo only goes back to {esc(R['midcap_data_start'])}, the backtest itself can only
          run from there, even though the ATH used to judge each dip reflects NIFTY's full history back to {esc(R['nifty_data_start'])}.
        </p>
      </div>
    </div>
    """

    kpis = []
    kpis.append(kpi_card(
        "Rotation episodes (closed)",
        'A "trade" is one complete NIFTY→midcap→NIFTY round trip. Both cost variants have identical episode timing — cost only changes fill prices, not when rotations happen.',
        [("Both variants", str(sf["num_episodes"]), "neutral")],
    ))
    kpis.append(kpi_card(
        "Win rate (midcap beat NIFTY over the same window)",
        "Of the closed episodes, the share where midcap's return during the year actually held beat what NIFTY itself returned over that identical window — i.e. the rotation was the right call in hindsight.",
        [("Frictionless", pct(sf.get("win_rate"), 0, signed=False), win_loss_kind(1) if sf.get("win_rate") else "neutral"),
         ("Cost-loaded", pct(sc.get("win_rate"), 0, signed=False), win_loss_kind(1) if sc.get("win_rate") else "neutral")],
    ))
    kpis.append(kpi_card(
        "Average outperformance per episode",
        "Mean of (midcap's return during the year held) minus (NIFTY's return over that identical window), across closed episodes. Positive means rotating helped, on average.",
        [("Frictionless", pct(sf.get("avg_outperformance_pct")), win_loss_kind(sf.get("avg_outperformance_pct"))),
         ("Cost-loaded", pct(sc.get("avg_outperformance_pct")), win_loss_kind(sc.get("avg_outperformance_pct")))],
    ))
    kpis.append(kpi_card(
        "Net return",
        f"Total % change in account equity from {esc(fr['start_date'])} to {esc(R['nifty_data_end'])}.",
        [("Frictionless", pct(fr["net_return_pct"]), win_loss_kind(fr["net_return_pct"])),
         ("Cost-loaded", pct(cl["net_return_pct"]), win_loss_kind(cl["net_return_pct"]))],
    ))
    kpis.append(kpi_card(
        "CAGR",
        "Compound annual growth rate over the actual backtest span (2019-02-04 onward — constrained by the midcap ETF's Yahoo history).",
        [("Frictionless", pct(fr["cagr_pct"]), win_loss_kind(fr["cagr_pct"])),
         ("Cost-loaded", pct(cl["cagr_pct"]), win_loss_kind(cl["cagr_pct"]))],
    ))
    kpis.append(kpi_card(
        "Max drawdown",
        f"Largest peak-to-trough decline of the account's own equity. Occurred {esc(fr['max_drawdown_peak_date'])} → {esc(fr['max_drawdown_trough_date'])} — the COVID crash: the account had already rotated into midcap by then, and midcap fell further than NIFTY did before the eventual recovery, making this WORSE than either static benchmark below.",
        [("Frictionless", pct(fr["max_drawdown_pct"], 1, signed=False), "negative"),
         ("Cost-loaded", pct(cl["max_drawdown_pct"], 1, signed=False), "negative")],
    ))
    kpis.append(kpi_card(
        "Longest time underwater",
        "Longest stretch, in calendar days, the account's equity stayed below a prior peak before a new all-time high.",
        [("Frictionless", f'{fr["longest_underwater_days"]:,} days', "neutral"),
         ("Cost-loaded", f'{cl["longest_underwater_days"]:,} days', "neutral")],
    ))

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
        cmp_card("Net return", f"Same start date ({esc(fr['start_date'])}) and starting balance for all four.",
                  [("Strategy — frictionless", pct(fr["net_return_pct"]), win_loss_kind(fr["net_return_pct"])),
                   ("Strategy — cost-loaded", pct(cl["net_return_pct"]), win_loss_kind(cl["net_return_pct"])),
                   ("NIFTY buy & hold", pct(bh_n["net_return_pct"]), win_loss_kind(bh_n["net_return_pct"])),
                   ("Midcap buy & hold", pct(bh_m["net_return_pct"]), win_loss_kind(bh_m["net_return_pct"]))]),
        cmp_card("CAGR", "Compound annual growth rate, identical date range for all four.",
                  [("Strategy — frictionless", pct(fr["cagr_pct"]), win_loss_kind(fr["cagr_pct"])),
                   ("Strategy — cost-loaded", pct(cl["cagr_pct"]), win_loss_kind(cl["cagr_pct"])),
                   ("NIFTY buy & hold", pct(bh_n["cagr_pct"]), win_loss_kind(bh_n["cagr_pct"])),
                   ("Midcap buy & hold", pct(bh_m["cagr_pct"]), win_loss_kind(bh_m["cagr_pct"]))]),
        cmp_card("Max drawdown", "Smaller (closer to 0%) is a shallower worst-case loss. The strategy's is the deepest of the three — see the KPI note above.",
                  [("Strategy — frictionless", pct(fr["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Strategy — cost-loaded", pct(cl["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("NIFTY buy & hold", pct(bh_n["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Midcap buy & hold", pct(bh_m["max_drawdown_pct"], 1, signed=False), "negative")]),
        cmp_card("Longest time underwater", "Longest stretch below a prior equity peak, in calendar days (buy-and-hold benchmarks shown for net return/CAGR/MDD only — underwater duration omitted here for the raw indices to keep the comparison to what was actually requested).",
                  [("Strategy — frictionless", f'{fr["longest_underwater_days"]:,} days', "neutral"),
                   ("Strategy — cost-loaded", f'{cl["longest_underwater_days"]:,} days', "neutral"),
                   ("NIFTY buy & hold", f'{bh_n["longest_underwater_days"]:,} days', "neutral"),
                   ("Midcap buy & hold", "—", "neutral")]),
    ]
    cmp_grid = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(cmp_cards)}</div>'

    eq_series = [
        {"name": "Strategy — frictionless", "color": COL["positive"], "points": fr["equity_curve"]},
        {"name": "Strategy — cost-loaded", "color": COL["assumption"], "points": cl["equity_curve"], "dash": True},
        {"name": "NIFTY buy & hold", "color": COL["text"], "points": bh_n["equity_curve"]},
        {"name": "Midcap buy & hold", "color": COL["negative"], "points": bh_m["equity_curve"], "dash": True},
    ]
    eq_svg, eq_legend = line_chart(eq_series, y_prefix=sym, height=460, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_rot")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Equity curve — {sym}{R['initial_capital']:,.0f} start ({esc(fr['start_date'])} to {esc(R['nifty_data_end'])})</h3>
        {pill('linear axis, starts at zero — not log-scaled', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the strategy's path sits between the two pure buy-and-hold lines for most of the period; whether that's "worth it" versus simply holding midcap the whole time is a judgment call the Limitations panel below speaks to.</p>
      <div class="flex items-center mb-2">{eq_legend}</div>
      {eq_svg}
    </div>
    """

    dd_series = [
        {"name": "Strategy — frictionless", "color": COL["positive"], "points": dd_points(fr["equity_curve"])},
        {"name": "NIFTY buy & hold", "color": COL["text"], "points": dd_points(bh_n["equity_curve"]), "dash": True},
        {"name": "Midcap buy & hold", "color": COL["negative"], "points": dd_points(bh_m["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=260, chart_id="dd_rot")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — during the COVID crash the strategy (green) fell further than plain NIFTY (white) because it had just rotated into the higher-beta midcap segment right as that segment kept falling.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    # episode table
    rows = []
    for i, ef in enumerate(fr["episodes"]):
        ec = cl["episodes"][i]
        win = ef["outperformance_pct"] > 0
        rows.append(f"""
        <tr>
          <td>{esc(ef.get('signal_date', '—'))}</td>
          <td>{esc(ef['switch_to_midcap_date'])}</td><td>{pct(ef['drawdown_at_switch_pct'], 1, signed=False)}</td>
          <td>{esc(ef['switch_back_date'])}</td><td>{ef['days_held']}</td>
          <td>{pct(ef['midcap_episode_return_pct'])}</td><td>{pct(ef['nifty_same_window_return_pct'])}</td>
          <td style="color:{'#37F083' if win else '#F2643C'}">{pct(ef['outperformance_pct'])}</td>
          <td>{pct(ec['midcap_episode_return_pct'])}</td><td style="color:{'#37F083' if ec['outperformance_pct']>0 else '#F2643C'}">{pct(ec['outperformance_pct'])}</td>
        </tr>""")

    ip = fr.get("in_progress_episode")
    in_progress_row = ""
    if ip:
        in_progress_row = f"""
        <tr class="in-progress">
          <td>{esc(ip.get('signal_date','—'))}</td>
          <td>{esc(ip['switch_to_midcap_date'])}</td><td>{pct(ip['drawdown_at_switch_pct'], 1, signed=False)}</td>
          <td colspan="2">scheduled {esc(ip['scheduled_switch_back'])} — still open as of {esc(ip['as_of'])}</td>
          <td colspan="4">mark-to-market value: {money(ip['mark_to_market_value'], sym, 0)} — not a closed episode, excluded from all statistics above</td>
        </tr>"""

    episodes_table = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Episode-by-episode log</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every rotation: the day the -15% signal actually fired, the day it executed, how deep NIFTY really was at that trigger, and how midcap's year compared with what NIFTY itself did over the identical stretch.</p>
      <div class="scrollbox">
      <table class="data-table">
        <thead><tr><th>Signal date</th><th>Switch to midcap</th><th>Drawdown at signal</th><th>Switch back to NIFTY</th><th>Days held</th>
        <th>Midcap return (frict.)</th><th>NIFTY, same window</th><th>Outperformance (frict.)</th>
        <th>Midcap return (cost-loaded)</th><th>Outperformance (cost-loaded)</th></tr></thead>
        <tbody>{''.join(rows)}{in_progress_row}</tbody>
      </table>
      </div>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Read this before concluding "rotating into midcap works"</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the two most important caveats behind the headline numbers, stated plainly.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        <span class="font-semibold text-[#E6EDF0]">Only 3 closed episodes exist</span> in the ~6.5 years this ETF has traded, and all 3 happened to have midcap outperform
        NIFTY over the year that followed. A 100% win rate on 3 events is an encouraging sign, not evidence of an edge — with a sample this small, a single future
        counter-example would flip the picture, and there is no statistical basis here to say the -15%/1-year rule is better than chance.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        <span class="font-semibold text-[#E6EDF0]">The risk story is not what you might expect.</span> The strategy's worst drawdown ({pct(fr['max_drawdown_pct'], 1, signed=False)})
        is actually deeper than either static benchmark ({pct(bh_n['max_drawdown_pct'], 1, signed=False)} for NIFTY, {pct(bh_m['max_drawdown_pct'], 1, signed=False)} for midcap) —
        because the account rotated into the higher-beta midcap segment right as the 2020 COVID crash was still unfolding, and midcap kept falling faster than NIFTY did before
        the eventual recovery. Buying the dip into a more volatile asset can make the ride down worse before it makes the ride back up better.
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
        <li class="mb-1.5">Only {sf['num_episodes']} closed rotation episodes exist in this data — every win-rate and average-outperformance figure above rests on an extremely small sample.</li>
        <li class="mb-1.5">"Midcap" was resolved to the NIFTY Midcap 150 tracking ETF ({esc(R['midcap_ticker'])}), confirmed with you in chat specifically because it has more representative, current-day composition than the alternative (NIFTY Midcap 50 index) — but its Yahoo history only starts {esc(R['midcap_data_start'])}, so the 2008 and 2011 crashes that the earlier two reports covered are entirely absent here.</li>
        <li class="mb-1.5">"-15% from ATH" and "hold for 365 days" were both taken literally from your instruction, not independently chosen or optimized — but neither was tested for sensitivity; a 10% or 20% trigger, or a 6-month or 2-year hold, could change every number here, possibly a lot.</li>
        <li class="mb-1.5">The entry (NIFTY→midcap) fills at the next day's open, a reactive signal; the exit (midcap→NIFTY, one year later) is modelled at that day's own close, a scheduled, known-in-advance event — this asymmetry is intentional and consistent with the earlier two reports, not an inconsistency.</li>
        <li class="mb-1.5">A new trigger is only evaluated starting the day AFTER a scheduled rotation back to NIFTY, not the same day — an assumption to avoid a same-day double-flip; if NIFTY is still deep in a drawdown at that point, the account could rotate right back into midcap almost immediately (this did not occur in this particular data window, but is structurally possible).</li>
        <li class="mb-1.5">The cost-loaded variant models only a flat 0.05% commission and a fixed one-tick slippage on each leg of each rotation (4 fills per full round trip) — no bid-ask spread widening, no market impact, no India-specific transaction taxes (STT, stamp duty, GST on brokerage), no ETF tracking error vs. the actual NIFTY Midcap 150 index.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modelled for the strategy or either buy-and-hold benchmark.</li>
        <li class="mb-1.5">This is a single, fixed rule tested once over a short, ~6.5-year window that happens to contain a global pandemic crash, a rate-hike correction, and a 2025 wobble — three very different market regimes compressed into three data points. There is no out-of-sample test and no check for whether these particular thresholds are curve-fit to this history.</li>
      </ul>
    </div>
    """

    body = f"""
    {header}
    {definitions_strip}
    <div class="px-10 py-6">
      {kpi_grid}
      <h2 class="text-lg font-bold text-[#E6EDF0] mt-8 mb-1">Strategy vs. buy-and-hold benchmarks</h2>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — same start date, same starting balance: net return, CAGR, max drawdown and longest time underwater against holding NIFTY alone or midcap alone the whole time.</p>
      {cmp_grid}
      {eq_panel}
      {dd_panel}
      {episodes_table}
      {honesty_note}
      <div class="mt-6">{limitations}</div>
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Flight to Midcap — NIFTY 50 Rotation Strategy</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("04_midcap_rotation.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 04_midcap_rotation.html")

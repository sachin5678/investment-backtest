"""Builds 10_momentum_sip.html from results9.json. Same self-contained
contract, smooth Catmull-Rom charts, honesty rules — including a prominent
disclosure of the listing-day data artifact that was removed before running
this backtest."""
import json
import html
import pandas as pd
from svg_charts import line_chart, area_underwater_chart, COL

with open("results9.json") as f:
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
      .kpi-val{font-size:26px;font-weight:700;letter-spacing:-0.01em;}
      .rank-1{background:rgba(55,240,131,0.08);}
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


LABELS = {"momentum": "Momentum ETF (HDFCMOMENT.NS)", "midcap": "Midcap (MID150BEES.NS)", "nifty": "NIFTY 50"}
COLORS = {"momentum": COL["assumption"], "midcap": COL["positive"], "nifty": COL["text"]}


def build():
    sym = R["currency_symbol"]
    variants = {k: v["frictionless"] for k, v in R["portfolios"].items()}
    ranked = sorted(variants.items(), key=lambda kv: kv[1]["xirr_pct"], reverse=True)

    data_quality_panel = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL_TIGHT} border-[#F2B03C]/40">
        <div class="flex items-center gap-2 mb-2">
          <h3 class="text-base font-bold text-[#E6EDF0]">Data-quality fix applied before running this backtest</h3>
          {pill('verified against raw Yahoo Finance data', 'assumption')}
        </div>
        <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — a real data artifact that would have shown a fake 90% crash if left in, and how it was corrected.</p>
        <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">{esc(R['momentum_data_note'])}</p>
      </div>
    </div>
    """

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">SIP in a Momentum ETF — vs. Midcap, vs. NIFTY 50</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Same ₹1,000/month vanilla SIP, no overlay of any kind, run into a momentum-factor ETF instead — compared head-to-head against midcap and NIFTY 50 over the identical, shorter window the momentum ETF's short history allows.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          Data: Yahoo Finance daily OHLC via yfinance — {esc(R['momentum_ticker'])}, {esc(R['midcap_ticker'])}, {esc(R['nifty_ticker'])}<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    definitions_strip = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL_TIGHT}">
        <p class="{WHAT_THIS_SHOWS} mb-2">WHAT THIS SHOWS — why the window here is much shorter than every other report in this series.</p>
        <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
          "Momentum ETF" was resolved (confirmed in chat) to the {pill('HDFC Nifty200 Momentum 30 ETF', 'assumption')} — the longest-history momentum-factor
          ETF available on Yahoo Finance for India, but that's still only since {esc(R['start_date'])}. To keep this a fair, apples-to-apples comparison, midcap
          and NIFTY 50 are ALSO restricted to that same {esc(R['start_date'])}–{esc(R['end_date'])} window here — not their full available history used in
          earlier reports, so don't compare this report's midcap/NIFTY numbers directly against reports 5-9.
        </p>
      </div>
    </div>
    """

    kpis = []
    for key in ["momentum", "midcap", "nifty"]:
        v = variants[key]
        is_winner = key == ranked[0][0]
        kpis.append(kpi_card(
            f"{LABELS[key]}{' — highest XIRR' if is_winner else ''}",
            f"Final value {money(v['final_value'], sym)} on {money(v['total_invested'], sym)} invested ({v['num_contributions']} months).",
            [("XIRR", pct(v['xirr_pct'], 2), win_loss_kind(v['xirr_pct'])),
             ("Max drawdown", pct(v['max_drawdown_pct'], 1, signed=False), "negative"),
             ("Net gain %", pct(v['net_gain_pct'], 1), win_loss_kind(v['net_gain_pct'])),
             ("Longest underwater", f"{v['longest_underwater_days']}d", "neutral")],
        ))
    kpi_grid = f'<div class="grid grid-cols-1 gap-4 mt-6">{"".join(kpis)}</div>'

    rank_rows = "".join(f"""
    <tr{' class="rank-1"' if i == 0 else ''}>
      <td>{i+1}</td><td>{esc(LABELS[k])}</td><td>{money(v['final_value'], sym)}</td>
      <td>{pct(v['xirr_pct'], 2)}</td><td>{pct(v['net_gain_pct'], 2)}</td><td>{pct(v['max_drawdown_pct'], 1, signed=False)}</td>
    </tr>""" for i, (k, v) in enumerate(ranked))
    rank_table = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Ranked by XIRR — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — over this specific ~2.8-year window, midcap comes out clearly ahead; the momentum ETF actually lagged NIFTY 50, let alone midcap.</p>
      <table class="data-table">
        <thead><tr><th>Rank</th><th>SIP target</th><th>Final value</th><th>XIRR</th><th>Net gain %</th><th>Max drawdown</th></tr></thead>
        <tbody>{rank_rows}</tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": LABELS[k], "color": COLORS[k], "points": weekly_resample(variants[k]["value_curve"]), "dash": k == "nifty"}
        for k in ["momentum", "midcap", "nifty"]
    ]
    eq_svg, eq_legend = line_chart(eq_series, y_prefix=sym, height=460, value_fmt=lambda v: f"{v:,.0f}",
                                    chart_id="eq_mom", smooth=True)
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Portfolio value over time — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
        {pill('smoothed curve through real weekly values', 'assumption')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the momentum ETF (amber) fell hard in 2024-2025 and, as of the last data point, still hasn't pulled meaningfully ahead of the money simply put in.</p>
      <div class="flex items-center mb-2">{eq_legend}</div>
      {eq_svg}
      <div class="{MUTED} mt-2">Curve is drawn through one real data point per calendar week connected with a smooth curve — every plotted value is a genuine historical value (post data-quality fix, above). KPI figures use the full daily series.</div>
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
        {"name": LABELS[k], "color": COLORS[k], "points": weekly_resample(dd_points(variants[k]["value_curve"], variants[k]["invested_curve"])), "dash": k == "nifty"}
        for k in ["momentum", "midcap", "nifty"]
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=260, chart_id="dd_mom", smooth=True)
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison (value ÷ invested, not raw value)</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the momentum ETF's SIP fell much further below its own money-in line than either midcap's or NIFTY's did over the same stretch — "momentum" factor investing is not inherently lower-risk.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    momentum, midcap = variants["momentum"], variants["midcap"]
    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">"Momentum" is a factor label, not a guarantee</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — why this result should not be read as "momentum investing doesn't work."</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        On this data, SIP-ing into the momentum ETF returned {pct(momentum['xirr_pct'], 2)} XIRR with a {pct(momentum['max_drawdown_pct'],1,signed=False)} drawdown —
        worse on both counts than midcap ({pct(midcap['xirr_pct'], 2)} XIRR, {pct(midcap['max_drawdown_pct'],1,signed=False)} drawdown) over the identical
        {esc(R['start_date'])}–{esc(R['end_date'])} window. Momentum strategies are known to go through exactly this kind of stretch — they chase recent
        winners, and when market leadership rotates hard (which India's did in 2024-2025), a momentum-tilted basket can underperform broader/other factor
        exposures for a while by design, not by flaw.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        This is also, by far, the shortest and youngest dataset in this whole report series — under 3 years, covering essentially one down-cycle for the
        momentum factor and no real up-cycle yet. It says very little about momentum investing generally, and a lot about one specific, unlucky-so-far
        entry window for this specific fund.
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
        <li class="mb-1.5">The momentum ETF's usable history is under 3 years — by far the shortest, least conclusive dataset in this series. A single down-cycle for one factor is not a verdict on that factor.</li>
        <li class="mb-1.5">The first-3-listing-day price artifact described above was identified and removed by hand for this specific ticker; it's a reasonable, disclosed judgment call, not an official data correction from Yahoo/NSE.</li>
        <li class="mb-1.5">Midcap and NIFTY are shown over the SAME shortened window as the momentum ETF for a fair comparison — their numbers here do NOT match reports 5-9, which use midcap/NIFTY's full available history.</li>
        <li class="mb-1.5">Only one momentum ETF (HDFC's) was tested; the ICICI and Motilal Oswal versions (shorter history each) could show different results even over their own overlapping windows, due to tracking differences and fund-level costs.</li>
        <li class="mb-1.5">The cost-loaded variant models only a flat 0.05% commission and a fixed one-tick slippage per contribution — no bid-ask spread widening (likely more material here, given this ETF's much lower daily volume than the midcap ETF), no market impact, no India-specific transaction taxes.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modelled.</li>
        <li class="mb-1.5">Drawdown and longest-underwater are computed on (value ÷ invested), not raw ₹ — the same methodology as every SIP report in this series.</li>
      </ul>
    </div>
    """

    body = f"""
    {header}
    {definitions_strip}
    {data_quality_panel}
    <div class="px-10 py-6">
      {kpi_grid}
      {rank_table}
      {eq_panel}
      {dd_panel}
      {honesty_note}
      <div class="mt-6">{limitations}</div>
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>SIP in Momentum ETF — vs Midcap, vs NIFTY</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("10_momentum_sip.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 10_momentum_sip.html")

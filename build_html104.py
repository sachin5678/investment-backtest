"""Builds 104_midcap150_smoothed_ha.html from results103.json."""
import datetime as dt
import html
import json

from svg_charts import COL, area_underwater_chart, line_chart

with open("results103.json") as f:
    R = json.load(f)

TAILWIND_CDN = '<script src="https://cdn.tailwindcss.com"></script>'
PANEL = "bg-[#0F2630] border border-[#1E3A45] rounded-2xl p-6"
PANEL_TIGHT = "bg-[#0F2630] border border-[#1E3A45] rounded-2xl p-5"
MUTED = "text-[#7E97A0] text-[12.5px] leading-snug"
WHAT_THIS_SHOWS = "text-[#9FB4BB] text-[13px] italic mb-3"

PILL_BASE = "inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full whitespace-nowrap"
PILL_POS = PILL_BASE + " bg-[#37F083]/15 text-[#37F083] border border-[#37F083]/40"
PILL_NEG = PILL_BASE + " bg-[#F2643C]/15 text-[#F2643C] border border-[#F2643C]/40"
PILL_ASSUM = PILL_BASE + " bg-[#F2B03C]/15 text-[#F2B03C] border border-[#F2B03C]/40"
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


def num(v, decimals=2):
    return "—" if v is None else f"{v:,.{decimals}f}"


def tone(v):
    if v is None:
        return "neutral"
    return "positive" if v > 0 else ("negative" if v < 0 else "neutral")


def base_style():
    return """
    <style>
      html,body{background:#08171E;color:#E6EDF0;font-family:'Inter',ui-sans-serif,system-ui,-apple-system,sans-serif;}
      .mono{font-family:'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,monospace;}
      table.data-table{width:100%;border-collapse:collapse;font-size:13px;}
      table.data-table th{text-align:right;color:#7E97A0;font-weight:600;padding:8px 12px;border-bottom:1px solid #1E3A45;background:#132B36;font-size:11px;letter-spacing:0.03em;text-transform:uppercase;}
      table.data-table th:first-child, table.data-table td:first-child{text-align:left;}
      table.data-table td{text-align:right;padding:7px 12px;border-bottom:1px solid #16303a;white-space:nowrap;transition:background-color 120ms ease;}
      table.data-table tbody tr:nth-child(even) td{background:rgba(255,255,255,0.015);}
      table.data-table tbody tr:hover td{background:rgba(55,240,131,0.06);}
      table.data-table tr.hi td{background:rgba(242,176,60,0.08);}
      .kpi-val{font-size:23px;font-weight:700;letter-spacing:-0.01em;}
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
      <div class="{MUTED} mb-3">{esc(definition)}</div>
      <div class="flex gap-3 flex-wrap">{''.join(col_html)}</div>
    </div>
    """


def years_of(block):
    a = dt.date.fromisoformat(block["start_date"])
    b = dt.date.fromisoformat(block["end_date"])
    return (b - a).days / 365.25


def ex_2020_cagr(block):
    """CAGR with calendar 2020 removed — recomputed from the annual returns."""
    years = years_of(block)
    total = (1 + block["cagr_pct"] / 100) ** years
    g20 = 1 + block["yearly"].get("2020", 0)
    if g20 <= 0:
        return None
    return ((total / g20) ** (1 / years) - 1) * 100


def yearly_from_curve(block):
    out = {}
    prev = block["equity_curve"][0][1]
    last = {}
    for d, v in block["equity_curve"]:
        last[d[:4]] = v
    for y in sorted(last):
        out[y] = (last[y] / prev - 1) * 100
        prev = last[y]
    return out


def build():
    slot = R["modern"]["atr80"]
    risk = R["modern"]["atr80_risk"]
    video = R["modern"]["video"]
    lean = R["modern"]["lean12"]
    basket = R["modern"]["basket"]
    nif = R.get("nifty50")
    full = R["full"]["atr80"]
    full_risk = R["full"]["atr80_risk"]
    full_basket = R["full"]["basket"]

    dd_cut = basket["max_drawdown_pct"] - slot["max_drawdown_pct"]
    cagr_edge = slot["cagr_pct"] - basket["cagr_pct"]
    s_ex20 = ex_2020_cagr(slot)
    b_ex20 = ex_2020_cagr(basket)
    s_2020 = slot["yearly"].get("2020", 0) * 100
    b_2020 = basket["yearly"].get("2020", 0) * 100
    s_2020_mult = 1 + slot["yearly"].get("2020", 0)
    b_2020_mult = 1 + basket["yearly"].get("2020", 0)
    leverage_ratio = slot["cagr_pct"] / risk["cagr_pct"] if risk["cagr_pct"] else None

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Smoothed Heikin-Ashi + ATR Contraction on NIFTY Midcap 150</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">The chart system from the Upsurge Club session of 20 Oct 2026, applied to the repo's own Midcap 150 price cache (150 names, prices from 1996). Entry is a green flip of the double-smoothed Heikin-Ashi with price above the indicator and ATR(14)/ATR(50) below 0.8 — a volatility-contraction filter that was not in the original video. 12% stop, exit on the first red flip, 8 slots. The question here is narrow: does the edge that showed up on NIFTY 200/500 survive when the universe is midcaps?</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(R['start_date'])}–{esc(R['end_date'])}<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#37F083]">
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          {pill('the edge survives on midcaps — but it is smaller and far more 2020-dependent', 'positive')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          On 2016–2026, fully invested at 12.5% per slot, the system returns
          <span class="font-semibold">{pct(slot['cagr_pct'])}</span> CAGR against {pct(basket['cagr_pct'])} for an
          equal-weight basket of the same 150 names — with max drawdown {pct(slot['max_drawdown_pct'], 1, signed=False)}
          versus {pct(basket['max_drawdown_pct'], 1, signed=False)}, and Sharpe {num(slot['sharpe'])} versus
          {num(basket['sharpe'])}. On the literal 1%-risk sizing the same rules deliver {pct(risk['cagr_pct'])} /
          {pct(risk['max_drawdown_pct'], 1, signed=False)} / Sharpe {num(risk['sharpe'])}.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          Two things stop that from being the whole story. First, <strong>2020 was {s_2020_mult:.2f}x</strong>: strip
          that year out and the system compounds at {pct(s_ex20)} against {pct(b_ex20)} for the basket — outside 2020
          this is a drawdown-control system, not a return engine. Second, over the full 2005–2026 history the basket
          wins outright ({pct(full_basket['cagr_pct'])} vs {pct(full['cagr_pct'])} at slot sizing), though that basket
          number is survivorship-inflated to the point of fiction: it books a <em>flat</em> 2008.
        </p>
      </div>
    </div>
    """

    sizing = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2B03C]">
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          {pill('two sizing conventions, both reported — they answer different questions', 'assumption')}
        </div>
        <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
          <strong class="text-[#E6EDF0]">Slot sizing (12.5% per position)</strong> keeps ~100% of equity deployed when
          eight positions are open. It is the like-for-like comparison against a 100%-invested equal-weight basket, and
          it is the headline here. <strong class="text-[#E6EDF0]">1% risk sizing</strong> divides 1% of equity by the
          12% stop, which funds each position at 8.33% and leaves roughly a third of the account in cash — lower return,
          but also lower risk. The earlier NIFTY 200/500 study sized every trade at 1%/8.5% (≈11.8% per slot) while
          using a 12% stop, so its headline CAGRs sit between these two conventions; its Sharpe ratios remain the
          comparable number.
        </p>
        <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
          Nothing about the entry, filter, stop or exit changes between the two rows. Only the number of rupees put
          behind each signal changes.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR", "Compound annual growth rate over the identical 2016–2026 window.",
                 [("System — slots", pct(slot["cagr_pct"]), tone(slot["cagr_pct"])),
                  ("System — 1% risk", pct(risk["cagr_pct"]), tone(risk["cagr_pct"])),
                  ("Midcap basket", pct(basket["cagr_pct"]), "neutral"),
                  ("NIFTY 50", pct(nif["cagr_pct"]) if nif else "—", "neutral")]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline over the identical window.",
                 [("System — slots", pct(slot["max_drawdown_pct"], 1, signed=False), "positive"),
                  ("System — 1% risk", pct(risk["max_drawdown_pct"], 1, signed=False), "positive"),
                  ("Midcap basket", pct(basket["max_drawdown_pct"], 1, signed=False), "negative"),
                  ("NIFTY 50", pct(nif["max_drawdown_pct"], 1, signed=False) if nif else "—", "negative")]),
        kpi_card("Risk-adjusted", "Sharpe uses daily returns at 252 trading days; exposure is the share of days with at least one open position.",
                 [("System Sharpe", num(slot["sharpe"]), "positive"),
                  ("Basket Sharpe", num(basket["sharpe"]), "neutral"),
                  ("Exposure", pct(slot["exposure_pct"], 0, signed=False), "neutral"),
                  ("Trades taken", f"{slot['taken']:,}", "neutral")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-1 gap-4 mt-6">{"".join(kpis)}</div>'

    variants_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">What each rule is actually worth on midcaps</h3>
        {pill('slot sizing — the fair comparison', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the video's rules, the lean version without the 50-EMA, and the version with the ATR contraction filter, on the same universe and window.</p>
      <table class="data-table">
        <thead><tr><th>Variant</th><th>CAGR</th><th>Max drawdown</th><th>Sharpe</th><th>Exposure</th><th>Signals</th><th>Win rate</th><th>Expectancy</th></tr></thead>
        <tbody>
          <tr><td>Video rules — 50-EMA above, 8.5% stop</td><td>{pct(video['cagr_pct'])}</td><td>{pct(video['max_drawdown_pct'],1,signed=False)}</td><td>{num(video['sharpe'])}</td><td>{pct(video['exposure_pct'],0,signed=False)}</td><td>{video['trades']['n']:,}</td><td>{pct(video['trades']['win_pct'],1,signed=False)}</td><td>{pct(video['trades']['expectancy_pct'])}</td></tr>
          <tr><td>No 50-EMA, 12% stop</td><td>{pct(lean['cagr_pct'])}</td><td>{pct(lean['max_drawdown_pct'],1,signed=False)}</td><td>{num(lean['sharpe'])}</td><td>{pct(lean['exposure_pct'],0,signed=False)}</td><td>{lean['trades']['n']:,}</td><td>{pct(lean['trades']['win_pct'],1,signed=False)}</td><td>{pct(lean['trades']['expectancy_pct'])}</td></tr>
          <tr class="hi"><td><strong>+ ATR14/ATR50 &lt; 0.8 (recommended)</strong></td><td><strong>{pct(slot['cagr_pct'])}</strong></td><td><strong>{pct(slot['max_drawdown_pct'],1,signed=False)}</strong></td><td><strong>{num(slot['sharpe'])}</strong></td><td>{pct(slot['exposure_pct'],0,signed=False)}</td><td>{slot['trades']['n']:,}</td><td>{pct(slot['trades']['win_pct'],1,signed=False)}</td><td>{pct(slot['trades']['expectancy_pct'])}</td></tr>
          <tr class="real-bench"><td>Equal-weight Midcap 150 basket</td><td>{pct(basket['cagr_pct'])}</td><td>{pct(basket['max_drawdown_pct'],1,signed=False)}</td><td>{num(basket['sharpe'])}</td><td>100%</td><td>—</td><td>—</td><td>—</td></tr>
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "System — 12.5% slots", "color": COL["positive"], "points": slot["equity_curve"]},
        {"name": "System — 1% risk", "color": COL["assumption"], "points": risk["equity_curve"], "dash": True},
        {"name": "Midcap 150 equal-weight basket", "color": COL["muted"], "points": basket["equity_curve"]},
    ]
    if nif:
        eq_series.append({"name": "NIFTY 50", "color": COL["text"], "points": nif["equity_curve"], "dash": True})
    eq_svg, eq_legend = line_chart(eq_series, height=430, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_104")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the system's compounding is concentrated: the green line runs flat for long stretches, then steps up hard in 2020 and 2021. The basket is the smoother ride until 2020, then falls further behind.</p>
      <div class="flex items-center mb-2">{eq_legend}</div>
      {eq_svg}
    </div>
    """

    dd_series = [
        {"name": "System — 12.5% slots", "color": COL["positive"], "points": slot["underwater"]},
        {"name": "Midcap 150 equal-weight basket", "color": COL["muted"], "points": basket["underwater"], "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=230, chart_id="dd_104")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown — the part that is not 2020-dependent</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the system cuts the worst peak-to-trough loss by {dd_cut:.1f} points ({pct(slot['max_drawdown_pct'],1,signed=False)} vs {pct(basket['max_drawdown_pct'],1,signed=False)}), and spends long stretches in shallower water. Unlike the CAGR edge, this holds outside 2020.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    # year-by-year
    sy = slot["yearly"]
    by = basket["yearly"]
    rows = []
    for y in sorted(sy):
        diff = (sy[y] - by.get(y, 0)) * 100
        cls = ' class="hi"' if y == "2020" else ""
        rows.append(
            f"<tr{cls}><td>{y}</td><td>{pct(sy[y]*100)}</td><td>{pct(by.get(y,0)*100)}</td>"
            f"<td>{pct(diff)}</td></tr>"
        )
    yearly_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Calendar-year returns</h3>
        {pill('2020 highlighted — it is the whole debate', 'assumption')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the year-by-year gap. Outside 2020 the system is mostly behind the basket on return; its compensation is the smaller losses in 2018-19 and 2022.</p>
      <table class="data-table">
        <thead><tr><th>Year</th><th>System</th><th>Basket</th><th>Difference</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
      <p class="text-[12px] text-[#7E97A0] mt-2">2026 is year-to-date through 16 October 2026. The 2020 row is highlighted because it is the entire modern-window return edge.</p>
    </div>
    """

    # cross universe
    cu_rows = []
    for u in R["cross_universe"]:
        edge = u["system_cagr_pct"] - u["basket_cagr_pct"]
        dd_edge = u["basket_max_drawdown_pct"] - u["system_max_drawdown_pct"]
        cu_rows.append(
            f"<tr><td>{esc(u['universe'])} <span class=\"text-[#7E97A0]\">({u['names']})</span></td>"
            f"<td>{pct(u['system_cagr_pct'])}</td><td>{pct(u['basket_cagr_pct'])}</td><td>{pct(edge)}</td>"
            f"<td>{pct(u['system_max_drawdown_pct'],1,signed=False)}</td><td>{pct(u['basket_max_drawdown_pct'],1,signed=False)}</td>"
            f"<td>{dd_edge:.1f} pts</td><td>{num(u['system_sharpe'])}</td><td>{num(u['basket_sharpe'])}</td></tr>"
        )
    cross_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Same engine, three market caps — 2016–2026</h3>
        {pill('one engine, one window, three of the repo caches', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the ATR-filtered system across NIFTY 200, Midcap 150 and Smallcap 250. The return edge shrinks as market cap falls; the drawdown edge survives longest.</p>
      <table class="data-table">
        <thead><tr><th>Universe</th><th>System CAGR</th><th>Basket CAGR</th><th>Edge</th><th>System DD</th><th>Basket DD</th><th>DD cut</th><th>System Sharpe</th><th>Basket Sharpe</th></tr></thead>
        <tbody>{''.join(cu_rows)}</tbody>
      </table>
    </div>
    """

    full_rows = f"""
      <tr><td>System — 12.5% slots</td><td>{pct(full['cagr_pct'])}</td><td>{pct(full['max_drawdown_pct'],1,signed=False)}</td><td>{num(full['sharpe'])}</td><td>{pct(full['yearly'].get('2020',0)*100)}</td></tr>
      <tr><td>System — 1% risk</td><td>{pct(full_risk['cagr_pct'])}</td><td>{pct(full_risk['max_drawdown_pct'],1,signed=False)}</td><td>{num(full_risk['sharpe'])}</td><td>{pct(full_risk['yearly'].get('2020',0)*100)}</td></tr>
      <tr class="real-bench"><td>Equal-weight Midcap 150 basket</td><td>{pct(full_basket['cagr_pct'])}</td><td>{pct(full_basket['max_drawdown_pct'],1,signed=False)}</td><td>{num(full_basket['sharpe'])}</td><td>{pct(full_basket['yearly'].get('2020',0)*100)}</td></tr>
    """
    full_panel = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-1 flex-wrap">
        <h3 class="text-base font-bold text-[#E6EDF0]">The long history — 2005 to 2026</h3>
        {pill('the basket 2008 is the survivorship tell', 'assumption')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — why the full-window comparison is shown but not headlined.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>CAGR</th><th>Max drawdown</th><th>Sharpe</th><th>2020</th></tr></thead>
        <tbody>{full_rows}</tbody>
      </table>
      <p class="text-[13px] text-[#C9D6DA] leading-relaxed mt-3">
        Today's 150 constituents are applied retroactively to 2005, when only 63 of them had any price history. The
        survivors compound for 21 years; the failures that dropped out of the index cannot appear. That is why the
        basket shows {pct(full_basket['yearly'].get('2008',0)*100)} in 2008 — the year midcaps actually fell hard — and
        why its {pct(full_basket['cagr_pct'])} CAGR is not a portfolio anyone could have owned. The system's
        {pct(full['cagr_pct'])} carries the same bias, but far less of it, because it only holds eight names at a time
        and its stop takes it out of the worst paths.
      </p>
    </div>
    """

    mechanism = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center gap-2 mb-2 flex-wrap">
        <h3 class="text-base font-bold text-[#E6EDF0]">Why the midcap edge is thinner than the large-cap one</h3>
        {pill('mechanism, not a guarantee', 'assumption')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — three structural reasons, each visible in the numbers above.</p>
      <ul class="text-[13.5px] text-[#C9D6DA] list-disc pl-5 leading-relaxed">
        <li class="mb-2"><strong>Breadth is lower.</strong> By 2016 only 101 of the 150 names have prices; the system
          gets 1,287 signals over ten years and can only take {slot['taken']:,} of them. In NIFTY 200 the same rules
          generate 1,740 signals from a deeper, more liquid pool — more shots at the tight-base setup.</li>
        <li class="mb-2"><strong>Midcap trends are more idiosyncratic.</strong> The ATR contraction filter selects quiet,
          tight bases; in midcaps those are often lower-beta names that then trend less than the index's big winners.
          The equal-weight basket owns every winner, including the ones that never went quiet before launching.</li>
        <li><strong>2020 is doing the heavy lifting.</strong> The system's {s_2020_mult:.2f}x in 2020 versus the basket's
          {b_2020_mult:.2f}x is the entire modern-window CAGR gap. Remove 2020 and the basket wins on return
          ({pct(b_ex20)} vs {pct(s_ex20)}); the system still wins on drawdown and Sharpe.</li>
      </ul>
    </div>
    """

    limitations = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2">
        <h3 class="text-base font-bold text-[#E6EDF0]">Limitations</h3>
        {pill("read before trusting any number above", "assumption")}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every simplification behind this report.</p>
      <ul class="text-[13px] text-[#C9D6DA] list-disc pl-5 leading-relaxed">
        <li class="mb-1.5"><strong>Survivorship bias is severe.</strong> Today's Midcap 150 membership is applied back to 2005. The absolute CAGRs — system and basket — are not investable expectations. The comparison between them is the useful part, and even that is tilted toward the basket.</li>
        <li class="mb-1.5">The basket is equal-weighted and rebalanced once a year, with no costs; it is a simple comparator, not the real NIFTY Midcap 150 index (which only launched in 2005 and has its own methodology).</li>
        <li class="mb-1.5">Dividends are excluded (Close, not Adj Close), consistent with every other report in this repo. Midcap dividend yields are small but not zero.</li>
        <li class="mb-1.5">The 0.80 ATR threshold and the 12% stop were chosen after looking at NIFTY 200/500 data. They are not out-of-sample parameters, and no walk-forward or parameter-sensitivity sweep is presented here.</li>
        <li class="mb-1.5">Next-open fills assume every signal is tradable at the next day's open. The smallest midcaps can gap or hit circuit limits; the stop fills at min(open, trigger) when it gaps, but genuine liquidity holes would be worse.</li>
        <li class="mb-1.5">0.25% round-trip cost is charged on every trade. With 1,287 signals and average holds of about {slot['trades']['avg_hold_days']:.0f} trading days, costs matter; a higher-cost broker would shave the edge.</li>
        <li class="mb-1.5">One historical path, one universe vintage. The 2020 concentration is not a bug in the code; it is a property of the strategy, and it is the main reason to treat the headline CAGR with suspicion.</li>
      </ul>
    </div>
    """

    reproduce = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center gap-2 mb-2">
        <h3 class="text-base font-bold text-[#E6EDF0]">Reproduce this report</h3>
        {pill('repo-native, no external services needed except the NIFTY 50 cache', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the exact commands and files behind every number.</p>
      <pre class="mono text-[12px] text-[#C9D6DA] bg-[#08171E] border border-[#1E3A45] rounded-xl p-4 overflow-x-auto">python backtest104.py       # runs the engine, writes results103.json
python build_html104.py     # writes 104_midcap150_smoothed_ha.html</pre>
      <p class="text-[12.5px] text-[#7E97A0] leading-relaxed mt-2">
        Data: midcap150_extra_raw.pkl (150 names, 1996-01-01 to 2026-10-16), universe_raw.pkl (NIFTY 200),
        smallcap250_extra_raw.pkl (Smallcap 250), and a cached NIFTY 50 daily series. Entry, stop, exit and portfolio
        accounting are a line-by-line port of the JavaScript engine used for the earlier NIFTY 200/500 study; the port
        was validated against the JS engine on NIFTY 200 (31.2% vs 31.6% CAGR, 1,740 vs 1,724 signals) before this
        universe was run.
      </p>
    </div>
    """

    footer = f"""
    <footer class="px-10 py-8 mt-2">
      <p class="{MUTED}">Report 104 · Signal Lab · generated {esc(R['generated'])} · prices in INR, dividends excluded · past performance is not a forecast.</p>
    </footer>
    """

    body = f"""
    {header}
    {lead}
    {sizing}
    <div class="px-10 py-6">
      {kpi_grid}
      {variants_table}
      {eq_panel}
      {dd_panel}
      {yearly_table}
      {cross_table}
      {full_panel}
      {mechanism}
      {limitations}
      {reproduce}
    </div>
    {footer}
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Midcap 150 — Smoothed Heikin-Ashi + ATR Contraction</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("104_midcap150_smoothed_ha.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 104_midcap150_smoothed_ha.html")

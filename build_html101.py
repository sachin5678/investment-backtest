"""Builds 101_propicks_india_cleanroom.html from results100.json."""
import json

from svg_charts import line_chart, area_underwater_chart, COL

with open("results100.json", encoding="utf-8") as f:
    R = json.load(f)

CYAN = "#6AE4FF"
DASH = "\u2014"

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
KIND_COLOR = {"positive": "#37F083", "negative": "#F2643C",
              "neutral": "#E6EDF0", "assumption": "#F2B03C"}

VAR_COLOR = {"mom_only": COL["assumption"], "pro_4": COL["positive"],
             "pro_4_gate": CYAN}
VAR_ORDER = ("mom_only", "pro_4", "pro_4_gate")

sc, mc = R["smallcap"], R["midcap"]


def pill(text, kind="assumption"):
    cls = {"positive": PILL_POS, "negative": PILL_NEG,
           "assumption": PILL_ASSUM, "neutral": PILL_NEUTRAL}[kind]
    dot = {"positive": "\u25cf", "negative": "\u25cf",
           "assumption": "\u25b2", "neutral": "\u25cf"}[kind]
    return f'<span class="{cls}">{dot} {text}</span>'


def esc(s):
    import html
    return html.escape(str(s))


def pct(v, decimals=1, signed=True):
    if v is None:
        return "\u2014"
    s = "+" if (signed and v > 0) else ""
    return f"{s}{v:,.{decimals}f}%"


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
      .pos{color:#37F083;} .neg{color:#F2643C;} .amb{color:#F2B03C;} .mut{color:#7E97A0;} .cy{color:#6AE4FF;}
    </style>
    """


def kpi_card(label, definition, cols):
    col_html = []
    for col_label, value_str, kind in cols:
        color = KIND_COLOR[kind]
        col_html.append(
            f'<div class="flex-1 min-w-[110px]">'
            f'<div class="text-[11px] text-[#7E97A0] mb-1 uppercase tracking-wide">{esc(col_label)}</div>'
            f'<div class="kpi-val mono" style="color:{color}">{value_str}</div></div>'
        )
    return f"""
    <div class="{PANEL_TIGHT}">
      <div class="text-[13px] font-semibold text-[#E6EDF0] mb-1">{esc(label)}</div>
      <div class="{MUTED} mb-3">{definition}</div>
      <div class="flex gap-3 flex-wrap">{''.join(col_html)}</div>
    </div>
    """


def var_label(k):
    return R["variant_labels"][k]


def series_row(name, v, cls=""):
    c = f' class="{cls}"' if cls else ""
    return (f"""<tr{c}><td>{esc(name)}</td><td>{pct(v['net_return_pct'])}</td>
    <td>{pct(v['cagr_pct'])}</td><td>{pct(v['max_drawdown_pct'],1,signed=False)}</td>
    <td>{v['longest_underwater_days']:,}d</td></tr>""")


def universe_table(uni):
    rows = []
    for k in VAR_ORDER:
        v = uni["variants"].get(k)
        if v and v.get("cost_loaded"):
            rows.append(series_row(var_label(k) + " (cost-loaded)",
                                   v["cost_loaded"]))
        if v and v.get("frictionless"):
            rows.append(series_row("&nbsp;&nbsp;\u21b3 " + var_label(k)
                                   + " (no costs)", v["frictionless"]))
    b = uni.get("benchmark") or {}
    if b:
        rows.append(series_row(uni["benchmark_name"], b, "real-bench"))
    rot_pill = pill(
        f"{uni['num_rebalances']} monthly rebalances \u00b7 "
        f"~{uni['avg_names_rotated_per_month']:.1f} names rotated/month",
        "neutral")
    window_txt = (f"{esc(uni['common_start'])} \u2192 "
                  f"{esc(uni['common_end'])}")
    return f"""
    <div class="{PANEL}">
      <div class="flex items-center justify-between mb-1 flex-wrap gap-2">
        <h3 class="text-base font-bold text-[#E6EDF0]">{esc(uni['label'])} — all series, identical window</h3>
        {rot_pill}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every variant over the identical {window_txt} window, so the ranking is fair. The indented rows drop transaction costs; the cost-loaded rows above them are the honest headline, and they are the ones to read.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
    """


def universe_charts(uni, chart_suffix):
    b = uni.get("benchmark") or {}

    def dd_points(equity):
        out, peak = [], None
        for d, v in equity:
            peak = v if peak is None else max(peak, v)
            out.append([d, (v / peak - 1.0) * 100.0])
        return out

    eq_series, dd_series = [], []
    if b.get("equity_curve"):
        eq_series.append({"name": uni["benchmark_name"], "color": COL["muted"],
                          "points": b["equity_curve"]})
        dd_series.append({"name": uni["benchmark_name"], "color": COL["muted"],
                          "points": dd_points(b["equity_curve"])})
    for k in VAR_ORDER:
        v = uni["variants"].get(k)
        if not (v and v.get("cost_loaded", {}).get("equity_curve")):
            continue
        c = v["cost_loaded"]["equity_curve"]
        eq_series.append({"name": var_label(k), "color": VAR_COLOR[k],
                          "points": c})
        dd_series.append({"name": var_label(k), "color": VAR_COLOR[k],
                          "points": dd_points(c)})

    eq_svg, eq_legend = line_chart(eq_series, height=400,
                                   value_fmt=lambda v: f"{v:,.0f}",
                                   chart_id=f"eq_{chart_suffix}")
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=230,
                                              chart_id=f"dd_{chart_suffix}")
    return f"""
    <div class="{PANEL}">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(uni['label'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — cost-loaded variants only. Grey is the real index, never a reconstruction.</p>
      <div class="flex items-center mb-2">{eq_legend}</div>
      {eq_svg}
      <h3 class="text-base font-bold text-[#E6EDF0] mt-6 mb-1">Drawdown — {esc(uni['label'])}</h3>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """


def robustness_table():
    rows = []
    for uname, uni in (("NIFTY Smallcap 250", sc), ("NIFTY Midcap 150", mc)):
        if not uni:
            continue
        for tag, sw in uni.get("sub_windows", {}).items():
            b = sw.get("benchmark") or {}
            cells = []
            for k in VAR_ORDER:
                m = sw["variants"].get(k)
                cells.append(f"<td>{pct(m['cagr_pct']) if m else DASH}</td>")
            rows.append(
                f"""<tr><td>{esc(uname)}</td><td>{esc(tag.replace('_',' ').title())}</td>
                <td class="mono">{esc(sw['start'])} \u2192 {esc(sw['end'])}</td>
                <td>{pct(b.get('cagr_pct'))}</td>{''.join(cells)}</tr>""")
    return f"""
    <div class="{PANEL} border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-1 flex-wrap">
        <h3 class="text-base font-bold text-[#E6EDF0]">Robustness — split the window in half</h3>
        {pill('the headline does not survive this cleanly', 'negative')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — 40 rebalances over 3.3 years is a thin sample, and this particular window was kind to Indian small/mid-caps overall. Cutting it in half shows where the edge actually came from. Cost-loaded CAGR throughout.</p>
      <table class="data-table">
        <thead><tr><th>Universe</th><th>Half</th><th>Window</th><th>Benchmark</th>
        <th>Momentum only</th><th>Four-pillar</th><th>+ cheapness gate</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mt-4">
        Read the second half carefully. On smallcaps the four-pillar composite's lead over its index collapses from
        <span class="mono">+{sc['sub_windows']['first_half']['variants']['pro_4']['cagr_pct'] - sc['sub_windows']['first_half']['benchmark']['cagr_pct']:.1f}pp</span>
        to <span class="mono">+{sc['sub_windows']['second_half']['variants']['pro_4']['cagr_pct'] - sc['sub_windows']['second_half']['benchmark']['cagr_pct']:.1f}pp</span>,
        and plain momentum actually beats the composite outright in that half. On midcaps the edge holds up much better.
        The honest summary is that the four-pillar structure earned its keep in the first half and has been roughly
        keeping pace since — not that it reliably compounds at 30% a year.
      </p>
    </div>
    """


def method_panel():
    gate_pill = pill("public sources only \u2014 no paywall, no private endpoints",
                     "neutral")
    return f"""
    <div class="{PANEL} border-[#6AE4FF]/40">
      <div class="flex items-center gap-2 mb-1 flex-wrap">
        <h3 class="text-base font-bold text-[#E6EDF0]">What was reconstructed, and how</h3>
        {gate_pill}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the inference chain from their published material to the scoring rules actually tested here. The full write-up is in docs/propicks-india-recon.md.</p>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-[13px] text-[#C9D6DA] leading-relaxed">
        <div>
          <div class="text-[#E6EDF0] font-semibold mb-2">What they publish</div>
          <ul class="list-disc pl-5 space-y-1">
            <li>Rebalance on the <span class="mono">first trading day</span> of each month, at that session's close.</li>
            <li><span class="mono">15\u201320</span> slots, <span class="mono">equal weight</span>, <span class="mono">4\u20138</span> names rotated per month.</li>
            <li>Removal is a <span class="mono">rank push-out</span>, explicitly not a sell signal.</li>
            <li>Every add/remove ships a rationale citing four things: a 3/6/12-month price return, a P/E and P/B with a "fair value" and its % upside, a revenue/EBITDA/profit growth rate, and the balance-sheet state.</li>
            <li>Universe filters first: market-cap band, index membership, liquidity floor, no penny stocks.</li>
          </ul>
        </div>
        <div>
          <div class="text-[#E6EDF0] font-semibold mb-2">What that implies</div>
          <p class="mb-2">The invariant four-bullet structure across every published rationale is the tell. It is a <span class="cy">momentum + value-vs-fair-value + growth + quality</span> composite, ranked monthly, with a fair-value gate.</p>
          <p>The mechanism is specific and worth naming: <span class="font-semibold text-[#E6EDF0]">buy earnings acceleration <em>before</em> the multiple re-rates, and rotate out once it has.</span> That is why a rationale can say "+47% in three months" and "trades at just 11x, PEG 0.19" in the same sentence \u2014 price rose while earnings rose faster, so the multiple compressed. This report tests whether that structure earns anything when rebuilt from scratch.</p>
        </div>
      </div>
    </div>
    """


def basket_panel(universe_label, variant, note):
    sample = variant.get("selections_sample") or []
    if not sample:
        return ""
    last = sample[-1]
    rows = "".join(f"<tr><td class='mono'>{esc(t)}</td></tr>"
                   for t in last["tickers"])
    return f"""
    <div class="{PANEL_TIGHT}">
      <div class="text-[13px] font-semibold text-[#E6EDF0] mb-1">{esc(universe_label)} — basket at the final rebalance</div>
      <div class="{MUTED} mb-3">{esc(note)}</div>
      <table class="data-table">
        <thead><tr><th>Ticker</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
      <div class="{MUTED} mt-3">Rebalance of {esc(last['date'])} \u00b7 {last['num_selected']} names \u00b7 {last['changed_vs_prev'] // 2} rotated in and out.</div>
    </div>
    """


def limitations():
    items = [
        "<span class='font-semibold text-[#F2B03C]'>Survivorship bias is the big one.</span> Today's NIFTY Smallcap 250 / Midcap 150 constituent lists are applied retroactively to every rebalance. Stocks that fell out of the index, delisted, merged or went bankrupt are missing from the entire history. This flatters every variant on this page and it is strongest for smallcaps, whose membership churns most. No result here should be read as a live-tradable track record.",
        "<span class='font-semibold text-[#F2B03C]'>The window is short and was kind.</span> 40 rebalances over 3.3 years, mid-2023 onward — a period in which the benchmark itself compounded at 16.6% (smallcap) and 15.8% (midcap). The half-window table above is the antidote; use it, not the headline.",
        "<span class='font-semibold text-[#F2B03C]'>The fair-value gate is a stand-in, not a replica.</span> Their fair-value engine is proprietary and unrecoverable. An absolute anchor was tried first and fails outright on Indian smallcaps: a Graham number puts the median stock 54\u201382% <em>below</em> fair value, so only 4\u201324% of names would ever clear such a gate. What is used instead is a peer-relative anchor (the universe's median P/E and median P/B applied to each stock's own earnings and book) — no invented macro assumption, but it is a proxy for 'cheaper than the median peer'.",
        "<span class='font-semibold text-[#F2B03C]'>The 90-day reporting lag.</span> A fundamental period is only usable 90 days after its period-end. Indian annual results for a March year-end are due within roughly 60 days, so this is deliberately conservative — it costs staleness rather than risking look-ahead. Without it, every value/growth/quality reading would be look-ahead and the whole result would be a fiction.",
        "<span class='font-semibold text-[#F2B03C]'>Only ~4\u20135 annual periods are available</span> from the data source, so the four-pillar variants cannot start before mid-2023 once the lag and a prior-year growth base are both satisfied. That is the entire reason for the short window.",
        "<span class='font-semibold text-[#F2B03C]'>Full equal-weight re-slice every month.</span> That charges buy and sell costs on ~100% of the book each rebalance. The real strategy rotates only 4\u20138 of 20 names, so these cost-loaded figures are a <span class='font-semibold'>conservative upper bound</span> on cost drag — the frictionless rows show how much. No impact cost, no taxes, no slippage beyond the sourced statutory ladder.",
        "<span class='font-semibold text-[#F2B03C]'>Growth is measured off each company's own fiscal calendar.</span> A stock's 'prior year' is its previous annual period in the data, not a calendar-aligned fiscal year — non-March year-ends are measured on their own clock rather than silently re-aligned.",
        "Unadjusted prices, no dividends modelled, no intraday fills, and signal-at-close / fill-at-close on the rebalance day (matching how the real strategy states it rebalances at the end of the first session).",
    ]
    lis = "".join(f'<li class="mb-1.5">{i}</li>' for i in items)
    return f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2">
        <h3 class="text-base font-bold text-[#E6EDF0]">Limitations — read before trusting any number above</h3>
        {pill('mandatory, not decorative', 'assumption')}
      </div>
      <ul class="text-[13px] text-[#C9D6DA] list-disc pl-5 leading-relaxed">{lis}</ul>
    </div>
    """


def build():
    sc_cagr = sc["variants"]["pro_4"]["cost_loaded"]["cagr_pct"]
    sc_bench = sc["benchmark"]["cagr_pct"]
    mc_cagr = mc["variants"]["pro_4"]["cost_loaded"]["cagr_pct"]
    mc_bench = mc["benchmark"]["cagr_pct"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Clean-room ProPicks India — Rebuilding the Four-Pillar Score From Public Sources</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">A from-scratch reconstruction of the <em>factor structure</em> behind Investing.com's ProPicks India strategies, inferred purely from their public methodology page and the press releases they publish on every monthly rebalance. Nothing was taken from the product — no paywall bypassed, no private endpoint called, no proprietary code or model weights obtained. It is then tested on Indian small-caps and mid-caps to ask the only question that matters: does that structure actually earn anything?</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(sc['common_start'])}\u2013{esc(sc['common_end'])}<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_pill_1 = pill(
        "four-pillar composite beats its index \u2014 but the edge is "
        "front-loaded", "assumption")
    lead_pill_2 = pill(
        f"~{sc['avg_names_rotated_per_month']:.1f} names rotated/month, "
        "matching their stated 4\u20138", "positive")

    lead = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2B03C]">
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          {lead_pill_1}
          {lead_pill_2}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Over {sc['num_rebalances']} monthly rebalances the four-pillar composite returned
          <span class="font-semibold">{pct(sc_cagr)} CAGR</span> on small-caps against
          <span class="font-semibold">{pct(sc_bench)}</span> for the NIFTY Smallcap 250, and
          <span class="font-semibold">{pct(mc_cagr)}</span> on mid-caps against
          <span class="font-semibold">{pct(mc_bench)}</span> for the NIFTY Midcap 150 — after real statutory and
          brokerage charges on a full monthly re-slice of the book. Plain momentum, the control, lands at
          {pct(sc['variants']['mom_only']['cost_loaded']['cagr_pct'])} and {pct(mc['variants']['mom_only']['cost_loaded']['cagr_pct'])}.
          Adding value, growth and quality on top of momentum is worth real money in both universes over the full window.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The caveat is the second half of the window, and it is the part to actually trade on. Cut the period in
          half and small-cap outperformance falls from
          <span class="mono">+{sc['sub_windows']['first_half']['variants']['pro_4']['cagr_pct'] - sc['sub_windows']['first_half']['benchmark']['cagr_pct']:.1f}pp</span>
          of CAGR to <span class="mono">+{sc['sub_windows']['second_half']['variants']['pro_4']['cagr_pct'] - sc['sub_windows']['second_half']['benchmark']['cagr_pct']:.1f}pp</span>,
          where plain momentum beats the composite outright. Mid-caps hold up far better. The structure works; the
          <em>30%-a-year</em> headline does not survive scrutiny, and on top of that every reconstruction here carries
          survivorship bias that flatters all variants equally. See the robustness table and limitations below.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("Small-cap — four-pillar vs its index",
                 "Cost-loaded CAGR over the identical window; the index row is a real index, not a reconstruction.",
                 [("Four-pillar", pct(sc_cagr), "positive"),
                  ("Momentum only", pct(sc['variants']['mom_only']['cost_loaded']['cagr_pct']), "assumption"),
                  ("Index", pct(sc_bench), "neutral")]),
        kpi_card("Mid-cap — four-pillar vs its index",
                 "Same construction on the NIFTY Midcap 150 universe.",
                 [("Four-pillar", pct(mc_cagr), "positive"),
                  ("Momentum only", pct(mc['variants']['mom_only']['cost_loaded']['cagr_pct']), "assumption"),
                  ("Index", pct(mc_bench), "neutral")]),
        kpi_card("Max drawdown — did it earn its risk?",
                 "Largest peak-to-trough decline, cost-loaded. The composite does not protect better than momentum; it earns more.",
                 [("Small-cap four-pillar", pct(sc['variants']['pro_4']['cost_loaded']['max_drawdown_pct'],1,signed=False), "negative"),
                  ("Small-cap index", pct(sc['benchmark']['max_drawdown_pct'],1,signed=False), "negative"),
                  ("Mid-cap four-pillar", pct(mc['variants']['pro_4']['cost_loaded']['max_drawdown_pct'],1,signed=False), "negative"),
                  ("Mid-cap index", pct(mc['benchmark']['max_drawdown_pct'],1,signed=False), "negative")]),
        kpi_card("What the fair-value gate is worth",
                 "Restricting the basket to names cheaper than the median peer. It costs return in both universes — the gate is not the edge.",
                 [("Small-cap, gate vs no gate", pct(sc['variants']['pro_4_gate']['cost_loaded']['cagr_pct'] - sc_cagr, 2), "negative"),
                  ("Mid-cap, gate vs no gate", pct(mc['variants']['pro_4_gate']['cost_loaded']['cagr_pct'] - mc_cagr, 2), "negative")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-1 gap-4 mt-6">{"".join(kpis)}</div>'

    cost_note = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">What trading this actually costs</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — a full equal-weight re-slice every month touches the whole book, which is why the gap between the loaded and frictionless rows is wide. The real strategy only rotates 4\u20138 of its 20 names, so this is deliberately pessimistic.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        Cost drag over the window is
        <span class="mono">{sc['variants']['pro_4']['frictionless']['cagr_pct'] - sc_cagr:.2f}pp</span> of CAGR on small-caps and
        <span class="mono">{mc['variants']['pro_4']['frictionless']['cagr_pct'] - mc_cagr:.2f}pp</span> on mid-caps. Implied rotation is
        <span class="mono">{sc['avg_names_rotated_per_month']:.1f}</span> and
        <span class="mono">{mc['avg_names_rotated_per_month']:.1f}</span> names per month respectively — which lands inside the
        4\u20138 band they state publicly, a small but real confirmation that the reconstructed turnover is in the right neighbourhood.
        Implementing it their way (trade only the 4\u20138 changes, never re-slice the retained names) would recover roughly half the
        cost drag shown here.
      </p>
    </div>
    """

    sc_note = ("What the four-pillar score actually holds. Not a "
               "recommendation \u2014 the output of one month's ranking.")
    mc_note = "Same, on the mid-cap universe."
    sc_basket = basket_panel(sc["label"], sc["variants"]["pro_4"], sc_note)
    mc_basket = basket_panel(mc["label"], mc["variants"]["pro_4"], mc_note)

    body = f"""
    {header}
    {lead}
    <div class="px-10 py-6">
      {kpi_grid}
      {method_panel()}
      <div class="mt-6 grid grid-cols-1 gap-6">
        {universe_table(sc)}
        {universe_charts(sc, "sc")}
        {universe_table(mc)}
        {universe_charts(mc, "mc")}
      </div>
      <div class="mt-6">{robustness_table()}</div>
      {cost_note}
      <div class="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
        {sc_basket}
        {mc_basket}
      </div>
      {limitations()}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Clean-room ProPicks India (Report 101)</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("101_propicks_india_cleanroom.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 101_propicks_india_cleanroom.html")

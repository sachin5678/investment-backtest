"""Builds 106_atr_x_hero.html from results105.json."""
import html
import json

from svg_charts import COL, area_underwater_chart, line_chart

with open("results105.json", encoding="utf-8") as f:
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

GROUP_ORDER = ["The hero", "Entry gate — contraction", "Entry gate — expansion",
               "Review keep — contraction", "Buy + keep", "Base hero context"]


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


def monthly_points(points):
    last = {}
    for d, v in points:
        last[d[:7]] = [d, v]
    return [last[k] for k in sorted(last)]


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
      table.data-table tr.best td{background:rgba(55,240,131,0.07);}
      table.data-table tr.worst td{background:rgba(242,100,60,0.08);}
      table.data-table tr.group td{background:#132B36;color:#9FB4BB;font-size:10.5px;text-transform:uppercase;letter-spacing:0.07em;font-weight:700;padding-top:14px;padding-bottom:8px;border-bottom:1px solid #1E3A45;}
      .kpi-val{font-size:23px;font-weight:700;letter-spacing:-0.01em;}
      .bar-track{background:#16303a;border-radius:999px;height:9px;overflow:hidden;}
      .bar-fill{height:9px;border-radius:999px;}
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


def build():
    vals = list(R["variants"].values())
    V = {v["key"]: v for v in vals}
    hero = V["hero98"]
    best = max((v for v in vals if v["group"] not in ("The hero", "Base hero context")),
               key=lambda v: v["cagr_pct"])
    best_entry = max((v for v in vals if v["group"] == "Entry gate — contraction"),
                     key=lambda v: v["cagr_pct"])
    atr08 = V["buy08"]
    atr05 = V["buy05"]
    buygt10 = V["buygt10"]
    keep12 = V["keep12"]
    buy11 = V["buy11"]

    d_best = best["cagr_pct"] - hero["cagr_pct"]
    d_best_entry = best_entry["cagr_pct"] - hero["cagr_pct"]
    d08 = atr08["cagr_pct"] - hero["cagr_pct"]
    dgt10 = buygt10["cagr_pct"] - hero["cagr_pct"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">ATR Contraction × the Hero — Does Volatility Contraction Improve the Max Strategy?</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Report 104's ATR(14)/ATR(50) filter, isolated from Heikin-Ashi. The &lt;0.8 contraction rule that helped the standalone HA system is the wrong filter for a 10-stock momentum book: only 11% of the top-10 names pass at a review, and the ATR-gated book ends up holding rank-39 names with 17% cash. Every threshold tested loses; the hero stays.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(R['start_date'])}–{esc(R['end_date'])}<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2643C]">
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          {pill('no ATR threshold improves the hero — the least-bad gives up 1.1pp with no drawdown benefit', 'negative')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          The untouched hero compounds at <span class="font-semibold">{pct(hero['cagr_pct'])}</span> with a
          {pct(hero['max_drawdown_pct'], 1, signed=False)} max drawdown, Sharpe {num(hero['sharpe'])} and
          {hero['trades']:,} closed trades. The best ATR variant — keep a holder only while ATR(14)/ATR(50) &lt; 1.2 —
          returns {pct(best['cagr_pct'], signed=False)} ({d_best:+.2f}pp), with the same
          {pct(best['max_drawdown_pct'], 1, signed=False)} drawdown and a lower Sharpe of {num(best['sharpe'])}.
          The best pure entry gate — buy ATR&lt;1.1 — returns {pct(best_entry['cagr_pct'], signed=False)}
          ({d_best_entry:+.2f}pp).
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The original report-104 threshold, ATR&lt;0.8, is the version that matters — and it is catastrophic:
          {pct(atr08['cagr_pct'], signed=False)} CAGR ({d08:+.2f}pp), {pct(atr08['max_drawdown_pct'], 1, signed=False)}
          drawdown and Sharpe {num(atr08['sharpe'])}. The holdings explain it: the gate lifts the average holding
          rank from {num(hero['avg_rank'], 1)} to {num(atr08['avg_rank'], 1)} and leaves
          {pct(atr08['avg_cash_pct'], 1, signed=False)} of the portfolio in cash at reviews. It is not timing the
          hero; it is replacing its leaders with lower-ranked quiet names.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("Return", "CAGR over the identical 2009–2026 window; 0.1% cost per side.",
                 [("Hero 98", pct(hero["cagr_pct"]), "positive"),
                  ("Best ATR — keep < 1.2", pct(best["cagr_pct"], signed=False), "negative"),
                  ("Delta", f"{d_best:+.2f}pp", "negative"),
                  ("ATR < 0.8 entry", pct(atr08["cagr_pct"], signed=False), "negative")]),
        kpi_card("Drawdown", "Largest peak-to-trough decline over the identical window.",
                 [("Hero 98", pct(hero["max_drawdown_pct"], 1, signed=False), "positive"),
                  ("Keep < 1.2", pct(best["max_drawdown_pct"], 1, signed=False), "neutral"),
                  ("Buy > 1.0", pct(buygt10["max_drawdown_pct"], 1, signed=False), "assumption"),
                  ("Buy < 0.8", pct(atr08["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("Risk-adjusted and turnover", "Sharpe uses daily returns; trades are closed round trips.",
                 [("Hero Sharpe", num(hero["sharpe"]), "positive"),
                  ("Best ATR Sharpe", num(best["sharpe"]), "negative"),
                  ("Hero trades", f"{hero['trades']:,}", "neutral"),
                  ("ATR<0.8 trades", f"{atr08['trades']:,}", "negative")]),
        kpi_card("Selection drift", "Average rank of the names held at reviews, and average cash left at those events.",
                 [("Hero rank", num(hero["avg_rank"], 1), "positive"),
                  ("Buy <1.1 rank", num(buy11["avg_rank"], 1), "assumption"),
                  ("Buy <0.8 rank", num(atr08["avg_rank"], 1), "negative"),
                  ("Buy <0.5 rank", num(atr05["avg_rank"], 1), "negative")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-1 gap-4 mt-6">{"".join(kpis)}</div>'

    # ---- full matrix ----
    rows_html = []
    for group in GROUP_ORDER:
        rows_html.append(f'<tr class="group"><td colspan="8">{esc(group)}</td></tr>')
        for v in [x for x in vals if x["group"] == group]:
            cls = []
            if v["key"] == "hero98":
                cls.append("hi")
            elif v["key"] == best["key"]:
                cls.append("best")
            elif v["key"] == "buy08":
                cls.append("worst")
            klass = f' class="{" ".join(cls)}"' if cls else ""
            delta = v["cagr_pct"] - hero["cagr_pct"]
            delta_s = "—" if v["key"] == "hero98" else f"{delta:+.2f}pp"
            rows_html.append(
                f'<tr{klass}><td>{esc(v["label"])}</td>'
                f'<td><strong>{pct(v["cagr_pct"], signed=False)}</strong></td>'
                f'<td style="color:{"#37F083" if delta > 0 else ("#F2643C" if delta < 0 else "#7E97A0")}">{delta_s}</td>'
                f'<td>{pct(v["max_drawdown_pct"], 1, signed=False)}</td>'
                f'<td>{num(v["sharpe"])}</td>'
                f'<td>{v["trades"]:,}</td>'
                f'<td>{num(v["avg_rank"], 1)}</td>'
                f'<td>{pct(v["avg_cash_pct"], 1, signed=False)}</td></tr>'
            )

    matrix = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1 gap-3 flex-wrap">
        <h3 class="text-base font-bold text-[#E6EDF0]">The full matrix — nineteen ATR variants</h3>
        {pill('hero row amber; least-bad ATR row green; report-104 threshold red', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — each row adds one ATR rule to the hero. Δ is CAGR versus the hero. “Avg rank” is the average momentum rank of the names held at reviews; “Cash” is the average cash left at those events. The engine fills slots from lower ranks when the gate excludes a top name, so a hard ATR gate shows up as rank drift and cash drag.</p>
      <div class="overflow-x-auto">
      <table class="data-table">
        <thead><tr><th>Variant</th><th>CAGR</th><th>Δ vs hero</th><th>Max DD</th><th>Sharpe</th><th>Trades</th><th>Avg rank</th><th>Cash</th></tr></thead>
        <tbody>{''.join(rows_html)}</tbody>
      </table>
      </div>
      <p class="{MUTED} mt-3">All rows: midcap150, Jun/Dec reviews, top 10, 0.1% cost per side, 0% slippage, fractional units, gold park when the regime is off. Tax is not modelled; the ATR variants trade somewhat more, so adding it would widen the gap.</p>
    </div>
    """

    # ---- charts ----
    eq_series = [
        {"name": "Hero 98 — Max stack A", "color": COL["positive"], "points": monthly_points(hero["equity_curve"])},
        {"name": "Keep ATR < 1.2", "color": COL["assumption"], "points": monthly_points(best["equity_curve"])},
        {"name": "Buy ATR < 1.1", "color": "#5AB0FF", "points": monthly_points(buy11["equity_curve"])},
        {"name": "Buy ATR < 0.8", "color": COL["negative"], "points": monthly_points(atr08["equity_curve"])},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=430, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_106")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — the hero vs the closest ATR variants</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the hero ends at {num(hero['final_x'], 0)}×; the least-bad ATR variant (keep &lt; 1.2) at {num(best['final_x'], 0)}×; the best entry gate (buy &lt; 1.1) at {num(buy11['final_x'], 0)}×; the report-104 threshold (buy &lt; 0.8) at {num(atr08['final_x'], 0)}×. The ATR lines are not vertically offset by a different regime; they simply own weaker momentum.</p>
      <div class="flex items-center mb-2">{eq_legend}</div>
      {eq_svg}
    </div>
    """

    dd_series = [
        {"name": "Hero 98 — Max stack A", "color": COL["positive"], "points": monthly_points(hero["underwater"])},
        {"name": "Buy ATR < 0.8", "color": COL["negative"], "points": monthly_points(atr08["underwater"])},
        {"name": "Buy ATR > 1.0", "color": COL["muted"], "points": monthly_points(buygt10["underwater"])},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=230, chart_id="dd_106")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown — the only ATR win costs 9pp of CAGR</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — buying ATR expansion (&gt; 1.0, grey) cuts the max drawdown from {pct(hero['max_drawdown_pct'], 1, signed=False)} to {pct(buygt10['max_drawdown_pct'], 1, signed=False)}, but gives up {abs(dgt10):.2f}pp of CAGR. The contraction gate (red) is deeper than the hero. There is no free risk reduction here.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    # ---- diagnostics ----
    pr = R["diagnostics"]["pass_rates"]
    pr_rows = "".join(
        f'<tr><td>{esc(p["label"])}</td><td>{pct(p["top10_pct"], 1, signed=False)}</td>'
        f'<td>{pct(p["all_pct"], 1, signed=False)}</td></tr>' for p in pr
    )
    bars = [
        ("Hero 98", hero["avg_rank"], hero["avg_cash_pct"], COL["positive"]),
        ("Buy ATR < 1.1", buy11["avg_rank"], buy11["avg_cash_pct"], "#5AB0FF"),
        ("Buy ATR < 1.0", V["buy10"]["avg_rank"], V["buy10"]["avg_cash_pct"], COL["assumption"]),
        ("Buy ATR < 0.8", atr08["avg_rank"], atr08["avg_cash_pct"], COL["negative"]),
        ("Buy ATR < 0.5", atr05["avg_rank"], atr05["avg_cash_pct"], COL["negative"]),
    ]
    max_rank = max(b[1] for b in bars)
    bar_html = "".join(
        f'<div class="mb-3"><div class="flex justify-between text-[12px] mb-1">'
        f'<span class="text-[#C9D6DA]">{esc(label)}</span>'
        f'<span class="mono text-[#9FB4BB]">rank {num(rank, 1)} · cash {pct(cash, 1, signed=False)}</span></div>'
        f'<div class="bar-track"><div class="bar-fill" style="width:{rank / max_rank * 100:.1f}%;background:{color}"></div></div></div>'
        for label, rank, cash, color in bars
    )

    diag = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">What the gate actually did</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the ATR filter is rare exactly where the hero's edge lives. The engine can fill slots from lower ranks, so the portfolio stays invested — in weaker names. At tighter thresholds it also sits in cash.</p>
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <div class="text-[12px] uppercase tracking-wide text-[#7E97A0] font-semibold mb-2">Pass rate at review dates</div>
          <table class="data-table">
            <thead><tr><th>Gate</th><th>Top-10 names</th><th>All ranked</th></tr></thead>
            <tbody>{pr_rows}</tbody>
          </table>
          <p class="{MUTED} mt-3">{R['diagnostics']['review_dates']} review dates. Only about one in nine top-10 momentum names passes the report-104 &lt;0.8 gate; about one in six of the full ranked list does. At &lt;1.0 roughly half the top names pass, which is why the damage shrinks but does not disappear.</p>
        </div>
        <div>
          <div class="text-[12px] uppercase tracking-wide text-[#7E97A0] font-semibold mb-2">Average holding rank (lower is better)</div>
          {bar_html}
          <p class="{MUTED} mt-3">The hero holds names at an average rank of {num(hero['avg_rank'], 1)}. The &lt;0.8 gate lifts that to {num(atr08['avg_rank'], 1)} and leaves {pct(atr08['avg_cash_pct'], 1, signed=False)} cash; &lt;0.5 holds rank {num(atr05['avg_rank'], 1)} names and sits {pct(atr05['avg_cash_pct'], 1, signed=False)} in cash.</p>
        </div>
      </div>
    </div>
    """

    # ---- why ----
    why = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Why every ATR version loses</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the failure is structural. ATR contraction is a short-horizon timing idea; the hero is a twice-a-year cross-sectional momentum book.</p>
      <ol class="list-decimal pl-5 space-y-3 text-[13.5px] text-[#C9D6DA] leading-relaxed">
        <li><strong class="text-[#E6EDF0]">The gate is rare where the edge lives.</strong> Only {pct(pr[0]['top10_pct'], 1, signed=False)} of the top-10 momentum names pass ATR&lt;0.8 at a review, versus {pct(pr[0]['all_pct'], 1, signed=False)} of all ranked names. The engine fills the slot from lower ranks, so the average holding rank jumps from {num(hero['avg_rank'], 1)} to {num(atr08['avg_rank'], 1)}. You are no longer running the hero; you are running a lower-momentum, lower-volatility book.</li>
        <li><strong class="text-[#E6EDF0]">Cash drag compounds the substitution.</strong> ATR&lt;0.8 averages {num(atr08['avg_holdings'], 1)} of 10 slots invested and {pct(atr08['avg_cash_pct'], 1, signed=False)} cash at review events. At ATR&lt;0.5 the book is {pct(atr05['avg_cash_pct'], 1, signed=False)} cash and makes only {atr05['trades']} trades. The filter can leave the strategy effectively uninvested.</li>
        <li><strong class="text-[#E6EDF0]">Loosening the gate only removes the damage.</strong> ATR&lt;0.9 costs {abs(V['buy09']['cagr_pct'] - hero['cagr_pct']):.2f}pp, ATR&lt;1.0 costs {abs(V['buy10']['cagr_pct'] - hero['cagr_pct']):.2f}pp, ATR&lt;1.1 costs {abs(buy11['cagr_pct'] - hero['cagr_pct']):.2f}pp. The keep filter at &lt;1.2 is the least-bad at {abs(d_best):.2f}pp, with the same drawdown and a lower Sharpe. No threshold flips the sign.</li>
        <li><strong class="text-[#E6EDF0]">The opposite gate buys drawdown relief at a steep price.</strong> Buying ATR&gt;1.0 cuts the max drawdown from {pct(hero['max_drawdown_pct'], 1, signed=False)} to {pct(buygt10['max_drawdown_pct'], 1, signed=False)}, but gives up {abs(dgt10):.2f}pp of CAGR; Calmar falls from {num(hero['calmar'])} to {num(buygt10['calmar'])}. If the goal is lower drawdown, the existing 200-EMA + gold does it more cheaply.</li>
        <li><strong class="text-[#E6EDF0]">Horizon mismatch, again.</strong> ATR(14)/ATR(50) tells you whether a stock has been quiet for a few weeks. The hero's ranking is built on 6- and 12-month momentum. The filter can replace the ranking, but it cannot improve it — and replacing it is what the table shows.</li>
      </ol>
    </div>
    """

    honest = f"""
    <div class="{PANEL} mt-6 border-l-4 border-l-[#F2B03C]">
      <div class="flex items-center gap-2 mb-3 flex-wrap">
        {pill('this is a statement about ATR as a hero overlay, not about ATR as a standalone tool', 'assumption')}
      </div>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Report 104 found ATR contraction useful inside the standalone HA stock system. That result is not
        contradicted here: the filter is being asked to do a different job. In a broad, 8-slot HA system, ATR
        contraction times individual entries out of a large opportunity set. In a concentrated 10-stock,
        twice-a-year momentum book, it removes the strongest names from a small set and replaces them with weaker
        ones. The instrument is the same; the portfolio construction is not.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Caveats: Midcap 150 is today's constituent list applied backwards, so absolute CAGRs are
        survivorship-inflated; this lab does not model tax; the window is 2009–2026. Those caveats apply to every
        row, so the ranking is robust even though the absolute numbers are optimistic.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        <strong class="text-[#E6EDF0]">Scope.</strong> This lab tests stock-level ATR(14)/ATR(50) as an entry gate
        and as a review keep rule, with thresholds from 0.5 to 1.2. It does not test an index-level ATR regime,
        ATR-based position sizing, or an ATR/12% stop-loss. Those are separate risk-design questions; the stop
        would also interact with the engine's review calendar and needs its own cash/refill treatment.
      </p>
    </div>
    """

    bottom = f"""
    <div class="px-10 py-6">
      <div class="{PANEL} border-2 border-[#37F083]">
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          {pill('keep ATR out of the hero — the 200-EMA + gold already does the risk job better', 'positive')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          No ATR threshold improves the hero. The least-bad version (keep &lt; 1.2) gives up {abs(d_best):.2f}pp of
          CAGR with no drawdown improvement; the report-104 threshold (&lt; 0.8) gives up {abs(d08):.2f}pp and takes
          on a deeper drawdown. The only variant that cuts drawdown — buy &gt; 1.0 — costs {abs(dgt10):.2f}pp of CAGR
          and lowers Calmar.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The hero remains report 98's Max stack A. If you want ATR exposure, run it where it was designed to work:
          inside the standalone HA system of report 104, with its own capital and its own 8-slot construction.
        </p>
      </div>
    </div>
    """

    method = f"""
    <div class="{PANEL_TIGHT} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Method and reproduction</h3>
      <p class="{MUTED} mb-2">Hero: report 98 Max stack A — midcap150, top 10, Jun/Dec reviews, keep-if 6m &gt; 0, exit rank 30, NIFTY 50 200-EMA regime with 100% GOLDBEES park, 0.1% cost per side.</p>
      <p class="{MUTED} mb-2">ATR: ATR(14)/ATR(50) on each stock's high/low/close, simple rolling means — the same definition used in report 104. A value below 1.0 means recent volatility is below its 50-day norm (contraction); above 1.0 means expansion. The buy rule gates new entries at the review; the keep rule forces a review exit when the ratio is above/below the threshold.</p>
      <p class="{MUTED} mb-3">Every variant runs through the same <span class="mono">ms_builder.py</span> engine used by reports 93–98. The hero regression gate is unchanged and still reproduces report 93 exactly. Window {esc(R['start_date'])}–{esc(R['end_date'])}.</p>
      <pre class="mono text-[12px] text-[#C9D6DA] bg-[#08171E] border border-[#1E3A45] rounded-xl p-4 overflow-x-auto">py -3 backtest106.py      # writes results105.json
py -3 build_html106.py    # writes 106_atr_x_hero.html
py -3 check_builder_regression.py   # hero must still match report 93</pre>
    </div>
    """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>106 — ATR Contraction × the Hero</title>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="min-h-screen">
{header}
{lead}
<div class="px-10">{kpi_grid}</div>
<div class="px-10">{matrix}{eq_panel}{dd_panel}{diag}{why}{honest}<div class="py-6">{method}</div></div>
{bottom}
</body>
</html>"""


if __name__ == "__main__":
    out = "106_atr_x_hero.html"
    html_out = "\n".join(line.rstrip() for line in build().splitlines()) + "\n"
    with open(out, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"wrote {out}")

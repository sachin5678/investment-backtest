"""Builds 107_nifty100_momentum_yearly_gold_switch.html from results106.json.

Static twin of the webapp's report 107 page: the same tick/untick filter
(gold switch, no switch, top 5/10/20, next-open vs same-close, rebalance
month), applied to the growth chart, the drawdown chart, the KPI table and
the all-12-months calendar table. Charts are inline SVG; the filter is a few
lines of inline JS that show/hide elements tagged with data-* attributes.
"""
import html
import json
import re
import statistics as st

from svg_charts import COL, area_underwater_chart, line_chart

with open("results106.json", encoding="utf-8") as f:
    R = json.load(f)

V = R["variants"]
TABLE = R["calendar_table"]

TAILWIND_CDN = '<script src="https://cdn.tailwindcss.com"></script>'
PANEL = "bg-[#0F2630] border border-[#1E3A45] rounded-2xl p-6"
PANEL_TIGHT = "bg-[#0F2630] border border-[#1E3A45] rounded-2xl p-5"
MUTED = "text-[#7E97A0] text-[12.5px] leading-snug"
WHAT = "text-[#9FB4BB] text-[13px] italic mb-3"
PILL_BASE = "inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full whitespace-nowrap"
PILLS = {
    "positive": PILL_BASE + " bg-[#37F083]/15 text-[#37F083] border border-[#37F083]/40",
    "negative": PILL_BASE + " bg-[#F2643C]/15 text-[#F2643C] border border-[#F2643C]/40",
    "assumption": PILL_BASE + " bg-[#F2B03C]/15 text-[#F2B03C] border border-[#F2B03C]/40",
}
N_COLOR = {5: "#F2B03C", 10: "#6AE4FF", 20: "#C77DFF"}
NS = (5, 10, 20)


def esc(s):
    return html.escape(str(s))


def pct(v, d=1, signed=True):
    if v is None:
        return "—"
    return f"{'+' if signed and v > 0 else ''}{v:,.{d}f}%"


def pill(text, kind="assumption"):
    return f'<span class="{PILLS[kind]}">{"▲" if kind == "assumption" else "●"} {text}</span>'


def med(rows, key, field):
    return st.median(r[key][field] for r in rows)


def monthly(points):
    last = {}
    for d, v in points:
        last[d[:7]] = [d, v]
    return [last[k] for k in sorted(last)]


def rebased(curve):
    pts = monthly(curve)
    base = pts[0][1]
    return [[d, v / base * 100.0] for d, v in pts]


def drawdown(curve):
    pts = monthly(curve)
    peak, out = 0.0, []
    for d, v in pts:
        peak = max(peak, v)
        out.append([d, (v / peak - 1.0) * 100.0])
    return out


def tint(hexcol, amount):
    h = hexcol.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    r, g, b = (round(c + (255 - c) * amount) for c in (r, g, b))
    return f"#{r:02X}{g:02X}{b:02X}"


def series_meta(key):
    v = V[key]
    t = v["tags"]
    if t.get("benchmark"):
        return {"n": 0, "gold": 0, "ex": "bench", "cal": "all", "color": "#AAB6C9", "dash": True, "name": v["display_label"]}
    color = N_COLOR[t["n"]]
    # unique colour per line (the tag script keys elements by order, but a
    # distinct hue keeps the legend readable): gold = base, plain = tinted
    if not t["gold"]:
        color = tint(color, 0.35)
    if t["exec"] == "close":
        color = tint(color, 0.25)
    return {"n": t["n"], "gold": 1 if t["gold"] else 0, "ex": t["exec"], "cal": t["cal"].lower(),
            "color": color, "dash": not t["gold"], "name": v["display_label"].rsplit(" · ", 1)[0]}


def tag_svg(svg, legend, metas):
    """Add data-* filter attributes, in series order, to each series' paths /
    end-dot / legend entry (svg_charts emits them strictly in series order)."""
    def attrs(m):
        return f'data-s="1" data-n="{m["n"]}" data-g="{m["gold"]}" data-ex="{m["ex"]}"'

    it = iter(metas)
    svg = re.sub(r'<path d="[^"]*" fill="none"', lambda mo: mo.group(0).replace("<path", f"<path {attrs(next(it))}"), svg)
    it = iter(metas)
    svg = re.sub(r'<circle cx=', lambda mo: f'<circle {attrs(next(it))} cx=', svg)
    it = iter(metas)
    legend = re.sub(r'<span class="inline-flex items-center gap-1.5 mr-4">',
                    lambda mo: f'<span class="inline-flex items-center gap-1.5 mr-4" {attrs(next(it))}>', legend)
    return svg, legend


def tag_area(svg, legend, metas):
    def attrs(m):
        return f'data-s="1" data-n="{m["n"]}" data-g="{m["gold"]}" data-ex="{m["ex"]}"'

    it = iter(metas)
    svg = re.sub(r'<path d="[^"]*" fill="#[0-9A-Fa-f]{6}" opacity="0.18"',
                 lambda mo: mo.group(0).replace("<path", f"<path {attrs(next(it))}"), svg)
    it = iter(metas)
    svg = re.sub(r'<path d="[^"]*" fill="none"', lambda mo: mo.group(0).replace("<path", f"<path {attrs(next(it))}"), svg)
    it = iter(metas)
    legend = re.sub(r'<span class="inline-flex items-center gap-1.5 mr-4">',
                    lambda mo: f'<span class="inline-flex items-center gap-1.5 mr-4" {attrs(next(it))}>', legend)
    return svg, legend


def chart_keys(cal):
    keys = [f"top{n}_{k}_{ex}_{cal}" for n in NS for ex in ("open", "close") for k in ("gold", "plain")]
    return keys + ["nifty50"]


def build():
    # ---- headline numbers, all from the data ----
    rows = {n: [r for r in TABLE if r["n"] == n] for n in NS}
    nifty = V["nifty50"]
    gold_better_dd = {n: sum(1 for r in rows[n] if r["open_gold"]["max_drawdown_pct"] > r["open_plain"]["max_drawdown_pct"]) for n in NS}
    gold_better_cagr = {n: sum(1 for r in rows[n] if r["open_gold"]["cagr_pct"] > r["open_plain"]["cagr_pct"]) for n in NS}

    def delta(n, ex, field):
        return med(rows[n], f"{ex}_gold", field) - med(rows[n], f"{ex}_plain", field)

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">NIFTY 100 Momentum 5 / 10 / 20 — Yearly Rebalance, With and Without the Gold Switch</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Report 45's NIFTY 100 momentum score, held top 5, top 10 or top 20, rebalanced once a year, with and without the 200-EMA gold regime switch — filled at the next day's open, with the legacy same-close fills shown for comparison.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">{esc(R['start_date'])}–{esc(R['end_date'])}<br/>Report generated {esc(R['generated'])}</div>
      </div>
    </header>"""

    lead = f"""
    <div class="px-10 pt-6"><div class="{PANEL} border-2 border-[#F2B03C]">
      <div class="flex items-center gap-2 mb-3 flex-wrap">
        {pill('the switch cuts drawdown in every month and every size — it only pays in CAGR for top 5 and top 10', 'assumption')}
      </div>
      <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
        With next-open fills and the median across all 12 possible yearly rebalance months, the gold switch cuts the max drawdown from
        {pct(med(rows[5], 'open_plain', 'max_drawdown_pct'), 1, False)} to {pct(med(rows[5], 'open_gold', 'max_drawdown_pct'), 1, False)} (top 5),
        {pct(med(rows[10], 'open_plain', 'max_drawdown_pct'), 1, False)} to {pct(med(rows[10], 'open_gold', 'max_drawdown_pct'), 1, False)} (top 10) and
        {pct(med(rows[20], 'open_plain', 'max_drawdown_pct'), 1, False)} to {pct(med(rows[20], 'open_gold', 'max_drawdown_pct'), 1, False)} (top 20),
        and the drawdown is shallower in {gold_better_dd[5]}, {gold_better_dd[10]} and {gold_better_dd[20]} of the 12 months respectively.
        NIFTY 50 over the same window: {pct(nifty['cagr_pct'], signed=False)} CAGR, {pct(nifty['max_drawdown_pct'], 1, False)} drawdown.
      </p>
      <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
        CAGR is where the sizes differ: the switch adds {delta(5, 'open', 'cagr_pct'):+.1f}pp (top 5) and {delta(10, 'open', 'cagr_pct'):+.1f}pp (top 10) at the median
        but costs {abs(delta(20, 'open', 'cagr_pct')):.1f}pp for top 20, where it beat the unswitched version in only {gold_better_cagr[20]} of 12 months.
        Top 10 with the switch is the steadiest of the six combinations; top 5 has the highest ceiling and the widest calendar sensitivity.
      </p>
    </div></div>"""

    kpis = []
    for n in NS:
        kpis.append(f"""
        <div class="{PANEL_TIGHT}">
          <div class="text-[13px] font-semibold text-[#E6EDF0] mb-1">Top {n} — median of the 12 rebalance months, next-open fills</div>
          <div class="flex gap-3 flex-wrap mt-2">
            <div class="flex-1 min-w-[120px]"><div class="text-[11px] text-[#7E97A0] mb-1 uppercase tracking-wide">CAGR no switch</div><div class="text-[23px] font-bold mono text-[#E6EDF0]">{pct(med(rows[n], 'open_plain', 'cagr_pct'), signed=False)}</div></div>
            <div class="flex-1 min-w-[120px]"><div class="text-[11px] text-[#7E97A0] mb-1 uppercase tracking-wide">CAGR gold switch</div><div class="text-[23px] font-bold mono text-[#37F083]">{pct(med(rows[n], 'open_gold', 'cagr_pct'), signed=False)}</div></div>
            <div class="flex-1 min-w-[120px]"><div class="text-[11px] text-[#7E97A0] mb-1 uppercase tracking-wide">Drawdown no switch</div><div class="text-[23px] font-bold mono text-[#F2643C]">{pct(med(rows[n], 'open_plain', 'max_drawdown_pct'), 1, False)}</div></div>
            <div class="flex-1 min-w-[120px]"><div class="text-[11px] text-[#7E97A0] mb-1 uppercase tracking-wide">Drawdown gold switch</div><div class="text-[23px] font-bold mono text-[#F2B03C]">{pct(med(rows[n], 'open_gold', 'max_drawdown_pct'), 1, False)}</div></div>
          </div>
        </div>""")
    kpi_grid = f'<div class="grid grid-cols-1 gap-4 mt-6">{"".join(kpis)}</div>'

    # ---- filter panel ----
    def chk(i, label, checked=True, swatch=None):
        sw = f'<span class="inline-block w-3 h-[3px] rounded" style="background:{swatch}"></span>' if swatch else ""
        return (f'<label class="inline-flex items-center gap-2 text-[13px] cursor-pointer select-none">'
                f'<input type="checkbox" id="{i}" {"checked" if checked else ""} class="cursor-pointer"/>{sw}{label}</label>')

    filter_panel = f"""
    <div class="{PANEL_TIGHT} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Filter strategies</h3>
      <p class="{WHAT}">Tick or untick to compare. The growth chart, drawdown chart, KPI table and calendar table all follow these boxes. Colour = portfolio size, solid line = gold regime switch, dashed = always invested, paler = the legacy same-close fills.</p>
      <div class="flex flex-wrap gap-x-10 gap-y-4">
        <div><div class="text-[11px] uppercase tracking-wide text-[#7E97A0] font-semibold mb-2">Gold regime switch</div>
          <div class="flex flex-col gap-1.5">{chk('f-gold', 'With switch (200-EMA → GOLDBEES)')}{chk('f-plain', 'Without switch (always invested)')}</div></div>
        <div><div class="text-[11px] uppercase tracking-wide text-[#7E97A0] font-semibold mb-2">Portfolio size</div>
          <div class="flex flex-col gap-1.5">{''.join(chk(f'f-n{n}', f'Top {n}', True, N_COLOR[n]) for n in NS)}</div></div>
        <div><div class="text-[11px] uppercase tracking-wide text-[#7E97A0] font-semibold mb-2">Execution</div>
          <div class="flex flex-col gap-1.5">{chk('f-open', 'Next-day open (headline)')}{chk('f-close', 'Same-day close (legacy)', False)}</div></div>
        <div><div class="text-[11px] uppercase tracking-wide text-[#7E97A0] font-semibold mb-2">Rebalance month (charts)</div>
          <div class="flex flex-col gap-1.5">
            <label class="inline-flex items-center gap-2 text-[13px] cursor-pointer"><input type="radio" name="cal" value="dec" checked/>December</label>
            <label class="inline-flex items-center gap-2 text-[13px] cursor-pointer"><input type="radio" name="cal" value="jun"/>June</label></div></div>
        <div><div class="text-[11px] uppercase tracking-wide text-[#7E97A0] font-semibold mb-2">Benchmark</div>
          <div class="flex flex-col gap-1.5">{chk('f-bench', 'NIFTY 50 buy &amp; hold', True, '#AAB6C9')}</div></div>
      </div>
    </div>"""

    # ---- charts, one pair per calendar ----
    chart_blocks = []
    for cal in ("dec", "jun"):
        keys = chart_keys(cal)
        metas = [series_meta(k) for k in keys]
        eq_series = [{"name": m["name"], "color": m["color"], "points": rebased(V[k]["equity_curve"]), "dash": m["dash"]}
                     for k, m in zip(keys, metas)]
        dd_series = [{"name": m["name"], "color": m["color"], "points": drawdown(V[k]["equity_curve"]), "dash": m["dash"]}
                     for k, m in zip(keys, metas)]
        eq_svg, eq_leg = tag_svg(*line_chart(eq_series, chart_id=f"eq-{cal}", y_label="Growth of 100"), metas)
        dd_svg, dd_leg = tag_area(*area_underwater_chart(dd_series, chart_id=f"dd-{cal}"), metas)
        label = "December" if cal == "dec" else "June"
        chart_blocks.append(f"""
        <div class="cal-block" data-cal="{cal}" {'' if cal == 'dec' else 'style="display:none"'}>
          <div class="{PANEL} mt-6">
            <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {label} yearly rebalance</h3>
            <p class="{WHAT}">Every strategy rebased to 100 on the first common date. Smooth curve through real month-end points.</p>
            {eq_svg}<div class="mt-3">{eq_leg}</div>
          </div>
          <div class="{PANEL} mt-6">
            <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown — {label} yearly rebalance</h3>
            <p class="{WHAT}">% below each strategy's own running peak (month-end points). The gold switch's job is visible here.</p>
            {dd_svg}<div class="mt-3">{dd_leg}</div>
          </div>
        </div>""")

    # ---- KPI table per calendar ----
    def kpi_rows(cal):
        out = []
        for k in chart_keys(cal):
            m = series_meta(k)
            v = V[k]
            out.append(f'<tr data-s="1" data-n="{m["n"]}" data-g="{m["gold"]}" data-ex="{m["ex"]}">'
                       f'<td><span class="inline-block w-3 h-[3px] rounded mr-2 align-middle" style="background:{m["color"]}"></span>{esc(v["display_label"])}</td>'
                       f'<td>{pct(v["net_return_pct"], 0)}</td><td><strong>{pct(v["cagr_pct"], signed=False)}</strong></td>'
                       f'<td>{pct(v["max_drawdown_pct"], 1, False)}</td><td>{v["longest_underwater_days"]:,}d</td></tr>')
        return "".join(out)

    kpi_tables = "".join(f"""
        <div class="cal-block" data-cal="{cal}" {'' if cal == 'dec' else 'style="display:none"'}>
          <table class="data-table"><thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
          <tbody>{kpi_rows(cal)}</tbody></table>
        </div>""" for cal in ("dec", "jun"))
    kpi_panel = f"""<div class="{PANEL} mt-6"><h3 class="text-base font-bold text-[#E6EDF0] mb-1">Strategy KPIs</h3>
      <p class="{WHAT}">Computed from each strategy's full daily series on the common window; follows the filter boxes.</p>{kpi_tables}</div>"""

    # ---- calendar table ----
    heads = [("open", "plain", "Next-open · No switch"), ("open", "gold", "Next-open · Gold switch"),
             ("close", "plain", "Same-close · No switch"), ("close", "gold", "Same-close · Gold switch")]
    thead = "<th>Top N</th><th>Month</th>" + "".join(
        f'<th data-ex="{e}" data-g="{1 if k == "gold" else 0}" data-c="1">{lbl}</th>' for e, k, lbl in heads)
    body = []
    for n in NS:
        for r in rows[n]:
            cells = "".join(f'<td data-ex="{e}" data-g="{1 if k == "gold" else 0}" data-c="1">{pct(r[f"{e}_{k}"]["cagr_pct"])} / '
                            f'<span style="color:#F2643C">{pct(r[f"{e}_{k}"]["max_drawdown_pct"], 1, False)}</span></td>' for e, k, _ in heads)
            body.append(f'<tr data-n="{n}" data-r="1"><td>{n}</td><td>{esc(r["calendar"])}</td>{cells}</tr>')
        cells = "".join(f'<td data-ex="{e}" data-g="{1 if k == "gold" else 0}" data-c="1"><strong>{pct(med(rows[n], f"{e}_{k}", "cagr_pct"))} / '
                        f'{pct(med(rows[n], f"{e}_{k}", "max_drawdown_pct"), 1, False)}</strong></td>' for e, k, _ in heads)
        body.append(f'<tr class="hi" data-n="{n}" data-r="1"><td>{n}</td><td>Median</td>{cells}</tr>')
    cal_panel = f"""<div class="{PANEL} mt-6"><h3 class="text-base font-bold text-[#E6EDF0] mb-1">Every yearly rebalance month — CAGR / max drawdown</h3>
      <p class="{WHAT}">A yearly rebalance is very sensitive to which month it happens in. One row per rebalance month; the highlighted row closing each block is the median of the 12. Follows the filter boxes.</p>
      <div class="overflow-x-auto"><table class="data-table"><thead><tr>{thead}</tr></thead><tbody>{''.join(body)}</tbody></table></div></div>"""

    # ---- prose ----
    method = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">How it is built</h3>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        <strong class="text-[#E6EDF0]">Strategy.</strong> Universe: today's NIFTY 100 constituents. Score: report 45's risk-adjusted 6-month and 12-month
        momentum, z-scored and averaged. Hold the top 5, 10 or 20 names equal-weight and rebalance once a year, in the last trading day of the chosen month.
        There are 12 possible calendars; December and June are charted in full and all 12 are tabulated.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        <strong class="text-[#E6EDF0]">Gold regime switch.</strong> When NIFTY 50 closes below its 200-day EMA the whole book moves to GOLDBEES until it closes back above,
        at which point a fresh top-N is bought. Same rule as reports 42–48, confirm days = 1. Without the switch the portfolio stays in stocks all year.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        <strong class="text-[#E6EDF0]">Execution.</strong> The headline numbers follow the project's next-open rule: a signal formed at day T's close is filled at
        T+1's open, old holdings sold and new ones bought together, with the overnight gap earned by the old position. The legacy same-close convention
        (reports 42–99) is shown alongside, untick it to hide it. The gap between the two is the price of not being able to trade at the very close that produced the signal.
      </p>
    </div>"""

    honest = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/60">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Disclosures &amp; limitations</h3>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        The universe is today's NIFTY 100 applied backwards, so every absolute CAGR is survivorship-inflated — compare rows with each other, not with an index fund.
        No transaction costs, slippage or taxes are modelled (a regime flip sells and rebuys the whole book, so the switch's real-world cost is higher than a once-a-year rebalance's).
        The window starts in 2009-09 because the 252-day momentum lookback and all 12 calendars must have valid data.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Opens come from the same Yahoo download as the dividend-adjusted closes. A handful of bad prints (missing, zero, or more than 30–40% away from that day's close) were replaced with that day's close.
        Results depend heavily on the rebalance month — a single calendar is an anecdote; use the medians.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        Top 10 with the switch is the best-behaved combination here, but it does not beat the unswitched version in every month: the switch is insurance against deep drawdowns, not a return engine.
        This is a proof-of-concept analysis, not investment advice.
      </p>
    </div>"""

    script = """
<script>
(function(){
  var $=function(i){return document.getElementById(i)};
  function apply(){
    var gold=$('f-gold').checked, plain=$('f-plain').checked, open=$('f-open').checked, close=$('f-close').checked, bench=$('f-bench').checked;
    var ns={5:$('f-n5').checked,10:$('f-n10').checked,20:$('f-n20').checked};
    var cal=document.querySelector('input[name=cal]:checked').value;
    document.querySelectorAll('.cal-block').forEach(function(b){b.style.display=(b.getAttribute('data-cal')===cal)?'':'none'});
    function showSeries(el){
      var n=+el.getAttribute('data-n'), g=el.getAttribute('data-g')==='1', ex=el.getAttribute('data-ex');
      if(ex==='bench') return bench;
      return (g?gold:plain) && (ex==='open'?open:close) && ns[n];
    }
    document.querySelectorAll('[data-s]').forEach(function(el){
      var on=showSeries(el);
      if(el.tagName==='tr'||el.tagName==='TR') el.style.display=on?'':'none';
      else if(el.tagName==='SPAN') el.style.display=on?'':'none';
      else el.style.visibility=on?'visible':'hidden';
    });
    document.querySelectorAll('[data-c]').forEach(function(el){
      var g=el.getAttribute('data-g')==='1', ex=el.getAttribute('data-ex');
      el.style.display=((g?gold:plain)&&(ex==='open'?open:close))?'':'none';
    });
    document.querySelectorAll('tr[data-r]').forEach(function(tr){
      tr.style.display=ns[+tr.getAttribute('data-n')]?'':'none';
    });
  }
  document.querySelectorAll('input').forEach(function(i){i.addEventListener('change',apply)});
  apply();
})();
</script>"""

    style = """
    <style>
      html,body{background:#08171E;color:#E6EDF0;font-family:'Inter',ui-sans-serif,system-ui,-apple-system,sans-serif;}
      .mono{font-family:'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,monospace;}
      table.data-table{width:100%;border-collapse:collapse;font-size:13px;}
      table.data-table th{text-align:right;color:#7E97A0;font-weight:600;padding:8px 12px;border-bottom:1px solid #1E3A45;background:#132B36;font-size:11px;letter-spacing:0.04em;text-transform:uppercase;}
      table.data-table th:first-child, table.data-table td:first-child{text-align:left;}
      table.data-table td{text-align:right;padding:7px 12px;border-bottom:1px solid #16303a;white-space:nowrap;}
      table.data-table tbody tr:nth-child(even) td{background:rgba(255,255,255,0.015);}
      table.data-table tbody tr:hover td{background:rgba(55,240,131,0.06);}
      table.data-table tr.hi td{background:rgba(242,176,60,0.10);}
    </style>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>107 — NIFTY 100 Momentum Yearly, Gold Switch</title>
{TAILWIND_CDN}
{style}
</head>
<body class="min-h-screen">
{header}
{lead}
<div class="px-10">{kpi_grid}{filter_panel}{''.join(chart_blocks)}{kpi_panel}{cal_panel}{method}{honest}<div class="py-6"></div></div>
{script}
</body>
</html>"""


if __name__ == "__main__":
    out = "107_nifty100_momentum_yearly_gold_switch.html"
    html_out = "\n".join(line.rstrip() for line in build().splitlines()) + "\n"
    with open(out, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"wrote {out} ({len(html_out):,} bytes)")

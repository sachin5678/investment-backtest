"""Builds 99_guard_timing_audit.html from results98.json."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results98.json", encoding="utf-8") as f:
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


def pct(v, decimals=1, signed=True):
    if v is None:
        return "—"
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
            f'<div class="flex-1 min-w-[110px]"><div class="text-[11px] text-[#7E97A0] mb-1 uppercase tracking-wide">{esc(col_label)}</div>'
            f'<div class="kpi-val mono" style="color:{color}">{value_str}</div></div>'
        )
    return f"""
    <div class="{PANEL_TIGHT}">
      <div class="text-[13px] font-semibold text-[#E6EDF0] mb-1">{esc(label)}</div>
      <div class="{MUTED} mb-3">{definition}</div>
      <div class="flex gap-3 flex-wrap">{''.join(col_html)}</div>
    </div>
    """


def build():
    r48, pub, fix = R["report48"], R["guard_as_published"], R["guard_corrected"]
    nif, gb = R["nifty"], R["gold_benchmark"]
    a = R["audit"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Timing Audit — the Gold-Strength Guard's +11.5pp That Wasn't</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Reports 91/92 introduced a guard on report 48's hedge leg: during a risk-off period, hold gold only while gold's own ~6-month return beats NIFTY's and is positive — else sit in flat cash. The first release claimed the guard added 11.5–11.9 points of CAGR on every rebalance calendar and cut drawdown to −20.0%. This report recomputes the published logic exactly as it shipped, side by side with the corrected logic, on one identical window, and accounts for every rupee of the difference.</p>
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
          {pill(f'same code, two timings: {a["published_cagr_gain_pp"]:+.2f}pp of CAGR collapses to {a["corrected_cagr_gain_pp"]:+.2f}pp', 'negative')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          The published guard showed CAGR rising from {pct(r48['cagr_pct'])} to {pct(pub['cagr_pct'])} — a terminal multiple of
          <span class="font-semibold">{a['published_terminal_multiple']:.2f}×</span> report 48. Corrected, the same guard produces
          {pct(fix['cagr_pct'])} — <span class="font-semibold">{a['corrected_terminal_multiple']:.2f}×</span>. Roughly all of the
          difference came from two classes of days where the published code used information it could not have had live:
          <span class="font-semibold">flip-off days</span> (whose realized return in report 48 is still stocks — the switch executes
          at that day's close) and <span class="font-semibold">same-day exit checks</span> (flat cash applied to the very close that
          tripped the check).
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          What survives is honest and small: <span class="font-semibold">{pct(fix['cagr_pct'])} vs {pct(r48['cagr_pct'])}
          ({a['corrected_cagr_gain_pp']:+.2f}pp)</span>, with max drawdown improving
          <span class="font-semibold">{a['corrected_dd_gain_pp']:+.2f}pp</span>
          ({pct(r48['max_drawdown_pct'],1,signed=False)} → {pct(fix['max_drawdown_pct'],1,signed=False)}). Reports 91 and 92 now
          publish these corrected numbers; this report is the audit trail.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mt-3">
          One more page carried the same phantom: the earlier findings-round release of this idea (the "Gold-Strength Guard Before
          Switching to Gold" finding, f10) published the identical double-digit gains across Midcap150, Smallcap250 and NIFTY100,
          on the same flawed day-level masks. It has been regenerated with this fix — its Midcap150 top-10 "both checks" variant
          now reads 42.08% CAGR / −22.63% drawdown (report 48's own, same window: 42.01% / −23.42%), versus the 54.80% / −19.95%
          it published at its older data vintage — and across all nine universe/size variants the honest effect runs
          −0.2 to +0.9pp of CAGR with drawdown between 0.8pp better and 1.4pp worse.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR — report 48 vs. the guard, two timings", "Identical window for every series; the guard trade is the only difference.",
                  [("Report 48 (no guard)", pct(r48["cagr_pct"]), "neutral"),
                   ("Guard, as published", pct(pub["cagr_pct"]), "negative"),
                   ("Guard, corrected", pct(fix["cagr_pct"]), "positive")]),
        kpi_card("Max drawdown — same three series", "Largest peak-to-trough decline; the published −20.0% was itself a product of the same artifact.",
                  [("Report 48 (no guard)", pct(r48["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Guard, as published", pct(pub["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Guard, corrected", pct(fix["max_drawdown_pct"], 1, signed=False), "positive")]),
        kpi_card("Terminal multiple vs. report 48 — the arithmetic", "Growth-of-100 end values, ratioed. The published multiple factorizes exactly into the two artifact classes.",
                  [("As published", f"{a['published_terminal_multiple']:.2f}×", "negative"),
                   ("Corrected", f"{a['corrected_terminal_multiple']:.2f}×", "positive"),
                   ("= fail-side × boundary", f"{a['fail_side_multiple']:.2f}× · {a['substitution_multiple']:.2f}×", "assumption")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-1 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, v, cls=""):
        c = f' class="{cls}"' if cls else ""
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(v['net_return_pct'])}</td><td>{pct(v['cagr_pct'])}</td>
        <td>{pct(v['max_drawdown_pct'],1,signed=False)}</td><td>{v['longest_underwater_days']:,}d</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">All five series, side by side</h3>
        {pill('grey rows = real benchmarks, not reconstructions', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every series over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window. The published guard's numbers are what reports 91/92 originally showed; the corrected row is what they show now.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("200-EMA regime filter + gold (report 48)", r48)}
          {row("+ gold-strength guard, AS PUBLISHED (timing bug)", pub, "mostly-flat")}
          {row("+ gold-strength guard, CORRECTED", fix)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
          {row("GOLDBEES.NS, buy & hold (real ETF)", gb, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "Report 48 (gold, no guard)", "color": COL["muted"], "points": r48["equity_curve"]},
        {"name": "Guard, as published (buggy)", "color": COL["negative"], "points": pub["equity_curve"]},
        {"name": "Guard, corrected", "color": COL["positive"], "points": fix["equity_curve"]},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_99")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — the phantom curve</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the red line is what the buggy code was measuring: a portfolio that retroactively sidesteps equity crash days. The green line is the same guard with honest timing — barely distinguishable from report 48 (grey).</p>
      <div class="flex items-center mb-2">{eq_legend}</div>
      {eq_svg}
    </div>
    """

    def dd_points(equity):
        out, peak = [], None
        for d, v in equity:
            peak = v if peak is None else max(peak, v)
            out.append([d, (v / peak - 1.0) * 100.0])
        return out

    dd_series = [
        {"name": "Report 48 (gold, no guard)", "color": COL["muted"], "points": dd_points(r48["equity_curve"])},
        {"name": "Guard, as published (buggy)", "color": COL["negative"], "points": dd_points(pub["equity_curve"])},
        {"name": "Guard, corrected", "color": COL["positive"], "points": dd_points(fix["equity_curve"])},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=240, chart_id="dd_99")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the published guard's shallower troughs are the artifact at work; the corrected guard trims drawdown by {a['corrected_dd_gain_pp']:.2f}pp, not 2.4pp.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    def sign_cls(v):
        return "pos" if v > 0 else ("neg" if v < 0 else "mut")

    boundary_rows = []
    for b in a["worst_boundary_days"]:
        charged_cls = "neg" if b["published_charged_pct"] > b["r48_pct"] else "amb"
        boundary_rows.append(
            f"""<tr><td class="mono">{esc(b['date'])}</td><td class="mono {sign_cls(b['r48_pct'])}">{b['r48_pct']:+.3f}%</td>
            <td class="mono {sign_cls(b['gold_pct'])}">{b['gold_pct']:+.3f}%</td>
            <td class="mono {charged_cls}">{b['published_charged_pct']:+.3f}%</td></tr>"""
        )

    mech1 = f"""
    <div class="{PANEL} mt-6 border-[#F2643C]/40">
      <div class="flex items-center gap-2 mb-2">
        <h3 class="text-base font-bold text-[#E6EDF0]">Mechanism 1 — the flip-off day ({a['flipoff_boundary_days']} days)</h3>
        {pill('the artifact', 'negative')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — report 48 flips to the hedge at a day's CLOSE, so that day's realized return is still 100% stocks. The published guard treated it as a 'cash' day and charged it gold's return ({a['flipoff_pass_days']} days) or flat cash ({a['flipoff_fail_days']} days) — erasing, on average, most of that day's move. Worst 12 shown.</p>
      <table class="data-table">
        <thead><tr><th>Date</th><th>Report 48 realized</th><th>Gold that day</th><th>Published charged</th></tr></thead>
        <tbody>{''.join(boundary_rows)}</tbody>
      </table>
      <p class="text-[13px] text-[#C9D6DA] leading-relaxed mt-3">
        2015-08-24 (the China-devaluation crash) and 2022-02-24 (the invasion) are the extremes: −11.3% and −6.2% days that the
        published code refunded in gold. The artifact is not a one-way gift, either — on 2026-02-02 gold itself fell −9.5% and
        the published version charged that bigger loss to a day the portfolio was in stocks — it is simply wrong on every one of
        these days, in whichever direction suits the trade the code wished it had made.
      </p>
    </div>
    """

    fail_entry_rows = []
    for b in a["worst_fail_entry_days"]:
        fail_entry_rows.append(
            f"""<tr><td class="mono">{esc(b['date'])}</td><td class="mono {sign_cls(b['r48_pct'])}">{b['r48_pct']:+.3f}%</td></tr>"""
        )

    mech2 = f"""
    <div class="{PANEL} mt-6 border-[#F2643C]/40">
      <div class="flex items-center gap-2 mb-2">
        <h3 class="text-base font-bold text-[#E6EDF0]">Mechanism 2 — same-day exit checks ({a['fail_entry_lookahead_days']} days)</h3>
        {pill('smaller, same disease', 'assumption')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the published exit rule sat in flat cash on any day whose own close tripped the gold checks: the guard left gold on the very day the going got bad, using that day's close to decide, and its position for that day. On the correct prior-close clock, the day that trips the check is borne first — the exit only protects the days after it. Worst 10 of these days shown.</p>
      <table class="data-table">
        <thead><tr><th>Date</th><th>Report 48 realized (gold side)</th></tr></thead>
        <tbody>{''.join(fail_entry_rows)}</tbody>
      </table>
    </div>
    """

    arith = f"""
    <div class="{PANEL} mt-6 border-[#6AE4FF]/40">
      <div class="flex items-center gap-2 mb-2">
        <h3 class="text-base font-bold text-[#E6EDF0]">The arithmetic — every rupee accounted for</h3>
        {pill('reconciliation', 'assumption')}
      </div>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-4">
        The two mechanisms touch disjoint sets of days, so their effects multiply:
        <span class="mono">{a['fail_side_multiple']:.2f}×</span> (zeroing same-day-detected fail days — the "small" half) ×
        <span class="mono">{a['substitution_multiple']:.2f}×</span> (resubstituting boundary and transition days with gold) =
        <span class="mono font-semibold">{a['published_terminal_multiple']:.2f}×</span> — exactly the published terminal multiple.
        With both corrected, the guard's multiple over report 48 is <span class="mono font-semibold">{a['corrected_terminal_multiple']:.2f}×</span>.
        Over a {esc(R['start_date'])}–{esc(R['end_date'])} window, a {a['published_terminal_multiple']:.2f}× head start compounds to
        the {a['published_cagr_gain_pp']:+.2f}pp of CAGR that was published; {a['corrected_terminal_multiple']:.2f}× compounds to
        {a['corrected_cagr_gain_pp']:+.2f}pp.
      </p>
    </div>
    """

    lessons = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2">
        <h3 class="text-base font-bold text-[#E6EDF0]">Limitations & the general lesson</h3>
        {pill("read before trusting any number above", "assumption")}
      </div>
      <ul class="text-[13px] text-[#C9D6DA] list-disc pl-5 leading-relaxed">
        <li class="mb-1.5">The corrected guard itself is not "proven good": +{a['corrected_cagr_gain_pp']:.2f}pp of CAGR is inside
        any plausible cost band, and −{abs(a['corrected_dd_gain_pp']):.2f}pp of drawdown is a trim, not a transformation. Reports
        91/92 now present it that way.</li>
        <li class="mb-1.5">The rule this audit enforces project-wide: strategies that act at a day's close must be evaluated on
        PRIOR-close information — a day's realized return belongs to the state decided at the previous close. Any day-level
        substitution (hedge swaps, exit checks, recovery dodges) is exactly where this class of bug hides, and aggregate metrics
        cannot see it — crash-day tables are the only way.</li>
        <li class="mb-1.5">Zero transaction costs throughout, matching reports 91/92's own convention; the guard adds few extra
        switch events (~{R['audit']['days_zeroed_corrected']} flat days across 21-odd regime blocks), so costs do not change the
        audit's conclusions about the artifact.</li>
        <li class="mb-1.5">Same reconstruction caveats as everywhere in this project: today's fixed Midcap150 constituent list
        applied retroactively (survivorship bias), equal weighting, unadjusted prices, no dividends.</li>
      </ul>
    </div>
    """

    body = f"""
    {header}
    {lead}
    <div class="px-10 py-6">
      {kpi_grid}
      {full_table}
      {eq_panel}
      {dd_panel}
      {mech1}
      {mech2}
      {arith}
      {lessons}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Timing Audit — Gold-Strength Guard (Report 99)</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("99_guard_timing_audit.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 99_guard_timing_audit.html")

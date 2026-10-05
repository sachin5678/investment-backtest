"""Builds 92_midcap150_gold_strength_guard_calendars.html from results91.json."""
import json
import html

with open("results91.json") as f:
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


def pp(v):
    s = "+" if v > 0 else ""
    return f"{s}{v:.2f}pp"


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
      tr.anchor-cal td{color:#6AE4FF;}
      .kpi-val{font-size:24px;font-weight:700;letter-spacing:-0.01em;}
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
    rows = R["by_calendar"]
    span, lookback = R["ema_span"], R["gold_lookback_days"]
    cagr_diffs = [r["cagr_diff_pp"] for r in rows]
    dd_diffs = [r["dd_diff_pp"] for r in rows]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Gold-Strength Guard — Does It Hold Up on Every Rebalance Calendar?</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Report 91 tested the gold-strength guard only on June/December, report 48's own calendar. Report 85 already asked whether the rebalance-month offset matters for report 48 itself; this asks the same question for report 91's guard — all six semi-annual calendars (Jun/Dec, Jul/Jan, Aug/Feb, Sep/Mar, Oct/Apr, Nov/May), same {span}-day EMA regime filter, same guard mechanism (gold's own {lookback}-day return must beat NIFTY's AND be positive, else flat cash) reused exactly as backtest91.py built it — nothing reimplemented.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(R['start_date'])}–{esc(R['end_date'])}<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#37F083]">
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          {pill(f'Every calendar gains {min(cagr_diffs):.1f} to {max(cagr_diffs):.1f}pp of CAGR, every one ends at -20.0% max drawdown', 'positive')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          Report 91's result was not a June/December artifact. The guard improves CAGR on all six calendars by a tight,
          consistent band — {min(cagr_diffs):+.2f}pp to {max(cagr_diffs):+.2f}pp — and drawdown lands at exactly -20.0%
          regardless of which months the stock picks refresh in, suggesting the same single structural episode (not the
          calendar choice) sets the floor on how deep this design can draw down with the guard active.
        </p>
      </div>
    </div>
    """

    def row(r, is_anchor):
        s, g = r["report48_standard"], r["gold_strength_guard"]
        cls = ' class="anchor-cal"' if is_anchor else ""
        anchor_note = " (report 91's own calendar)" if is_anchor else ""
        return f"""<tr{cls}><td>{esc(r['calendar_label'])}{anchor_note}</td>
        <td>{pct(s['cagr_pct'])}</td><td>{pct(s['max_drawdown_pct'],1,signed=False)}</td>
        <td>{pct(g['cagr_pct'])}</td><td>{pct(g['max_drawdown_pct'],1,signed=False)}</td>
        <td>{pp(r['cagr_diff_pp'])}</td><td>{pp(r['dd_diff_pp'])}</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">All six calendars, report 48 vs. the guard</h3>
        {pill("cyan row = report 91's own calendar", "neutral")}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every calendar over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window (narrower than report 91's own single-calendar window, since this is the overlap across all six calendars at once).</p>
      <table class="data-table">
        <thead><tr><th>Calendar</th><th>R48 CAGR</th><th>R48 DD</th><th>Guard CAGR</th><th>Guard DD</th><th>CAGR Δ</th><th>DD Δ</th></tr></thead>
        <tbody>{''.join(row(r, r['calendar_label'] == 'Jun/Dec') for r in rows)}</tbody>
      </table>
    </div>
    """

    kpis = [
        kpi_card("CAGR improvement range across all six calendars", "The guard's CAGR gain over report 48, min to max across every calendar tested.",
                  [("Smallest gain", pp(min(cagr_diffs)), "positive"), ("Largest gain", pp(max(cagr_diffs)), "positive")]),
        kpi_card("Drawdown improvement range across all six calendars", "The guard's drawdown improvement over report 48 (positive = shallower), min to max.",
                  [("Smallest improvement", pp(min(dd_diffs)), "positive"), ("Largest improvement", pp(max(dd_diffs)), "positive")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">{"".join(kpis)}</div>'

    limitations = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2">
        <h3 class="text-base font-bold text-[#E6EDF0]">Limitations</h3>
        {pill("read before trusting any number above", "assumption")}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every simplification behind this backtest.</p>
      <ul class="text-[13px] text-[#C9D6DA] list-disc pl-5 leading-relaxed">
        <li class="mb-1.5">Same limitations as report 91 apply to every calendar here: zero transaction costs on the
        guard's extra gold↔cash switches, the 126-day lookback wasn't tuned or compared against alternatives, and flat
        cash earns literally 0% rather than a liquid-fund yield.</li>
        <li class="mb-1.5">This report's window (2009-02-27 onward) is narrower than report 91's own single-calendar
        window (2009-01-02 onward) because it's restricted to the overlap across all six calendars' own first-valid-
        rebalance dates at once — same convention report 85 used for report 48 itself.</li>
        <li class="mb-1.5">Today's fixed Midcap150 constituent list is applied retroactively across the whole window
        (survivorship bias). Equal weighting, no F&O-eligibility screen, unadjusted prices, no dividends modeled — same
        as every other reconstruction here.</li>
      </ul>
    </div>
    """

    body = f"""
    {header}
    {lead_disclosure}
    <div class="px-10 py-6">
      {kpi_grid}
      {full_table}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Gold-Strength Guard — Calendar Sensitivity</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("92_midcap150_gold_strength_guard_calendars.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 92_midcap150_gold_strength_guard_calendars.html")

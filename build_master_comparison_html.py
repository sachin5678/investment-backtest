"""
Builds master_comparison.html — a single, dedicated page presenting every
momentum-strategy variant tested across reports 11/12 and 33-70 in one
sortable, filterable table: CAGR, max drawdown, Sharpe, and Sortino,
each shown against that row's own NIFTY 50 benchmark on the identical
window. No charts — pure table, designed to answer "which combination
and logic wins, at a glance" the way every other page here answers a
narrower question with prose and charts.

Data comes from master_comparison.json (built by build_master_comparison.py,
which recomputes each variant's own full daily equity series rather than
reusing any report's downsampled chart data, so Sharpe/Sortino here are
computed correctly from true daily returns).
"""
import json
import html

with open("master_comparison.json") as f:
    R = json.load(f)

ROWS = R["rows"]
CATEGORIES = ["Baseline", "Weighting", "Regime Filter", "Filter + Hedge", "Trend Filter",
              "Stop-Loss", "Momentum Formula", "Exposure Scaling"]
UNIVERSES = ["Midcap150", "Smallcap250", "NIFTY100", "NIFTY500"]

CAT_COLOR = {
    "Baseline": "#7E97A0", "Weighting": "#6AE4FF", "Regime Filter": "#37F083",
    "Filter + Hedge": "#F2B03C", "Trend Filter": "#8B5CF6", "Stop-Loss": "#F2643C",
    "Momentum Formula": "#6AE4FF", "Exposure Scaling": "#37F083",
}


def esc(s):
    return html.escape(str(s))


def pct(v, decimals=1, signed=True):
    if v is None:
        return "—"
    s = "+" if (signed and v > 0) else ""
    return f"{s}{v:,.{decimals}f}%"


def ratio(v):
    if v is None:
        return "—"
    return f"{v:.2f}"


def metric_cell(value, bench, fmt_fn, higher_is_better=True):
    if value is None:
        return '<td class="metric-cell"><span class="metric-primary muted-val">—</span></td>'
    win = None
    if bench is not None:
        win = (value > bench) if higher_is_better else (value < bench)
    cls = "win" if win is True else ("lose" if win is False else "")
    bench_str = fmt_fn(bench) if bench is not None else "—"
    return (f'<td class="metric-cell"><span class="metric-primary {cls}">{fmt_fn(value)}</span>'
            f'<span class="metric-bench">vs {bench_str}</span></td>')


def build_row(r):
    cat_color = CAT_COLOR.get(r["category"], "#7E97A0")
    return f"""
    <tr data-universe="{esc(r['universe'])}" data-category="{esc(r['category'])}"
        data-cagr="{r['cagr_pct'] if r['cagr_pct'] is not None else ''}"
        data-dd="{r['max_drawdown_pct'] if r['max_drawdown_pct'] is not None else ''}"
        data-sharpe="{r['sharpe'] if r['sharpe'] is not None else ''}"
        data-sortino="{r['sortino'] if r['sortino'] is not None else ''}"
        data-report="{r['report']}">
      <td class="label-cell">
        <div class="universe-tag">{esc(r['universe'])}</div>
        <div class="strategy-label">{esc(r['label'])}</div>
        <div class="category-tag" style="color:{cat_color};border-color:{cat_color}44;background:{cat_color}14">{esc(r['category'])}</div>
      </td>
      <td class="window-cell">{esc(r['start_date'])}<span class="arrow">→</span>{esc(r['end_date'])}<div class="report-ref">Report {r['report']}</div></td>
      {metric_cell(r['cagr_pct'], r['bench_cagr_pct'], lambda v: pct(v), True)}
      {metric_cell(r['max_drawdown_pct'], r['bench_max_drawdown_pct'], lambda v: pct(v, 1, False), True)}
      {metric_cell(r['sharpe'], r['bench_sharpe'], ratio, True)}
      {metric_cell(r['sortino'], r['bench_sortino'], ratio, True)}
    </tr>"""


def build():
    rows_html = "\n".join(build_row(r) for r in ROWS)
    universe_pills = "".join(
        f'<button class="filter-pill" data-filter-type="universe" data-filter-value="{esc(u)}">{esc(u)}</button>'
        for u in UNIVERSES)
    category_pills = "".join(
        f'<button class="filter-pill" data-filter-type="category" data-filter-value="{esc(c)}" style="--pill-color:{CAT_COLOR[c]}">{esc(c)}</button>'
        for c in CATEGORIES)

    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"/>
<title>Momentum Strategy Lab — Master Comparison</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {{
    --ground:#08171E; --panel:#0F2630; --panel-2:#132B36; --border:#1E3A45;
    --positive:#37F083; --negative:#F2643C; --assumption:#F2B03C; --accent:#6AE4FF;
    --text:#E6EDF0; --muted:#7E97A0; --muted-2:#9FB4BB;
  }}
  * {{ box-sizing: border-box; }}
  html,body {{
    background:var(--ground); color:var(--text); margin:0; padding:0;
    font-family:'Inter',ui-sans-serif,system-ui,-apple-system,sans-serif;
    -webkit-font-smoothing:antialiased;
  }}
  .mono {{ font-family:'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,monospace; }}
  a {{ color:var(--accent); }}

  header.top {{
    border-bottom:1px solid var(--border); background:rgba(15,38,48,0.6);
    padding:28px 40px 24px; position:sticky; top:0; z-index:30; backdrop-filter:blur(6px);
  }}
  .top-row {{ display:flex; align-items:flex-start; justify-content:space-between; gap:24px; flex-wrap:wrap; }}
  h1 {{ font-size:22px; font-weight:800; margin:0 0 6px; letter-spacing:-0.01em; }}
  .subtitle {{ color:var(--muted-2); font-size:13.5px; line-height:1.5; max-width:760px; margin:0; }}
  .back-link {{ font-size:12.5px; color:var(--muted); text-decoration:none; white-space:nowrap; }}
  .back-link:hover {{ color:var(--accent); }}

  .controls {{ margin-top:18px; display:flex; flex-direction:column; gap:10px; }}
  .filter-row {{ display:flex; align-items:center; gap:8px; flex-wrap:wrap; }}
  .filter-row-label {{ font-size:10.5px; text-transform:uppercase; letter-spacing:0.06em; color:var(--muted); width:64px; flex-shrink:0; }}
  .filter-pill {{
    font-family:inherit; font-size:12px; font-weight:600; padding:5px 12px; border-radius:999px;
    background:transparent; border:1px solid var(--border); color:var(--muted-2); cursor:pointer;
    transition:all 120ms ease; white-space:nowrap;
  }}
  .filter-pill:hover {{ border-color:var(--muted-2); color:var(--text); }}
  .filter-pill.active {{
    background:var(--pill-color, var(--accent)); border-color:var(--pill-color, var(--accent));
    color:#08171E;
  }}
  .filter-pill[data-filter-type="universe"].active {{ background:var(--accent); border-color:var(--accent); }}
  .status-row {{ display:flex; align-items:center; gap:14px; font-size:12px; color:var(--muted); margin-top:4px; }}
  .reset-link {{ background:none; border:none; color:var(--accent); font-size:12px; font-family:inherit; cursor:pointer; padding:0; }}
  .reset-link:hover {{ text-decoration:underline; }}

  main {{ padding:24px 40px 60px; }}
  .table-wrap {{
    background:var(--panel); border:1px solid var(--border); border-radius:16px;
    overflow:auto; max-height:calc(100vh - 260px);
  }}
  table {{ width:100%; border-collapse:collapse; font-size:13px; min-width:920px; }}
  thead th {{
    position:sticky; top:0; background:var(--panel-2); z-index:5;
    text-align:left; font-size:10.5px; text-transform:uppercase; letter-spacing:0.05em;
    color:var(--muted); font-weight:700; padding:12px 16px; border-bottom:1px solid var(--border);
    cursor:pointer; user-select:none; white-space:nowrap;
  }}
  thead th:hover {{ color:var(--text); }}
  thead th.sorted {{ color:var(--accent); }}
  thead th .sort-arrow {{ display:inline-block; margin-left:4px; opacity:0.5; font-size:10px; }}
  thead th.sorted .sort-arrow {{ opacity:1; }}
  thead th.metric-head {{ text-align:right; }}

  tbody tr {{ border-bottom:1px solid #16303a; transition:background-color 120ms ease; }}
  tbody tr:nth-child(even) {{ background:rgba(255,255,255,0.015); }}
  tbody tr:hover {{ background:rgba(55,240,131,0.05); }}
  tbody tr.hidden {{ display:none; }}
  td {{ padding:10px 16px; vertical-align:top; }}

  .label-cell {{ min-width:230px; }}
  .universe-tag {{ font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.05em; color:var(--accent); margin-bottom:2px; }}
  .strategy-label {{ font-size:13.5px; font-weight:600; color:var(--text); line-height:1.3; margin-bottom:5px; }}
  .category-tag {{
    display:inline-block; font-size:10.5px; font-weight:600; padding:2px 8px; border-radius:999px;
    border:1px solid; white-space:nowrap;
  }}

  .window-cell {{ font-family:'JetBrains Mono',monospace; font-size:11px; color:var(--muted); white-space:nowrap; min-width:150px; }}
  .window-cell .arrow {{ margin:0 4px; opacity:0.5; }}
  .report-ref {{ font-size:10px; color:#5b7079; margin-top:3px; }}

  .metric-cell {{ text-align:right; min-width:108px; }}
  .metric-primary {{
    display:block; font-family:'JetBrains Mono',monospace; font-size:14.5px; font-weight:700;
    letter-spacing:-0.01em; color:var(--text);
  }}
  .metric-primary.win {{ color:var(--positive); }}
  .metric-primary.lose {{ color:var(--negative); }}
  .metric-primary.muted-val {{ color:var(--muted); font-weight:500; }}
  .metric-bench {{
    display:block; font-family:'JetBrains Mono',monospace; font-size:10.5px; color:var(--muted);
    margin-top:1px;
  }}

  .legend {{
    display:flex; align-items:center; gap:18px; flex-wrap:wrap; margin:14px 0 0;
    font-size:11.5px; color:var(--muted-2);
  }}
  .legend-item {{ display:flex; align-items:center; gap:6px; }}
  .legend-swatch {{ width:9px; height:9px; border-radius:3px; }}

  footer {{ padding:20px 40px 40px; color:var(--muted); font-size:12px; line-height:1.6; }}
  footer a {{ color:var(--muted-2); }}

  @media (max-width: 860px) {{
    header.top, main, footer {{ padding-left:18px; padding-right:18px; }}
    .filter-row-label {{ width:auto; }}
  }}
</style>
</head>
<body>

<header class="top">
  <div class="top-row">
    <div>
      <h1>Momentum Strategy Lab — Master Comparison</h1>
      <p class="subtitle">Every momentum-strategy variant tested across this project's front-loaded weighting,
      inverse-vol weighting, 200-EMA regime filter, gold/liquid-fund hedges, universe-specific trend filters,
      trailing stops, absolute momentum gates, and smooth exposure scaling — {len(ROWS)} rows across
      {len(UNIVERSES)} universes, each measured against NIFTY 50 on its own identical window. No charts here —
      sort or filter to find what actually worked.</p>
    </div>
    <a class="back-link" href="dashboard.html">← Back to all reports</a>
  </div>
  <div class="controls">
    <div class="filter-row">
      <span class="filter-row-label">Universe</span>
      {universe_pills}
    </div>
    <div class="filter-row">
      <span class="filter-row-label">Idea</span>
      {category_pills}
    </div>
    <div class="status-row">
      <span id="rowCount">{len(ROWS)} of {len(ROWS)} rows</span>
      <button class="reset-link" id="resetBtn">Reset filters</button>
    </div>
  </div>
</header>

<main>
  <div class="table-wrap">
    <table id="cmpTable">
      <thead>
        <tr>
          <th data-sort="label">Strategy</th>
          <th data-sort="window">Window</th>
          <th class="metric-head" data-sort="cagr">CAGR <span class="sort-arrow">▾</span></th>
          <th class="metric-head" data-sort="dd">Max drawdown</th>
          <th class="metric-head" data-sort="sharpe">Sharpe</th>
          <th class="metric-head" data-sort="sortino">Sortino</th>
        </tr>
      </thead>
      <tbody id="cmpBody">
        {rows_html}
      </tbody>
    </table>
  </div>
  <div class="legend">
    <div class="legend-item"><span class="legend-swatch" style="background:var(--positive)"></span> beats NIFTY 50 on that metric</div>
    <div class="legend-item"><span class="legend-swatch" style="background:var(--negative)"></span> trails NIFTY 50 on that metric</div>
    <div class="legend-item">Small "vs X%" caption under each number is NIFTY 50's own value over the identical window.</div>
  </div>
</main>

<footer>
  Sharpe and Sortino assume a 0% risk-free rate (same simplification as every "cash earns 0%" convention used
  elsewhere in this project) and are computed from each variant's true daily equity series, not the downsampled
  chart data individual reports embed — see <a href="build_master_comparison.py">build_master_comparison.py</a>
  for the exact reconstruction of every row. Every row links back to its full report via the "Report N" reference
  in the Window column; open <a href="dashboard.html">dashboard.html</a> to read the full disclosure, honesty
  note, and limitations behind any number here.
</footer>

<script>
const ROWS_META = {json.dumps([{"universe": r["universe"], "category": r["category"]} for r in ROWS])};
const activeFilters = {{ universe: null, category: null }};
let sortState = {{ key: "cagr", dir: "desc" }};

function getRows() {{ return Array.from(document.querySelectorAll("#cmpBody tr")); }}

function applyFilters() {{
  const rows = getRows();
  let visible = 0;
  rows.forEach(tr => {{
    const u = tr.dataset.universe, c = tr.dataset.category;
    const show = (!activeFilters.universe || u === activeFilters.universe) &&
                 (!activeFilters.category || c === activeFilters.category);
    tr.classList.toggle("hidden", !show);
    if (show) visible++;
  }});
  document.getElementById("rowCount").textContent = visible + " of " + rows.length + " rows";
}}

function applySort() {{
  const tbody = document.getElementById("cmpBody");
  const rows = getRows();
  const key = sortState.key, dir = sortState.dir;
  const dataKey = {{ cagr: "cagr", dd: "dd", sharpe: "sharpe", sortino: "sortino" }}[key];
  rows.sort((a, b) => {{
    let av, bv;
    if (key === "label") {{
      av = a.querySelector(".strategy-label").textContent.toLowerCase();
      bv = b.querySelector(".strategy-label").textContent.toLowerCase();
      return dir === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
    }}
    if (key === "window") {{
      av = a.dataset.report; bv = b.dataset.report;
      return dir === "asc" ? (av - bv) : (bv - av);
    }}
    av = parseFloat(a.dataset[dataKey]); bv = parseFloat(b.dataset[dataKey]);
    if (isNaN(av)) av = -Infinity; if (isNaN(bv)) bv = -Infinity;
    return dir === "asc" ? (av - bv) : (bv - av);
  }});
  rows.forEach(tr => tbody.appendChild(tr));

  document.querySelectorAll("thead th").forEach(th => {{
    th.classList.toggle("sorted", th.dataset.sort === key);
    const arrow = th.querySelector(".sort-arrow");
    if (th.dataset.sort === key) {{
      if (!arrow) {{
        const span = document.createElement("span");
        span.className = "sort-arrow";
        th.appendChild(span);
      }}
      th.querySelector(".sort-arrow").textContent = dir === "asc" ? "▴" : "▾";
    }} else if (arrow) {{
      arrow.textContent = "▾";
    }}
  }});
}}

document.querySelectorAll(".filter-pill").forEach(btn => {{
  btn.addEventListener("click", () => {{
    const type = btn.dataset.filterType, value = btn.dataset.filterValue;
    const isActive = activeFilters[type] === value;
    document.querySelectorAll(`.filter-pill[data-filter-type="${{type}}"]`).forEach(b => b.classList.remove("active"));
    activeFilters[type] = isActive ? null : value;
    if (!isActive) btn.classList.add("active");
    applyFilters();
  }});
}});

document.getElementById("resetBtn").addEventListener("click", () => {{
  activeFilters.universe = null; activeFilters.category = null;
  document.querySelectorAll(".filter-pill").forEach(b => b.classList.remove("active"));
  applyFilters();
}});

document.querySelectorAll("thead th[data-sort]").forEach(th => {{
  th.addEventListener("click", () => {{
    const key = th.dataset.sort;
    if (sortState.key === key) {{
      sortState.dir = sortState.dir === "asc" ? "desc" : "asc";
    }} else {{
      sortState.key = key;
      // desc puts the "best" value first for every metric here: DD is
      // stored as a negative number, so descending (least negative /
      // shallowest first) is "best first", same as CAGR/Sharpe/Sortino.
      sortState.dir = "desc";
    }}
    applySort();
  }});
}});

applySort();
</script>

</body></html>"""


if __name__ == "__main__":
    with open("master_comparison.html", "w", encoding="utf-8") as f:
        f.write(build())
    print(f"Wrote master_comparison.html with {len(ROWS)} rows")

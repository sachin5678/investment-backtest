"""Hand-rolled inline SVG chart helpers — no chart library, just path/line/text elements."""
import datetime as dt

COL = {
    "ground": "#08171E",
    "panel": "#0F2630",
    "border": "#1E3A45",
    "positive": "#37F083",
    "assumption": "#F2B03C",
    "negative": "#F2643C",
    "text": "#E6EDF0",
    "muted": "#7E97A0",
}


def _parse(d):
    return dt.datetime.strptime(d, "%Y-%m-%d")


def _fmt_num(v, decimals=0):
    return f"{v:,.{decimals}f}"


def catmull_rom_path(pts):
    """Build a smooth SVG path (cubic Beziers) that passes exactly through every
    (x, y) pixel point in `pts`, using a standard Catmull-Rom-to-Bezier
    conversion. Unlike a moving average, this never alters the real values —
    it only softens the straight-line segments between them into curves."""
    if len(pts) < 3:
        return "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    p = [pts[0]] + list(pts) + [pts[-1]]
    d = [f"M {p[1][0]:.1f},{p[1][1]:.1f}"]
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        c1x = p1[0] + (p2[0] - p0[0]) / 6.0
        c1y = p1[1] + (p2[1] - p0[1]) / 6.0
        c2x = p2[0] - (p3[0] - p1[0]) / 6.0
        c2y = p2[1] - (p3[1] - p1[1]) / 6.0
        d.append(f"C {c1x:.1f},{c1y:.1f} {c2x:.1f},{c2y:.1f} {p2[0]:.1f},{p2[1]:.1f}")
    return " ".join(d)


def _nice_ticks(lo, hi, n=5):
    if hi <= lo:
        hi = lo + 1
    span = hi - lo
    raw_step = span / n
    mag = 10 ** (len(str(int(raw_step))) - 1) if raw_step >= 1 else 1
    for m in (1, 2, 2.5, 5, 10):
        step = m * mag
        if step >= raw_step:
            break
    ticks = []
    v = lo - (lo % step) if lo % step != 0 else lo
    while v <= hi + step:
        ticks.append(v)
        v += step
    return [t for t in ticks if lo - step <= t <= hi + step]


def line_chart(series, width=1180, height=360, y_label="", x_is_dates=True,
               force_zero=True, value_fmt=None, y_prefix="", y_suffix="",
               chart_id="chart", smooth=True):
    """
    series: list of {"name": str, "color": "#hex", "points": [[date_str_or_x, value], ...], "dash": bool}
    Renders a zero-based (unless force_zero=False) line chart as inline SVG —
    straight segments, or a Catmull-Rom smooth curve through the same real
    points if smooth=True. Returns an <svg>...</svg> string plus an HTML legend.
    """
    margin = {"top": 24, "right": 24, "bottom": 40, "left": 88}
    plot_w = width - margin["left"] - margin["right"]
    plot_h = height - margin["top"] - margin["bottom"]

    all_vals = [p[1] for s in series for p in s["points"]]
    if x_is_dates:
        all_x = [_parse(p[0]) for s in series for p in s["points"]]
        x_min, x_max = min(all_x), max(all_x)
        x_span = (x_max - x_min).days or 1
    else:
        all_x = [p[0] for s in series for p in s["points"]]
        x_min, x_max = min(all_x), max(all_x)
        x_span = (x_max - x_min) or 1

    y_min_data, y_max_data = min(all_vals), max(all_vals)
    y_min = 0.0 if force_zero else y_min_data
    y_max = y_max_data * 1.08 if y_max_data > 0 else y_max_data * 0.92
    if y_max == y_min:
        y_max = y_min + 1

    def xs(x):
        xv = (x - x_min).days if x_is_dates else (x - x_min)
        return margin["left"] + (xv / x_span) * plot_w

    def ys(y):
        return margin["top"] + plot_h - ((y - y_min) / (y_max - y_min)) * plot_h

    ticks = _nice_ticks(y_min, y_max, 5)

    svg = [f'<svg viewBox="0 0 {width} {height}" class="w-full h-auto" role="img" aria-label="line chart" id="{chart_id}">']
    svg.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="{COL["panel"]}"/>')

    # gridlines + y labels
    for t in ticks:
        y = ys(t)
        svg.append(f'<line x1="{margin["left"]}" y1="{y:.1f}" x2="{width-margin["right"]}" y2="{y:.1f}" '
                    f'stroke="{COL["border"]}" stroke-width="1" stroke-dasharray="2,3"/>')
        label = value_fmt(t) if value_fmt else _fmt_num(t)
        svg.append(f'<text x="{margin["left"]-10}" y="{y+4:.1f}" text-anchor="end" font-size="12" '
                    f'fill="{COL["muted"]}" font-family="monospace">{y_prefix}{label}{y_suffix}</text>')

    # zero baseline emphasis if within range
    if y_min <= 0 <= y_max:
        y0 = ys(0)
        svg.append(f'<line x1="{margin["left"]}" y1="{y0:.1f}" x2="{width-margin["right"]}" y2="{y0:.1f}" '
                    f'stroke="{COL["muted"]}" stroke-width="1"/>')

    # x axis ticks (first, middle, last dates)
    if x_is_dates:
        tick_dates = [x_min, x_min + (x_max - x_min) / 4, x_min + (x_max - x_min) / 2,
                      x_min + 3 * (x_max - x_min) / 4, x_max]
        for td in tick_dates:
            x = xs(td)
            svg.append(f'<text x="{x:.1f}" y="{height-margin["bottom"]+20}" text-anchor="middle" '
                        f'font-size="12" fill="{COL["muted"]}" font-family="monospace">{td.strftime("%Y-%m")}</text>')

    # axis frame
    svg.append(f'<line x1="{margin["left"]}" y1="{margin["top"]}" x2="{margin["left"]}" '
                f'y2="{height-margin["bottom"]}" stroke="{COL["border"]}" stroke-width="1"/>')
    svg.append(f'<line x1="{margin["left"]}" y1="{height-margin["bottom"]}" x2="{width-margin["right"]}" '
                f'y2="{height-margin["bottom"]}" stroke="{COL["border"]}" stroke-width="1"/>')

    legend_html = []
    for s in series:
        pts = s["points"]
        px_pts = []
        for p in pts:
            x = xs(_parse(p[0])) if x_is_dates else xs(p[0])
            y = ys(p[1])
            px_pts.append((x, y))
        path_d = catmull_rom_path(px_pts) if smooth else "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in px_pts)
        dash = ' stroke-dasharray="6,4"' if s.get("dash") else ""
        svg.append(f'<path d="{path_d}" fill="none" stroke="{s["color"]}" stroke-width="2"{dash} '
                    f'stroke-linejoin="round" stroke-linecap="round"/>')
        last = pts[-1]
        lx = xs(_parse(last[0])) if x_is_dates else xs(last[0])
        ly = ys(last[1])
        svg.append(f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="3.5" fill="{s["color"]}"/>')
        legend_html.append(
            f'<span class="inline-flex items-center gap-1.5 mr-4"><span class="inline-block w-3 h-0.5" '
            f'style="background:{s["color"]}"></span><span class="text-[13px]" style="color:{COL["text"]}">{s["name"]}</span></span>'
        )

    svg.append("</svg>")
    return "".join(svg), "".join(legend_html)


def area_underwater_chart(series, width=1180, height=220, chart_id="uw", smooth=True):
    """series: list of {"name","color","points":[[date,drawdown_pct<=0]...]}. y-axis 0 at top."""
    margin = {"top": 16, "right": 24, "bottom": 32, "left": 70}
    plot_w = width - margin["left"] - margin["right"]
    plot_h = height - margin["top"] - margin["bottom"]

    all_x = [_parse(p[0]) for s in series for p in s["points"]]
    x_min, x_max = min(all_x), max(all_x)
    x_span = (x_max - x_min).days or 1
    all_vals = [p[1] for s in series for p in s["points"]]
    y_min = min(all_vals + [0]) * 1.05
    y_max = 0

    def xs(x):
        return margin["left"] + ((x - x_min).days / x_span) * plot_w

    def ys(y):
        return margin["top"] + ((0 - y) / (0 - y_min)) * plot_h if y_min != 0 else margin["top"]

    ticks = [t for t in _nice_ticks(y_min, 0, 4) if t <= 0]  # drawdown is never positive — don't show a >0% gridline
    svg = [f'<svg viewBox="0 0 {width} {height}" class="w-full h-auto" role="img" aria-label="drawdown chart" id="{chart_id}">']
    svg.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="{COL["panel"]}"/>')
    for t in ticks:
        y = ys(t)
        svg.append(f'<line x1="{margin["left"]}" y1="{y:.1f}" x2="{width-margin["right"]}" y2="{y:.1f}" '
                    f'stroke="{COL["border"]}" stroke-width="1" stroke-dasharray="2,3"/>')
        svg.append(f'<text x="{margin["left"]-10}" y="{y+4:.1f}" text-anchor="end" font-size="12" '
                    f'fill="{COL["muted"]}" font-family="monospace">{t:.0f}%</text>')

    legend_html = []
    for s in series:
        pts = s["points"]
        px_pts = [(xs(_parse(p[0])), ys(p[1])) for p in pts]
        zero_y = ys(0)
        if smooth:
            line_d = catmull_rom_path(px_pts)
            area_d = (f"M {xs(x_min):.1f},{zero_y:.1f} L {px_pts[0][0]:.1f},{px_pts[0][1]:.1f} "
                      + line_d.split(" ", 1)[1] + f" L {xs(x_max):.1f},{zero_y:.1f} Z")
        else:
            top_pts = [f"{x:.1f},{y:.1f}" for x, y in px_pts]
            area_d = f"M {xs(x_min):.1f},{zero_y:.1f} L " + " L ".join(top_pts) + f" L {xs(x_max):.1f},{zero_y:.1f} Z"
            line_d = "M " + " L ".join(top_pts)
        svg.append(f'<path d="{area_d}" fill="{s["color"]}" opacity="0.18"/>')
        dash = ' stroke-dasharray="6,4"' if s.get("dash") else ""
        svg.append(f'<path d="{line_d}" fill="none" stroke="{s["color"]}" stroke-width="1.6"{dash}/>')
        legend_html.append(
            f'<span class="inline-flex items-center gap-1.5 mr-4"><span class="inline-block w-3 h-0.5" '
            f'style="background:{s["color"]}"></span><span class="text-[13px]" style="color:{COL["text"]}">{s["name"]}</span></span>'
        )
    svg.append(f'<line x1="{margin["left"]}" y1="{height-margin["bottom"]}" x2="{width-margin["right"]}" '
                f'y2="{height-margin["bottom"]}" stroke="{COL["border"]}" stroke-width="1"/>')
    tick_dates = [x_min, x_min + (x_max - x_min) / 2, x_max]
    for td in tick_dates:
        x = xs(td)
        svg.append(f'<text x="{x:.1f}" y="{height-margin["bottom"]+18}" text-anchor="middle" '
                    f'font-size="12" fill="{COL["muted"]}" font-family="monospace">{td.strftime("%Y-%m")}</text>')
    svg.append("</svg>")
    return "".join(svg), "".join(legend_html)

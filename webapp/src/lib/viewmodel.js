import { humanize } from "./format";

// purely structural wrapper keys that add no information to a series label
const LABEL_BLOCKLIST = new Set(["instruments", "variants", "portfolios", "configs"]);

function isSeriesObject(obj) {
  if (!obj || typeof obj !== "object" || Array.isArray(obj)) return false;
  const hasCurve = Array.isArray(obj.equity_curve) || Array.isArray(obj.value_curve);
  return (
    hasCurve &&
    typeof obj.max_drawdown_pct === "number" &&
    typeof obj.longest_underwater_days === "number"
  );
}

function buildLabel(pathSegments) {
  const kept = pathSegments.filter((s) => !LABEL_BLOCKLIST.has(s));
  const segments = kept.length ? kept : pathSegments;
  return segments.map(humanize).join(" / ");
}

/** Walks a fetched results*.json object and finds every "series" sub-object
 * (one that has an equity_curve/value_curve + the standard metric fields
 * every backtest*.py in this project always writes). Returns a flat list,
 * so the UI can render any report's data without a bespoke per-report
 * mapping — new reports that follow the same JSON conventions just work. */
export function extractSeries(root, { maxDepth = 6 } = {}) {
  const found = [];

  function walk(obj, path, depth) {
    if (depth > maxDepth || !obj || typeof obj !== "object") return;
    if (Array.isArray(obj)) {
      // arrays of records (e.g. selections_sample) aren't series containers
      return;
    }
    if (isSeriesObject(obj)) {
      const curveKey = Array.isArray(obj.equity_curve) ? "equity_curve" : "value_curve";
      const growthKey = typeof obj.cagr_pct === "number" ? "cagr_pct" : "xirr_pct";
      found.push({
        path: path.join("/"),
        label: buildLabel(path),
        curve: obj[curveKey],
        investedCurve: Array.isArray(obj.invested_curve) ? obj.invested_curve : null,
        netReturnPct: obj.net_return_pct ?? null,
        growthPct: typeof obj[growthKey] === "number" ? obj[growthKey] : null,
        growthLabel: growthKey === "cagr_pct" ? "CAGR" : "XIRR",
        maxDrawdownPct: obj.max_drawdown_pct,
        longestUnderwaterDays: obj.longest_underwater_days,
        maxDrawdownPeakDate: obj.max_drawdown_peak_date ?? null,
        maxDrawdownTroughDate: obj.max_drawdown_trough_date ?? null,
      });
      return; // don't descend into a matched series object further
    }
    for (const [key, value] of Object.entries(obj)) {
      if (value && typeof value === "object") walk(value, [...path, key], depth + 1);
    }
  }

  walk(root, [], 0);

  // safety net: if the blocklist-shortened labels still collide for some
  // future report, disambiguate by restoring the last dropped path segment
  // rather than silently letting two series share one chart line/key.
  const counts = {};
  found.forEach((s) => {
    counts[s.label] = (counts[s.label] || 0) + 1;
  });
  found.forEach((s) => {
    if (counts[s.label] > 1) {
      s.label = `${s.label} (${s.path.split("/").join(" / ")})`;
    }
  });

  return found;
}

/** Converts a [ [dateStr, value], ... ] curve into Recharts-friendly rows,
 * re-basing to 100 at the first point so differently-scaled series overlay
 * sensibly (a report can opt out by passing rebase=false). */
export function curveToRows(curve, { rebase = true } = {}) {
  if (!curve || !curve.length) return [];
  const base = rebase ? curve[0][1] : 1;
  return curve.map(([date, value]) => ({ date, value: rebase ? (value / base) * 100 : value }));
}

/** Merges several series' curves into one array of {date, seriesLabel: value, ...}
 * rows for a multi-line Recharts chart, aligned by date (left join on the
 * union of all dates seen, forward-filled from each series' own last value). */
export function mergeSeriesForChart(seriesList, { rebase = true } = {}) {
  const perSeries = seriesList.map((s) => curveToRows(s.curve, { rebase }));
  const allDates = new Set();
  perSeries.forEach((rows) => rows.forEach((r) => allDates.add(r.date)));
  const sortedDates = Array.from(allDates).sort();

  const rows = sortedDates.map((date) => ({ date }));
  seriesList.forEach((s, i) => {
    const rowsForSeries = perSeries[i];
    let ptr = 0;
    let lastValue = null;
    rows.forEach((row) => {
      while (ptr < rowsForSeries.length && rowsForSeries[ptr].date <= row.date) {
        lastValue = rowsForSeries[ptr].value;
        ptr += 1;
      }
      row[s.label] = lastValue;
    });
  });
  return rows;
}

/** Evenly samples down to at most maxPoints REAL rows (always keeping the
 * first and last) — this is what actually makes a chart read as smooth: a
 * curve fit through too many closely-packed noisy points looks jagged no
 * matter the interpolation, but the same monotone curve through ~250 real
 * points reads cleanly while still being drawn from genuine data, not an
 * average. */
export function downsampleRows(rows, maxPoints = 260) {
  if (rows.length <= maxPoints) return rows;
  const step = (rows.length - 1) / (maxPoints - 1);
  const out = [];
  const seen = new Set();
  for (let i = 0; i < maxPoints; i += 1) {
    const idx = Math.round(i * step);
    if (!seen.has(idx)) {
      seen.add(idx);
      out.push(rows[idx]);
    }
  }
  return out;
}

/** Drawdown (% below running peak) series for one merged-chart row set,
 * computed per named key on the already-merged, date-aligned rows. */
export function drawdownRows(rows, seriesLabels) {
  const peaks = {};
  return rows.map((row) => {
    const out = { date: row.date };
    seriesLabels.forEach((label) => {
      const v = row[label];
      if (v === null || v === undefined) {
        out[label] = null;
        return;
      }
      peaks[label] = peaks[label] === undefined ? v : Math.max(peaks[label], v);
      out[label] = ((v - peaks[label]) / peaks[label]) * 100;
    });
    return out;
  });
}

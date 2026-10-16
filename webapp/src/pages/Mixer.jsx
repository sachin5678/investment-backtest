import { useEffect, useMemo, useRef, useState } from "react";
import { ALL_ITEMS, ITEM_BY_ID } from "../data/reportsIndex";
import { fetchResults } from "../lib/datacache";
import { extractSeries } from "../lib/viewmodel";
import { pct } from "../lib/format";
import { downloadCsv } from "../lib/csv";
import Panel, { WhatThisShows } from "../components/Panel";
import SmoothChart from "../components/SmoothChart";
import MsPill from "../components/MsPill";

const MAX_PICKS = 8;
const JSON_ITEMS = ALL_ITEMS.filter((it) => it.file.endsWith(".json"));

function resolveSeries(json, path) {
  if (!json) return null;
  const found = extractSeries(json);
  if (!found.length) return null;
  if (path) {
    const hit = found.find((s) => s.path === path);
    if (hit) return hit;
  }
  return found[0];
}

/** Union-axis blend: forward-fill each curve across the union of all dates,
 * then compound the weight-averaged step returns into one combined curve.
 * Weights are held constant (the standard fixed-weight portfolio). */
function buildMix(entries) {
  if (!entries.length) return null;
  const live = entries.filter((e) => e.curve?.length > 1 && (e.w || 0) > 0);
  if (!live.length) return null;
  const wsum = live.reduce((a, e) => a + e.w, 0);
  const maps = live.map((e) => ({ w: e.w, m: new Map(e.curve) }));
  const dateSet = new Set();
  for (const { m } of maps) for (const d of m.keys()) dateSet.add(d);
  const dates = [...dateSet].sort();
  if (dates.length < 2) return null;

  const snaps = [];
  const last = maps.map(() => null);
  for (const d of dates) {
    maps.forEach((x, i) => {
      const v = x.m.get(d);
      if (v !== undefined) last[i] = v;
    });
    snaps.push([...last]);
  }
  let startI = 0;
  for (; startI < snaps.length; startI++) {
    if (snaps[startI].every((v) => v !== null && !Number.isNaN(v))) break;
  }
  if (startI >= snaps.length - 1) return null;

  let value = 100;
  const rows = [[dates[startI], 100]];
  for (let k = startI + 1; k < snaps.length; k++) {
    const a = snaps[k - 1];
    const b = snaps[k];
    let r = 0;
    for (let i = 0; i < maps.length; i++) {
      if (a[i] > 0 && b[i] > 0) r += maps[i].w * (b[i] / a[i] - 1);
    }
    value *= 1 + r / wsum;
    rows.push([dates[k], value]);
  }
  return rows;
}

function curveMetrics(rows) {
  if (!rows || rows.length < 2) return null;
  const first = rows[0];
  const last = rows[rows.length - 1];
  const days = (new Date(last[0]) - new Date(first[0])) / 86400000;
  const years = days / 365.25;
  const total = last[1] / first[1] - 1;
  let peak = first[1];
  let mdd = 0;
  for (const [, v] of rows) {
    if (v > peak) peak = v;
    const dd = v / peak - 1;
    if (dd < mdd) mdd = dd;
  }
  return {
    totalPct: total * 100,
    cagrPct: years > 0 ? (Math.pow(last[1] / first[1], 1 / years) - 1) * 100 : null,
    maxDdPct: mdd * 100,
    start: first[0],
    end: last[0],
  };
}

export default function Mixer() {
  const [picks, setPicks] = useState([]);
  const [weights, setWeights] = useState({});
  const [resolved, setResolved] = useState({});
  const [query, setQuery] = useState("");
  const [showNifty, setShowNifty] = useState(true);
  const nextId = useRef(1);

  // load every file any pick (or the NIFTY overlay) needs, once
  useEffect(() => {
    const files = new Set(picks.map((p) => p.file));
    if (showNifty) files.add("results47.json");
    for (const file of files) {
      if (resolved[file] !== undefined) continue;
      setResolved((prev) => ({ ...prev, [file]: "loading" }));
      fetchResults(file)
        .then((j) => setResolved((prev) => ({ ...prev, [file]: j })))
        .catch((e) => setResolved((prev) => ({ ...prev, [file]: { error: e.message } })));
    }
  }, [picks, showNifty, resolved]);

  const pickedItemIds = useMemo(() => new Set(picks.map((p) => p.itemId)), [picks]);

  const seriesOptions = useMemo(() => {
    const out = {};
    for (const [file, json] of Object.entries(resolved)) {
      if (json && typeof json === "object" && !json.error && json !== "loading") {
        out[file] = extractSeries(json).map((s) => ({ path: s.path, label: s.label }));
      }
    }
    return out;
  }, [resolved]);

  const entries = useMemo(() => {
    const out = [];
    for (const p of picks) {
      const json = resolved[p.file];
      if (!json || json === "loading" || json.error) continue;
      const s = resolveSeries(json, p.path);
      if (!s?.curve?.length) continue;
      const item = ITEM_BY_ID[p.itemId];
      out.push({
        id: p.id,
        label: item?.title || p.file,
        sub: s.label,
        curve: s.curve,
        w: weights[p.id] ?? 1,
      });
    }
    return out;
  }, [picks, resolved, weights]);

  const mix = useMemo(() => buildMix(entries), [entries]);
  const metrics = useMemo(() => curveMetrics(mix), [mix]);

  const niftyCurve = useMemo(() => {
    if (!showNifty) return null;
    const json = resolved["results47.json"];
    if (!json || json === "loading" || json.error) return null;
    const found = extractSeries(json);
    const s =
      found.find((x) => x.path.toLowerCase() === "nifty") ||
      found.find((x) => x.path.toLowerCase().includes("nifty"));
    return s?.curve || null;
  }, [showNifty, resolved]);

  const wsum = entries.reduce((a, e) => a + (e.w || 0), 0);
  const hasZeroWeights = entries.length > 0 && wsum <= 0;

  const chartSeries = useMemo(() => {
    const out = [];
    if (mix) out.push({ label: "Mix", curve: mix });
    if (niftyCurve) out.push({ label: "NIFTY 50", curve: niftyCurve });
    return out;
  }, [mix, niftyCurve]);

  const pickerList = useMemo(() => {
    const q = query.trim().toLowerCase();
    return JSON_ITEMS.filter((it) => {
      if (!q) return true;
      return (
        it.title.toLowerCase().includes(q) ||
        it.subtitle.toLowerCase().includes(q) ||
        it.id.toLowerCase() === q ||
        it.file.toLowerCase().includes(q)
      );
    });
  }, [query]);

  const addPick = (it) => {
    if (pickedItemIds.has(it.id) || picks.length >= MAX_PICKS) return;
    setPicks((prev) => [...prev, { id: nextId.current++, itemId: it.id, file: it.file, path: null }]);
  };

  return (
    <div className="space-y-6 w-full">
      <Panel>
        <h3 className="text-base font-bold text-text mb-1">Multi-system mixer — blend any of the backtests into one</h3>
        <WhatThisShows>
          Pick any number of this project&rsquo;s strategy series and blend them into one combined curve with weights
          you set — weights held constant, each strategy&rsquo;s own moves compounded together. The curves are the
          archived chart series (≤1500 points), so the blend&rsquo;s CAGR and drawdown are close estimates, not fresh
          backtests.
        </WhatThisShows>

        <div className="flex flex-col xl:flex-row gap-6">
          {/* ---- picker ---- */}
          <div className="xl:w-[340px] shrink-0">
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search all strategies…"
              className="w-full bg-ground text-text border border-border rounded-lg px-3 py-2 text-[13px] mb-2.5 focus-visible:outline-2 focus-visible:outline-accent"
            />
            <div className="rounded-xl border border-border max-h-[420px] overflow-y-auto">
              {pickerList.map((it) => {
                const added = pickedItemIds.has(it.id);
                const full = picks.length >= MAX_PICKS;
                return (
                  <button
                    key={it.id}
                    onClick={() => addPick(it)}
                    disabled={added || full}
                    className={`w-full text-left px-3 py-2 border-b border-border/60 last:border-0 transition-colors ${
                      added
                        ? "opacity-45 cursor-default"
                        : full
                          ? "opacity-30 cursor-not-allowed"
                          : "cursor-pointer hover:bg-white/[0.03]"
                    }`}
                  >
                    <span className="block text-[12.5px] font-semibold text-text leading-tight">
                      <span className="font-mono text-[11px] text-muted mr-1.5">{it.id}</span>
                      {it.title}
                    </span>
                    <span className="block text-[11px] text-muted truncate">{it.subtitle}</span>
                  </button>
                );
              })}
              {pickerList.length === 0 && <p className="text-muted text-[12.5px] px-3 py-3">No matches.</p>}
            </div>
            <p className="text-[11.5px] text-muted mt-2">
              {picks.length}/{MAX_PICKS} selected — click to add, × in the list to remove.
            </p>
          </div>

          {/* ---- picks + results ---- */}
          <div className="flex-1 min-w-0 space-y-5">
            {picks.length === 0 && (
              <p className="text-muted text-[13px] border border-dashed border-border rounded-xl px-4 py-8 text-center">
                Add strategies on the left to build a mix.
              </p>
            )}

            {picks.map((p) => {
              const json = resolved[p.file];
              const item = ITEM_BY_ID[p.itemId];
              const opts = seriesOptions[p.file] || [];
              const chosen = json && json !== "loading" && !json.error ? resolveSeries(json, p.path) : null;
              const w = weights[p.id] ?? 1;
              return (
                <div key={p.id} className="rounded-xl border border-border px-3.5 py-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <span className="text-[13px] font-semibold text-text">
                        <span className="font-mono text-[11px] text-muted mr-1.5">{p.itemId}</span>
                        {item?.title || p.file}
                      </span>
                      <span className="block text-[11.5px] text-muted truncate">
                        {json === "loading"
                          ? "loading…"
                          : json?.error
                            ? `failed: ${json.error}`
                            : chosen
                              ? chosen.label
                              : p.file}
                      </span>
                    </div>
                    <button
                      onClick={() => setPicks((prev) => prev.filter((x) => x.id !== p.id))}
                      className="text-muted hover:text-negative text-[15px] leading-none cursor-pointer shrink-0 px-1"
                      aria-label="Remove"
                    >
                      ×
                    </button>
                  </div>
                  <div className="flex items-center gap-3 mt-2 flex-wrap">
                    {opts.length > 1 && (
                      <select
                        value={chosen?.path || ""}
                        onChange={(e) =>
                          setPicks((prev) => prev.map((x) => (x.id === p.id ? { ...x, path: e.target.value } : x)))
                        }
                        className="flex-1 min-w-[200px] bg-ground text-text border border-border rounded-lg px-2.5 py-1.5 text-[12px] cursor-pointer focus-visible:outline-2 focus-visible:outline-accent"
                      >
                        {opts.map((o) => (
                          <option key={o.path} value={o.path}>
                            {o.label}
                          </option>
                        ))}
                      </select>
                    )}
                    <label className="inline-flex items-center gap-2 text-[12px] text-muted-2">
                      weight
                      <input
                        type="number"
                        min="0"
                        step="0.5"
                        value={w}
                        onChange={(e) => setWeights((prev) => ({ ...prev, [p.id]: Math.max(0, Number(e.target.value) || 0) }))}
                        className="w-[70px] bg-ground text-text border border-border rounded-lg px-2 py-1 text-[12px] font-mono focus-visible:outline-2 focus-visible:outline-accent"
                      />
                      <span className="font-mono text-muted">
                        {wsum > 0 ? `${Math.round(((w || 0) / wsum) * 100)}% of mix` : "—"}
                      </span>
                    </label>
                  </div>
                </div>
              );
            })}

            {picks.length > 0 && (
              <div className="flex items-center gap-2 flex-wrap">
                <button
                  onClick={() => setWeights(Object.fromEntries(picks.map((p) => [p.id, 1])))}
                  className="text-[12px] font-semibold text-muted border border-border rounded-lg px-3 py-1.5 hover:text-text hover:border-muted-2 transition-colors cursor-pointer"
                >
                  Equal weights
                </button>
                <button
                  onClick={() => {
                    setPicks([]);
                    setWeights({});
                  }}
                  className="text-[12px] font-semibold text-muted border border-border rounded-lg px-3 py-1.5 hover:text-text hover:border-muted-2 transition-colors cursor-pointer"
                >
                  Clear
                </button>
                <label className="inline-flex items-center gap-2 text-[12.5px] text-muted-2 cursor-pointer select-none ml-auto">
                  <input
                    type="checkbox"
                    checked={showNifty}
                    onChange={(e) => setShowNifty(e.target.checked)}
                    className="accent-[#6ae4ff]"
                  />
                  NIFTY 50 overlay
                </label>
              </div>
            )}

            {hasZeroWeights && (
              <p className="text-assumption text-[12.5px]">
                Every weight is zero — set at least one above zero to build the mix.
              </p>
            )}

            {metrics && (
              <>
                <div className="flex gap-5 flex-wrap text-[13px] text-muted-2">
                  <span>
                    Total return{" "}
                    <span className={`font-mono font-semibold ${metrics.totalPct >= 0 ? "text-positive" : "text-negative"}`}>
                      {pct(metrics.totalPct)}
                    </span>
                  </span>
                  <span>
                    CAGR{" "}
                    <span className={`font-mono font-semibold ${metrics.cagrPct >= 0 ? "text-positive" : "text-negative"}`}>
                      {metrics.cagrPct === null ? "—" : pct(metrics.cagrPct)}
                    </span>
                  </span>
                  <span>
                    Max drawdown <span className="font-mono font-semibold text-negative">{pct(metrics.maxDdPct)}</span>
                  </span>
                  <span className="text-muted">
                    {metrics.start} → {metrics.end}
                  </span>
                  <button
                    onClick={() =>
                      downloadCsv(
                        "mix.csv",
                        mix.map(([date, value]) => ({ date, value: Math.round(value * 100) / 100 }))
                      )
                    }
                    className="text-[11.5px] font-semibold text-muted hover:text-text transition-colors cursor-pointer"
                  >
                    ⇩ CSV
                  </button>
                </div>
                {chartSeries.length > 1 && (
                  <p className="text-[11.5px] text-muted -mb-1">
                    Chart rebases both lines to 100 at their own first point for an apples-to-apples shape; the mix
                    metrics above are computed on the full blend window.
                  </p>
                )}
                <SmoothChart series={chartSeries} height={360} />
                <div className="overflow-x-auto rounded-xl border border-border">
                  <table className="w-full text-[12.5px] border-collapse">
                    <thead>
                      <tr>
                        {["Component", "Weight", "Own CAGR", "Own max DD", "Own total return"].map((h, i) => (
                          <th
                            key={h}
                            className={`sticky top-0 bg-panel-2 text-muted font-semibold px-3 py-2 text-[11px] uppercase tracking-wide border-b border-border ${
                              i === 0 ? "text-left" : "text-right"
                            }`}
                          >
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {entries.map((e) => {
                        const m = curveMetrics(e.curve);
                        return (
                          <tr key={e.id} className="border-b border-border/60 last:border-0">
                            <td className="px-3 py-1.5 text-left">
                              <span className="text-text">{e.label}</span>
                              <span className="block text-muted text-[11px] truncate max-w-[380px]">{e.sub}</span>
                            </td>
                            <td className="px-3 py-1.5 text-right font-mono text-muted-2">
                              {wsum > 0 ? `${Math.round(((e.w || 0) / wsum) * 100)}%` : "—"}
                            </td>
                            <td className="px-3 py-1.5 text-right font-mono text-muted-2">
                              {m?.cagrPct != null ? pct(m.cagrPct) : "—"}
                            </td>
                            <td className="px-3 py-1.5 text-right font-mono text-negative">
                              {m ? pct(m.maxDdPct) : "—"}
                            </td>
                            <td className="px-3 py-1.5 text-right font-mono text-muted-2">
                              {m ? pct(m.totalPct) : "—"}
                            </td>
                          </tr>
                        );
                      })}
                      {metrics && (
                        <tr className="bg-panel-2/60">
                          <td className="px-3 py-2 text-left font-semibold">Mix (constant weights)</td>
                          <td className="px-3 py-2 text-right font-mono">100%</td>
                          <td className="px-3 py-2 text-right font-mono font-semibold text-text">
                            {metrics.cagrPct === null ? "—" : pct(metrics.cagrPct)}
                          </td>
                          <td className="px-3 py-2 text-right font-mono font-semibold text-negative">
                            {pct(metrics.maxDdPct)}
                          </td>
                          <td className="px-3 py-2 text-right font-mono font-semibold text-text">
                            {pct(metrics.totalPct)}
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
                <p className="text-muted-2 text-[12px] italic flex items-center gap-2">
                  <MsPill kind="neutral">estimate</MsPill>
                  Blends run on each series&rsquo; archived chart-resolution curve — directionally right, not a
                  re-run of either backtest at full resolution.
                </p>
              </>
            )}
          </div>
        </div>
      </Panel>
    </div>
  );
}

import { useEffect, useMemo, useState } from "react";
import { pct } from "../lib/format";
import Panel, { WhatThisShows } from "../components/Panel";
import LockedReportGate from "../components/LockedReportGate";
import { useAuth } from "../context/AuthContext";

const DATA_BASE = "./data/";

const UNIVERSES = ["Midcap150", "Smallcap250", "NIFTY100", "NIFTY500"];
const CATEGORIES = [
  "Baseline",
  "Weighting",
  "Basket Size",
  "Regime Filter",
  "Filter + Hedge",
  "Core-Satellite",
  "Trend Filter",
  "Stop-Loss",
  "Momentum Formula",
  "Exposure Scaling",
];
const CATEGORY_COLOR = {
  Baseline: "text-muted-2 border-muted-2/40",
  Weighting: "text-accent border-accent/40",
  "Basket Size": "text-[#f25ca6] border-[#f25ca6]/40",
  "Regime Filter": "text-positive border-positive/40",
  "Filter + Hedge": "text-assumption border-assumption/40",
  "Core-Satellite": "text-[#ff8a5c] border-[#ff8a5c]/40",
  "Trend Filter": "text-[#b39dff] border-[#b39dff]/40",
  "Stop-Loss": "text-negative border-negative/40",
  "Momentum Formula": "text-accent border-accent/40",
  "Exposure Scaling": "text-positive border-positive/40",
};

const COLUMNS = [
  { key: "cagr", label: "CAGR", higherIsBetter: true, decimals: 1 },
  { key: "dd", label: "Max drawdown", higherIsBetter: true, decimals: 1 },
  { key: "sharpe", label: "Sharpe", higherIsBetter: true, decimals: 2, ratio: true },
  { key: "sortino", label: "Sortino", higherIsBetter: true, decimals: 2, ratio: true },
];

function ratioFmt(v) {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return v.toFixed(2);
}

function FilterPill({ label, active, onClick, colorClass }) {
  return (
    <button
      onClick={onClick}
      className={`text-[12px] font-semibold px-3 py-1.5 rounded-full border cursor-pointer transition-colors whitespace-nowrap
        ${active ? `bg-white/[0.06] ${colorClass || "border-accent text-accent"}` : "border-border text-muted-2 hover:text-text hover:border-muted-2"}`}
    >
      {label}
    </button>
  );
}

function MetricCell({ value, bench, col }) {
  if (value === null || value === undefined) {
    return (
      <td className="px-3 py-2.5 text-right whitespace-nowrap">
        <span className="block font-mono text-[14px] text-muted">—</span>
      </td>
    );
  }
  const win = bench === null || bench === undefined ? null : col.higherIsBetter ? value > bench : value < bench;
  const cls = win === true ? "text-positive" : win === false ? "text-negative" : "text-text";
  const fmt = col.ratio ? ratioFmt : (v) => pct(v, col.decimals, true);
  return (
    <td className="px-3 py-2.5 text-right whitespace-nowrap">
      <span className={`block font-mono text-[14.5px] font-bold ${cls}`}>{fmt(value)}</span>
      <span className="block font-mono text-[10.5px] text-muted mt-0.5">vs {fmt(bench)}</span>
    </td>
  );
}

export default function Comparison() {
  const { isLoggedIn } = useAuth();
  const [rows, setRows] = useState(null);
  const [error, setError] = useState(null);
  const [universe, setUniverse] = useState(null);
  const [category, setCategory] = useState(null);
  const [sort, setSort] = useState({ key: "cagr", dir: "desc" });

  useEffect(() => {
    // Locked out entirely when logged out — same as a premium report, the
    // data behind this table is never even fetched (see ReportPage.jsx).
    if (!isLoggedIn) return;
    fetch(DATA_BASE + "master_comparison.json")
      .then((r) => {
        if (!r.ok) throw new Error("Could not load master_comparison.json");
        return r.json();
      })
      .then((data) => setRows(data.rows))
      .catch((e) => setError(e.message));
  }, [isLoggedIn]);

  const filtered = useMemo(() => {
    if (!rows) return [];
    return rows.filter((r) => (!universe || r.universe === universe) && (!category || r.category === category));
  }, [rows, universe, category]);

  const sorted = useMemo(() => {
    const keyMap = { cagr: "cagr_pct", dd: "max_drawdown_pct", sharpe: "sharpe", sortino: "sortino" };
    const field = keyMap[sort.key];
    const copy = [...filtered];
    copy.sort((a, b) => {
      const av = a[field] ?? -Infinity;
      const bv = b[field] ?? -Infinity;
      return sort.dir === "asc" ? av - bv : bv - av;
    });
    return copy;
  }, [filtered, sort]);

  function toggleSort(key) {
    setSort((prev) => (prev.key === key ? { key, dir: prev.dir === "asc" ? "desc" : "asc" } : { key, dir: "desc" }));
  }

  if (!isLoggedIn) {
    return <LockedReportGate title="Master Comparison" />;
  }

  if (error) {
    return (
      <Panel accent="danger">
        <p className="text-text">Couldn't load the comparison data: {error}</p>
        <p className="text-muted text-sm mt-2">
          Make sure <code className="font-mono">master_comparison.json</code> exists in{" "}
          <code className="font-mono">public/data/</code>.
        </p>
      </Panel>
    );
  }

  if (!rows) {
    return <div className="text-muted text-sm animate-pulse">Loading the master comparison…</div>;
  }

  return (
    <div className="space-y-5 w-full">
      <Panel tight>
        <WhatThisShows>
          Every momentum-strategy variant tested across this project's front-loaded weighting, inverse-vol weighting, 200-EMA
          regime filter, gold/liquid-fund hedges, universe-specific trend filters, trailing stops, absolute momentum gates, and
          smooth exposure scaling — {rows.length} rows across {UNIVERSES.length} universes, each measured against NIFTY 50 on
          its own identical window. No charts here — sort or filter to find what actually worked. Sharpe/Sortino assume a 0%
          risk-free rate and are computed from each variant's true daily equity series (not the downsampled chart data
          individual reports embed).
        </WhatThisShows>

        <div className="space-y-2.5">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[10.5px] uppercase tracking-wide text-muted w-16 shrink-0">Universe</span>
            {UNIVERSES.map((u) => (
              <FilterPill key={u} label={u} active={universe === u} colorClass="border-accent text-accent" onClick={() => setUniverse(universe === u ? null : u)} />
            ))}
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[10.5px] uppercase tracking-wide text-muted w-16 shrink-0">Idea</span>
            {CATEGORIES.map((c) => (
              <FilterPill key={c} label={c} active={category === c} colorClass={CATEGORY_COLOR[c]} onClick={() => setCategory(category === c ? null : c)} />
            ))}
          </div>
          <div className="flex items-center gap-3 text-[12px] text-muted pt-1">
            <span>{sorted.length} of {rows.length} rows</span>
            {(universe || category) && (
              <button
                onClick={() => { setUniverse(null); setCategory(null); }}
                className="text-accent cursor-pointer hover:underline"
              >
                Reset filters
              </button>
            )}
          </div>
        </div>
      </Panel>

      <Panel className="!p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-[13px] border-collapse min-w-[760px]">
            <thead>
              <tr>
                <th className="sticky top-0 bg-panel-2 text-left text-muted font-semibold px-3 py-2.5 text-[11px] uppercase tracking-wide border-b border-border">
                  Strategy
                </th>
                {COLUMNS.map((col) => (
                  <th
                    key={col.key}
                    onClick={() => toggleSort(col.key)}
                    className={`sticky top-0 bg-panel-2 text-right font-semibold px-3 py-2.5 text-[11px] uppercase tracking-wide border-b border-border cursor-pointer select-none whitespace-nowrap
                      ${sort.key === col.key ? "text-accent" : "text-muted hover:text-text"}`}
                  >
                    {col.label} <span className={sort.key === col.key ? "opacity-100" : "opacity-40"}>{sort.key === col.key && sort.dir === "asc" ? "▴" : "▾"}</span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.map((r, i) => (
                <tr
                  key={`${r.universe}-${r.label}`}
                  className={`border-b border-border transition-colors hover:bg-white/[0.04] ${i % 2 === 1 ? "bg-white/[0.015]" : ""}`}
                >
                  <td className="px-3 py-2.5 align-top min-w-[220px]">
                    <div className="text-[10px] font-bold uppercase tracking-wide text-accent">{r.universe}</div>
                    <div className="text-[13.5px] font-semibold text-text leading-snug my-0.5">{r.label}</div>
                    <div className="flex items-center gap-2">
                      <span className={`inline-block text-[10px] font-semibold px-2 py-0.5 rounded-full border ${CATEGORY_COLOR[r.category] || "text-muted border-border"}`}>
                        {r.category}
                      </span>
                      <span className="text-[10px] text-muted font-mono">Report {r.report}</span>
                    </div>
                  </td>
                  <MetricCell value={r.cagr_pct} bench={r.bench_cagr_pct} col={COLUMNS[0]} />
                  <MetricCell value={r.max_drawdown_pct} bench={r.bench_max_drawdown_pct} col={COLUMNS[1]} />
                  <MetricCell value={r.sharpe} bench={r.bench_sharpe} col={COLUMNS[2]} />
                  <MetricCell value={r.sortino} bench={r.bench_sortino} col={COLUMNS[3]} />
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <div className="flex items-center gap-4 flex-wrap text-[11.5px] text-muted-2 px-1">
        <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-sm bg-positive inline-block" /> beats NIFTY 50 on that metric</span>
        <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-sm bg-negative inline-block" /> trails NIFTY 50 on that metric</span>
        <span>Small "vs X%" caption is NIFTY 50's own value over the identical window.</span>
      </div>
    </div>
  );
}

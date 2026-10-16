import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ALL_ITEMS } from "../data/reportsIndex";
import { loadLab, labSeriesRows } from "../lib/mslab";
import { pct } from "../lib/format";
import Panel, { WhatThisShows } from "../components/Panel";
import HealthCard from "../components/HealthCard";
import RobustnessCard from "../components/RobustnessCard";
import MsPill from "../components/MsPill";

// results files can be shared by several index entries (e.g. both sides of
// an A/B pair) — the first entry wins for labeling purposes.
const FILE_TO_ITEM = {};
for (const it of ALL_ITEMS) {
  if (!it.file.endsWith(".json")) continue;
  if (!FILE_TO_ITEM[it.file]) FILE_TO_ITEM[it.file] = it;
}

function toneClass(score) {
  if (score === null || score === undefined) return "text-muted";
  if (score >= 70) return "text-positive";
  if (score >= 50) return "text-assumption";
  return "text-negative";
}

export default function Health() {
  const [lab, setLab] = useState(null);
  const [error, setError] = useState(null);
  const [query, setQuery] = useState("");
  const [strategiesOnly, setStrategiesOnly] = useState(true);
  const [sortKey, setSortKey] = useState("score");
  const [selectedKey, setSelectedKey] = useState(null);
  const [didInit, setDidInit] = useState(false);

  useEffect(() => {
    let on = true;
    loadLab()
      .then((j) => on && setLab(j))
      .catch((e) => on && setError(e.message));
    return () => {
      on = false;
    };
  }, []);

  const rows = useMemo(() => {
    return labSeriesRows(lab).map((r) => {
      const item = FILE_TO_ITEM[r.file];
      return { ...r, title: item?.title || r.file, id: item?.id || null };
    });
  }, [lab]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const val = (r) => {
      switch (sortKey) {
        case "cagr":
          return r.health?.curve_metrics?.cagr_pct ?? -1e9;
        case "dd":
          return r.health?.curve_metrics?.max_drawdown_pct ?? -1e9;
        case "win":
          return r.health?.trade_metrics?.win_rate_pct ?? -1;
        default:
          return r.health?.score ?? -1;
      }
    };
    return rows
      .filter((r) => (strategiesOnly ? r.kind === "strategy" : true))
      .filter((r) => {
        if (!q) return true;
        return (
          r.title.toLowerCase().includes(q) ||
          r.label.toLowerCase().includes(q) ||
          r.file.toLowerCase().includes(q) ||
          r.kind.toLowerCase().includes(q)
        );
      })
      .sort((a, b) => val(b) - val(a) || (b.health?.score ?? 0) - (a.health?.score ?? 0));
  }, [rows, query, strategiesOnly, sortKey]);

  // preselect the top-scoring strategy once, so the detail card is never
  // empty on first paint — but never override the user's own click.
  useEffect(() => {
    if (!didInit && filtered.length > 0) {
      setSelectedKey(`${filtered[0].file}|${filtered[0].path}`);
      setDidInit(true);
    }
  }, [filtered, didInit]);

  const selected = useMemo(
    () => rows.find((r) => `${r.file}|${r.path}` === selectedKey) || null,
    [rows, selectedKey]
  );

  return (
    <div className="space-y-6 w-full">
      <Panel>
        <h3 className="text-base font-bold text-text mb-1">Strategy health — MomentumScore&rsquo;s 10-target scorecard</h3>
        <WhatThisShows>
          Every scored series across all {lab ? Object.keys(lab.reports).length : ""} results files, checked against the
          10 target ranges MomentumScore&rsquo;s own health score uses — worst-day, CAGR, tail-month, monthly
          volatility, growth-vs-fall on the curve; win rate, winner/loser size, gain/loss ratio and trade-tail on the
          trade log where one exists. Score = share of ranges met.{" "}
          {lab?.method_note ? <span className="not-italic">Curve checks run on each report&rsquo;s archived chart series (≤1500 points) — close, not bit-exact.</span> : null}
        </WhatThisShows>
        {error && <p className="text-negative text-[13px] mb-3">{error}</p>}
        {!lab && !error && <p className="text-muted text-sm animate-pulse">Scoring every archived series…</p>}
        {lab && (
          <>
            <div className="flex flex-wrap items-center gap-3 mb-4">
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search strategy, universe, file…"
                className="flex-1 min-w-[220px] bg-ground text-text border border-border rounded-lg px-3 py-2 text-[13px] focus-visible:outline-2 focus-visible:outline-accent"
              />
              <label className="inline-flex items-center gap-2 text-[12.5px] text-muted-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={strategiesOnly}
                  onChange={(e) => setStrategiesOnly(e.target.checked)}
                  className="accent-[#6ae4ff]"
                />
                Strategies only
              </label>
              <label className="inline-flex items-center gap-2 text-[12.5px] text-muted-2">
                Sort by
                <select
                  value={sortKey}
                  onChange={(e) => setSortKey(e.target.value)}
                  className="bg-ground text-text border border-border rounded-lg px-2.5 py-1.5 text-[12.5px] cursor-pointer focus-visible:outline-2 focus-visible:outline-accent"
                >
                  <option value="score">Health score</option>
                  <option value="cagr">CAGR</option>
                  <option value="dd">Max drawdown</option>
                  <option value="win">Win rate</option>
                </select>
              </label>
              <span className="text-[12px] text-muted">
                {filtered.length} of {rows.length} series
              </span>
            </div>
            <div className="overflow-x-auto rounded-xl border border-border max-h-[70vh] overflow-y-auto">
              <table className="w-full text-[13px] border-collapse">
                <thead>
                  <tr>
                    {["Strategy", "Type", "Health", "CAGR", "Max DD", "Win rate", "Both halves"].map((h, i) => (
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
                  {filtered.map((r) => {
                    const key = `${r.file}|${r.path}`;
                    const active = key === selectedKey;
                    const score = r.health?.score;
                    const cagr = r.health?.curve_metrics?.cagr_pct;
                    const dd = r.health?.curve_metrics?.max_drawdown_pct;
                    const win = r.health?.trade_metrics?.win_rate_pct;
                    const halves = r.robustness?.halves;
                    return (
                      <tr
                        key={key}
                        onClick={() => setSelectedKey(key)}
                        className={`border-b border-border/60 cursor-pointer transition-colors ${
                          active ? "bg-accent-dim" : "hover:bg-white/[0.03]"
                        }`}
                      >
                        <td className="px-3 py-2 text-left">
                          <span className="font-semibold text-text">{r.title}</span>
                          {r.id && <span className="text-muted font-mono text-[11px] ml-1.5">{r.id}</span>}
                          <span className="block text-muted text-[11.5px] truncate max-w-[440px]">
                            {r.label} · {r.file}
                          </span>
                        </td>
                        <td className="px-3 py-2 text-right">
                          <MsPill kind={r.kind === "strategy" ? "info" : "neutral"}>{r.kind}</MsPill>
                        </td>
                        <td className={`px-3 py-2 text-right font-mono font-semibold ${toneClass(score)}`}>
                          {score ?? "—"}
                        </td>
                        <td className="px-3 py-2 text-right font-mono text-muted-2">
                          {typeof cagr === "number" ? pct(cagr) : "—"}
                        </td>
                        <td className="px-3 py-2 text-right font-mono text-negative">
                          {typeof dd === "number" ? pct(dd) : "—"}
                        </td>
                        <td className="px-3 py-2 text-right font-mono text-muted-2">
                          {typeof win === "number" ? `${win}%` : "—"}
                        </td>
                        <td className="px-3 py-2 text-right">
                          {!halves ? (
                            <span className="text-muted">—</span>
                          ) : halves.passed_both ? (
                            <MsPill kind="pass">BOTH</MsPill>
                          ) : halves.passed_any ? (
                            <MsPill kind="warn">ONE</MsPill>
                          ) : (
                            <MsPill kind="fail">NONE</MsPill>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </>
        )}
      </Panel>

      {selected && (
        <Panel>
          <div className="flex items-start justify-between gap-3 flex-wrap mb-4">
            <div className="min-w-0">
              <h4 className="text-[15px] font-bold text-text">
                {selected.title}
                {selected.id && <span className="text-muted font-mono text-[12px] ml-2">{selected.id}</span>}
              </h4>
              <p className="text-muted text-[12.5px]">
                {selected.label} · {selected.file}
              </p>
            </div>
            {selected.id && (
              <Link
                to={`/report/${selected.id}`}
                className="text-accent text-[13px] font-medium border border-accent/40 rounded-full px-3.5 py-1.5 transition-colors hover:bg-accent-dim"
              >
                Open report {selected.id} →
              </Link>
            )}
          </div>
          <HealthCard health={selected.health} />
          {selected.robustness && (
            <div className="mt-6">
              <RobustnessCard robustness={selected.robustness} />
            </div>
          )}
        </Panel>
      )}
    </div>
  );
}

import { useEffect, useMemo, useState } from "react";
import { ALL_ITEMS } from "../data/reportsIndex";
import { loadLab, msLabel } from "../lib/mslab";
import { money } from "../lib/format";
import Panel, { WhatThisShows } from "../components/Panel";
import TaxTable from "../components/TaxTable";

const FILE_TO_ITEM = {};
for (const it of ALL_ITEMS) {
  if (!it.file.endsWith(".json")) continue;
  if (!FILE_TO_ITEM[it.file]) FILE_TO_ITEM[it.file] = it;
}

export default function Tax() {
  const [lab, setLab] = useState(null);
  const [error, setError] = useState(null);
  const [selectedKey, setSelectedKey] = useState(null);

  useEffect(() => {
    let on = true;
    loadLab()
      .then((j) => on && setLab(j))
      .catch((e) => on && setError(e.message));
    return () => {
      on = false;
    };
  }, []);

  const entries = useMemo(() => {
    if (!lab) return [];
    const out = [];
    for (const [file, list] of Object.entries(lab.taxes || {})) {
      for (const [i, e] of list.entries()) {
        out.push({ key: `${file}|${i}`, file, ...e });
      }
    }
    return out;
  }, [lab]);

  // default to the deepest trade log — the most interesting tax surface
  useEffect(() => {
    if (entries.length && !selectedKey) {
      const best = [...entries].sort((a, b) => (b.n_closed_trades || 0) - (a.n_closed_trades || 0))[0];
      setSelectedKey(best?.key ?? null);
    }
  }, [entries, selectedKey]);

  const selected = entries.find((e) => e.key === selectedKey) || null;
  const item = selected ? FILE_TO_ITEM[selected.file] : null;

  return (
    <div className="space-y-6 w-full">
      <Panel>
        <h3 className="text-base font-bold text-text mb-1">Capital-gains tax estimator — every trade-log report</h3>
        <WhatThisShows>
          What each report&rsquo;s own trade log would have owed under Indian capital-gains rules: 15%/10% (LTCG above
          ₹1,00,000) for sales before 23 Jul 2024; 20%/12.5% (above ₹1,25,000) on and after; 4% cess; short-then-long
          loss set-off with 8-year carry-forward; s.112A grandfathering via the 31-Jan-2025 FMV. Estimates, not tax
          advice — and only as good as each report&rsquo;s own entry prices and sizing.
        </WhatThisShows>
        {error && <p className="text-negative text-[13px]">{error}</p>}
        {!lab && !error && <p className="text-muted text-sm animate-pulse">Reading the tax reports…</p>}
        {lab && (
          <div className="flex flex-col lg:flex-row gap-5">
            <div className="lg:w-[340px] shrink-0 space-y-1.5 lg:max-h-[72vh] lg:overflow-y-auto pr-1">
              {entries.map((e) => {
                const active = e.key === selectedKey;
                const it = FILE_TO_ITEM[e.file];
                return (
                  <button
                    key={e.key}
                    onClick={() => setSelectedKey(e.key)}
                    className={`w-full text-left px-3 py-2.5 rounded-lg border cursor-pointer transition-colors focus-visible:outline-2 focus-visible:outline-accent ${
                      active ? "bg-accent-dim border-accent text-text" : "border-border text-muted hover:text-text hover:border-muted-2"
                    }`}
                  >
                    <span className="block text-[12.5px] font-semibold leading-tight">
                      {it?.title || e.file}
                      {it?.id && <span className="font-mono text-[11px] ml-1.5 opacity-70">{it.id}</span>}
                    </span>
                    <span className="block text-[11px] text-muted truncate">
                      {msLabel(e.label)} · {e.n_closed_trades} closed trades
                    </span>
                    <span className="block text-[11.5px] font-mono text-muted-2 mt-0.5">
                      tax ≈ {money(e.totals?.total_tax, "₹", 0)}
                    </span>
                  </button>
                );
              })}
            </div>
            <div className="flex-1 min-w-0">
              {selected ? (
                <>
                  <div className="flex gap-4 flex-wrap mb-4 text-[12.5px] text-muted-2">
                    <span>
                      Total tax{" "}
                      <span className="font-mono text-text font-semibold">
                        {money(selected.totals?.total_tax, "₹", 0)}
                      </span>
                    </span>
                    <span>
                      on realized P&amp;L{" "}
                      <span className="font-mono text-text">{money(selected.totals?.total_realised_pnl, "₹", 0)}</span>
                    </span>
                    <span>
                      effective{" "}
                      <span className="font-mono text-text font-semibold">
                        {selected.totals?.tax_pct_of_realised_pnl}%
                      </span>
                    </span>
                    {selected.totals?.n_grandfathered_trades > 0 && (
                      <span>
                        grandfathered trades{" "}
                        <span className="font-mono text-text">{selected.totals.n_grandfathered_trades}</span>
                      </span>
                    )}
                    <span className="text-muted">
                      window {selected.first_entry} → {selected.last_exit}
                    </span>
                  </div>
                  <TaxTable report={selected} />
                  {selected.notes?.length > 0 && (
                    <ul className="mt-3 space-y-1">
                      {selected.notes.map((n) => (
                        <li key={n} className="text-muted-2 text-[12px] list-disc ml-4">
                          {n}
                        </li>
                      ))}
                    </ul>
                  )}
                </>
              ) : (
                <p className="text-muted text-sm">Select a trade log on the left.</p>
              )}
            </div>
          </div>
        )}
      </Panel>
    </div>
  );
}

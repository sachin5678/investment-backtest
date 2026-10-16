import { useEffect, useMemo, useState } from "react";
import { pct, money } from "../lib/format";
import { extractSeries } from "../lib/viewmodel";
import Panel, { WhatThisShows } from "../components/Panel";
import SmoothChart from "../components/SmoothChart";

// The five "builder labs" — reports 94–98. Each file is a normal results
// JSON whose `variants` block holds one full series object per experiment
// (auto-detected by extractSeries), all run through the same engine as
// report 93's hero, one knob changed at a time. This page is the
// cross-lab view: every variant, every lab, side by side.
const DATA_BASE = "./data/";

const LABS = [
  {
    id: "94",
    file: "results93.json",
    name: "Protect",
    blurb: "The market-timing layer — gold vs cash, daily checks vs at-review, VIX, Supertrend, NIFTY 500.",
  },
  {
    id: "95",
    file: "results94.json",
    name: "Conditions",
    blurb: "keep-if / buy-only-if / sell-when rules — momentum, swings, Supertrend, RSI, VIX, turnover, sectors.",
  },
  {
    id: "96",
    file: "results95.json",
    name: "Money",
    blurb: "Compounding off, SIP with step-up, buy-the-dip top-ups, and the momentum-discipline pair.",
  },
  {
    id: "97",
    file: "results96.json",
    name: "Pick & Rebalance",
    blurb: "Exit-rank leash, entry-rank gate, sector caps, whole units, heavier friction.",
  },
  {
    id: "98",
    file: "results97.json",
    name: "Max Strategy",
    blurb: "Every winning knob from labs 94–97 stacked into one strategy, with full robustness.",
  },
];

function HalvesCell({ halves }) {
  if (!halves || !Array.isArray(halves.halves)) {
    return <span className="font-mono text-[13px] text-muted">—</span>;
  }
  const total = halves.halves.length;
  const passed = halves.halves.filter((h) => h.passed === true).length;
  const cls = passed === total ? "text-positive" : passed === 0 ? "text-negative" : "text-assumption";
  return (
    <span className={`font-mono text-[13px] font-bold ${cls}`}>
      {passed}/{total}
      <span className="block text-[10.5px] text-muted font-normal mt-0.5">beats NIFTY per half</span>
    </span>
  );
}

export default function Builder() {
  const [labs, setLabs] = useState(null);
  const [error, setError] = useState(null);
  const [activeId, setActiveId] = useState("94");

  useEffect(() => {
    // 98 may not exist yet while the labs are still being run — a missing
    // file just disables that tab instead of failing the whole page.
    Promise.all(
      LABS.map((lab) =>
        fetch(DATA_BASE + lab.file)
          .then((r) => (r.ok ? r.json() : null))
          .catch(() => null)
      )
    )
      .then((data) => setLabs(data))
      .catch((e) => setError(e.message));
  }, []);

  const activeIndex = LABS.findIndex((l) => l.id === activeId);
  const activeLab = LABS[activeIndex];
  const activeData = labs?.[activeIndex];

  const rows = useMemo(() => {
    if (!activeData?.variants) return [];
    const heroLabel = activeData.hero_label;
    const entries = Object.entries(activeData.variants).map(([label, v]) => ({
      label,
      isHero: label === heroLabel,
      cagr: v.cagr_pct,
      dd: v.max_drawdown_pct,
      net: v.net_return_pct,
      health: v.health?.score ?? null,
      tax: v.tax?.total_tax ?? null,
      halves: v.halves ?? null,
      final: v.final_value ?? null,
      contributed: v.contributed_total ?? null,
      trades: v.stats?.total_trades ?? null,
    }));
    const hero = entries.find((e) => e.isHero);
    entries.forEach((e) => {
      e.delta = hero && e.cagr !== null && hero.cagr !== null ? e.cagr - hero.cagr : null;
    });
    entries.sort((a, b) => (b.cagr ?? -Infinity) - (a.cagr ?? -Infinity));
    return entries;
  }, [activeData]);

  const heroRow = rows.find((r) => r.isHero);
  const bestChallenger = rows.find((r) => !r.isHero);

  if (error) {
    return (
      <Panel accent="danger">
        <p className="text-text">Couldn't load the builder labs: {error}</p>
      </Panel>
    );
  }

  if (!labs) {
    return <div className="text-muted text-sm animate-pulse">Loading builder labs…</div>;
  }

  const series = activeData ? extractSeries(activeData) : [];

  return (
    <div className="space-y-6 w-full">
      <Panel tight>
        <h2 className="text-lg font-bold text-text mb-1">MomentumScore Builder Labs</h2>
        <WhatThisShows>
          Reports 94–98 apply the momentumscore.in strategy builder's own tabs — Protect, Conditions, Money, Pick —
          one knob at a time on top of report 48/93's hero, then stack the winners. Every variant is the same engine
          as report 93 (the hero row of the Protect lab reproduces it exactly), run frictionless and with 0.1%/side
          costs, then scored with the same health/halves/tax layer. Numbers are never recalculated here — they are
          read straight from each lab's results file.
        </WhatThisShows>
        <div className="flex gap-2 flex-wrap">
          {LABS.map((lab, i) => {
            const available = !!labs[i];
            const active = lab.id === activeId;
            return (
              <button
                key={lab.id}
                disabled={!available}
                onClick={() => setActiveId(lab.id)}
                className={`px-3.5 py-2 rounded-xl border text-left cursor-pointer transition-colors
                  ${active ? "bg-accent-dim border-accent" : "border-border hover:border-muted-2"}
                  ${available ? "" : "opacity-40 cursor-not-allowed"}`}
              >
                <span className={`block text-[12px] font-mono ${active ? "text-accent" : "text-muted"}`}>
                  Report {lab.id}
                </span>
                <span className={`block text-[13.5px] font-bold ${active ? "text-text" : "text-muted-2"}`}>
                  {lab.name}
                </span>
              </button>
            );
          })}
        </div>
      </Panel>

      {activeData && (
        <>
          <Panel tight>
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div className="min-w-0">
                <h3 className="text-base font-bold text-text mb-0.5">{activeData.lab_title}</h3>
                <p className="text-muted-2 text-[13px]">{activeLab.blurb}</p>
              </div>
              <div className="text-right shrink-0">
                <span className="block text-[11px] text-muted uppercase tracking-wide">Hero</span>
                <span className="block text-[13px] font-semibold text-assumption">{activeData.hero_label}</span>
                <span className="block text-[11.5px] text-muted mono">
                  {activeData.start_date}–{activeData.end_date}
                </span>
              </div>
            </div>
            {bestChallenger && heroRow && bestChallenger.cagr !== null && (
              <div className="flex gap-2 flex-wrap mt-3">
                <span className="text-[12px] px-2.5 py-1 rounded-full border border-positive/40 text-positive bg-positive/10">
                  Best variant by CAGR: {bestChallenger.label} — {pct(bestChallenger.cagr)}
                  {bestChallenger.delta !== null && ` (${bestChallenger.delta >= 0 ? "+" : ""}${bestChallenger.delta.toFixed(1)}pp vs hero)`}
                </span>
                <span className="text-[12px] px-2.5 py-1 rounded-full border border-border text-muted-2">
                  Hero: {pct(heroRow.cagr)} at {pct(heroRow.dd, 1, false)} max drawdown
                </span>
              </div>
            )}
          </Panel>

          <Panel tight>
            <h3 className="text-base font-bold text-text mb-1">Every variant, one table</h3>
            <WhatThisShows>
              Sorted by CAGR. Δ vs hero is the CAGR difference against the lab's own hero row (report 93's exact
              configuration). Halves = how many of the two half-periods the variant beat NIFTY 50 in — the same
              robustness check report 93 carries.
            </WhatThisShows>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-[13px]">
                <thead>
                  <tr className="text-[11px] uppercase tracking-wide text-muted">
                    <th className="text-left font-semibold px-3 py-2 border-b border-border">Variant</th>
                    <th className="text-right font-semibold px-3 py-2 border-b border-border">CAGR</th>
                    <th className="text-right font-semibold px-3 py-2 border-b border-border">Δ vs hero</th>
                    <th className="text-right font-semibold px-3 py-2 border-b border-border">Max DD</th>
                    <th className="text-right font-semibold px-3 py-2 border-b border-border">Net return</th>
                    <th className="text-right font-semibold px-3 py-2 border-b border-border">Health</th>
                    <th className="text-right font-semibold px-3 py-2 border-b border-border">Halves</th>
                    <th className="text-right font-semibold px-3 py-2 border-b border-border">Tax paid</th>
                    <th className="text-right font-semibold px-3 py-2 border-b border-border">Final value</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr
                      key={r.label}
                      className={r.isHero ? "bg-accent-dim/40" : "hover:bg-white/[0.02]"}
                    >
                      <td className="text-left px-3 py-2.5 border-b border-border/60 max-w-[340px]">
                        <span className="font-semibold text-text">{r.label}</span>
                        {r.isHero && (
                          <span className="ml-2 text-[10.5px] font-bold px-1.5 py-0.5 rounded-full border border-accent/50 text-accent bg-accent/10 align-middle">
                            HERO · REPORT 93
                          </span>
                        )}
                        {r.trades !== null && (
                          <span className="block text-[11px] text-muted mt-0.5">{r.trades} trades</span>
                        )}
                      </td>
                      <td className="text-right px-3 py-2.5 border-b border-border/60 font-mono font-bold text-[14px]">
                        <span className={r.delta === null || r.delta >= 0 ? "text-positive" : "text-text"}>{pct(r.cagr)}</span>
                      </td>
                      <td className="text-right px-3 py-2.5 border-b border-border/60 font-mono text-[13px]">
                        {r.delta === null ? "—" : (
                          <span className={r.delta > 0.05 ? "text-positive" : r.delta < -0.05 ? "text-negative" : "text-muted"}>
                            {r.delta >= 0 ? "+" : ""}{r.delta.toFixed(1)}pp
                          </span>
                        )}
                      </td>
                      <td className="text-right px-3 py-2.5 border-b border-border/60 font-mono text-[13px] text-text">
                        {pct(r.dd, 1, false)}
                      </td>
                      <td className="text-right px-3 py-2.5 border-b border-border/60 font-mono text-[13px] text-muted-2">
                        {pct(r.net)}
                      </td>
                      <td className="text-right px-3 py-2.5 border-b border-border/60 font-mono text-[13px]">
                        {r.health === null ? "—" : (
                          <span className={r.health >= 60 ? "text-positive" : r.health >= 40 ? "text-assumption" : "text-negative"}>
                            {r.health}/100
                          </span>
                        )}
                      </td>
                      <td className="text-right px-3 py-2.5 border-b border-border/60">
                        <HalvesCell halves={r.halves} />
                      </td>
                      <td className="text-right px-3 py-2.5 border-b border-border/60 font-mono text-[12.5px] text-muted-2">
                        {r.tax === null ? "—" : money(r.tax)}
                      </td>
                      <td className="text-right px-3 py-2.5 border-b border-border/60 font-mono text-[12.5px] text-muted-2">
                        {r.final === null ? "—" : money(r.final)}
                        {r.contributed !== null && r.contributed > 100000 && (
                          <span className="block text-[10.5px] text-muted">
                            contributed {money(r.contributed)}
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>

          <Panel>
            <h3 className="text-base font-bold text-text mb-1">Growth of 100 — every variant of this lab</h3>
            <WhatThisShows>
              Each variant rebased to 100 at the window's start, after 0.1%/side costs. The hero line is the same
              curve report 93 ships, so any gap you see is exactly the knob this lab changed.
            </WhatThisShows>
            <SmoothChart series={series} valuePrefix="" />
          </Panel>

          {activeData.notes?.length > 0 && (
            <Panel tight>
              <h3 className="text-base font-bold text-text mb-2">How to read this lab — the fine print</h3>
              <ul className="space-y-2">
                {activeData.notes.map((n, i) => (
                  <li key={i} className="text-[13px] text-muted-2 leading-relaxed flex gap-2">
                    <span className="text-accent shrink-0">•</span>
                    <span>{n}</span>
                  </li>
                ))}
              </ul>
            </Panel>
          )}
        </>
      )}
    </div>
  );
}

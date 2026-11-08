import { useMemo, useState } from "react";
import Panel, { WhatThisShows } from "./Panel";

// stable per-strategy styling for report 107's series: hue = portfolio size,
// solid = gold regime switch, dashed = no switch, dotted and faded = the
// legacy same-close execution convention.
const N_COLOR = { 5: "#ffb84d", 10: "#6ae4ff", 20: "#c77dff" };

export function styleFor(tags) {
  if (!tags) return {};
  if (tags.benchmark) return { color: "#aab6c9", dash: "2 4", opacity: 1 };
  const color = N_COLOR[tags.n] ?? "#aab6c9";
  if (tags.exec === "close") return { color, dash: tags.gold ? "1 4" : "1 8", opacity: 0.65 };
  return { color, dash: tags.gold ? undefined : "6 4", opacity: 1 };
}

export function hasStrategyTags(series) {
  return series.some((s) => s.tags && s.tags.gold !== undefined);
}

function Check({ checked, onChange, children, swatch }) {
  return (
    <label className="inline-flex items-center gap-2 text-[13px] text-text cursor-pointer select-none">
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} className="accent-[#6ae4ff] cursor-pointer" />
      {swatch && <span className="inline-block w-3 h-[3px] rounded" style={{ background: swatch }} />}
      {children}
    </label>
  );
}

function Group({ title, children }) {
  return (
    <div className="min-w-[160px]">
      <div className="text-[11px] uppercase tracking-wide text-muted font-semibold mb-2">{title}</div>
      <div className="flex flex-col gap-1.5">{children}</div>
    </div>
  );
}

/** Check/uncheck filter for a multi-strategy report. Returns the filtered,
 * styled series list, the filter state (so tables can follow it) and the
 * control panel to render. */
export function useStrategyFilter(series) {
  const [gold, setGold] = useState(true);
  const [plain, setPlain] = useState(true);
  const [open, setOpen] = useState(true);
  const [close, setClose] = useState(false);
  const [ns, setNs] = useState({ 5: true, 10: true, 20: true });
  const [bench, setBench] = useState(true);
  const [cal, setCal] = useState("Dec");

  const calendars = useMemo(() => [...new Set((series ?? []).map((s) => s.tags?.cal).filter(Boolean))], [series]);

  const filtered = useMemo(
    () =>
      (series ?? [])
        .filter((s) => {
          const t = s.tags;
          if (!t) return true;
          if (t.benchmark) return bench;
          if (t.cal && t.cal !== cal) return false;
          if (t.gold ? !gold : !plain) return false;
          if (t.exec === "open" ? !open : !close) return false;
          return !!ns[t.n];
        })
        .map((s) => ({ ...s, ...styleFor(s.tags) })),
    [series, gold, plain, open, close, ns, bench, cal]
  );

  const filter = { gold, plain, open, close, ns, cal };

  const panel = (
    <Panel tight>
      <h3 className="text-base font-bold text-text mb-1">Filter strategies</h3>
      <WhatThisShows>
        Tick or untick to compare. The KPI table, growth chart, drawdown chart and calendar table below all follow these boxes. Colour = portfolio
        size, solid line = gold regime switch, dashed = always invested, dotted and faded = the legacy same-close fills.
      </WhatThisShows>
      <div className="flex flex-wrap gap-x-10 gap-y-4">
        <Group title="Gold regime switch">
          <Check checked={gold} onChange={setGold}>With switch (200-EMA → GOLDBEES)</Check>
          <Check checked={plain} onChange={setPlain}>Without switch (always invested)</Check>
        </Group>
        <Group title="Portfolio size">
          {[5, 10, 20].map((n) => (
            <Check key={n} checked={ns[n]} onChange={(v) => setNs({ ...ns, [n]: v })} swatch={N_COLOR[n]}>
              Top {n}
            </Check>
          ))}
        </Group>
        <Group title="Execution">
          <Check checked={open} onChange={setOpen}>Next-day open (headline)</Check>
          <Check checked={close} onChange={setClose}>Same-day close (legacy)</Check>
        </Group>
        <Group title="Rebalance month (charts)">
          {calendars.map((c) => (
            <label key={c} className="inline-flex items-center gap-2 text-[13px] text-text cursor-pointer select-none">
              <input type="radio" name="cal107" checked={cal === c} onChange={() => setCal(c)} className="accent-[#6ae4ff] cursor-pointer" />
              {c === "Dec" ? "December" : c === "Jun" ? "June" : c}
            </label>
          ))}
        </Group>
        <Group title="Benchmark">
          <Check checked={bench} onChange={setBench} swatch="#aab6c9">NIFTY 50 buy &amp; hold</Check>
        </Group>
      </div>
      {filtered.length === 0 && <p className="text-negative text-[13px] mt-3">Nothing selected — tick at least one box in each group.</p>}
    </Panel>
  );

  return { filtered, filter, panel };
}

import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { GROUPS, ALL_ITEMS, ITEM_BY_ID } from "../data/reportsIndex";
import { fetchResults } from "../lib/datacache";
import { extractSeries } from "../lib/viewmodel";
import { money, pct } from "../lib/format";
import Panel, { WhatThisShows } from "../components/Panel";

const LS_KEY = "msport.tracked_portfolios_v1";
const JSON_ITEMS = ALL_ITEMS.filter((it) => it.file.endsWith(".json"));

function readStore() {
  try {
    const raw = JSON.parse(localStorage.getItem(LS_KEY));
    return Array.isArray(raw) ? raw : [];
  } catch {
    return [];
  }
}

function writeStore(list) {
  localStorage.setItem(LS_KEY, JSON.stringify(list));
}

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

export default function Track() {
  const [list, setList] = useState(() => readStore());
  const [computed, setComputed] = useState({});
  const [resolved, setResolved] = useState({});

  // form state
  const [name, setName] = useState("");
  const [itemId, setItemId] = useState("48");
  const [path, setPath] = useState("");
  const [startDate, setStartDate] = useState(() =>
    new Date(Date.now() - 5 * 365.25 * 86400000).toISOString().slice(0, 10)
  );
  const [capital, setCapital] = useState(100000);
  const [formError, setFormError] = useState(null);

  const item = ITEM_BY_ID[itemId];
  const formJson = item ? resolved[item.file] : null;

  useEffect(() => {
    if (item && item.file.endsWith(".json") && resolved[item.file] === undefined) {
      setResolved((prev) => ({ ...prev, [item.file]: "loading" }));
      fetchResults(item.file)
        .then((j) => setResolved((prev) => ({ ...prev, [item.file]: j })))
        .catch((e) => setResolved((prev) => ({ ...prev, [item.file]: { error: e.message } })));
    }
  }, [item, resolved]);

  const formSeries = useMemo(() => {
    if (!formJson || formJson === "loading" || formJson.error) return [];
    return extractSeries(formJson);
  }, [formJson]);

  // recompute every saved portfolio against its strategy's own curve
  useEffect(() => {
    let alive = true;
    (async () => {
      const out = {};
      for (const p of list) {
        try {
          let json = resolved[p.file];
          if (!json || json === "loading") json = await fetchResults(p.file);
          if (json?.error) throw new Error(json.error);
          const s = resolveSeries(json, p.path);
          const curve = s?.curve || [];
          if (curve.length < 2) {
            out[p.id] = { error: "no curve data" };
            continue;
          }
          const at = curve.find(([d]) => d >= p.startDate) || null;
          const last = curve[curve.length - 1];
          if (!at || at[1] <= 0) {
            out[p.id] = { error: `curve has no point on/after ${p.startDate}` };
            continue;
          }
          const units = p.capital / at[1];
          const nowValue = units * last[1];
          const pnl = nowValue - p.capital;
          const years = Math.max(1e-9, (new Date(last[0]) - new Date(at[0])) / 86400000 / 365.25);
          out[p.id] = {
            symbol: json.currency_symbol || "₹",
            seriesLabel: s?.label || p.path || "—",
            atDate: at[0],
            lastDate: last[0],
            nowValue,
            pnl,
            retPct: (nowValue / p.capital - 1) * 100,
            cagrPct: (Math.pow(nowValue / p.capital, 1 / years) - 1) * 100,
          };
        } catch (e) {
          out[p.id] = { error: e.message };
        }
      }
      if (alive) setComputed(out);
    })();
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [list]);

  const add = () => {
    setFormError(null);
    if (!item) return;
    if (!startDate) {
      setFormError("Pick a start date.");
      return;
    }
    const cap = Number(capital);
    if (!cap || cap <= 0) {
      setFormError("Capital must be a positive number.");
      return;
    }
    const entry = {
      id: Date.now(),
      name: name.trim() || `${item.title} — ${startDate}`,
      itemId: item.id,
      file: item.file,
      path: path || null,
      startDate,
      capital: cap,
    };
    const next = [...list, entry];
    setList(next);
    writeStore(next);
    setName("");
  };

  const remove = (id) => {
    const next = list.filter((p) => p.id !== id);
    setList(next);
    writeStore(next);
  };

  return (
    <div className="space-y-6 w-full">
      <Panel>
        <h3 className="text-base font-bold text-text mb-1">My portfolios — paper-track any strategy from any date</h3>
        <WhatThisShows>
          Save a &ldquo;what if I had started then&rdquo; position in any backtest series: pick the strategy, the series,
          a start date and capital. Values mark the strategy&rsquo;s own archived curve at its latest data point — a
          paper tracker against the backtest, not live prices. Everything stays in this browser
          (localStorage).
        </WhatThisShows>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3 items-end">
          <label className="block">
            <span className="block text-[11px] font-semibold uppercase tracking-wide text-muted mb-1.5">Name</span>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Gold-hedge from Maharashtra day"
              className="w-full bg-ground text-text border border-border rounded-lg px-3 py-2 text-[13px] focus-visible:outline-2 focus-visible:outline-accent"
            />
          </label>
          <label className="block">
            <span className="block text-[11px] font-semibold uppercase tracking-wide text-muted mb-1.5">Strategy</span>
            <select
              value={itemId}
              onChange={(e) => {
                setItemId(e.target.value);
                setPath("");
              }}
              className="w-full bg-ground text-text border border-border rounded-lg px-3 py-2 text-[13px] cursor-pointer focus-visible:outline-2 focus-visible:outline-accent"
            >
              {GROUPS.map((g) => (
                <optgroup key={g.label} label={g.label}>
                  {g.items
                    .filter((it) => it.file.endsWith(".json"))
                    .map((it) => (
                      <option key={it.id} value={it.id}>
                        {it.id} — {it.title}
                      </option>
                    ))}
                </optgroup>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="block text-[11px] font-semibold uppercase tracking-wide text-muted mb-1.5">Series</span>
            <select
              value={path}
              onChange={(e) => setPath(e.target.value)}
              className="w-full bg-ground text-text border border-border rounded-lg px-3 py-2 text-[13px] cursor-pointer focus-visible:outline-2 focus-visible:outline-accent"
            >
              <option value="">{formSeries.length > 1 ? "Main series (first)" : formSeries[0]?.label || "loading…"}</option>
              {formSeries.length > 1 &&
                formSeries.map((s) => (
                  <option key={s.path} value={s.path}>
                    {s.label}
                  </option>
                ))}
            </select>
          </label>
          <label className="block">
            <span className="block text-[11px] font-semibold uppercase tracking-wide text-muted mb-1.5">Start date</span>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full bg-ground text-text border border-border rounded-lg px-3 py-2 text-[13px] focus-visible:outline-2 focus-visible:outline-accent"
            />
          </label>
          <label className="block">
            <span className="block text-[11px] font-semibold uppercase tracking-wide text-muted mb-1.5">Capital</span>
            <input
              type="number"
              min="1"
              value={capital}
              onChange={(e) => setCapital(e.target.value)}
              className="w-full bg-ground text-text border border-border rounded-lg px-3 py-2 text-[13px] font-mono focus-visible:outline-2 focus-visible:outline-accent"
            />
          </label>
          <button
            onClick={add}
            className="bg-accent-dim border border-accent text-accent font-semibold rounded-lg px-4 py-2 text-[13px] hover:bg-accent/20 transition-colors cursor-pointer"
          >
            + Track this portfolio
          </button>
        </div>
        {formError && <p className="text-negative text-[12.5px] mt-2">{formError}</p>}
      </Panel>

      <Panel>
        <h3 className="text-base font-bold text-text mb-3">Tracked portfolios</h3>
        {list.length === 0 ? (
          <p className="text-muted text-[13px]">Nothing tracked yet — add one above.</p>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-border">
            <table className="w-full text-[12.5px] border-collapse">
              <thead>
                <tr>
                  {["Portfolio", "Strategy", "Start → as of", "Capital", "Value now", "P&L", "Return", "CAGR", ""].map(
                    (h, i) => (
                      <th
                        key={h + i}
                        className={`sticky top-0 bg-panel-2 text-muted font-semibold px-3 py-2 text-[11px] uppercase tracking-wide border-b border-border ${
                          i === 0 || i === 1 || i === 2 ? "text-left" : "text-right"
                        }`}
                      >
                        {h}
                      </th>
                    )
                  )}
                </tr>
              </thead>
              <tbody>
                {[...list]
                  .sort((a, b) => a.startDate < b.startDate ? 1 : -1)
                  .map((p) => {
                    const c = computed[p.id];
                    const it = ITEM_BY_ID[p.itemId];
                    const sym = c?.symbol || "₹";
                    return (
                      <tr key={p.id} className="border-b border-border/60 last:border-0">
                        <td className="px-3 py-2 text-left">
                          <span className="font-semibold text-text">{p.name}</span>
                        </td>
                        <td className="px-3 py-2 text-left">
                          {it ? (
                            <Link to={`/report/${it.id}`} className="text-accent hover:underline">
                              {it.id} — {it.title}
                            </Link>
                          ) : (
                            p.file
                          )}
                          <span className="block text-muted text-[11px] truncate max-w-[320px]">
                            {c?.seriesLabel || p.path || "main series"}
                          </span>
                        </td>
                        <td className="px-3 py-2 text-left font-mono text-muted-2">
                          {c && !c.error ? `${c.atDate} → ${c.lastDate}` : p.startDate}
                        </td>
                        <td className="px-3 py-2 text-right font-mono text-muted-2">{money(p.capital, sym, 0)}</td>
                        {c?.error ? (
                          <td colSpan={5} className="px-3 py-2 text-left text-assumption text-[12px]">
                            {c.error}
                          </td>
                        ) : c ? (
                          <>
                            <td className="px-3 py-2 text-right font-mono text-text">{money(c.nowValue, sym, 0)}</td>
                            <td
                              className={`px-3 py-2 text-right font-mono ${c.pnl >= 0 ? "text-positive" : "text-negative"}`}
                            >
                              {money(c.pnl, sym, 0)}
                            </td>
                            <td
                              className={`px-3 py-2 text-right font-mono ${c.retPct >= 0 ? "text-positive" : "text-negative"}`}
                            >
                              {pct(c.retPct)}
                            </td>
                            <td className="px-3 py-2 text-right font-mono text-muted-2">{pct(c.cagrPct)}</td>
                          </>
                        ) : (
                          <td colSpan={5} className="px-3 py-2 text-left text-muted text-[12px]">
                            computing…
                          </td>
                        )}
                        <td className="px-3 py-2 text-right">
                          <button
                            onClick={() => remove(p.id)}
                            className="text-muted hover:text-negative text-[14px] leading-none cursor-pointer px-1"
                            aria-label="Remove"
                          >
                            ×
                          </button>
                        </td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </div>
  );
}

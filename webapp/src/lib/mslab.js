import { humanize } from "./format";

// Loads webapp/public/data/ms_lab.json (written by build_ms_lab.py at the
// repo root) exactly once per session. Every screen that shows the
// MomentumScore-style review data (health scores, robustness halves, tax
// reports) goes through here.
const LAB_BLOCKLIST = new Set(["instruments", "variants", "portfolios", "configs"]);

let cache = null;
let inflight = null;

export function loadLab() {
  if (cache) return Promise.resolve(cache);
  if (!inflight) {
    inflight = fetch("./data/ms_lab.json")
      .then((r) => {
        if (!r.ok) {
          throw new Error(
            "ms_lab.json not found — run `py -3 build_ms_lab.py` in the repo root to regenerate it"
          );
        }
        return r.json();
      })
      .then((j) => {
        cache = j;
        return j;
      })
      .catch((e) => {
        inflight = null;
        throw e;
      });
  }
  return inflight;
}

/** "instruments/NIFTY50/variants/frictionless" -> "Nifty50 / Frictionless" */
export function msLabel(path) {
  if (!path) return "";
  const segs = String(path).split("/");
  const kept = segs.filter((s) => !LAB_BLOCKLIST.has(s));
  return (kept.length ? kept : segs).map(humanize).join(" / ");
}

/** Every scored series across every report file, flattened for the health
 * leaderboard. Shape per row: {file, path, label, kind, health, robustness}. */
export function labSeriesRows(lab) {
  if (!lab) return [];
  const rows = [];
  for (const [file, rep] of Object.entries(lab.reports || {})) {
    for (const s of rep.series || []) {
      rows.push({
        file,
        path: s.path,
        label: msLabel(s.path),
        kind: s.kind,
        health: s.health || null,
        robustness: s.robustness || null,
      });
    }
  }
  return rows;
}

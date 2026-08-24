// One accent hue per strategy category, purely for the icon-glow badge on
// each strategy card — a quick visual "which family is this" cue at a
// glance, distinct from the green/red gain/loss semantics used elsewhere.
const PALETTE = {
  "NIFTY 50 Breakout System": "#6ae4ff",
  "Cash Timing (NIFTY 50)": "#ffb84d",
  "Midcap Rotation": "#c77dff",
  "SIP + Tactical Overlays (Midcap)": "#34e0a1",
  "Momentum Factor": "#ff9d5c",
  "Quality Factor": "#ff6ec7",
  "Midcap Momentum + Gold": "#f2e86a",
  "Sector Rotation": "#5ec8f2",
  "Momentum + Gold, Drawdown-Triggered": "#ff5c72",
  "Beyond India": "#8f9dff",
};
const FALLBACK = Object.values(PALETTE);

export function colorForCategory(label, index = 0) {
  return PALETTE[label] ?? FALLBACK[index % FALLBACK.length];
}

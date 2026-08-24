// mirrors the @theme tokens in index.css — kept in sync manually since
// Recharts needs raw hex/rgba strings, not CSS var references.
export const COLORS = {
  ground: "#0a0f1a",
  panel: "#131a2b",
  panel2: "#1a2338",
  border: "rgba(255, 255, 255, 0.09)",
  accent: "#6ae4ff",
  positive: "#34e0a1",
  assumption: "#ffb84d",
  negative: "#ff5c72",
  text: "#f3f6fa",
  muted: "#8593ab",
  muted2: "#aab6c9",
};

// chart-line rotation for overlaying several series on one chart — leads
// with the brand signal cyan for the first (usually most-featured) series,
// then a colorblind-considerate rotation of hues distinct from the
// positive/negative pair so a multi-series overlay never reads as a
// gain/loss signal by accident.
export const SERIES_PALETTE = [
  COLORS.accent,
  "#c77dff", // violet
  "#ffb84d", // amber
  "#34e0a1", // green
  "#ff5c72", // coral
  COLORS.muted2,
  "#5ec8f2", // sky blue
  "#f2e86a", // pale yellow
];

export function seriesColor(index) {
  return SERIES_PALETTE[index % SERIES_PALETTE.length];
}

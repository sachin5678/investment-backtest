// the same dark palette used across every static HTML report in this project
export const COLORS = {
  ground: "#08171E",
  panel: "#0F2630",
  panel2: "#132B36",
  border: "#1E3A45",
  positive: "#37F083",
  assumption: "#F2B03C",
  negative: "#F2643C",
  text: "#E6EDF0",
  muted: "#7E97A0",
  muted2: "#9FB4BB",
};

// a small, colorblind-considerate rotation for overlaying many series on one chart
export const SERIES_PALETTE = [
  COLORS.positive,
  COLORS.negative,
  COLORS.assumption,
  "#5EC8F2", // sky blue — extra hue beyond the base 3-color pill system, chart-only
  COLORS.text,
  COLORS.muted2,
  "#C77DFF", // violet — extra hue, chart-only
  "#F2E86A", // pale yellow — extra hue, chart-only
];

export function seriesColor(index) {
  return SERIES_PALETTE[index % SERIES_PALETTE.length];
}

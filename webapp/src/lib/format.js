export function pct(v, decimals = 1, signed = true) {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  const s = signed && v > 0 ? "+" : "";
  return `${s}${v.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })}%`;
}

export function money(v, symbol = "₹", decimals = 0) {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  const sign = v < 0 ? "-" : "";
  return `${sign}${symbol}${Math.abs(v).toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })}`;
}

export function kindOf(v) {
  if (v === null || v === undefined || Number.isNaN(v)) return "neutral";
  return v > 0 ? "positive" : v < 0 ? "negative" : "neutral";
}

/** title-case a snake_case / camel path segment into a readable label */
export function humanize(key) {
  return key
    .replace(/_/g, " ")
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

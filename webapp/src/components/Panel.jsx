export default function Panel({ children, className = "", tight = false, accent = null }) {
  const border = accent === "danger" ? "border-2 border-negative" : "border border-border";
  const padding = tight ? "p-5" : "p-6";
  return (
    <div className={`bg-panel ${border} rounded-2xl ${padding} ${className}`}>{children}</div>
  );
}

export function WhatThisShows({ children }) {
  if (!children) return null;
  return <p className="text-muted-2 text-[13px] italic mb-3">{children}</p>;
}

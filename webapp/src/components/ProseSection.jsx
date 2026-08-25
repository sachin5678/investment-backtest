import { useState } from "react";
import Panel, { WhatThisShows } from "./Panel";
import Pill from "./Pill";
import LoginModal from "./LoginModal";

function ProsePanel({ panel }) {
  const isLimitations = panel.heading === "Limitations";
  return (
    <Panel accent={panel.pills.some((p) => p.kind === "negative") ? "danger" : null}>
      {(panel.heading || panel.pills.length > 0) && (
        <div className="flex items-center gap-2 mb-2 flex-wrap">
          {panel.heading && <h3 className="text-base font-bold text-text">{panel.heading}</h3>}
          {panel.pills.map((p, i) => (
            <Pill key={i} kind={p.kind}>
              {p.text}
            </Pill>
          ))}
        </div>
      )}
      <WhatThisShows>{panel.what_this_shows}</WhatThisShows>
      {panel.paragraphs.map((p, i) => (
        <p key={i} className="text-[13.5px] text-muted-2 leading-relaxed mb-3 last:mb-0">
          {p}
        </p>
      ))}
      {panel.list_items.length > 0 && (
        <ul className={`text-[13px] text-muted-2 list-disc pl-5 leading-relaxed ${isLimitations ? "space-y-1.5" : ""}`}>
          {panel.list_items.map((li, i) => (
            <li key={i}>{li}</li>
          ))}
        </ul>
      )}
    </Panel>
  );
}

/** Renders the faithfully-extracted disclosure/honesty-note/limitations
 * prose from the original static report, collapsed behind a toggle by
 * default so the default view stays scannable — nothing is summarized or
 * dropped, it's the same text, just tucked behind one click.
 *
 * `locked`: when true (not logged in), this text was never fetched at all
 * — see ReportPage.jsx, which only requests report_prose from Supabase
 * for a signed-in session — so there's nothing to toggle; a login prompt
 * renders instead. */
export default function ProseSection({ content, open, onToggle, locked }) {
  const [loginOpen, setLoginOpen] = useState(false);

  if (locked) {
    return (
      <div className="mt-6">
        <button
          onClick={() => setLoginOpen(true)}
          className="w-full flex items-center justify-between gap-3 px-5 py-3 rounded-xl border border-assumption/40 bg-assumption/5 text-left cursor-pointer transition-colors hover:border-assumption focus-visible:outline-2 focus-visible:outline-accent"
        >
          <span className="text-sm font-semibold text-text">🔒 Log in to read the full analysis, disclosures &amp; limitations</span>
          <span className="text-assumption text-xs font-semibold">Log in →</span>
        </button>
        {loginOpen && <LoginModal onClose={() => setLoginOpen(false)} />}
      </div>
    );
  }

  if (!content) return null;
  const panels = content.pages.flatMap((p) => p.panels);
  if (!panels.length) return null;

  return (
    <div className="mt-6">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between gap-3 px-5 py-3 rounded-xl border border-border bg-panel-2 text-left cursor-pointer transition-colors hover:border-muted focus-visible:outline-2 focus-visible:outline-accent"
        aria-expanded={open}
      >
        <span className="text-sm font-semibold text-text">
          {open ? "Hide" : "Read"} the full analysis, disclosures &amp; limitations
        </span>
        <span className="text-muted text-xs">{open ? "▲ collapse" : "▼ expand"}</span>
      </button>
      {open && (
        <div className="mt-4 space-y-4">
          {panels.map((panel, i) => (
            <ProsePanel key={i} panel={panel} />
          ))}
        </div>
      )}
    </div>
  );
}

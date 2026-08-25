import { useState } from "react";
import Panel from "./Panel";
import LoginModal from "./LoginModal";

const ICON_LOCK = "M6 11h12v9h-12z M9 11V7a3 3 0 0 1 6 0v4";

/** Shown instead of a premium report's KPIs/charts/prose when the visitor
 * isn't logged in — the report's own results JSON is never even fetched
 * in this state (see ReportPage.jsx), so there's genuinely nothing here
 * to inspect, not just something visually hidden. */
export default function LockedReportGate({ title }) {
  const [loginOpen, setLoginOpen] = useState(false);

  return (
    <Panel className="text-center py-14">
      <div className="w-14 h-14 rounded-full bg-assumption/10 flex items-center justify-center mx-auto mb-5">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6 text-assumption">
          <path d={ICON_LOCK} />
        </svg>
      </div>
      <h2 className="text-lg font-bold text-text mb-2">This is a premium strategy</h2>
      <p className="text-[13.5px] text-muted max-w-[420px] mx-auto leading-relaxed mb-6">
        “{title}” — its full backtest results, charts, and trade-level detail are only shown to logged-in users.
      </p>
      <button
        onClick={() => setLoginOpen(true)}
        className="inline-flex items-center text-[13px] font-semibold rounded-full bg-text text-ground px-5 py-2.5 transition-opacity hover:opacity-85 cursor-pointer focus-visible:outline-2 focus-visible:outline-accent"
      >
        Log in to view
      </button>
      {loginOpen && <LoginModal onClose={() => setLoginOpen(false)} />}
    </Panel>
  );
}

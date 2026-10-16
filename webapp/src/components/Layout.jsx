import { useState } from "react";
import { Outlet, useParams, useLocation, Link } from "react-router-dom";
import Sidebar from "./Sidebar";
import AuthButton from "./AuthButton";
import { ITEM_BY_ID } from "../data/reportsIndex";

// header titles for the Tools routes (everything outside report/:id and
// /compare, which derive their own titles from ITEM_BY_ID)
const TOOL_TITLES = {
  "/builder": {
    title: "Builder Labs",
    subtitle: "Reports 94–98 — MomentumScore's builder tabs (Protect, Conditions, Money, Pick), one knob at a time, then stacked",
  },
  "/health": {
    title: "Strategy Health",
    subtitle: "MomentumScore's 10-target scorecard, applied to every series in the project",
  },
  "/tax": {
    title: "Capital-Gains Tax",
    subtitle: "What each report's own trade log would owe under Indian capital-gains rules — estimate",
  },
  "/mix": {
    title: "Multi-System Mixer",
    subtitle: "Blend any strategies into one constant-weight combined curve",
  },
  "/track": {
    title: "My Portfolios",
    subtitle: "Paper-track any strategy from any date — saved in this browser",
  },
  "/ranks": {
    title: "Ranking Preview",
    subtitle: "Report 93's exit-rank-52 review engine, recomputed at the latest close",
  },
};

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { id } = useParams();
  const location = useLocation();
  const item = ITEM_BY_ID[id];
  const isCompare = location.pathname === "/compare";
  const tool = TOOL_TITLES[location.pathname] || null;

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      {sidebarOpen && (
        <button
          aria-label="Close navigation"
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 bg-black/50 z-30 md:hidden cursor-pointer"
        />
      )}
      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <div className="flex items-center gap-4 px-6 py-3.5 border-b border-border bg-panel/50 sticky top-0 z-20 backdrop-blur-sm">
          <button
            aria-label="Toggle navigation"
            onClick={() => setSidebarOpen((v) => !v)}
            className="md:hidden text-muted border border-border rounded-lg px-3 py-2 text-sm cursor-pointer"
          >
            ☰
          </button>
          {item ? (
            <>
              <div className="min-w-0 flex-1">
                <h2 className="text-[15px] font-semibold text-text truncate">{item.title}</h2>
                <p className="text-xs text-muted truncate">{item.subtitle}</p>
              </div>
              <AuthButton />
              <Link
                to="/"
                className="hidden sm:inline-flex items-center gap-1.5 text-[13px] font-medium text-accent border border-accent/40 rounded-full px-3.5 py-1.5 shrink-0 transition-colors hover:bg-accent-dim focus-visible:outline-2 focus-visible:outline-accent"
              >
                Overview
              </Link>
            </>
          ) : isCompare || tool ? (
            <>
              <div className="min-w-0 flex-1">
                <h2 className="text-[15px] font-semibold text-text truncate">
                  {tool ? tool.title : "Master Comparison"}
                </h2>
                <p className="text-xs text-muted truncate">
                  {tool ? tool.subtitle : "Every strategy variant, sortable and filterable, against NIFTY 50"}
                </p>
              </div>
              <AuthButton />
              <Link
                to="/"
                className="hidden sm:inline-flex items-center gap-1.5 text-[13px] font-medium text-accent border border-accent/40 rounded-full px-3.5 py-1.5 shrink-0 transition-colors hover:bg-accent-dim focus-visible:outline-2 focus-visible:outline-accent"
              >
                Overview
              </Link>
            </>
          ) : (
            <div className="flex-1 flex justify-end">
              <AuthButton />
            </div>
          )}
        </div>
        <div className="flex-1 px-4 sm:px-8 py-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

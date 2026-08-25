import { useState } from "react";
import { Outlet, useParams, Link } from "react-router-dom";
import Sidebar from "./Sidebar";
import AuthButton from "./AuthButton";
import { ITEM_BY_ID } from "../data/reportsIndex";

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { id } = useParams();
  const item = ITEM_BY_ID[id];

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

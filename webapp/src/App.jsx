import { HashRouter, Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import ReportPage from "./pages/ReportPage";
import Overview from "./pages/Overview";
import { AuthProvider } from "./context/AuthContext";

// HashRouter (not BrowserRouter) is deliberate: it makes every route work
// when the built app is served as plain static files — from a GitHub Pages
// subpath, or even opened directly from disk — with no server-side rewrite
// rules needed for deep links like #/report/07.
// The Overview page is a full-bleed landing page with its own transparent
// top nav — deliberately NOT nested inside the sidebar app-shell (Layout),
// the same way a product's marketing site and its logged-in app are two
// different layouts. Picking a strategy from Overview is what transitions
// you into the sidebar-driven "app" at /report/:id.
export default function App() {
  return (
    <AuthProvider>
      <HashRouter>
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/" element={<Layout />}>
            <Route path="report/:id" element={<ReportPage />} />
          </Route>
          {/* Defensive fallback: HashRouter treats the WHOLE url hash as its
              routing namespace, so a plain in-page anchor like #methodology
              (rather than #/methodology) rewrites the hash to something no
              route matches, which otherwise renders blank. The in-page nav
              links now intercept clicks and scroll manually instead of
              touching the hash (see lib/scrollTo.js) — this catch-all is
              just a safety net for any hash that still ends up unmatched
              (an old bookmark, a stale tab, direct hash entry). */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </HashRouter>
    </AuthProvider>
  );
}

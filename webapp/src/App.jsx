import { HashRouter, Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import ReportPage from "./pages/ReportPage";
import { ALL_ITEMS } from "./data/reportsIndex";

// HashRouter (not BrowserRouter) is deliberate: it makes every route work
// when the built app is served as plain static files — from a GitHub Pages
// subpath, or even opened directly from disk — with no server-side rewrite
// rules needed for deep links like #/report/07.
export default function App() {
  const firstId = ALL_ITEMS[0].id;
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to={`/report/${firstId}`} replace />} />
          <Route path="report/:id" element={<ReportPage />} />
        </Route>
      </Routes>
    </HashRouter>
  );
}

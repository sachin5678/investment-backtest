# NIFTY & Midcap Strategy Lab

A Vite + React + Tailwind (v4) web app for the 18 NIFTY/Midcap/Smallcap backtest
reports in this project — a daily-use replacement for the old iframe-based
`dashboard.html` hub, with real smooth charts (Recharts) instead of hand-rolled
inline SVG.

## Local development

From the `webapp/` folder:

```bash
npm install
npm run dev
```

This starts the Vite dev server (defaults to `http://localhost:5173/`). Open
it and it redirects to `#/report/01`; use the sidebar or the "Jump to a
report" dropdown to move between all 18 reports.

To build and sanity-check the production bundle locally:

```bash
npm run build
npm run preview
```

## How data flows into the app

- `public/data/results*.json` — the 17 backtest output files (same JSON
  every `build_html*.py` script already consumes), copied as-is from the
  project root.
- `public/data/report_content.json` — the prose (disclosures, honesty pills,
  "what this shows" notes, limitations) extracted from the 18 already-built
  static HTML reports by `../extract_report_content.py`. Regenerate it with:

  ```bash
  py -3 ../extract_report_content.py
  ```

  from the project root, any time the static HTML reports' text changes.
- `src/data/reportsIndex.js` — the list of all 18 reports (id, title,
  subtitle, icon, which `resultsN.json` file it reads), grouped the same way
  as the old dashboard's sidebar.
- `src/lib/viewmodel.js` — a **generic** detector (`extractSeries`) that
  walks any `resultsN.json` looking for series-shaped objects (an
  `equity_curve`/`value_curve` plus the standard metric fields every
  `backtest*.py` writes). Because it's schema-driven rather than hand-mapped
  per report, a new report's JSON usually needs zero new code — see below.

## Adding report 19 (or any future report)

1. Copy the new `resultsN.json` into `public/data/`.
2. Add one entry to the `GROUPS` array in `src/data/reportsIndex.js`
   (`{ id, file, icon, title, subtitle }`) — copy the shape of an existing
   entry.
3. Re-run `py -3 ../extract_report_content.py` so
   `report_content.json` picks up the new report's static HTML prose (only
   needed if a matching `NN_*.html` exists).
4. Load `#/report/19` locally and check the browser console — if the new
   report's JSON nests two series under a path that collapses to the same
   label (rare — `extractSeries` has a dedup safety net for this), add the
   colliding wrapper key to `LABEL_BLOCKLIST` in `src/lib/viewmodel.js`, or
   let the safety net's auto-suffix handle it.

No other code changes are needed for a report that follows the existing
`backtest*.py` JSON conventions.

## Deploying to GitHub Pages

The app is already built for this: `react-router-dom`'s `HashRouter` (not
`BrowserRouter`) means every route is a URL fragment (`#/report/07`), so
GitHub Pages' static file server can serve it with zero rewrite rules. Vite's
`base: './'` (in `vite.config.js`) makes every asset reference relative, so
the build works from a repo subpath (`https://<user>.github.io/<repo>/`) as
well as from a custom domain root.

**Option A — GitHub Actions (recommended, deploys on every push):**

1. Push this project to a GitHub repo.
2. In the repo settings → Pages, set Source to "GitHub Actions".
3. Add `.github/workflows/deploy.yml` at the repo root:

   ```yaml
   name: Deploy to GitHub Pages
   on:
     push:
       branches: [main]
   permissions:
     contents: read
     pages: write
     id-token: write
   jobs:
     build:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-node@v4
           with:
             node-version: 20
         - run: npm ci
           working-directory: webapp
         - run: npm run build
           working-directory: webapp
         - uses: actions/upload-pages-artifact@v3
           with:
             path: webapp/dist
     deploy:
       needs: build
       runs-on: ubuntu-latest
       environment:
         name: github-pages
         url: ${{ steps.deployment.outputs.page_url }}
       steps:
         - id: deployment
           uses: actions/deploy-pages@v4
   ```

4. Push to `main` — the app builds and deploys automatically. The site will
   be live at `https://<user>.github.io/<repo>/`.

**Option B — `gh-pages` package (manual deploys from your machine):**

```bash
npm install -D gh-pages
```

Add to `package.json` `scripts`: `"deploy": "npm run build && gh-pages -d dist"`,
then run:

```bash
npm run deploy
```

This pushes `dist/` to a `gh-pages` branch, which you point GitHub Pages at
in the repo settings (Source: "Deploy from a branch" → `gh-pages` / `root`).

Either way, `public/data/*.json` ships inside `dist/` automatically (Vite
copies everything under `public/` verbatim) — no separate data hosting step
needed.

## Project structure

```
webapp/
  public/data/            results*.json + report_content.json
  src/
    components/            Sidebar, Layout, Panel, KpiTable, SmoothChart,
                            DrawdownChart, ProseSection, Pill, Icon
    data/reportsIndex.js    the 18-report catalog (sidebar groups)
    lib/
      viewmodel.js          extractSeries() + chart data helpers
      format.js             number/date formatting helpers
      colors.js             shared palette + per-series chart colors
    pages/ReportPage.jsx     generic per-report page (used by all 18)
    App.jsx                 HashRouter + routes
```

## Relationship to `dashboard.html`

The old `dashboard.html` (iframe hub over the 18 standalone HTML reports)
still works and still exists at the project root — it's untouched. This app
is the intended replacement for daily use (native charts, faster nav, one
consistent UI), but nothing stops you from keeping both; the standalone
`NN_*.html` files are still the canonical, most detailed version of each
report's write-up if you ever need to double check a number.

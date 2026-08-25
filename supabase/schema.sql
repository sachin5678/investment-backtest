-- Signal Lab — premium content gating schema.
--
-- Run this once in the Supabase SQL editor (Project → SQL Editor → New
-- query) for a fresh project, before running scripts/seed_supabase.py.
--
-- Two tables, both with Row Level Security enabled so access is enforced
-- by Postgres itself, not just hidden in the frontend:
--
--   report_prose     — the "strategy logic, disclosures & limitations"
--                       text for EVERY report (1-31). Readable only when
--                       logged in — this is what makes "always hide
--                       analysis from free users" a real guarantee rather
--                       than a UI convenience, since the text is never
--                       present in the public bundle at all.
--
--   premium_reports   — the full results JSON (KPIs, equity curves, trade
--                        logs) for reports 11 and up. Readable only when
--                        logged in. Reports 1-10 keep their results JSON
--                        in the public static webapp/public/data/ files
--                        (the agreed free tier), so they are NOT stored
--                        here.
--
-- Both tables are keyed by report_id (matches the "id" field in
-- webapp/src/data/reportsIndex.js, e.g. "11", "24", "31").

create table if not exists report_prose (
  report_id text primary key,
  content jsonb not null,
  updated_at timestamptz not null default now()
);

create table if not exists premium_reports (
  report_id text primary key,
  results jsonb not null,
  updated_at timestamptz not null default now()
);

alter table report_prose enable row level security;
alter table premium_reports enable row level security;

-- Drop-then-create so this script is safe to re-run.
drop policy if exists "authenticated read report_prose" on report_prose;
create policy "authenticated read report_prose"
  on report_prose for select
  to authenticated
  using (true);

drop policy if exists "authenticated read premium_reports" on premium_reports;
create policy "authenticated read premium_reports"
  on premium_reports for select
  to authenticated
  using (true);

-- landing_stats: the ONE thing that's deliberately public, no login
-- required — three aggregate marketing numbers for the homepage hero
-- ("31 strategies tested", "best CAGR found", "markets covered"). These
-- are computed once across ALL 31 reports (including premium ones) so
-- they always reflect the true totals regardless of who's viewing, but
-- they carry no per-strategy detail — nothing here identifies which
-- specific strategy produced the best number, so nothing premium leaks
-- through this table.
create table if not exists landing_stats (
  id int primary key default 1,
  strategies_tested int not null,
  best_cagr_pct numeric not null,
  markets_covered int not null,
  longest_backtest_years int not null,
  updated_at timestamptz not null default now(),
  constraint landing_stats_singleton check (id = 1)
);

alter table landing_stats enable row level security;

drop policy if exists "anyone read landing_stats" on landing_stats;
create policy "anyone read landing_stats"
  on landing_stats for select
  to anon, authenticated
  using (true);

-- No insert/update/delete policies for the anon or authenticated roles on
-- any of the three tables above — writes only ever happen from
-- scripts/seed_supabase.py using the service_role key, which bypasses RLS
-- entirely and is never shipped to the browser.

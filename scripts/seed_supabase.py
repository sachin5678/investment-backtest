"""
One-time (and safely re-runnable) seed script for the Supabase premium-
content backend. Run this AFTER creating a Supabase project and applying
supabase/schema.sql in its SQL editor.

Uses the service_role key (bypasses RLS, admin-only) — never commit this
key or put it in the frontend. Reads it from the environment:

    SUPABASE_URL=https://xxxx.supabase.co
    SUPABASE_SERVICE_ROLE_KEY=eyJ...

Set them for one command (PowerShell):
    $env:SUPABASE_URL="https://xxxx.supabase.co"; $env:SUPABASE_SERVICE_ROLE_KEY="eyJ..."; py -3 scripts/seed_supabase.py

What it does:
  1. Creates (or confirms) the login user: username "sachin" -> internal
     email sachin@signal-lab.local, password 121101, pre-confirmed (no
     real email ever sent or needed).
  2. Reads webapp/src/data/reportsIndex.js to get the canonical
     {report_id -> results filename} map for every report.
  3. Upserts EVERY report's extracted prose (from
     webapp/public/data/report_content.json, produced by
     extract_report_content.py) into the report_prose table.
  4. Upserts the full results JSON for every report with id >= 11 into the
     premium_reports table, reading each one straight from the project
     root's resultsN.json files (NOT from webapp/public/data/, which only
     keeps the free tier's 1-10 going forward).
"""
import json
import os
import re
import sys

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGIN_USERNAME = "sachin"
LOGIN_EMAIL = "sachin@signal-lab.local"
LOGIN_PASSWORD = "121101"
PREMIUM_MIN_ID = 11


def env_or_die(name):
    v = os.environ.get(name)
    if not v:
        print(f"Missing required environment variable: {name}", file=sys.stderr)
        sys.exit(1)
    return v


def parse_reports_index():
    """Extract {id: file} for every report from reportsIndex.js without
    needing a JS runtime — the file is a flat, consistently-formatted
    array of object literals, so a line-oriented regex is reliable here."""
    path = os.path.join(ROOT, "webapp", "src", "data", "reportsIndex.js")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    pattern = re.compile(r'id:\s*"(\d+)"\s*,\s*file:\s*"([^"]+)"')
    return {m.group(1): m.group(2) for m in pattern.finditer(text)}


def create_login_user(base_url, service_key):
    url = f"{base_url}/auth/v1/admin/users"
    headers = {"apikey": service_key, "Authorization": f"Bearer {service_key}", "Content-Type": "application/json"}

    # Does the user already exist? list + filter (admin endpoint supports
    # a simple paginated list; the dataset here is tiny).
    r = requests.get(url, headers=headers, params={"page": 1, "per_page": 200})
    r.raise_for_status()
    existing = next((u for u in r.json().get("users", []) if u.get("email") == LOGIN_EMAIL), None)
    if existing:
        # make sure the password matches what we expect, idempotently
        uid = existing["id"]
        r2 = requests.put(f"{url}/{uid}", headers=headers, json={"password": LOGIN_PASSWORD, "email_confirm": True})
        r2.raise_for_status()
        print(f"Login user already existed (id={uid}) — password re-synced.")
        return

    r = requests.post(url, headers=headers, json={
        "email": LOGIN_EMAIL, "password": LOGIN_PASSWORD, "email_confirm": True,
        "user_metadata": {"username": LOGIN_USERNAME},
    })
    r.raise_for_status()
    print(f"Created login user {LOGIN_USERNAME} ({LOGIN_EMAIL}).")


def upsert_rows(base_url, service_key, table, rows, conflict_col):
    if not rows:
        return
    url = f"{base_url}/rest/v1/{table}"
    headers = {
        "apikey": service_key, "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates",
    }
    r = requests.post(url, headers=headers, params={"on_conflict": conflict_col}, json=rows)
    if not r.ok:
        print(f"  FAILED upserting into {table}: {r.status_code} {r.text[:300]}", file=sys.stderr)
        r.raise_for_status()


def main():
    base_url = env_or_die("SUPABASE_URL").rstrip("/")
    service_key = env_or_die("SUPABASE_SERVICE_ROLE_KEY")

    create_login_user(base_url, service_key)

    id_to_file = parse_reports_index()
    print(f"Found {len(id_to_file)} reports in reportsIndex.js")

    content_path = os.path.join(ROOT, "report_content.json")
    with open(content_path, encoding="utf-8") as f:
        all_content = json.load(f)

    prose_rows = [{"report_id": rid, "content": content} for rid, content in all_content.items()]
    upsert_rows(base_url, service_key, "report_prose", prose_rows, "report_id")
    print(f"Upserted prose for {len(prose_rows)} reports into report_prose.")

    premium_rows = []
    for rid, fname in id_to_file.items():
        if int(rid) < PREMIUM_MIN_ID:
            continue
        results_path = os.path.join(ROOT, fname)
        if not os.path.exists(results_path):
            print(f"  WARNING: {fname} not found for report {rid}, skipping", file=sys.stderr)
            continue
        with open(results_path, encoding="utf-8") as f:
            results = json.load(f)
        premium_rows.append({"report_id": rid, "results": results})

    upsert_rows(base_url, service_key, "premium_reports", premium_rows, "report_id")
    print(f"Upserted {len(premium_rows)} premium reports (id >= {PREMIUM_MIN_ID}) into premium_reports.")

    print("\nDone. Remember to remove the id>=11 results*.json files from webapp/public/data/")
    print("(see scripts/remove_public_premium_data.py) so they're no longer served statically.")


if __name__ == "__main__":
    main()

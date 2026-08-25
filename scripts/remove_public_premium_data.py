"""
Removes premium-tier data files from webapp/public/data/ now that they
live in Supabase instead (see supabase/schema.sql, scripts/seed_supabase.py):

  - report_content.json — the prose/analysis text for EVERY report (1-31)
    is gated behind login now, so it can never sit in a public static file.
  - resultsN.json for every report with id >= 11 — the full KPI/equity-curve
    data for the premium tier now lives only in the RLS-protected
    premium_reports table.

Reports 1-10's own resultsN.json files are left untouched — those stay
free and public, per the agreed tier split.

Safe to re-run; silently skips files that are already gone.
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC_DATA = os.path.join(ROOT, "webapp", "public", "data")
PREMIUM_MIN_ID = 11


def parse_reports_index():
    path = os.path.join(ROOT, "webapp", "src", "data", "reportsIndex.js")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    pattern = re.compile(r'id:\s*"(\d+)"\s*,\s*file:\s*"([^"]+)"')
    return {m.group(1): m.group(2) for m in pattern.finditer(text)}


def main():
    removed = []

    content_path = os.path.join(PUBLIC_DATA, "report_content.json")
    if os.path.exists(content_path):
        os.remove(content_path)
        removed.append("report_content.json")

    id_to_file = parse_reports_index()
    for rid, fname in id_to_file.items():
        if int(rid) < PREMIUM_MIN_ID:
            continue
        fpath = os.path.join(PUBLIC_DATA, fname)
        if os.path.exists(fpath):
            os.remove(fpath)
            removed.append(fname)

    if removed:
        print(f"Removed {len(removed)} file(s) from webapp/public/data/:")
        for r in removed:
            print(f"  - {r}")
    else:
        print("Nothing to remove — already clean.")


if __name__ == "__main__":
    main()

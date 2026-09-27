"""Extracts the prose (headings, disclosure/limitations/honesty-note text)
from every already-generated, already-verified NN_*.html report into a
single JSON keyed by report id, for the new React app to render faithfully
without re-typing any of it. Deliberately SKIPS any panel that contains a
<table> or <svg> or a "kpi-val" element — those are data panels that the
React app rebuilds natively (as real components bound to the JSON results),
not text to copy.
"""
import json
import re
import glob
from bs4 import BeautifulSoup

FILES = sorted(glob.glob("[0-9][0-9]_*.html"))


def is_data_panel(div):
    if div.find("table") or div.find("svg"):
        return True
    for el in div.find_all(class_=True):
        classes = el.get("class") or []
        if any("kpi-val" in c for c in classes):
            return True
    return False


def extract_pills(el):
    out = []
    for span in el.find_all("span"):
        classes = " ".join(span.get("class") or [])
        if "rounded-full" not in classes:
            continue
        kind = "assumption" if "F2B03C" in classes else (
            "positive" if "37F083" in classes else (
                "negative" if "F2643C" in classes else "neutral"))
        text = span.get_text(strip=True).lstrip("●▲ ").strip()
        out.append({"kind": kind, "text": text})
    return out


def clean_text(el):
    # drop pill spans from the running text so prose reads cleanly; pills are
    # surfaced separately per panel
    el = BeautifulSoup(str(el), "html.parser")
    for span in el.find_all("span"):
        classes = " ".join(span.get("class") or [])
        if "rounded-full" in classes:
            span.replace_with(f'"{span.get_text(strip=True).lstrip("● ▲ ")}"')
    text = el.get_text(" ", strip=True)
    text = re.sub(r"\s+([:.,;)])", r"\1", text)   # no space before punctuation
    text = re.sub(r"(\()\s+", r"\1", text)          # no space after an opening paren
    text = re.sub(r"\s{2,}", " ", text)             # collapse any double spaces
    return text


def extract_panels(root):
    panels = []
    seen_ids = set()
    for div in root.find_all("div", class_=True):
        classes = " ".join(div.get("class") or [])
        if "rounded-2xl" not in classes:
            continue
        if id(div) in seen_ids:
            continue
        # skip nested panels (only take the outermost rounded-2xl containers)
        if div.find_parent("div", class_=lambda c: c and "rounded-2xl" in c):
            continue
        if is_data_panel(div):
            continue
        heading_el = div.find(["h2", "h3"])
        heading = heading_el.get_text(strip=True) if heading_el else None
        pills = extract_pills(div)
        # "WHAT THIS SHOWS" italic line, if present
        what_shows_el = div.find(class_=lambda c: c and "italic" in c)
        what_shows = what_shows_el.get_text(strip=True) if what_shows_el else None
        paragraphs = []
        for p in div.find_all("p"):
            if what_shows_el and p is what_shows_el:
                continue
            txt = clean_text(p)
            if txt:
                paragraphs.append(txt)
        list_items = [li.get_text(strip=True) for li in div.find_all("li")]
        if not (heading or paragraphs or list_items):
            continue
        panels.append({
            "heading": heading, "pills": pills, "what_this_shows": what_shows,
            "paragraphs": paragraphs, "list_items": list_items,
        })
        seen_ids.add(id(div))
    return panels


def main():
    result = {}
    for fp in FILES:
        report_id = fp.split("_")[0]
        html = open(fp, encoding="utf-8").read()
        soup = BeautifulSoup(html, "html.parser")
        header = soup.find("header")
        title = header.find("h1").get_text(strip=True) if header else None
        subtitle = header.find("p").get_text(strip=True) if header else None
        source_div = header.find("div", class_=lambda c: c and "mono" in c) if header else None
        source_line = source_div.get_text(" ", strip=True) if source_div else None

        body_root = soup.find("body")
        panels = extract_panels(body_root)

        entry = result.setdefault(report_id, {
            "title": title, "subtitle": subtitle, "source_line": source_line,
            "pages": [],
        })
        entry["pages"].append({"file": fp, "panels": panels})

    with open("webapp/public/data/report_content.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1, ensure_ascii=False)

    for rid, entry in result.items():
        total_panels = sum(len(p["panels"]) for p in entry["pages"])
        print(f"{rid}: {entry['title']!r} — {total_panels} prose panel(s) across {len(entry['pages'])} file(s)")


if __name__ == "__main__":
    main()

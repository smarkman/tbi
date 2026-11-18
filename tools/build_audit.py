"""Build the TBI content audit workbook from the two browser exports.

Usage:
  python3 tools/build_audit.py tbi-cms-export.json tbi-page-copy.json audit/

Outputs (in the output dir):
  tbi-content-audit.xlsx   - Summary, All Pages, Duplicates, Full Copy tabs
  tbi-pages.csv            - one row per page (same as the All Pages tab)
  tbi-site-copy.md         - all live page copy, cleaned, grouped by section
"""
import csv, hashlib, json, os, re, sys
from collections import Counter, defaultdict
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

TODAY_YEAR = 2026
EDITOR_CHROME = (
    ".only_edit_mode,.edit-buttons-overlay,[class*=cke],.add_content_tabs,.top_links_wrapper,"
    ".search_area_wrapper,.right_box2,script,style,noscript,.content_button,.remove_links,"
    ".breadcrumbpaginationh1section,.ui-icon,.add_link"
)

CATEGORIES = [
    ("B'nai Mitzvah", r"mitzvah|mitzvot|b'nai|bnai"),
    ("Giving & Funds", r"fund|donat|tribute|giving|give|pay|dues|pledge|campaign|kol nidre appeal|yahrzeit|memorial|sponsor|honor"),
    ("Preschool", r"preschool|pre-school|early childhood|\b2's\b|\b3's\b|\b4's\b|pre-k|aardvark|toddler|kadima"),
    ("Religious School & Youth", r"religious school|hebrew school|youth|teen|confirmation|usy|kadima|madrich|school"),
    ("Adult Learning", r"adult (ed|learn)|class|lecture|study|torah|talmud|lunch and learn|learning|book club|scholar"),
    ("Worship & Holidays", r"shabbat|service|minyan|high holy|rosh|yom kippur|sukkot|simchat|chanukah|hanukkah|purim|passover|pesach|seder|shavuot|tisha|selichot|holiday|kabbalat|havdalah|tot shabbat"),
    ("Community & Events", r"party|gala|dinner|brunch|concert|trip|social|celebrat|festival|picnic|bbq|event|night|program|sisterhood|men's club|brotherhood|hadassah|volunteer|mitzvah day|film|comedy"),
    ("About & Membership", r"about|member|join|staff|clergy|rabbi|cantor|board|leadership|history|mission|contact|visit|directions|welcome|policy|policies|faq|employment|job|rental|life cycle|lifecycle|funeral|wedding|conversion|cemetery|gift shop|newsletter|bulletin|home"),
]

EVENTISH = re.compile(r"party|gala|dinner|brunch|concert|trip|picnic|bbq|celebrat|night|program|special time|kadima|\b\d{1,2}(:\d\d)?\s*(am|pm)\b|lecture|film|comedy|workshop|training|seminar", re.I)


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def categorize(name, url):
    hay = f"{name} {url}".lower()
    for cat, pat in CATEGORIES:
        if re.search(pat, hay):
            return cat
    return "Other"


def clean_page(html):
    soup = BeautifulSoup(html or "", "lxml")
    for t in soup.select(EDITOR_CHROME):
        t.decompose()
    main = soup.select_one("#maincontent") or soup.select_one(".maincontent") or soup.body or soup
    blocks = []
    for el in main.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "td", "blockquote"]):
        if el.find(["p", "li", "td", "h1", "h2", "h3", "h4", "blockquote"]):
            continue  # leaf blocks only, avoid duplicate text
        t = re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()
        if not t:
            continue
        if el.name.startswith("h"):
            blocks.append("#" * int(el.name[1]) + " " + t)
        elif el.name == "li":
            blocks.append("- " + t)
        else:
            blocks.append(t)
    raw_words = len(main.get_text(" ", strip=True).split())
    if sum(len(b.split()) for b in blocks) < raw_words * 0.7:  # copy that sits directly in divs/spans
        t = re.sub(r"[ \t ]+", " ", main.get_text("\n", strip=True))
        blocks = [l.strip() for l in t.split("\n") if l.strip()]
    text = "\n\n".join(dict.fromkeys(blocks))  # dedupe identical consecutive-ish blocks
    links = [a.get("href", "") for a in main.find_all("a", href=True)]
    images = [i.get("src", "") for i in main.find_all("img", src=True)]
    return text, links, images


def main(cms_path, copy_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    cms = {r["view_url"]: r for r in json.load(open(cms_path))["records"]}
    copy = json.load(open(copy_path))["records"]

    pages = []
    for r in copy:
        meta = cms.get(r.get("view_url"), {})
        f = meta.get("fields", {})
        g = lambda k: (f.get(k) or {}).get("value", "").strip()
        text, links, images = clean_page(r.get("html", ""))
        name = (r.get("admin_name") or g("info[name]")).strip()
        url = g("info[url]") or urlparse(r.get("view_url", "")).path
        body_words = len(re.sub(r"^#+ ", "", text, flags=re.M).split())
        years = [int(y) for y in re.findall(r"\b(20[0-3]\d)\b", f"{name} {text}")]
        pages.append({
            "admin_name": name,
            "url": url,
            "view_url": r.get("view_url", ""),
            "edit_url": r.get("edit_url", ""),
            "status": r.get("status", ""),
            "privacy": g("info[privacy]"),
            "http_status": r.get("http_status", ""),
            "redirects_to": r.get("final_url") if r.get("final_url") and r.get("final_url") != r.get("view_url") else "",
            "seo_title": g("info[title]"),
            "h1_override": g("info[h1]"),
            "meta_description": g("info[meta_description]"),
            "category": categorize(name, url),
            "word_count": body_words,
            "links": len(links),
            "pdf_links": sum(1 for l in links if l.lower().split("?")[0].endswith(".pdf")),
            "images": len(images),
            "years_mentioned": ", ".join(str(y) for y in sorted(set(years))),
            "latest_year": max(years) if years else "",
            "cms_id": g("id"),
            "text": text,
            "_links": links,
            "_hash": hashlib.md5(norm(text).encode()).hexdigest() if body_words >= 15 else "",
        })

    # inbound links from other pages' copy
    by_path = {p["url"].rstrip("/").lower(): p for p in pages}
    for p in pages:
        p["inbound_links"] = 0
    for p in pages:
        for l in set(p["_links"]):
            u = urlparse(l)
            if u.netloc and "tbiport.org" not in u.netloc:
                continue
            t = by_path.get(u.path.rstrip("/").lower())
            if t and t is not p:
                t["inbound_links"] += 1

    # duplicates: same normalized name or identical copy
    name_groups, text_groups = defaultdict(list), defaultdict(list)
    for p in pages:
        name_groups[norm(p["admin_name"])].append(p)
        if p["_hash"]:
            text_groups[p["_hash"]].append(p)
    dup_rows, gid = [], 0
    for kind, groups in (("Same name", name_groups), ("Identical copy", text_groups)):
        for key, grp in groups.items():
            if len(grp) > 1 and key:
                gid += 1
                for p in grp:
                    p.setdefault("dup_groups", []).append(f"{kind} #{gid}")
                    dup_rows.append({"group": f"{kind} #{gid}", "admin_name": p["admin_name"], "url": p["url"], "status": p["status"], "word_count": p["word_count"], "view_url": p["view_url"], "edit_url": p["edit_url"]})

    # recommendation
    for p in pages:
        dup = ", ".join(p.pop("dup_groups", []))
        p["duplicate_of"] = dup
        reasons = []
        stale = p["latest_year"] and p["latest_year"] < TODAY_YEAR - 0 and (EVENTISH.search(p["admin_name"]) or p["category"] in ("Community & Events", "Worship & Holidays"))
        if p["status"].lower().startswith("unpub"):
            rec = "Retire"; reasons.append("already unpublished")
        elif p["http_status"] not in (200, "200"):
            rec = "Fix or retire"; reasons.append(f"page returns {p['http_status'] or 'error'}")
        elif p["category"] == "B'nai Mitzvah":
            rec = "Archive"; reasons.append("individual simcha page - move to a private/archived area")
        elif p["word_count"] < 15:
            rec = "Retire or fill"; reasons.append("no real copy on page")
        elif stale:
            rec = "Retire"; reasons.append(f"past event (latest year mentioned {p['latest_year']})")
        elif dup:
            rec = "Merge"; reasons.append("duplicate of another page")
        elif EVENTISH.search(p["admin_name"]) and p["category"] in ("Community & Events",):
            rec = "Review"; reasons.append("looks like a one-off event page")
        else:
            rec = "Keep & rewrite"
        if rec in ("Keep & rewrite", "Review", "Merge"):
            if not p["meta_description"]:
                reasons.append("no meta description")
            if not p["seo_title"]:
                reasons.append("no SEO title")
            if p["word_count"] < 60:
                reasons.append("thin copy")
        p["recommendation"] = rec
        p["notes"] = "; ".join(reasons)

    cols = ["recommendation", "notes", "category", "admin_name", "url", "status", "privacy", "http_status", "redirects_to",
            "word_count", "inbound_links", "links", "pdf_links", "images", "years_mentioned", "duplicate_of",
            "seo_title", "h1_override", "meta_description", "view_url", "edit_url", "cms_id"]
    order = {"Keep & rewrite": 0, "Review": 1, "Merge": 2, "Fix or retire": 3, "Retire or fill": 4, "Archive": 5, "Retire": 6}
    pages.sort(key=lambda p: (order[p["recommendation"]], p["category"], -p["inbound_links"], p["admin_name"].lower()))

    # ---- CSV ----
    with open(os.path.join(out_dir, "tbi-pages.csv"), "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=cols + ["text"], extrasaction="ignore")
        w.writeheader(); w.writerows(pages)

    # ---- Markdown copy deck ----
    with open(os.path.join(out_dir, "tbi-site-copy.md"), "w", encoding="utf-8") as fh:
        fh.write("# TBI website copy (exported from ShulCloud)\n\n")
        for cat in [c for c, _ in CATEGORIES] + ["Other"]:
            grp = [p for p in pages if p["category"] == cat and p["recommendation"] in ("Keep & rewrite", "Review", "Merge")]
            if not grp:
                continue
            fh.write(f"\n---\n\n# {cat} ({len(grp)} pages)\n")
            for p in grp:
                fh.write(f"\n## {p['admin_name']}\n\n`{p['url']}` · {p['word_count']} words · {p['recommendation']}\n\n{p['text'] or '_(no copy)_'}\n")

    # ---- Workbook ----
    wb = Workbook()
    hdr_font, hdr_fill = Font(bold=True, color="FFFFFF"), PatternFill("solid", fgColor="1F3A5F")
    fills = {"Keep & rewrite": "D9EAD3", "Review": "FFF2CC", "Merge": "FCE5CD", "Fix or retire": "F4CCCC", "Retire or fill": "EFEFEF", "Archive": "EFEFEF", "Retire": "EFEFEF"}

    def sheet(ws, headers, rows, widths):
        ws.append(headers)
        for c in ws[1]:
            c.font, c.fill = hdr_font, hdr_fill
        for r in rows:
            ws.append([r.get(h, "") if not isinstance(r.get(h), list) else len(r[h]) for h in headers])
        for i, wdt in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = wdt
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions

    ws = wb.active; ws.title = "Summary"
    recs, cats = Counter(p["recommendation"] for p in pages), Counter(p["category"] for p in pages)
    keep = [p for p in pages if p["recommendation"] in ("Keep & rewrite", "Review", "Merge")]
    rows = [("TBI website content audit", ""), ("Pages in CMS", len(pages)), ("", ""), ("Recommendation", "Pages")]
    rows += [(k, recs[k]) for k in order if recs[k]]
    rows += [("", ""), ("Category (all pages)", "Pages")] + cats.most_common()
    rows += [("", ""), ("Health of pages to keep", "")]
    rows += [("Pages to keep / review / merge", len(keep)),
             ("  with no meta description", sum(not p["meta_description"] for p in keep)),
             ("  with no SEO title", sum(not p["seo_title"] for p in keep)),
             ("  with thin copy (<60 words)", sum(p["word_count"] < 60 for p in keep)),
             ("  linking to PDFs", sum(p["pdf_links"] > 0 for p in keep)),
             ("Total words on pages to keep", sum(p["word_count"] for p in keep))]
    for r in rows:
        ws.append(list(r))
    ws["A1"].font = Font(bold=True, size=14)
    for r in ws.iter_rows():
        if r[0].value in ("Recommendation", "Category (all pages)", "Health of pages to keep"):
            r[0].font = r[1].font = Font(bold=True)
    ws.column_dimensions["A"].width, ws.column_dimensions["B"].width = 40, 12

    ws = wb.create_sheet("All Pages")
    sheet(ws, cols, pages, [16, 45, 22, 40, 35, 12, 10, 8, 20, 9, 9, 7, 7, 7, 14, 20, 30, 20, 40, 40, 40, 10])
    for row in ws.iter_rows(min_row=2):
        row[0].fill = PatternFill("solid", fgColor=fills[row[0].value])

    ws = wb.create_sheet("Duplicates")
    sheet(ws, ["group", "admin_name", "url", "status", "word_count", "view_url", "edit_url"], dup_rows, [20, 45, 40, 12, 10, 45, 45])

    ws = wb.create_sheet("Full Copy")
    sheet(ws, ["recommendation", "category", "admin_name", "url", "word_count", "text"], pages, [16, 22, 40, 35, 9, 120])
    for row in ws.iter_rows(min_row=2):
        row[5].alignment = Alignment(wrap_text=True, vertical="top")
        row[5].value = (row[5].value or "")[:32000]

    wb.save(os.path.join(out_dir, "tbi-content-audit.xlsx"))
    print(json.dumps({"pages": len(pages), "recommendations": recs, "categories": cats, "dup_rows": len(dup_rows)}, default=dict, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:4])

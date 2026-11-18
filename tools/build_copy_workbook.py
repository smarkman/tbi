"""Build the TBI copy-update workbook.

Usage:
  python3 tools/build_copy_workbook.py tbi-cms-export.json audit/tbi-pages.csv docs/copy-refresh.md docs/TBI-copy-workbook.xlsx
"""
import csv, json, re, sys
from collections import OrderedDict
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

cms_path, pages_csv, copy_md, out = sys.argv[1:5]

# New site map: recommended page -> (menu section, new URL, old URLs it replaces)
SITEMAP = OrderedDict([
    ("Home", ("Home", "/", ["/"])),
    ("Welcome to Temple Beth Israel", ("About", "/about", ["/welcome"])),
    ("Clergy and staff", ("About", "/about/clergy-staff", ["/about-us/our-clergy", "/about-us/our-staff", "/welcome/board-leadership", "/welcome/board-leadership-old", "/learning/preschool/preschool-director"])),
    ("Visit us", ("About", "/about/visit", ["/contact", "/directions"])),
    ("Prayer at TBI", ("Pray", "/pray", ["/pray", "/prayer"])),
    ("Shabbat", ("Pray", "/pray/shabbat", ["/pray/shabbat-services"])),
    ("Minyan", ("Pray", "/pray/minyan", ["/pray/minyan"])),
    ("Holidays and festivals", ("Pray", "/pray/holidays", ["/pray/holidaysfestivals"])),
    ("Life events", ("Life Events", "/life-events", ["/life-cycle"])),
    ("Learning at TBI", ("Learn", "/learn", ["/learn", "/learning"])),
    ("TBI Preschool", ("Learn", "/learn/preschool", ["/learn/preschool", "/preschool/aboutus", "/learn/preschool/preschoolprograms", "/learn/preschool/first-friends-program", "/learn/preschool/extendedcare", "/learn/preschool/summer-camp", "/learn/preschool/summerfun", "/learn/preschool/parents-association"])),
    ("Religious School", ("Learn", "/learn/religious-school", ["/learn/religious-school", "/learn/religious-school/about-our-religious-school", "/learn/religious-school/grade-highlights", "/learning/religious-school/religious-school", "/learn/religious-school/information-and-registration"])),
    ("Teens", ("Learn", "/learn/teens", ["/learn/religious-school/tbi-high", "/learn/religious-school/madrichim", "/learn/youth-family-programs"])),
    ("Adult learning", ("Learn", "/learn/adult-learning", ["/learn/life-long-learning"])),
    ("Get involved", ("Community", "/community", ["/community", "/worship/holidays"])),
    ("Sisterhood", ("Community", "/community/sisterhood", ["/community/sisterhood"])),
    ("Men's Club", ("Community", "/community/mens-club", ["/community/mens-club"])),
    ("Social Action", ("Community", "/community/social-action", ["/community/social-justice", "/giving/social-action"])),
    ("Caring community", ("Community", "/community/caring-community", ["/community/helping-and-healing"])),
    ("Library", ("Community", "/community/library", ["/library.html"])),
    ("College Connection", ("Community", "/community/college-connection", ["/community/college-connection"])),
    ("Membership", ("Join", "/join", ["/membership", "/membership/faq"])),
    ("Interfaith families", ("Join", "/join/interfaith-families", ["/membership/interfaith"])),
    ("Support TBI", ("Give", "/give", ["/give", "/tributes"])),
    ("Sponsorships and dedications", ("Give", "/give/sponsorships", ["/sponsor"])),
    ("Kol Nidrei Appeal", ("Give", "/give/kol-nidrei", ["/kn"])),
    ("The Morashah Society", ("Give", "/give/legacy", ["/willplanning"])),
])
SECTION_FALLBACK = {"About & Membership": "/about", "Adult Learning": "/learn/adult-learning", "Community & Events": "/community",
                    "Giving & Funds": "/give", "Preschool": "/learn/preschool", "Religious School & Youth": "/learn/religious-school",
                    "Worship & Holidays": "/pray", "B'nai Mitzvah": "/life-events", "Other": "/"}

# ---- parse the copy deck into sections ----
md = open(copy_md, encoding="utf-8").read().split("\n---\n", 1)[-1] if copy_md.endswith(".md") else ""
sections, cur, buf = OrderedDict(), None, []
SKIP = {"How to use this document", "Voice and style", "Please confirm before publishing"}
def flush():
    if cur and cur not in SKIP and "\n".join(buf).strip():
        sections[cur] = "\n".join(buf).strip()
for line in md.splitlines():
    m = re.match(r"^(#{1,2}) (.+)$", line)
    if m:
        flush(); cur, buf = m.group(2).strip(), []
    else:
        buf.append(line)
flush()
confirm_block = re.search(r"# Please confirm before publishing\n(.*)$", md, re.S).group(1).strip()
style_block = re.search(r"# Voice and style\n(.*?)\n# Home", md, re.S).group(1).strip()

def split_seo(body):
    seo = re.search(r"\*SEO title:\*\s*(.+)", body); meta = re.search(r"\*Meta description:\*\s*(.+)", body)
    clean = re.sub(r"\n?\*(SEO title|Meta description):\*.*", "", body).strip()
    clean = re.sub(r"\*\*(.+?)\*\*", r"\1", clean)  # plain text for spreadsheet cells
    clean = re.sub(r"(?<!\w)\*(.+?)\*(?!\w)", r"\1", clean)
    return clean, seo.group(1).strip() if seo else "", meta.group(1).strip() if meta else ""

# ---- page data ----
cms = {r["view_url"]: r for r in json.load(open(cms_path))["records"]}
rows = list(csv.DictReader(open(pages_csv, encoding="utf-8-sig")))
by_url = {r["url"]: r for r in rows}
url_to_new = {}
for new, (sec, nurl, olds) in SITEMAP.items():
    for o in olds:
        url_to_new.setdefault(o, new)

YEAR = re.compile(r"\b(20[01]\d|202[0-5])\b")
PERSONAL = re.compile(r"[\w.+-]+@(gmail|yahoo|aol|hotmail|outlook|icloud)\.com", re.I)
def flags(r):
    t = r["text"]; f = []
    if PERSONAL.search(t): f.append("personal email address")
    if "zoom.us" in t.lower() or "zoom link" in t.lower(): f.append("Zoom link")
    if YEAR.search(r["admin_name"] + " " + t): f.append("mentions past years")
    if re.search(r"this year|recently|new this|coming soon|over two years ago", t, re.I): f.append("time-sensitive wording")
    if "Burlington" in t: f.append("wrong address (Burlington, VT)")
    if re.search(r"click here|read more", t, re.I): f.append("'click here'/'read more' links")
    if int(r["pdf_links"] or 0): f.append(f"{r['pdf_links']} PDF link(s)")
    return "; ".join(f)

def action_for(r):
    rec, url = r["recommendation"], r["url"]
    if url in url_to_new:
        new = url_to_new[url]; nurl = SITEMAP[new][1]
        return ("Rewrite" if SITEMAP[new][2][0] == url else "Merge into"), new, nurl
    name = r["admin_name"].lower()
    if "boardleadership" in name:
        return "Merge into", "Clergy and staff", "/about/clergy-staff"
    if re.search(r"payment|registration|\breg\b|enrollment|bill me|add-ons|form", name) or re.search(r"preschoolreg|rsinitreg|rsenrollment|register", url):
        return "Keep: form or payment page (refresh intro copy)", "", url
    if url.startswith("/donation/") or url.startswith("/campaign/") or url.startswith("/payments/"):
        return "Keep: giving page (refresh copy, link from Give)", "Support TBI", url
    if rec == "Archive":
        return "Set to Logged in Only (simcha page)", "", ""
    if rec in ("Retire", "Retire or fill"):
        return "Unpublish", "", SECTION_FALLBACK.get(r["category"], "/")
    if rec == "Fix or retire":
        return "Fix or unpublish", "", SECTION_FALLBACK.get(r["category"], "/")
    if rec == "Merge":
        return "Merge with duplicate, then review", "", SECTION_FALLBACK.get(r["category"], "/")
    return "Review: keep, merge or unpublish", "", SECTION_FALLBACK.get(r["category"], "/")

# ---- workbook ----
wb = Workbook()
H = Font(bold=True, color="FFFFFF"); HF = PatternFill("solid", fgColor="002E3F")
WRAP = Alignment(wrap_text=True, vertical="top")
FILL = {"Rewrite": "E6F4FB", "Merge into": "F1F9EC", "Keep: form or payment page (refresh intro copy)": "E6F4FB", "Keep: giving page (refresh copy, link from Give)": "E6F4FB", "Unpublish": "F2F2F2", "Set to Logged in Only (simcha page)": "FFF4D6"}
STATUS = '"Not started,Drafting,In review,Approved,Published in ShulCloud"'

def header(ws, cols, widths):
    ws.append(cols)
    for c in ws[1]:
        c.font, c.fill, c.alignment = H, HF, Alignment(wrap_text=True, vertical="center")
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "C2"; ws.row_dimensions[1].height = 34
def cap(t):
    t = re.sub(r"^#{1,6} ", "", t or "", flags=re.M)
    if t[:1] in ("=", "+", "@"):  # Excel would treat these as formulas
        t = "\u200b" + t
    return t if len(t) < 32000 else t[:31900] + "\n…[truncated: see the JSON export for the full text]"

# Read me
ws = wb.active; ws.title = "Read me"
ws.column_dimensions["A"].width = 120
readme = [
    ("TBI website copy workbook", True),
    ("Every page in the ShulCloud CMS (1,093) with its current copy, the recommended new copy, and a column for the final approved copy.", False),
    ("", False),
    ("Tabs", True),
    ("1. Core pages: the ~27 pages of the new site. Current copy (all old pages it replaces), recommended copy, final copy, SEO fields, owner and status. Work here first.", False),
    ("2. All pages: every existing CMS page with its name, URL, active status, recommended action, where it goes in the new site, flags, and its current copy.", False),
    ("3. Redirects: old web addresses that should forward to the new pages, so bookmarks and Google links keep working.", False),
    ("4. Facts to confirm: details that may be out of date. Fill in the answer before publishing.", False),
    ("5. Style guide: the voice and house style for all new copy.", False),
    ("", False),
    ("How to work through it", True),
    ("1. Assign an owner to each core page (clergy, education directors, executive director, committee chairs).", False),
    ("2. The owner edits the recommended copy and pastes the approved version into 'Final copy'. Set Status to Approved.", False),
    ("3. Answer everything on 'Facts to confirm'.", False),
    ("4. The web editor builds each page in ShulCloud from 'Final copy', fills in the SEO title and meta description, and sets Status to Published.", False),
    ("5. Unpublish or restrict the pages on 'All pages' as recommended, and set up the redirects.", False),
    ("", False),
    ("Key", True),
    ("Active = Yes means the page is visible on the site today. Active = No means it is already unpublished.", False),
    ("Recommended actions: Rewrite (becomes a new core page) · Merge into (its content folds into a core page) · Unpublish (no useful copy, or a past event) · Set to Logged in Only (individual simcha pages with children's names) · Review (needs a human decision).", False),
    ("Text in [BRACKETS] or marked [CONFIRM] in the recommended copy needs a detail from TBI.", False),
    ("Copy over 32,000 characters is cut off in a cell (very rare); the full text is in the JSON export.", False),
]
for text, bold in readme:
    ws.append([text]); c = ws.cell(ws.max_row, 1); c.alignment = WRAP
    if bold: c.font = Font(bold=True, size=14 if ws.max_row == 1 else 12, color="002E3F")

# Core pages
ws = wb.create_sheet("Core pages")
cols = ["#", "New page", "Menu section", "New URL", "Replaces these current pages", "Current pages active?", "Current copy (combined)", "Recommended copy", "Final copy (approved)",
        "Current SEO title", "Recommended SEO title", "Current meta description", "Recommended meta description", "Facts to confirm on this page", "Owner", "Status", "Notes"]
header(ws, cols, [4, 24, 12, 24, 40, 16, 70, 70, 60, 26, 34, 34, 44, 34, 16, 16, 30])
dv = DataValidation(type="list", formula1=STATUS, allow_blank=True); ws.add_data_validation(dv)
for i, (new, (sec, nurl, olds)) in enumerate(SITEMAP.items(), 1):
    body, seo, meta = split_seo(sections.get(new, ""))
    olds_found = [by_url[o] for o in olds if o in by_url]
    current = "\n\n".join(f"CURRENT PAGE: {r['admin_name']} ({r['url']})\n{'-' * 40}\n{r['text']}" for r in olds_found)
    replaces = "\n".join(f"{r['admin_name']}  {r['url']}" for r in olds_found)
    active = "\n".join(("Yes" if r["status"] == "Visible" else "No") + f"  {r['url']}" for r in olds_found)
    cur_seo = "\n".join(filter(None, ((cms.get(r["view_url"], {}).get("fields", {}).get("info[title]") or {}).get("value", "").strip() for r in olds_found))) or "(none)"
    cur_meta = "\n".join(filter(None, ((cms.get(r["view_url"], {}).get("fields", {}).get("info[meta_description]") or {}).get("value", "").strip() for r in olds_found))) or "(none)"
    conf = "; ".join(sorted(set(re.findall(r"\[CONFIRM[^\]]*\]|\[[A-Z][^\]]{3,}\]", sections.get(new, "")))))
    ws.append([i, new, sec, nurl, replaces, active, cap(current), cap(body), "", cur_seo, seo, cur_meta, meta, conf, "", "Not started", ""])
    for c in ws[ws.max_row]: c.alignment = WRAP
    ws.row_dimensions[ws.max_row].height = 300
    dv.add(f"P{ws.max_row}")
ws.auto_filter.ref = ws.dimensions

# All pages
ws = wb.create_sheet("All pages")
cols = ["Page name (admin)", "Current URL", "Active?", "Visibility", "Loads (HTTP)", "Category", "Words", "Recommended action", "Goes into (new page)", "New URL / redirect to",
        "Why", "Things to fix", "Current SEO title", "Current meta description", "Current copy", "Recommended copy", "Final copy (approved)", "Status", "Live page", "Edit in ShulCloud"]
header(ws, cols, [36, 34, 9, 12, 8, 20, 8, 26, 24, 24, 34, 34, 26, 30, 70, 30, 40, 16, 34, 34])
dv2 = DataValidation(type="list", formula1=STATUS, allow_blank=True); ws.add_data_validation(dv2)
order = {"Rewrite": 0, "Merge into": 1}
rows_sorted = sorted(rows, key=lambda r: (order.get(action_for(r)[0], 2), r["category"], r["admin_name"].lower()))
for r in rows_sorted:
    act, new, nurl = action_for(r)
    f = cms.get(r["view_url"], {}).get("fields", {})
    g = lambda k: (f.get(k) or {}).get("value", "").strip()
    rec_copy = f"See 'Core pages' row: {new}" if new else ""
    ws.append([r["admin_name"], r["url"], "Yes" if r["status"] == "Visible" else "No", r["privacy"], r["http_status"], r["category"], int(r["word_count"] or 0),
               act, new, nurl, r["notes"], flags(r), g("info[title]"), g("info[meta_description]"), cap(r["text"]), rec_copy, "", "Not started", r["view_url"], r["edit_url"]])
    row = ws[ws.max_row]
    for c in row: c.alignment = Alignment(vertical="top", wrap_text=c.column in (11, 12, 15))
    row[7].fill = PatternFill("solid", fgColor=FILL.get(act, "FFFFFF"))
    ws.row_dimensions[ws.max_row].height = 60
    dv2.add(f"R{ws.max_row}")
ws.auto_filter.ref = ws.dimensions

# Redirects
ws = wb.create_sheet("Redirects")
header(ws, ["Old URL", "Old page name", "Redirect to", "Reason", "Done?"], [44, 40, 30, 40, 10])
seen = set()
for r in rows_sorted:
    act, new, nurl = action_for(r)
    if not nurl or r["url"] == nurl or r["url"] in seen or act.startswith("Set to"):
        continue
    if act in ("Rewrite", "Merge into") or (r["status"] == "Visible" and (int(r["inbound_links"] or 0) > 0 or int(r["word_count"] or 0) >= 60)):
        seen.add(r["url"])
        ws.append([r["url"], r["admin_name"], nurl, "Moved to the new site structure" if new else "Page unpublished; send visitors to the closest section", ""])
ws.freeze_panes = "A2"; ws.auto_filter.ref = ws.dimensions

# Facts to confirm
ws = wb.create_sheet("Facts to confirm")
header(ws, ["#", "Item", "Who can answer", "Answer", "Done?"], [4, 90, 22, 50, 10])
for line in confirm_block.splitlines():
    m = re.match(r"^(\d+)\. (.+)$", line.strip())
    if m:
        ws.append([int(m.group(1)), re.sub(r"\*\*(.+?)\*\*", r"\1", m.group(2)), "", "", ""])
        for c in ws[ws.max_row]: c.alignment = WRAP
extra = ["Headshot of Rabbi Sharyn Perlman for the clergy page.",
         "Confirm the photo used for Rabbi Mishkin is current.",
         "Board of Trustees list: names and roles for the single leadership grid.",
         "Preschool class days and hours for 2's, 3's and 4's/Pre-K, and current enrichment programs.",
         "Parking, accessibility and building security notes for the Visit page.",
         "A 3–4 sentence homepage welcome in Rabbi Mishkin's voice.",
         "Role email addresses to replace personal emails (e.g. socialaction@, sisterhood@, ritual@).",
         "Photography: 10–15 current, high-resolution photos (Shabbat, preschool, Religious School, holidays, community)."]
n = ws.max_row
for j, e in enumerate(extra, n):
    ws.append([j, e, "", "", ""]); ws.cell(ws.max_row, 2).alignment = WRAP
ws.freeze_panes = "A2"

# Style guide
ws = wb.create_sheet("Style guide"); ws.column_dimensions["A"].width = 120
for line in style_block.splitlines():
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", line).strip()
    if not t: continue
    ws.append([t]); c = ws.cell(ws.max_row, 1); c.alignment = WRAP
    if line.startswith("**") and line.rstrip().endswith("**"): c.font = Font(bold=True, color="002E3F")

wb.save(out)
print("core pages", len(SITEMAP), "| sections parsed", len(sections), "| missing copy:", [k for k in SITEMAP if k not in sections], "| all pages", len(rows), "| redirects", len(seen))

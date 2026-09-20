#!/usr/bin/env python3
"""Build physo/index.html, the hub page for the physics lessons.

Sources, all inside physo/:
  lessons/*.html      one self-contained lesson each; listed automatically
  slides/*            slide decks (pdf/html); listed automatically by file name
  problems/*          problem-set PDFs; listed automatically by file name
  content.md          hand-written sections: videos, extra materials, problem
                      books, and any other heading. Items are Markdown links:
                        - [Title](https://...) — optional note
                      YouTube links become thumbnail cards.
Every lesson gets a noindex tag if it lacks one. Run by publish.sh.
"""
import html, re
from pathlib import Path
from urllib.parse import urlparse, parse_qs, quote

ROOT = Path(__file__).resolve().parent
NOINDEX = '<meta name="robots" content="noindex, nofollow, noarchive">'

# Section order and headings. content.md headings are matched to these keys
# case-insensitively; unknown headings are appended as extra sections.
SECTIONS = [
    ("lessons",   "Сабақтар"),
    ("slides",    "Слайдтар"),
    ("problems",  "Есептер жинақтары"),
    ("videos",    "Бейнесабақтар"),
    ("materials", "Қосымша материалдар"),
    ("books",     "Есептер кітаптары"),
]
ALIASES = {
    "сабақтар": "lessons", "lessons": "lessons",
    "слайдтар": "slides", "slides": "slides",
    "есептер жинақтары": "problems", "есептер": "problems", "problems": "problems",
    "бейнесабақтар": "videos", "бейне": "videos", "videos": "videos", "видео": "videos",
    "қосымша материалдар": "materials", "материалдар": "materials", "materials": "materials",
    "есептер кітаптары": "books", "кітаптар": "books", "books": "books",
}

def esc(s): return html.escape(s, quote=True)

def meta(src, name):
    m = re.search(r'<meta\s+name=["\']%s["\']\s+content=["\']([^"\']*)["\']' % name, src, re.I)
    return html.unescape(m.group(1)).strip() if m else ""

def title_of(src, fallback):
    m = re.search(r"<title>(.*?)</title>", src, re.I | re.S)
    if not m: return fallback
    t = html.unescape(re.sub(r"\s+", " ", m.group(1))).strip()
    return re.split(r"\s+[|—–]\s+", t)[0] or fallback

def ensure_noindex(path, src):
    if re.search(r'<meta\s+name=["\']robots["\']', src, re.I): return src
    new = re.sub(r"(<head[^>]*>)", r"\1\n" + NOINDEX, src, count=1, flags=re.I)
    if new != src: path.write_text(new, encoding="utf-8")
    return new

def sort_key(p):
    m = re.match(r"(\d+)", p.stem)
    return (0, int(m.group(1)), p.stem) if m else (1, 0, p.stem.lower())

def nice_name(p):
    s = re.sub(r"^\d+[-_.\s]*", "", p.stem)
    return re.sub(r"[-_]+", " ", s).strip() or p.stem

def youtube_id(url):
    u = urlparse(url)
    if u.netloc.endswith("youtu.be"): return u.path.strip("/").split("/")[0]
    if "youtube.com" in u.netloc:
        if u.path == "/watch": return parse_qs(u.query).get("v", [""])[0]
        m = re.match(r"/(?:shorts|embed|live)/([\w-]{11})", u.path)
        if m: return m.group(1)
    return ""

# ---- collect items: (title, href, note, kind) ---------------------------------
items = {k: [] for k, _ in SECTIONS}
extra = []  # (heading, [items])

for p in sorted((ROOT / "lessons").glob("*.html"), key=sort_key):
    src = ensure_noindex(p, p.read_text(encoding="utf-8", errors="replace"))
    items["lessons"].append((title_of(src, p.stem), f"lessons/{p.name}", meta(src, "description"), "lesson"))

for key, folder, exts in (("slides", "slides", {".pdf", ".html", ".pptx", ".key"}),
                          ("problems", "problems", {".pdf", ".html", ".docx"})):
    d = ROOT / folder
    if d.is_dir():
        for p in sorted(d.iterdir(), key=sort_key):
            if p.suffix.lower() in exts and not p.name.startswith("."):
                note = p.suffix.upper().lstrip(".")
                items[key].append((nice_name(p), f"{folder}/{quote(p.name)}", note, "file"))

cm = ROOT / "content.md"
if cm.exists():
    cur = None
    for line in cm.read_text(encoding="utf-8").splitlines():
        h = re.match(r"^##\s+(.+?)\s*$", line)
        if h:
            name = h.group(1).strip()
            key = ALIASES.get(name.lower())
            if key: cur = items[key]
            else:
                extra.append((name, [])); cur = extra[-1][1]
            continue
        it = re.match(r"^\s*[-*]\s+\[(.+?)\]\((\S+?)\)\s*(?:[—–-]+\s*(.*))?$", line)
        if it and cur is not None:
            t, url, note = it.group(1).strip(), it.group(2).strip(), (it.group(3) or "").strip()
            kind = "video" if youtube_id(url) else "link"
            cur.append((t, url, note, kind))

# ---- render --------------------------------------------------------------------
def render_item(t, href, note, kind):
    ext = ' target="_blank" rel="noopener"' if href.startswith("http") else ""
    if kind == "video":
        vid = youtube_id(href)
        return (f'<a class="card video" href="{esc(href)}"{ext}>'
                f'<span class="thumb"><img src="https://i.ytimg.com/vi/{vid}/hqdefault.jpg" alt="" loading="lazy"></span>'
                f'<span class="t">{esc(t)}</span>' + (f'<span class="d">{esc(note)}</span>' if note else "") + "</a>")
    cls = {"lesson": "card lesson", "file": "card file"}.get(kind, "card link")
    return (f'<a class="{cls}" href="{esc(href)}"{ext}><span class="t">{esc(t)}</span>'
            + (f'<span class="d">{esc(note)}</span>' if note else "") + "</a>")

def render_section(key, heading, lst):
    if not lst: return ""
    wrap = "grid videos" if key == "videos" else ("list numbered" if key == "lessons" else "grid")
    body = "\n".join("      " + render_item(*i) for i in lst)
    return f'  <section id="{esc(key)}">\n    <h2>{esc(heading)}</h2>\n    <div class="{wrap}">\n{body}\n    </div>\n  </section>\n'

sections_html = "".join(render_section(k, h, items[k]) for k, h in SECTIONS)
sections_html += "".join(render_section(f"extra{i}", h, lst) for i, (h, lst) in enumerate(extra))
if not sections_html.strip():
    sections_html = '  <p class="empty">Материалдар әзірше қосылмаған.</p>\n'

nav = " · ".join(f'<a href="#{k}">{esc(h)}</a>' for k, h in SECTIONS if items[k])

page = f"""<!DOCTYPE html>
<html lang="kk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{NOINDEX}
<title>Физика — олимпиадаға дайындық</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='30' fill='%231b3a5c'/%3E%3Ccircle cx='32' cy='32' r='5' fill='%23ffd166'/%3E%3Cellipse cx='32' cy='32' rx='22' ry='9' fill='none' stroke='%23ffd166' stroke-width='2.5' transform='rotate(-30 32 32)'/%3E%3Cellipse cx='32' cy='32' rx='22' ry='9' fill='none' stroke='%23ffd166' stroke-width='2.5' transform='rotate(30 32 32)'/%3E%3C/svg%3E">
<style>
  :root {{ --ink:#1b2430; --muted:#5f6b7a; --line:#e3e7ec; --accent:#1b3a5c; --gold:#ffd166; --bg:#f7f8fa; --card:#fff; }}
  * {{ box-sizing:border-box }}
  body {{ margin:0; font:17px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; color:var(--ink); background:var(--bg) }}
  header {{ background:var(--accent); color:#fff; padding:40px 20px 30px }}
  .wrap {{ max-width:900px; margin:0 auto }}
  h1 {{ margin:0 0 6px; font-size:2rem; line-height:1.2 }}
  header p {{ margin:0; color:#cfd8e3 }}
  nav {{ margin-top:18px; font-size:.9rem; color:#8fa3ba }}
  nav a {{ color:#e8eef5; text-decoration:none; font-weight:500 }}
  nav a:hover {{ color:var(--gold) }}
  main {{ padding:8px 20px 60px }}
  section {{ margin-top:36px }}
  h2 {{ font-size:1.25rem; margin:0 0 14px; padding-bottom:8px; border-bottom:2px solid var(--gold); display:inline-block }}
  .card {{ display:block; padding:14px 16px; background:var(--card); border:1px solid var(--line); border-radius:12px; color:inherit; text-decoration:none; transition:transform .12s, box-shadow .12s }}
  .card:hover {{ transform:translateY(-1px); box-shadow:0 6px 18px rgba(27,58,92,.10) }}
  .card .t {{ display:block; font-weight:600; line-height:1.35 }}
  .card .d {{ display:block; color:var(--muted); font-size:.9rem; margin-top:4px }}
  .list.numbered {{ counter-reset:n }}
  .list.numbered .card {{ counter-increment:n; display:grid; grid-template-columns:2.2em 1fr; gap:2px 12px; margin-bottom:10px }}
  .list.numbered .card::before {{ content:counter(n); grid-row:1 / span 2; font-weight:700; color:var(--accent); font-size:1.15rem; align-self:start }}
  .list.numbered .card .d {{ grid-column:2 }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(260px, 1fr)); gap:12px }}
  .card.file .t::before {{ content:"📄 "; }}
  .card.link .t::before {{ content:"🔗 "; }}
  .card.video {{ padding:0; overflow:hidden }}
  .card.video .thumb {{ display:block; aspect-ratio:16/9; overflow:hidden; background:#000 }}
  .card.video .thumb img {{ width:100%; height:100%; object-fit:cover; display:block }}
  .card.video .t {{ padding:10px 14px 0 }}
  .card.video .d {{ padding:0 14px 12px }}
  .card.video .t:last-child {{ padding-bottom:12px }}
  .empty {{ color:var(--muted); padding:24px 0 }}
  footer {{ color:var(--muted); font-size:.85rem; text-align:center; padding:0 20px 40px }}
  @media (max-width:520px) {{ .grid {{ grid-template-columns:1fr }} }}
</style>
</head>
<body>
<header><div class="wrap">
  <h1>Физика</h1>
  <p>Олимпиадаға дайындық · 8-сынып</p>
  <nav>{nav}</nav>
</div></header>
<main><div class="wrap">
{sections_html}</div></main>
<footer>Бекдәулет Шүкірғалиев · жеке оқу беті</footer>
</body>
</html>
"""
(ROOT / "index.html").write_text(page, encoding="utf-8")
for k, h in SECTIONS:
    if items[k]: print(f"{h}: {len(items[k])}")
for h, lst in extra: print(f"{h}: {len(lst)} (extra)")

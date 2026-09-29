#!/usr/bin/env python3
"""Build the site: content/*.md  ->  site/**/index.html  (no dependencies).

content/index.md          -> site/index.html
content/work_at_form.md   -> site/work_at_form/index.html

Syntax cheat sheet: content/README.md
"""
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT, SITE, TEMPLATE = ROOT / "content", ROOT / "site", ROOT / "templates" / "page.html"


# ---------- inline markdown ----------
def inline(text: str) -> str:
    """**bold**, *italic*, `code`, [link](url). Raw HTML like <br> passes through."""
    text = re.sub(r"`([^`]+)`", lambda m: f"<code>{html.escape(m[1])}</code>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", text)

    def link(m):
        label, url = m[1], m[2]
        ext = ' target="_blank" rel="noopener"' if url.startswith("http") else ""
        return f'<a href="{url}"{ext}>{label}</a>'

    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, text)


def split(value: str, n: int) -> list[str]:
    parts = [p.strip() for p in value.split("|")]
    return parts + [""] * (n - len(parts))


# ---------- block renderer ----------
class Page:
    def __init__(self, root: str):
        self.root = root  # "" for /, "../" for /work_at_form/

    def media(self, name: str) -> str:
        return name if name.startswith(("http", "/")) else f"{self.root}assets/media/{name}"

    def blocks(self, lines: list[str]) -> str:
        """Render the body of one section. Consecutive stat:/paper:/list lines are grouped."""
        out, para, smalls, i = [], [], [], 0

        def flush():
            if para:
                out.append(f"<p>{inline(' '.join(para))}</p>")
                para.clear()
            if smalls:  # consecutive small projects / cards form a grid
                cls = "pgrid" if 'project card' in smalls[0] else "smalls"
                out.append(f'<div class="{cls}">{"".join(smalls)}</div>')
                smalls.clear()

        while i < len(lines):
            line = lines[i].rstrip()
            s = line.strip()
            key, _, val = s.partition(":")
            key, val = key.strip().lower(), val.strip()

            if not s:  # blank line ends a paragraph, but keeps a card grid open
                if para:
                    out.append(f"<p>{inline(' '.join(para))}</p>"); para.clear()
            elif s.startswith("# "):
                flush(); out.append(f"<h1>{inline(s[2:])}</h1>")
            elif s.startswith("### "):
                flush(); out.append(f"<h3>{inline(s[4:])}</h3>")
            elif s.startswith("|"):  # markdown table
                flush()
                rows = []
                while i < len(lines) and lines[i].strip().startswith("|"):
                    rows.append(lines[i].strip()); i += 1
                out.append(self.table(rows)); continue
            elif s.startswith("- "):  # bullet list
                flush()
                items = []
                while i < len(lines) and lines[i].strip().startswith("- "):
                    items.append(f"<li>{inline(lines[i].strip()[2:])}</li>"); i += 1
                out.append(f"<ul>{''.join(items)}</ul>"); continue
            elif key == "label":
                flush(); out.append(f'<span class="label">{inline(val)}</span>')
            elif key == "lead":
                flush(); out.append(f'<p class="lead">{inline(val)}</p>')
            elif key == "note":
                flush(); out.append(f'<p class="muted small">{inline(val)}</p>')
            elif key == "muted":
                flush(); out.append(f'<p class="muted">{inline(val)}</p>')
            elif key == "photo":
                flush(); out.append(f'<img class="avatar" src="{self.media(val)}" alt="Felix Hammer">')
            elif key == "chips":
                flush()
                chips = inline(val).replace("</a>", " ↗</a>").split("·")
                out.append(f'<div class="chips">{"".join(c.strip() for c in chips)}</div>')
            elif key == "button":
                flush()
                btns = []
                while i < len(lines) and lines[i].strip().lower().startswith("button:"):
                    text, url = split(lines[i].strip()[7:], 2)
                    cls = "btn" if not btns else "btn ghost"
                    btns.append(f'<a class="{cls}" href="{url}">{inline(text)}</a>'); i += 1
                out.append(f'<p class="buttons">{"".join(btns)}</p>'); continue
            elif key == "number":
                flush()
                n = int(re.sub(r"\D", "", val))
                out.append(f'<div class="num" data-count="{n}">{n:,}</div>')
            elif key == "stat":
                flush()
                stats = []
                while i < len(lines) and lines[i].strip().lower().startswith("stat:"):
                    big, text = split(lines[i].strip()[5:], 2)
                    stats.append(f'<div class="stat"><b>{inline(big)}</b><span>{inline(text)}</span></div>'); i += 1
                out.append(f'<div class="stats">{"".join(stats)}</div>'); continue
            elif key == "paper":
                flush()
                status, title, authors = split(val, 3)
                a = f'<p class="muted small" style="margin:0">{inline(authors)}</p>' if authors else ""
                out.append(f'<div class="paper"><span class="status">{inline(status)}</span><h3>{inline(title)}</h3>{a}</div>')
            elif key == "image":
                flush()
                src, caption = split(val, 2)
                cap = f"<figcaption>{inline(caption)}</figcaption>" if caption else ""
                alt = html.escape(re.sub(r"<[^>]+>|[*_`]", "", caption) or src, quote=True)
                out.append(f'<figure><img src="{self.media(src)}" alt="{alt}" loading="lazy">{cap}</figure>')
            elif key == "compare":
                flush()
                left, right, caption = split(val, 3)
                out.append(self.compare(left, right, caption))
            elif key == "project":
                if para: flush()
                title, size = split(val, 2)
                inner = []
                i += 1
                while i < len(lines) and lines[i].strip() != "/project":
                    inner.append(lines[i]); i += 1
                card = self.project(title, size or "main", inner)
                if size in ("small", "card"):
                    smalls.append(card)
                else:
                    flush(); out.append(card)
            elif key == "cv":
                flush()
                when, what, where, desc = split(val, 4)
                d = f"<p>{inline(desc)}</p>" if desc else ""
                w = f'<div class="where">{inline(where)}</div>' if where else ""
                out.append(f'<div class="cv-item"><div class="when">{inline(when)}</div><div><h3>{inline(what)}</h3>{w}{d}</div></div>')
            elif key == "box":  # box: … /box  -> highlighted feature card
                flush()
                inner = []
                i += 1
                while i < len(lines) and lines[i].strip() != "/box":
                    inner.append(lines[i]); i += 1
                out.append(f'<div class="feature">{self.blocks(inner)}</div>')
            elif key == "details":
                flush()
                inner = []
                i += 1
                while i < len(lines) and lines[i].strip() != "/details":
                    inner.append(lines[i]); i += 1
                body = self.blocks(inner)
                out.append(f"<details><summary>{inline(val)}</summary>{body}</details>")
            else:
                para.append(s)
            i += 1
        flush()
        return "\n".join(out)

    def media_item(self, spec: str) -> str:
        """a.jpg | a.png:fit (letterboxed) | a.gif | a.mp4 (muted loop)"""
        name, _, mode = spec.strip().partition(":")
        cls = ' class="fit"' if mode == "fit" else ""
        src = self.media(name)
        if name.endswith(".mp4"):
            return f'<video{cls} src="{src}" muted loop playsinline autoplay preload="metadata"></video>'
        return f'<img{cls} src="{src}" alt="" loading="lazy">'

    def project(self, title: str, size: str, lines: list[str]) -> str:
        """project: Title | headline|main|small  …  /project
        Inside: media: a.jpg, b.gif  ·  quote: …  ·  links: [GitHub](url) · [Paper](url)  ·  plain text."""
        media, figs, quote, links, rest = [], [], "", "", []
        for line in lines:
            k, _, v = line.strip().partition(":")
            k = k.strip().lower()
            if k == "figure":  # wide diagrams at natural size, stacked
                figs = [f.strip() for f in v.split(",") if f.strip()]
            elif k == "media":
                media = [m for m in v.split(",") if m.strip()]
            elif k == "quote":
                quote = f'<p class="quote">{inline(v.strip())}</p>'
            elif k == "links":
                links = f'<div class="plinks">{"".join(a.strip() for a in inline(v.strip()).split("·"))}</div>'
            else:
                rest.append(line)
        m = ""
        if size == "card":  # one visual only: first figure or media item.  name:cover fills the frame
            first = (figs or media or [""])[0].strip()
            if first:
                name, _, mode = first.partition(":")
                el = self.media_item(name)
                m = f'<div class="pvis {"cover" if mode == "cover" else "fit"}">{el}</div>'
            media, figs = [], []
        if media:
            items = "".join(self.media_item(x) for x in media)
            dots = f'<div class="media-dots">{"<i></i>" * len(media)}</div>' if len(media) > 1 else ""
            m = f'<div class="media">{items}</div>{dots}'
        if figs:
            m = "".join(f'<img class="pfig" src="{self.media(f)}" alt="" loading="lazy">' for f in figs) + m
        anchor = re.sub(r"[^a-z0-9]+", "-", re.sub(r"<[^>]+>", "", inline(title)).lower()).strip("-")
        return (f'<article class="project {size}" id="{anchor}">{m if size == "card" else f'<div class="pvis">{m}</div>'}'
                f'<div class="ptext"><h3>{inline(title)}</h3>{quote}{self.blocks(rest)}{links}</div></article>')

    def table(self, rows: list[str]) -> str:
        cells = lambda r: [c.strip() for c in r.strip("|").split("|")]
        head, body = cells(rows[0]), [cells(r) for r in rows[1:] if not re.fullmatch(r"[|\s:-]+", r)]
        th = "".join(f"<th>{inline(c)}</th>" for c in head)
        trs = []
        for r in body:
            us = any("**" in c for c in r)  # a bold cell marks "our" row
            tds = "".join(f"<td>{inline(c.replace('**', ''))}</td>" for c in r)
            trs.append(f'<tr{" class=\"us\"" if us else ""}>{tds}</tr>')
        return f'<div class="tbl"><table><tr>{th}</tr>{"".join(trs)}</table></div>'

    def compare(self, left: str, right: str, caption: str) -> str:
        l_src, _, l_tag = left.partition("=")
        r_src, _, r_tag = right.partition("=")
        cap = f'<p class="muted small" style="margin-top:8px">{inline(caption)}</p>' if caption else ""
        return f'''<div class="compare" id="cmp">
  <video class="bottom" src="{self.media(r_src.strip())}" muted loop playsinline autoplay preload="metadata"></video>
  <video class="top" src="{self.media(l_src.strip())}" muted loop playsinline autoplay preload="metadata"></video>
  <div class="handle"></div>
  <span class="tag l">{l_tag.strip()}</span><span class="tag r">{r_tag.strip()}</span>
  <input type="range" min="0" max="100" value="50" aria-label="Compare {l_tag.strip()} and {r_tag.strip()}">
</div>{cap}'''

    # ---------- sections ----------
    def section(self, heading: str, lines: list[str]) -> str:
        chapter = re.match(r"(\d+)\s+(.*)", heading)
        if heading == "hero":
            return self.hero(lines)
        if chapter:
            top = f'<span class="ch-no">{chapter[1]}</span>\n<h2>{inline(chapter[2])}</h2>'
        elif re.fullmatch(r"[a-z0-9-]+", heading):  # plain id like "intro": no visible heading
            top = ""
        else:
            top = f"<h2>{inline(heading)}</h2>"
        body = self.blocks(lines)
        # photo + first paragraph side by side
        body = re.sub(r'(<img class="avatar"[^>]*>)\n(<p[^>]*>.*?</p>)', r'<div class="me">\1\2</div>', body, count=1, flags=re.S)
        cls = ' class="big"' if 'class="num"' in body else ""
        cls = ' class="home"' if heading == "home" else cls
        return f'<section{cls}>\n<div class="wrap reveal">\n{top}\n{body}\n</div>\n</section>'

    def hero(self, lines: list[str]) -> str:
        video = next((l.split(":", 1)[1].strip() for l in lines if l.strip().lower().startswith("video:")), "")
        poster = next((l.split(":", 1)[1].strip() for l in lines if l.strip().lower().startswith("poster:")), "")
        rest = [l for l in lines if not l.strip().lower().startswith(("video:", "poster:"))]
        v = ""
        if video:  # video: hero  ->  hero_1080.mp4 on desktop, hero_720.mp4 on phones
            v = f'''<div class="wide">
  <video id="hero-video" autoplay muted loop playsinline poster="{self.media(poster)}" title="Click for video controls">
    <source src="{self.media(video + '_1080.mp4')}" type="video/mp4" media="(min-width: 900px)">
    <source src="{self.media(video + '_720.mp4')}" type="video/mp4">
  </video>
</div>'''
        return f'<div class="hero">\n<div class="wrap">\n{self.blocks(rest)}\n</div>\n{v}\n</div>'  # title first, then video


# ---------- page ----------
def parse(md: str) -> tuple[dict, list[tuple[str, list[str]]]]:
    meta = {}
    if md.startswith("---"):
        _, fm, md = md.split("---", 2)
        for line in fm.strip().splitlines():
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
    sections, cur = [], None
    for line in md.splitlines():
        if line.startswith("## "):
            cur = (line[3:].strip(), []); sections.append(cur)
        elif line.strip().startswith("%%"):  # %% comment lines are ignored (Obsidian style)
            continue
        elif cur:
            cur[1].append(line)
    return meta, sections


def build_one(src: Path, template: str) -> Path:
    slug = src.stem
    out = SITE / "index.html" if slug == "index" else SITE / slug / "index.html"
    root = "" if slug == "index" else "../"
    meta, sections = parse(src.read_text(encoding="utf-8"))
    page = Page(root)
    main = "\n\n".join(page.section(h, lines) for h, lines in sections)
    note = meta.get("footer", "")
    fill = {
        "title": html.escape(meta.get("title", "Felix Hammer")),
        "description": html.escape(meta.get("description", "")),
        "root": root,
        "source": src.name,
        "main": main,
        "topbar": "" if slug == "index" else
            f'<header class="bar" id="bar">\n  <a href="{root}">Felix Hammer</a>\n  <a href="#contact">Contact ↓</a>\n</header>',
        "footer_note": f'<p class="muted">{inline(note)}</p>' if note else "",
        "home_link": "" if slug == "index" else f'<a href="{root}">← Home</a>',
    }
    result = re.sub(r"\{\{(\w+)\}\}", lambda m: fill[m[1]], template)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(result, encoding="utf-8")
    return out


def build() -> list[Path]:
    template = TEMPLATE.read_text(encoding="utf-8")
    return [build_one(p, template) for p in sorted(CONTENT.glob("*.md")) if p.name != "README.md"]


if __name__ == "__main__":
    for p in build():
        print("built", p.relative_to(ROOT))
    sys.exit(0)

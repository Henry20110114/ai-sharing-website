#!/usr/bin/env python3
"""Site build helper. Needs only Python 3.

    python3 build.py                 stamp the shared head / header / footer into every page
                                     and set the asset version from the asset files' contents
    python3 build.py --stage         same, then `git add` the files it changed (used by the pre-commit hook)
    python3 build.py new SECTION SLUG [TITLE]
                                     create SECTION/SLUG.html from templates/article.html,
                                     e.g. python3 build.py new courses llm-intro-1 大语言模型入门

Pages mark their shared regions with comments:

    <!-- head --> ... <!-- /head -->          (add `noindex` for an unlisted page: <!-- head noindex -->)
    <!-- header active="courses" --> ... <!-- /header -->
    <!-- footer --> ... <!-- /footer -->

Whatever sits between a pair of markers is replaced with partials/head.html,
partials/header.html or partials/footer.html. Everything outside the markers is left alone.
"""
import datetime
import hashlib
import html
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE_URL = "https://xiuyuanwang.org"
ASSET_FILES = ("style.css", "main.js", "article.js")
SECTIONS = {
    "courses": {"zh": "课程分享", "en": "Courses", "back_en": "Back to courses", "page": "/courses.html"},
    "qa":      {"zh": "经验答疑", "en": "Q&A",     "back_en": "Back to Q&A",     "page": "/qa.html"},
    "fields":  {"zh": "学科方向", "en": "Fields",  "back_en": "Back to fields",  "page": "/fields.html"},
    "news":    {"zh": "AI 资讯",  "en": "AI News", "back_en": "Back to AI news", "page": "/news.html"},
}


def read(path):
    return path.read_text(encoding="utf-8")


def asset_version():
    digest = hashlib.sha1()
    for name in ASSET_FILES:
        path = ROOT / "assets" / name
        if path.exists():
            digest.update(path.read_bytes())
    return digest.hexdigest()[:8]


def html_files():
    for path in sorted(ROOT.rglob("*.html")):
        parts = path.relative_to(ROOT).parts
        if parts[0] == "partials" or any(part.startswith(".") for part in parts):
            continue
        yield path


def page_url(path):
    rel = path.relative_to(ROOT).as_posix()
    return SITE_URL + "/" if rel == "index.html" else SITE_URL + "/" + rel


def first(pattern, text, default=""):
    match = re.search(pattern, text, re.S)
    return match.group(1).strip() if match else default


def fill_region(text, name, make_body):
    pattern = re.compile(
        r"(<!-- " + name + r"((?: [^>]*?)?) -->)(.*?)(<!-- /" + name + r" -->)", re.S
    )

    def repl(match):
        return match.group(1) + "\n" + make_body(match.group(2)).strip("\n") + "\n" + match.group(4)

    return pattern.sub(repl, text)


def stamp(text, path, partials, version):
    title = html.unescape(first(r"<title>(.*?)</title>", text))
    desc = html.unescape(first(r'<meta name="description" content="(.*?)"', text))
    head = (
        partials["head"]
        .replace("{{title}}", html.escape(title, quote=True))
        .replace("{{description}}", html.escape(desc, quote=True))
        .replace("{{url}}", page_url(path))
    )
    def head_region(attrs):
        if "noindex" in attrs:
            return '<meta name="robots" content="noindex, nofollow">\n' + head
        return head

    text = fill_region(text, "head", head_region)

    def header(attrs):
        active = first(r'active="([^"]*)"', attrs)
        out = partials["header"]
        if active:
            out = out.replace(f'data-nav="{active}"', f'data-nav="{active}" class="active"')
        return out

    text = fill_region(text, "header", header)
    text = fill_region(text, "footer", lambda attrs: partials["footer"])
    text = re.sub(r"(/assets/[\w.-]+\.(?:css|js|svg|png))\?v=[\w.-]+", r"\1?v=" + version, text)
    return text


def build(stage=False):
    partials = {name: read(ROOT / "partials" / f"{name}.html") for name in ("head", "header", "footer")}
    version = asset_version()
    changed = []
    for path in html_files():
        before = read(path)
        if "<!-- header" not in before:
            print(f"warning: {path.relative_to(ROOT)} has no shared-region markers, skipped")
            continue
        after = stamp(before, path, partials, version)
        if after != before:
            path.write_text(after, encoding="utf-8")
            changed.append(path)
    for path in changed:
        print("updated", path.relative_to(ROOT))
    if not changed:
        print("everything already up to date")
    if stage and changed:
        subprocess.run(["git", "add", "--"] + [str(p.relative_to(ROOT)) for p in changed], cwd=ROOT, check=True)
    print("asset version", version)


def new(section, slug, title=None):
    if section not in SECTIONS:
        sys.exit(f"unknown section {section!r}; choose one of: {', '.join(SECTIONS)}")
    info = SECTIONS[section]
    target = ROOT / section / f"{slug}.html"
    if target.exists():
        sys.exit(f"{target.relative_to(ROOT)} already exists")

    text = read(ROOT / "templates" / "article.html")
    today = datetime.date.today().isoformat()
    text = re.sub(r'<!-- header active="[^"]*" -->', f'<!-- header active="{section}" -->', text)
    text = re.sub(
        r'(<p class="post-meta">).*?(</p>)',
        lambda m: f'{m.group(1)}<span class="zh">{info["zh"]}</span><span class="en">{info["en"]}</span> · {today}{m.group(2)}',
        text, count=1, flags=re.S,
    )
    text = re.sub(
        r'<a class="post-back" href="[^"]*">.*?</a>',
        lambda m: f'<a class="post-back" href="{info["page"]}"><span class="zh">← 返回{info["zh"]}</span><span class="en">← {info["back_en"]}</span></a>',
        text, count=1, flags=re.S,
    )
    if title:
        safe = html.escape(title, quote=True)
        text = text.replace("<title>文章标题 · AI 学习与交流</title>", f"<title>{safe} · AI 学习与交流</title>")
        text = text.replace('<span class="zh">文章标题</span>', f'<span class="zh">{safe}</span>')

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    print(f"created {target.relative_to(ROOT)}")
    href = f"/{section}/{slug}.html"
    shown = html.escape(title or "标题", quote=True)
    print(f"\nnext: write the article, then add an entry on {info['page']}:\n")
    if section == "news":
        print(f'''<article class="news-entry">
  <span class="entry-meta">{today}</span>
  <h3><a href="{href}"><span class="zh">{shown}</span><span class="en">Title</span></a></h3>
  <p><span class="zh">一两句摘要。</span><span class="en">One or two sentence summary.</span></p>
</article>''')
    else:
        print(f'''<a class="entry-card" href="{href}">
  <h3><span class="zh">{shown}</span><span class="en">Title</span></h3>
  <p><span class="zh">一句话简介。</span><span class="en">One-line description.</span></p>
  <span class="entry-meta"><span class="zh">入门 · 8 讲</span><span class="en">Beginner · 8 lectures</span></span>
</a>''')
    print()
    build()


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["new"]:
        if len(args) < 3:
            sys.exit(__doc__)
        new(args[1], args[2], " ".join(args[3:]) or None)
    elif args in ([], ["--stage"]):
        build(stage=bool(args))
    else:
        sys.exit(__doc__)

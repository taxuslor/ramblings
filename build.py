#!/usr/bin/env python3
"""
Minimal static blog builder.
Reads markdown files from posts/, generates HTML into dist/.
No external dependencies beyond Python 3.6+ standard library.
For richer markdown (tables, fenced code, etc.), pip install markdown.
"""

import os, re, html, shutil, json
from pathlib import Path
from datetime import datetime

ROOT   = Path(__file__).parent
POSTS  = ROOT / "posts"
STATIC = ROOT / "static"
DIST   = ROOT / "dist"

# ---------- tiny markdown converter (no deps) ----------

def md_to_html(text):
    """Good-enough markdown → HTML for casual notes."""
    lines = text.split('\n')
    out, in_code, in_ul, in_ol, in_p = [], False, False, False, False

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul: out.append('</ul>'); in_ul = False
        if in_ol: out.append('</ol>'); in_ol = False

    def close_p():
        nonlocal in_p
        if in_p: out.append('</p>'); in_p = False

    for line in lines:
        stripped = line.strip()

        # fenced code blocks
        if stripped.startswith('```'):
            if in_code:
                out.append('</code></pre>')
                in_code = False
            else:
                close_p(); close_lists()
                lang = stripped[3:].strip()
                cls = f' class="language-{lang}"' if lang else ''
                out.append(f'<pre><code{cls}>')
                in_code = True
            continue
        if in_code:
            out.append(html.escape(line))
            continue

        # blank line
        if not stripped:
            close_p(); close_lists()
            continue

        # headings
        m = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if m:
            close_p(); close_lists()
            n = len(m.group(1))
            out.append(f'<h{n}>{inline(m.group(2))}</h{n}>')
            continue

        # hr
        if re.match(r'^[-*_]{3,}\s*$', stripped):
            close_p(); close_lists()
            out.append('<hr/>')
            continue

        # unordered list
        m = re.match(r'^[-*+]\s+(.+)$', stripped)
        if m:
            close_p()
            if not in_ul:
                close_lists()
                out.append('<ul>'); in_ul = True
            out.append(f'<li>{inline(m.group(1))}</li>')
            continue

        # ordered list
        m = re.match(r'^\d+\.\s+(.+)$', stripped)
        if m:
            close_p()
            if not in_ol:
                close_lists()
                out.append('<ol>'); in_ol = True
            out.append(f'<li>{inline(m.group(1))}</li>')
            continue

        # blockquote
        m = re.match(r'^>\s*(.*)', stripped)
        if m:
            close_p(); close_lists()
            out.append(f'<blockquote><p>{inline(m.group(1))}</p></blockquote>')
            continue

        # paragraph
        if not in_p:
            close_lists()
            out.append('<p>'); in_p = True
            out.append(inline(stripped))
        else:
            out.append('<br/>' + inline(stripped))

    close_p(); close_lists()
    if in_code: out.append('</code></pre>')
    return '\n'.join(out)


def inline(text):
    """Inline markdown: bold, italic, code, links, images."""
    text = html.escape(text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1"/>', text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    return text


# ---------- parse frontmatter ----------

def parse_post(filepath):
    raw = filepath.read_text(encoding='utf-8')
    meta = {}
    body = raw

    # YAML-ish frontmatter between ---
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', raw, re.DOTALL)
    if m:
        for line in m.group(1).split('\n'):
            k, _, v = line.partition(':')
            if v: meta[k.strip()] = v.strip().strip('"').strip("'")
        body = m.group(2)

    slug = filepath.stem
    # try to extract date from filename: 2026-04-15-title
    dm = re.match(r'^(\d{4}-\d{2}-\d{2})-(.+)$', slug)
    if dm:
        meta.setdefault('date', dm.group(1))
        slug = dm.group(2)

    meta.setdefault('title', slug.replace('-', ' ').title())
    meta.setdefault('date', datetime.fromtimestamp(filepath.stat().st_mtime).strftime('%Y-%m-%d'))

    return {
        'title': meta['title'],
        'date': meta['date'],
        'tags': [t.strip() for t in meta.get('tags', '').split(',') if t.strip()],
        'slug': slug,
        'body_html': md_to_html(body),
        'body_plain': body,
    }


# ---------- HTML templates ----------

def page_shell(title, body, back=False):
    back_link = '<a href="." class="back">&larr; back</a>' if back else ''
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="style.css"/>
</head>
<body>
<div class="container">
  <header>
    {back_link}
    <a href="." class="site-title">taxuslor / notes</a>
  </header>
  <main>{body}</main>
  <footer>
    <span>&copy; {datetime.now().year} taxuslor</span>
    <a href="https://taxuslor.github.io">constellation &rarr;</a>
  </footer>
</div>
</body>
</html>'''


def render_index(posts):
    items = []
    for p in posts:
        tags_html = ''.join(f'<span class="tag">{t}</span>' for t in p['tags'])
        items.append(f'''
    <a href="{p['slug']}.html" class="post-item">
      <div class="post-meta">
        <time>{p['date']}</time>
        {tags_html}
      </div>
      <h2>{html.escape(p['title'])}</h2>
    </a>''')
    body = '<div class="post-list">' + ''.join(items) + '</div>'
    return page_shell('notes — taxuslor', body)


def render_post(p):
    tags_html = ''.join(f'<span class="tag">{t}</span>' for t in p['tags'])
    body = f'''
<article>
  <div class="post-header">
    <h1>{html.escape(p['title'])}</h1>
    <div class="post-meta"><time>{p['date']}</time>{tags_html}</div>
  </div>
  <div class="post-body">{p['body_html']}</div>
</article>'''
    return page_shell(p['title'] + ' — taxuslor', body, back=True)


# ---------- build ----------

def build():
    # clean
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()

    # copy static assets
    if STATIC.exists():
        for f in STATIC.iterdir():
            shutil.copy2(f, DIST / f.name)

    # parse posts
    md_files = sorted(POSTS.glob('*.md'), reverse=True)
    if not md_files:
        print("No posts found in posts/. Creating a welcome post.")
        return

    posts = [parse_post(f) for f in md_files]
    posts.sort(key=lambda p: p['date'], reverse=True)

    # write index
    (DIST / 'index.html').write_text(render_index(posts), encoding='utf-8')

    # write posts
    for p in posts:
        (DIST / f"{p['slug']}.html").write_text(render_post(p), encoding='utf-8')

    print(f"Built {len(posts)} posts → dist/")


if __name__ == '__main__':
    build()

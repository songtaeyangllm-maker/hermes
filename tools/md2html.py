#!/usr/bin/env python3
"""
Hermes Markdown → HTML Converter
================================
Convert markdown to styled HTML for blogs/notes/SNS. No external deps.

Features: headings, bold/italic, links, code blocks, inline code, lists,
blockquotes, tables, horizontal rules, images, emoji.

Usage:
    python tools/md2html.py <file.md> [--out page.html] [--title "..."] [--theme dark]
    python tools/md2html.py <file.md> --stdout     # print HTML to console
    python tools/md2html.py hello.md --out hello.html --title "내 블로그"
"""

import argparse
import html
import re
from pathlib import Path

# ---------- Inline formatting ----------
def inline(text):
    text = html.escape(text)
    # Images ![alt](url)
    text = re.sub(r'!\[([^\]]*)\]\(([^)\s]+)(?:\s+"[^"]*")?\)',
                  r'<img src="\2" alt="\1" class="md-img">', text)
    # Links [text](url)
    text = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)',
                  r'<a href="\2">\1</a>', text)
    # Inline code `code`
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # Bold **text**
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    # Italic *text*
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', text)
    return text

def is_table_sep(line):
    stripped = line.strip()
    return bool(re.match(r'^\|?[\s:|-]+\|?$', stripped)) and '-' in stripped and stripped.replace('|', '').replace(' ', '').replace('-', '').replace(':', '') == ''

def parse_table(lines, i):
    """Parse a markdown table starting at line i. Returns (html, next_index)."""
    rows = []
    while i < len(lines) and lines[i].strip().startswith('|'):
        row = lines[i].strip().strip('|')
        cells = [c.strip() for c in row.split('|')]
        rows.append(cells)
        i += 1
    if len(rows) < 2:
        return '', i
    align = []
    for cell in rows[1]:
        c = cell.strip()
        left, right = c.startswith(':'), c.endswith(':')
        if left and right: align.append('center')
        elif right: align.append('right')
        elif left: align.append('left')
        else: align.append('')
    h = '<table><thead><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in rows[0]) + '</tr></thead><tbody>'
    for row in rows[2:]:
        h += '<tr>'
        for j, c in enumerate(row):
            style = f' style="text-align:{align[j]}"' if j < len(align) and align[j] else ''
            h += f'<td{style}>{inline(c)}</td>'
        h += '</tr>'
    h += '</tbody></table>'
    return h, i

def convert(md_text):
    lines = md_text.split('\n')
    out = []
    i = 0
    in_code = False
    code_buf = []
    in_list = False
    list_type = None
    in_quote = False

    def close_list():
        nonlocal in_list, list_type
        if in_list:
            out.append(f'</{list_type}>')
            in_list = False
            list_type = None

    def close_quote():
        nonlocal in_quote
        if in_quote:
            out.append('</blockquote>')
            in_quote = False

    while i < len(lines):
        line = lines[i]

        # Code block fences
        if line.strip().startswith('```'):
            if not in_code:
                in_code = True
                lang = line.strip()[3:].strip()
                code_buf = []
                out.append(f'<pre><code class="lang-{lang}">')
            else:
                in_code = False
                out.append(html.escape('\n'.join(code_buf)) + '</code></pre>')
            i += 1
            continue

        if in_code:
            code_buf.append(line)
            i += 1
            continue

        stripped = line.strip()

        # Blank line
        if not stripped:
            close_list(); close_quote(); out.append(''); i += 1; continue

        # Table
        if stripped.startswith('|') and i + 1 < len(lines) and is_table_sep(lines[i+1]):
            close_list(); close_quote()
            html_table, i = parse_table(lines, i)
            out.append(html_table)
            continue

        # Headings
        m = re.match(r'^(#{1,6})\s+(.*)$', stripped)
        if m:
            close_list(); close_quote()
            level = len(m.group(1))
            out.append(f'<h{level}>{inline(m.group(2))}</h{level}>')
            i += 1; continue

        # Horizontal rule
        if re.match(r'^(-{3,}|\*{3,}|_{3,})$', stripped):
            close_list(); close_quote()
            out.append('<hr>'); i += 1; continue

        # Blockquote
        if stripped.startswith('>'):
            if not in_quote:
                in_quote = True
                out.append('<blockquote>')
            inner = stripped.lstrip('>').strip()
            out.append('<p>' + inline(inner) + '</p>')
            i += 1; continue
        else:
            close_quote()

        # Lists
        m_ul = re.match(r'^[-*+]\s+(.*)$', stripped)
        m_ol = re.match(r'^\d+[.)]\s+(.*)$', stripped)
        if m_ul or m_ol:
            item = m_ul.group(1) if m_ul else m_ol.group(1)
            new_type = 'ul' if m_ul else 'ol'
            if not in_list or list_type != new_type:
                close_list()
                in_list = True
                list_type = new_type
                out.append(f'<{new_type}>')
            out.append(f'<li>{inline(item)}</li>')
            i += 1; continue

        # Regular paragraph
        close_list()
        out.append('<p>' + inline(stripped) + '</p>')
        i += 1

    # Close open blocks
    if in_code:
        out.append(html.escape('\n'.join(code_buf)) + '</code></pre>')
    close_list(); close_quote()

    return '\n'.join(out)

# ---------- Wrapper ----------
def wrap(body, title, theme):
    themes = {
        'dark': ('#0b0b12', '#13131c', '#ececf5', '#23233a', '#7c5cff', '#6b6f82'),
        'light': ('#f5f5fa', '#ffffff', '#1a1a24', '#e0e0ea', '#6a46e5', '#7a7a8c'),
        'sepia': ('#f7f1e3', '#fffdf6', '#4a3f2e', '#e5d9c0', '#8b5e3c', '#9c8c74'),
    }
    bg, card, text, border, accent, muted = themes.get(theme, themes['dark'])
    return f"""<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:-apple-system,'Segoe UI',Roboto,'Noto Sans KR',sans-serif;
          background:{bg}; color:{text}; line-height:1.8; padding:30px 20px; }}
  .wrap {{ max-width:720px; margin:0 auto; background:{card};
          border:1px solid {border}; border-radius:20px; padding:40px 48px; }}
  h1,h2,h3,h4,h5,h6 {{ margin:1.4em 0 0.6em; line-height:1.3; }}
  h1 {{ padding-bottom:0.3em; border-bottom:2px solid {border}; font-size:2em; }}
  h2 {{ font-size:1.5em; border-bottom:1px solid {border}; padding-bottom:0.2em; }}
  p {{ margin:0.8em 0; }}
  a {{ color:{accent}; }}
  code {{
      background:rgba(124,92,255,0.1); padding:0.15em 0.4em; border-radius:4px;
      font-family:'JetBrains Mono',Consolas,monospace; font-size:0.9em; }}
  pre {{ background:{'#' if theme=='dark' else '#'}0d0d12; padding:16px; border-radius:12px;
        overflow-x:auto; border:1px solid {border}; }}
  pre code {{ background:transparent; padding:0; }}
  blockquote {{ border-left:4px solid {accent}; margin:1em 0; padding:0.5em 1em;
                background:rgba(124,92,255,0.06); border-radius:0 8px 8px 0; }}
  ul,ol {{ padding-left:1.6em; margin:0.8em 0; }}
  li {{ margin:0.3em 0; }}
  table {{ border-collapse:collapse; width:100%; margin:1em 0; }}
  th,td {{ border:1px solid {border}; padding:8px 14px; text-align:left; }}
  th {{ background:rgba(124,92,255,0.1); }}
  img {{ max-width:100%; border-radius:10px; }}
  hr {{ border:none; border-top:1px solid {border}; margin:2em 0; }}
</style></head>
<body><div class="wrap">
{body}
<p style="text-align:center;color:{muted};font-size:0.8em;margin-top:3em;border-top:1px solid {border};padding-top:1.5em;">
  ⚡ generated by Hermes Agent · {theme} theme</p>
</div></body></html>
"""

def main():
    ap = argparse.ArgumentParser(prog='md2html.py')
    ap.add_argument('file')
    ap.add_argument('--out', help='output html file (default: <name>.html in same dir)')
    ap.add_argument('--title', default='Hermes Markdown')
    ap.add_argument('--theme', default='dark', choices=['dark', 'light', 'sepia'])
    ap.add_argument('--stdout', action='store_true')
    args = ap.parse_args()

    src = Path(args.file)
    if not src.exists():
        print(f"❌ 파일 없음: {src}")
        return
    md_text = src.read_text(encoding='utf-8')

    # Auto title from first H1 if not provided
    title = args.title
    if title == 'Hermes Markdown':
        m = re.search(r'^#\s+(.+)$', md_text, re.M)
        if m:
            title = m.group(1).strip()

    body = convert(md_text)
    page = wrap(body, title, args.theme)

    if args.stdout:
        print(page)
        return

    out = Path(args.out) if args.out else src.with_suffix('.html')
    out.write_text(page, encoding='utf-8')
    print(f"✅ {src.name} → {out.name} ({theme_label(args.theme)}, {len(page)//1024}KB)")

def theme_label(t):
    return {'dark': '다크', 'light': '라이트', 'sepia': '세피아'}.get(t, t)

if __name__ == '__main__':
    main()

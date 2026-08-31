#!/usr/bin/env python3
"""
Hermes Status Badge Generator
=============================
Generate SVG status badges / cards from live workspace data: code lines,
tool count, project count, last refresh, etc. Use in README, blog, or SNS.

Usage:
    python tools/badge.py [--out C:/hermes/projects/badge/status.svg]
    python tools/badge.py --card   # big summary card instead of flat badge
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

WS = Path('C:/hermes')

def run_lines():
    """Count py lines."""
    total = 0
    for p in (WS / 'tools').glob('*.py'):
        try:
            total += len(p.read_text(encoding='utf-8').splitlines())
        except Exception:
            pass
    return total

def count_py():
    return len(list((WS / 'tools').glob('*.py')))

def project_count():
    try:
        data = json.load(open(WS / 'projects' / 'projects.json', encoding='utf-8'))
        projects = data if isinstance(data, list) else data.get('projects', [])
        active = sum(1 for p in projects if (p.get('status') == 'active'))
        return len(projects), active
    except Exception:
        return 0, 0

def tree_count():
    n = 0
    for p in (WS).rglob('*.py'):
        n += 1
    for p in (WS).rglob('*.html'):
        n += 1
    for p in (WS).rglob('*.js'):
        n += 1
    return n

def flat_badge():
    py_lines = run_lines()
    tools = count_py()
    projects, active = project_count()
    files = tree_count()
    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    W = 820; H = 34
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="0">
<stop offset="0%" stop-color="#7c5cff"/><stop offset="100%" stop-color="#5c8aff"/>
</linearGradient></defs>
<rect x="0" y="0" width="{W}" height="{H}" rx="8" fill="#13131c" stroke="#23233a"/>
<text x="16" y="22" font-family="monospace" font-size="13" fill="#ececf5" font-weight="bold">⚡ HERMES</text>
<text x="88" y="22" font-family="monospace" font-size="12" fill="#b39cff">{py_lines}줄</text>
<text x="160" y="22" font-family="monospace" font-size="12" fill="#5ce6a8">{tools}도구</text>
<text x="232" y="22" font-family="monospace" font-size="12" fill="#ffcf5c">{projects}프로젝트</text>
<text x="340" y="22" font-family="monospace" font-size="12" fill="#5cd6ff">{files}파일</text>
<text x="420" y="22" font-family="monospace" font-size="12" fill="#6b6f82">│ {now}</text>
</svg>
""", {'py_lines': py_lines, 'tools': tools, 'projects': projects, 'files': files}

def card_badge():
    py_lines = run_lines()
    tools = count_py()
    projects, active = project_count()
    files = tree_count()
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    W = 420; H = 220
    # helper
    cells = [
        ('📝', f'{py_lines}', '코드 줄'),
        ('🛠️', f'{tools}', '도구'),
        ('🗂️', f'{projects}', '프로젝트'),
        ('📄', f'{files}', '파일'),
    ]
    cell_html = ''
    cx = 24
    for emoji, val, label in cells:
        cell_html += f"""<g>
<rect x="{cx}" y="96" width="84" height="66" rx="12" fill="#0d0d17" stroke="#23233a"/>
<text x="{cx+42}" y="124" font-family="monospace" font-size="22" text-anchor="middle" fill="#ececf5" font-weight="bold">{val}</text>
<text x="{cx+42}" y="146" font-family="monospace" font-size="11" text-anchor="middle" fill="#6b6f82">{label}</text>
</g>"""
        cx += 96
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
<stop offset="0%" stop-color="#1a1430"/><stop offset="100%" stop-color="#13131c"/>
</linearGradient></defs>
<rect x="0" y="0" width="{W}" height="{H}" rx="20" fill="url(#bg)" stroke="#23233a" stroke-width="1.5"/>
<text x="24" y="46" font-family="monospace" font-size="17" fill="#b39cff" font-weight="bold">Hermes Workspace</text>
<text x="24" y="70" font-family="monospace" font-size="11" fill="#6b6f82">내가 자유롭게 만든 개인 지휘 센터</text>
<rect x="396" y="26" width="0" height="0" rx="4"/>
{cell_html}
<text x="24" y="192" font-family="monospace" font-size="10" fill="#6b6f82">갱신: {now} · Hermes Agent</text>
<rect x="348" y="176" width="48" height="14" rx="7" fill="#7c5cff"/>
<text x="372" y="186" font-family="monospace" font-size="8" fill="#fff" text-anchor="middle">v2.0</text>
</svg>
""", {'py_lines': py_lines, 'tools': tools, 'projects': projects, 'files': files}

def main():
    ap = argparse.ArgumentParser(prog='badge.py')
    ap.add_argument('--card', action='store_true', help='big summary card')
    ap.add_argument('--out', default='C:/hermes/projects/badge/status.svg')
    args = ap.parse_args()

    svg, stats = card_badge() if args.card else flat_badge()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg, encoding='utf-8')
    print(f"✅ 뱃지 생성: {out}")
    print(f"   📝 {stats['py_lines']}줄 · 🛠️ {stats['tools']}도구 · 🗂️ {stats['projects']}프로젝트 · 📄 {stats['files']}파일")

if __name__ == '__main__':
    main()

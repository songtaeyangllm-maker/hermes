#!/usr/bin/env python3
"""
Hermes Diary & Notes CLI
========================
Write and manage dated diary entries and notes in notes/.

Usage:
    python tools/diary.py write            # write today's entry (opens editor / or prompt)
    python tools/diary.py write --text "..."   # quick entry
    python tools/diary.py read [date]      # read entry (default today)
    python tools/diary.py list             # list all entries
    python tools/diary.py search <keyword> # search entries
    python tools/diary.py today            # show today's summary
    python tools/diary.py stats            # entry stats

Dates: YYYY-MM-DD (default today). Entries stored as notes/diary/YYYY-MM-DD.md
"""

import argparse
import sys
import subprocess
from datetime import datetime
from pathlib import Path

NOTES_DIR = Path(r"C:\hermes\notes") / 'diary'

def ensure():
    NOTES_DIR.mkdir(parents=True, exist_ok=True)

def entry_path(date_str):
    return NOTES_DIR / f"{date_str}.md"

def today_str():
    return datetime.now().strftime('%Y-%m-%d')

def cmd_write(args, date_str, text):
    ensure()
    path = entry_path(date_str)
    if text:
        content = text.strip() + "\n"
    else:
        # Try to open default editor, else fall back to stdin lines
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        print(f"📝 Writing entry for {date_str} (비어있을 경우 Ctrl+D / 빈 줄 2개로 종료)")
        print("-" * 40)
        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            if line.strip() == '' and lines and lines[-1].strip() == '':
                break
            lines.append(line)
        content = "\n".join(lines).strip() + "\n"
    # Append if entry exists, else create with header
    if path.exists():
        with open(path, 'a', encoding='utf-8') as f:
            f.write(f"\n## 추가 {datetime.now().strftime('%H:%M')}\n{content}")
        action = "추가"
    else:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"# 📔 {date_str}\n\n{content}")
        action = "생성"
    print(f"✅ {action} 완료: {path.name}")

def cmd_read(args, date_str):
    path = entry_path(date_str)
    if not path.exists():
        print(f"📭 {date_str}에 작성된 일기가 없습니다.")
        return
    print(path.read_text(encoding='utf-8'))

def cmd_list(args):
    ensure()
    entries = sorted(NOTES_DIR.glob('*.md'), reverse=True)
    if not entries:
        print("📭 아직 작성된 일기가 없습니다.")
        return
    print(f"📚 일기 목록 ({len(entries)}개)")
    print("-" * 40)
    for e in entries:
        text = e.read_text(encoding='utf-8')
        lines = [l for l in text.splitlines() if l.strip()][:3]
        first = next((l for l in text.splitlines() if l.strip() and not l.startswith('#')), '')
        print(f"  📄 {e.stem}  •  {first[:40] if first else ''}")

def cmd_search(args, keyword):
    ensure()
    print(f"🔍 '{keyword}' 검색 결과")
    print("-" * 40)
    found = 0
    for e in sorted(NOTES_DIR.glob('*.md'), reverse=True):
        text = e.read_text(encoding='utf-8')
        if keyword.lower() in text.lower():
            found += 1
            for i, line in enumerate(text.splitlines()):
                if keyword.lower() in line.lower():
                    print(f"  📄 {e.stem}: {line.strip()[:70]}")
                    break
    if not found:
        print("  검색 결과 없음")

def cmd_stats(args):
    ensure()
    entries = list(NOTES_DIR.glob('*.md'))
    total_chars = sum(len(e.read_text(encoding='utf-8')) for e in entries)
    print("📊 일기 통계")
    print("=" * 30)
    print(f"  총 일기 수: {len(entries)}")
    print(f"  총 글자 수: {total_chars}")
    if entries:
        dates = [e.stem for e in entries]
        print(f"  최초: {min(dates)}")
        print(f"  최근: {max(dates)}")

def cmd_export(args):
    """Export diary data as JSON for heatmap widgets."""
    ensure()
    entries = sorted(NOTES_DIR.glob('*.md'))
    import json, datetime
    data = {
        'generated': datetime.date.today().isoformat(),
        'entries': [],
        'total': len(entries),
        'total_chars': 0,
    }
    for e in entries:
        text = e.read_text(encoding='utf-8')
        n = len(text)
        data['total_chars'] += n
        data['entries'].append({'date': e.stem, 'chars': n, 'lines': text.count('\n') + 1})
    # Build last-365-day heatmap grid (date -> count)
    today = datetime.date.today()
    grid = {}
    for d in data['entries']:
        grid[d['date']] = 1
    data['heatmap'] = grid
    print(json.dumps(data, ensure_ascii=False, indent=2))

def main():
    ap = argparse.ArgumentParser(prog='diary.py')
    sub = ap.add_subparsers(dest='cmd', required=True)

    p_write = sub.add_parser('write', help='write entry')
    p_write.add_argument('--text', help='quick text')
    p_write.add_argument('--date', default=today_str())

    p_read = sub.add_parser('read', help='read entry')
    p_read.add_argument('date', nargs='?', default=today_str())

    sub.add_parser('list', help='list entries')
    p_search = sub.add_parser('search', help='search entries')
    p_search.add_argument('keyword')
    sub.add_parser('today', help='today summary')
    sub.add_parser('stats', help='stats')
    sub.add_parser('export', help='export JSON (heatmap)')

    args = ap.parse_args()
    ensure()

    if args.cmd == 'write':
        cmd_write(args, args.date, args.text)
    elif args.cmd == 'read':
        cmd_read(args, args.date)
    elif args.cmd == 'list':
        cmd_list(args)
    elif args.cmd == 'search':
        cmd_search(args, args.keyword)
    elif args.cmd == 'today':
        cmd_read(args, today_str())
    elif args.cmd == 'stats':
        cmd_stats(args)
    elif args.cmd == 'export':
        cmd_export(args)

if __name__ == '__main__':
    main()

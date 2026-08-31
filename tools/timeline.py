#!/usr/bin/env python3
"""
Hermes Activity Timeline
=======================
Collect workspace activity (git commits, diary entries, reports, project
updates) and produce a JSON for the HTML timeline widget.

Usage:
    python tools/timeline.py                        # build data + write projects/timeline/timeline_data.js + .json
    python tools/timeline.py --json                 # print JSON to stdout
"""

import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

WS = Path('C:/hermes')

def git_log(n=50):
    if not (WS / '.git').exists():
        return []
    try:
        r = subprocess.run(['git', 'log', f'-{n}', '--pretty=format:%H|%ad|%s',
                            '--date=iso', '--no-color'], cwd=str(WS),
                           capture_output=True, text=True, timeout=30)
    except Exception:
        return []
    events = []
    for line in r.stdout.strip().splitlines():
        if not line:
            continue
        parts = line.split('|')
        if len(parts) < 3:
            continue
        sha, date, msg = parts[0], parts[1], '|'.join(parts[2:])
        try:
            dt = datetime.fromisoformat(date.strip())
        except Exception:
            continue
        events.append({'type': 'git', 'ts': dt.isoformat(), 'title': '📦 git 커밋',
                       'detail': msg, 'ref': sha[:7]})
    return events

def diary_events():
    events = []
    for f in (WS / 'notes' / 'diary').glob('*.md'):
        m = re.match(r'(\d{4}-\d{2}-\d{2})', f.stem)
        if not m:
            continue
        try:
            dt = datetime.strptime(m.group(1), '%Y-%m-%d')
        except Exception:
            continue
        txt = f.read_text(encoding='utf-8', errors='ignore').strip()
        first = txt.splitlines()[0] if txt.splitlines() else '일기'
        events.append({'type': 'diary', 'ts': dt.isoformat(), 'title': '📔 일기 작성',
                       'detail': first[:60]})
    return events

def report_events():
    events = []
    for f in (WS / 'notes' / 'reports').glob('*.md'):
        m = re.match(r'report_(\d{4}-\d{2}-\d{2})', f.stem)
        if not m:
            continue
        try:
            dt = datetime.strptime(m.group(1), '%Y-%m-%d')
        except Exception:
            continue
        events.append({'type': 'report', 'ts': dt.isoformat(), 'title': '📊 일일 보고서',
                       'detail': f.stem})
    return events

def collect():
    events = git_log() + diary_events() + report_events()
    events.sort(key=lambda e: e['ts'], reverse=True)
    return events

def main():
    ap = argparse.ArgumentParser(prog='timeline.py')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--out-dir', default='C:/hermes/projects/timeline')
    args = ap.parse_args()

    events = collect()
    if args.json:
        print(json.dumps(events, ensure_ascii=False, indent=2))
        return

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    js = 'window.HERMES_TIMELINE = ' + json.dumps(events, ensure_ascii=False)
    (out / 'timeline_data.js').write_text(js, encoding='utf-8')
    (out / 'timeline_data.json').write_text(json.dumps(events, ensure_ascii=False, indent=2), encoding='utf-8')
    types = {}
    for e in events:
        types[e['type']] = types.get(e['type'], 0) + 1
    print(f"✅ 타임라인 생성: {out}")
    print(f"   총 {len(events)}개 이벤트 · " + ', '.join(f"{k}:{v}" for k, v in types.items()))

if __name__ == '__main__':
    main()

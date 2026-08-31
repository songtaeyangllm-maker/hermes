#!/usr/bin/env python3
"""
Hermes Auto-Commit
==================
Stage and commit workspace changes automatically (used by cron / CLI).

Usage:
    python tools/autocommit.py            # commit all changes
    python tools/autocommit.py --check    # just report dirty state
    python tools/autocommit.py --message "custom"
"""

import argparse
import subprocess
from datetime import datetime
from pathlib import Path

WS = Path('C:/hermes')

def git(*args, cwd=WS):
    return subprocess.run(['git'] + list(args), cwd=str(cwd),
                          capture_output=True, text=True)

def is_dirty():
    r = git('status', '--porcelain')
    return bool(r.stdout.strip())

def commit(message):
    git('add', '-A')
    r = git('commit', '-m', message)
    return r

def main():
    ap = argparse.ArgumentParser(prog='autocommit.py')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--message', default=None)
    args = ap.parse_args()

    if not (WS / '.git').exists():
        print("❌ git 저장소 없음 (git init 필요)")
        return

    dirty = is_dirty()
    if args.check:
        files = git('status', '--porcelain').stdout.strip().splitlines()
        summary = {}
        for f in files:
            status, path = f[:2].strip(), f[3:]
            ext = path.split('.')[-1] if '.' in path else 'none'
            summary[ext] = summary.get(ext, 0) + 1
        total = len(files)
        desc = ', '.join(f".{k}:{v}" for k, v in sorted(summary.items())) if summary else "깨끗"
        print(f"{'🟢 깨끗함' if not dirty else '🟡 변경 '}{total}개 파일 ({desc})")
        return

    if not dirty:
        print("🟢 변경 사항 없음 — 커밋 스킵")
        return

    message = args.message or f"auto: 워크스페이스 갱신 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    r = commit(message)
    files = len(git('status', '--porcelain').stdout.strip().splitlines())
    print(f"✅ 커밋 완료: {message}")
    print(f"   남은 변경: {files}개")
    # show short stat
    s = git('show', '--stat', '--oneline', 'HEAD').stdout.strip().splitlines()
    for line in s[-3:]:
        print(f"   {line}")

if __name__ == '__main__':
    main()

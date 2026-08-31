#!/usr/bin/env python3
"""
Hermes Folder Treemap Scanner
=============================
Scan a directory and produce a JSON treemap (hierarchical sizes) for the
HTML visualization widget (projects/treemap/).

Usage:
    python tools/treemap.py [dir] [--depth N] [--out dir]
    # default dir = C:/hermes, out = projects/treemap/tree_data.json
"""

import argparse
import json
import os
from pathlib import Path

def human(n):
    for u in ['B', 'KB', 'MB', 'GB', 'TB']:
        if n < 1024 or u == 'TB':
            return f"{n:.1f}{u}" if u != 'B' else f"{int(n)}B"
        n /= 1024

def scan(path, depth, max_depth, hard_limit_mb=50):
    """Return {name, size, children:[...]} lazily. Cut subtrees that exceed depth.
    hard_limit_mb: skip descending into folders larger than this (treat as leaf)."""
    p = Path(path)
    children = []
    total = 0
    try:
        if depth >= max_depth:
            # leaf: sum file sizes quickly
            total = 0
            for f in p.rglob('*'):
                try:
                    if f.is_file():
                        total += f.stat().st_size
                except OSError:
                    pass
            return {'name': p.name, 'size': total, 'children': []}

        for entry in sorted(p.iterdir(), key=lambda e: e.name.lower()):
            try:
                if entry.is_file():
                    sz = entry.stat().st_size
                    total += sz
                    children.append({'name': entry.name, 'size': sz, 'children': []})
                elif entry.is_dir():
                    sub = scan(entry, depth + 1, max_depth)
                    if sub['size'] > 0:
                        total += sub['size']
                        children.append(sub)
                # limit children to top N by size to keep JSON manageable
                children.sort(key=lambda c: c['size'], reverse=True)
            except OSError:
                continue
    except OSError:
        pass
    children.sort(key=lambda c: c['size'], reverse=True)
    return {'name': p.name, 'size': total, 'children': children[:40]}

def main():
    ap = argparse.ArgumentParser(prog='treemap.py')
    ap.add_argument('dir', nargs='?', default='C:/hermes')
    ap.add_argument('--depth', type=int, default=3)
    ap.add_argument('--out', default='C:/hermes/projects/treemap/tree_data.json')
    args = ap.parse_args()

    root = Path(args.dir)
    if not root.exists():
        print(f"❌ 경로 없음: {root}")
        return

    print(f"🔍 스캔 중: {root} (depth {args.depth}) ...")
    data = scan(root, 0, args.depth)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    js = 'window.HERMES_TREE = ' + json.dumps(data, ensure_ascii=False)
    out.with_suffix('.js').write_text(js, encoding='utf-8')
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f"✅ 완료: {human(data['size'])} · 자식 {len(data['children'])}개")
    print(f"  데이터: {out}")
    print(f"  JS:     {out.with_suffix('.js')}")

if __name__ == '__main__':
    main()

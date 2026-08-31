#!/usr/bin/env python3
"""
Hermes File Utilities
=====================
Practical file tools: image resize/convert, batch rename, duplicate finder,
folder size, and cleanup.

Usage:
    # Image tools (Pillow)
    python tools/file_utils.py img-resize <file> [--width 800] [--height 600]
    python tools/file_utils.py img-convert <file> --to png
    python tools/file_utils.py img-compress <file> [--quality 70]

    # Batch rename
    python tools/file_utils.py rename <dir> --prefix img_ --num 1        # img_001.jpg...
    python tools/file_utils.py rename <dir> --suffix _bak
    python tools/file_utils.py rename <dir> --ext .md                    # lowercase ext

    # Analysis
    python tools/file_utils.py dup <dir>              # find duplicate files by size+hash
    python tools/file_utils.py size <dir>             # folder size breakdown
    python tools/file_utils.py large <dir> --top 10   # largest files

    # Cleanup
    python tools/file_utils.py clean <dir> --ext .tmp --dry-run   # delete .tmp (dry run)
"""

import argparse
import hashlib
import os
import sys
from collections import defaultdict
from pathlib import Path

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}

def human(n):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"

def _load_image(path):
    try:
        from PIL import Image
        global _PIL_Image
        _PIL_Image = Image
        return Image.open(path)
    except ImportError:
        print("❌ Pillow(PIL) 필요: pip install Pillow")
        sys.exit(1)

#----------
def _pil():
    """Return the PIL Image module (lazy import)."""
    global _PIL_Image
    if '_PIL_Image' not in globals():
        try:
            from PIL import Image
            _PIL_Image = Image
        except ImportError:
            print("❌ Pillow(PIL) 필요: pip install Pillow")
            sys.exit(1)
    return _PIL_Image

# ---------- Image tools ----------
def img_resize(path, width, height):
    p = Path(path)
    if not p.exists():
        print(f"❌ 파일 없음: {p}")
        return
    Image = _pil()
    img = _load_image(p).convert('RGB')
    orig = img.size
    if width and height:
        img = img.resize((width, height), Image.LANCZOS)
    elif width:
        ratio = width / img.width
        img = img.resize((width, int(img.height * ratio)), Image.LANCZOS)
    elif height:
        ratio = height / img.height
        img = img.resize((int(img.width * ratio), height), Image.LANCZOS)
    else:
        print("❌ --width 또는 --height 지정 필요")
        return
    out = p.with_name(f"{p.stem}_resized{p.suffix}")
    img.save(out)
    print(f"✅ {p.name} ({orig[0]}x{orig[1]}) -> {out.name} ({img.size[0]}x{img.size[1]})")

def img_convert(path, to_fmt):
    p = Path(path)
    if not p.exists():
        print(f"❌ 파일 없음: {p}")
        return
    img = _load_image(p)
    if img.mode in ('RGBA', 'LA', 'P') and to_fmt == 'jpg':
        img = img.convert('RGB')  # JPEG no alpha
    out = p.with_suffix('.' + to_fmt)
    img.save(out)
    print(f"✅ {p.name} -> {out.name}")

def img_compress(path, quality):
    p = Path(path)
    if not p.exists():
        print(f"❌ 파일 없음: {p}")
        return
    img = _load_image(p).convert('RGB')
    old_size = p.stat().st_size
    out = p.with_name(f"{p.stem}_q{quality}{p.suffix}")
    img.save(out, quality=quality, optimize=True)
    new_size = out.stat().st_size
    saved = (1 - new_size / old_size) * 100 if old_size else 0
    print(f"✅ 압축: {human(old_size)} -> {human(new_size)} ({saved:.0f}% 절약)")

# ---------- Batch rename ----------
def rename(dir, prefix, suffix, ext):
    d = Path(dir)
    if not d.is_dir():
        print(f"❌ 디렉토리 없음: {d}")
        return
    files = sorted([f for f in d.iterdir() if f.is_file()])
    if not files:
        print("📭 파일 없음")
        return
    count = 0
    for i, f in enumerate(files, 1):
        new_name = ""
        if prefix is not None:
            new_name = f"{prefix}{i:03d}{f.suffix}"
        elif suffix is not None:
            new_name = f"{f.stem}{suffix}{f.suffix}"
        elif ext is not None:
            new_name = f"{f.stem}{ext.lower()}"
        if not new_name or new_name == f.name:
            continue
        target = d / new_name
        if target.exists():
            print(f"  ⚠️  건너뜀 (이미 존재): {new_name}")
            continue
        f.rename(target)
        print(f"  🔄 {f.name} -> {new_name}")
        count += 1
    print(f"✅ {count}개 이름 변경")

# ---------- Analysis ----------
def find_duplicates(dir):
    d = Path(dir)
    if not d.is_dir():
        print(f"❌ 디렉토리 없음: {d}")
        return
    # Group by size first
    by_size = defaultdict(list)
    for f in d.rglob('*'):
        if f.is_file():
            try:
                by_size[f.stat().st_size].append(f)
            except OSError:
                pass
    dup_groups = []
    for size, files in by_size.items():
        if len(files) < 2:
            continue
        # Hash candidates
        hashes = defaultdict(list)
        for f in files:
            h = hashlib.md5()
            with open(f, 'rb') as fp:
                for chunk in iter(lambda: fp.read(8192), b''):
                    h.update(chunk)
            hashes[h.hexdigest()].append(f)
        for h, group in hashes.items():
            if len(group) > 1:
                dup_groups.append(group)
    if not dup_groups:
        print("✅ 중복 파일 없음")
        return
    print(f"🔍 중복 그룹 {len(dup_groups)}개 발견:")
    for group in dup_groups:
        print(f"  - {human(group[0].stat().st_size)}:")
        for f in group:
            print(f"      📄 {f}")

def folder_size(dir):
    d = Path(dir)
    if not d.is_dir():
        print(f"❌ 디렉토리 없음: {d}")
        return
    with os.scandir(d) as it:
        entries = [e for e in it if e.is_dir()]
    print(f"📊 '{d.name}/' 하위 폴더 크기:")
    print("-" * 40)
    table = []
    for e in entries:
        total = sum(f.stat().st_size for f in Path(e.path).rglob('*') if f.is_file())
        table.append((e.name, total))
    table.sort(key=lambda x: -x[1])
    total_all = sum(t[1] for t in table)
    for name, size in table:
        pct = (size / total_all * 100) if total_all else 0
        bar = '█' * int(pct / 5)
        print(f"  {name:12s} {human(size):>10s}  {bar}")
    print(f"{'─'*40}")
    print(f"  {'TOTAL':12s} {human(total_all):>10s}")

def largest_files(dir, top):
    d = Path(dir)
    if not d.is_dir():
        print(f"❌ 디렉토리 없음: {d}")
        return
    files = [(f, f.stat().st_size) for f in d.rglob('*')
             if f.is_file() and 'node_modules' not in str(f) and '__pycache__' not in str(f)]
    files.sort(key=lambda x: -x[1])
    print(f"📦 '{d.name}/' 최대 파일 {len(files[:top])}개:")
    for f, size in files[:top]:
        print(f"  {human(size):>10s}  {f}")

# ---------- Cleanup ----------
def clean(dir, ext, dry_run):
    d = Path(dir)
    if not d.is_dir():
        print(f"❌ 디렉토리 없음: {d}")
        return
    if not ext.startswith('.'):
        ext = '.' + ext
    targets = [f for f in d.rglob(f'*{ext}') if f.is_file()]
    if not targets:
        print(f"📭 {ext} 파일 없음")
        return
    removed = 0
    for f in targets:
        if dry_run:
            print(f"  🔎 [dry] 삭제 예정: {f}")
        else:
            f.unlink()
            print(f"  🗑️  삭제: {f}")
        removed += 1
    mode = " (dry-run, 실제 삭제 안함)" if dry_run else ""
    print(f"✅ {removed}개 {ext} 파일 처리{mode}")

def main():
    ap = argparse.ArgumentParser(prog='file_utils.py')
    sub = ap.add_subparsers(dest='cmd', required=True)

    r = sub.add_parser('img-resize'); r.add_argument('file'); r.add_argument('--width', type=int); r.add_argument('--height', type=int)
    c = sub.add_parser('img-convert'); c.add_argument('file'); c.add_argument('--to', required=True)
    q = sub.add_parser('img-compress'); q.add_argument('file'); q.add_argument('--quality', type=int, default=70)

    rn = sub.add_parser('rename'); rn.add_argument('dir'); rn.add_argument('--prefix'); rn.add_argument('--suffix'); rn.add_argument('--ext')

    dp = sub.add_parser('dup'); dp.add_argument('dir')
    sz = sub.add_parser('size'); sz.add_argument('dir')
    lg = sub.add_parser('large'); lg.add_argument('dir'); lg.add_argument('--top', type=int, default=10)

    cl = sub.add_parser('clean'); cl.add_argument('dir'); cl.add_argument('--ext', required=True); cl.add_argument('--dry-run', action='store_true')

    args = ap.parse_args()

    try:
        if args.cmd == 'img-resize':
            img_resize(args.file, args.width, args.height)
        elif args.cmd == 'img-convert':
            img_convert(args.file, args.to.lower().lstrip('.'))
        elif args.cmd == 'img-compress':
            img_compress(args.file, args.quality)
        elif args.cmd == 'rename':
            rename(args.dir, args.prefix, args.suffix, args.ext)
        elif args.cmd == 'dup':
            find_duplicates(args.dir)
        elif args.cmd == 'size':
            folder_size(args.dir)
        elif args.cmd == 'large':
            largest_files(args.dir, args.top)
        elif args.cmd == 'clean':
            clean(args.dir, args.ext, args.dry_run)
    except TypeError:
        ap.print_help()

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Hermes Wordcloud Generator
========================
Generate a wordcloud image from workspace notes/diary/README using Pillow
(a simple adequate-spacing layout — no external wordcloud library).

Usage:
    python tools/wordcloud.py                    # default: notes + README
    python tools/wordcloud.py C:/hermes/notes    # custom dir
    python tools/wordcloud.py --top 40 --out C:/hermes/projects/wordcloud/wc.png
    python tools/wordcloud.py --shape circle     # circle or rectangle
"""

import argparse
import math
import random
import re
from collections import Counter
from pathlib import Path

def _pil():
    from PIL import Image, ImageDraw, ImageFont
    return Image, ImageDraw, ImageFont

def gather_text(dirs):
    words = []
    stop = set("""그리고 그리고 그런 그래서 그리고는 아니 이 그 것 를 에 은 는 이 가 을 의 에서 로 하다 있다 되다 하 수 있다 있다고""".split())
    for d in dirs:
        for root in [Path(d)]:
            if root.is_file():
                files = [root]
            else:
                files = list(root.rglob('*'))
            for f in files:
                if f.is_file() and f.suffix in {'.md', '.txt'}:
                    try:
                        txt = f.read_text(encoding='utf-8', errors='ignore').lower()
                    except Exception:
                        continue
                    # korean chunks + ascii words
                    ko = re.findall(r'[가-힣]{2,}', txt)
                    en = re.findall(r'[a-z][a-z0-9_]{2,}', txt)
                    for w in ko + en:
                        if w not in stop and len(w) >= 2:
                            words.append(w)
    return words

def layout(size, padding, W, H):
    """Place word boxes greedily avoiding overlaps."""
    Image, ImageDraw, ImageFont = _pil()
    placed = []
    placed_rects = []  # list of (x,y,w,h)
    random.seed(42)
    # sort by size desc to place big first
    def collides(x, y, w, h):
        for (px, py, pw, ph) in placed_rects:
            if x < px + pw + padding and px < x + w + padding and \
               y < py + ph + padding and py < y + h + padding:
                return True
        return False

    for word, freq, fs in size:
        # font metrics
        img = Image.new('RGB', (1, 1))
        dr = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', fs)
        except Exception:
            font = ImageFont.load_default()
        # measure
        bbox = dr.textbbox((0, 0), word, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        if tw <= 0 or th <= 0:
            continue
        # try positions (spiral outward)
        found = False
        for i in range(400):
            # pseudo spiral
            cx = W // 2 + int((random.random() - 0.3) * W * 0.8)
            cy = H // 2 + int((random.random() - 0.3) * H * 0.7)
            x = cx - tw // 2
            y = cy - th // 2
            if 0 <= x and 0 <= y and x + tw <= W and y + th <= H:
                if not collides(x, y, tw, th):
                    placed.append((word, freq, fs, x, y, tw, th, font, bbox))
                    placed_rects.append((x, y, tw, th))
                    found = True
                    break
        # fallback: random
        if not found:
            for _ in range(200):
                x = random.randint(0, max(0, W - tw))
                y = random.randint(0, max(0, H - th))
                if not collides(x, y, tw, th):
                    placed.append((word, freq, fs, x, y, tw, th, font, bbox))
                    placed_rects.append((x, y, tw, th))
                    break
    return placed

def main():
    ap = argparse.ArgumentParser(prog='wordcloud.py')
    ap.add_argument('dir', nargs='*', default=['C:/hermes/notes', 'C:/hermes/README.md'])
    ap.add_argument('--top', type=int, default=36)
    ap.add_argument('--out', default='C:/hermes/projects/wordcloud/wc.png')
    ap.add_argument('--size', default='1200x800')
    ap.add_argument('--bg', default='#13131c')
    args = ap.parse_args()

    Image, ImageDraw, ImageFont = _pil()
    words = gather_text(args.dir)
    if not words:
        print("❌ 텍스트 없음")
        return
    counts = Counter(words)
    top = counts.most_common(args.top)
    maxf = max(f for _, f in top)

    W, H = (int(x) for x in args.size.lower().split('x'))
    img = Image.new('RGB', (W, H), args.bg)
    dr = ImageDraw.Draw(img)

    # font sizes scaled by frequency
    size_items = []
    for word, freq in top:
        fs = int(26 + (freq / maxf) * 90)  # 26..116
        size_items.append((word, freq, fs))

    # colors
    palette = ['#7c5cff', '#5c8aff', '#5ce6a8', '#ffcf5c', '#ff7c9e',
               '#ff8a5c', '#5cd6ff', '#b39cff', '#ffffff', '#ff6b9d']
    placed = layout(size_items, 4, W, H)
    for word, freq, fs, x, y, tw, th, font, bbox in placed:
        col = random.choice(palette)
        # adjust for baseline
        dr.text((x - bbox[0], y - bbox[1]), word, font=font, fill=col)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print(f"✅ 워드클라우드 생성: {out}")
    print(f"   {len(top)}개 단어 · 크기 {W}x{H}")
    top3 = ', '.join(f"{w}({f})" for w, f in top[:3])
    print(f"   상위: {top3}")

if __name__ == '__main__':
    main()

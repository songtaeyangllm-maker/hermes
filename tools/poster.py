#!/usr/bin/env python3
"""
Hermes SNS Poster Generator
===========================
Composite a shareable workspace-summary poster image (Pillow): headline,
KPI stats, mini bar chart, and footer. Several themes.

Usage:
    python tools/poster.py                     # dark theme -> projects/poster/poster.png
    python tools/poster.py --theme neon        # neon
    python tools/poster.py --theme ocean       # ocean
    python tools/poster.py --list              # list themes
"""
import argparse
import json
import os
import subprocess
import sys

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

THEMES = {
    "dark":  {"bg": (11, 11, 18), "card": (19, 19, 28), "fg": (236, 236, 245),
              "muted": (107, 111, 130), "accent": (124, 92, 255), "bar": (92, 138, 255)},
    "neon":  {"bg": (8, 8, 20), "card": (20, 14, 44), "fg": (240, 240, 255),
              "muted": (150, 140, 220), "accent": (0, 255, 200), "bar": (255, 0, 200)},
    "ocean": {"bg": (7, 18, 35), "card": (10, 28, 50), "fg": (232, 244, 255),
              "muted": (120, 160, 200), "accent": (0, 200, 255), "bar": (80, 180, 255)},
    "sunset": {"bg": (28, 12, 30), "card": (46, 20, 40), "fg": (255, 240, 245),
              "muted": (220, 150, 170), "accent": (255, 150, 80), "bar": (255, 120, 150)},
}


def _pil():
    from PIL import Image, ImageDraw, ImageFont
    return Image, ImageDraw, ImageFont


def _font(size):
    _, _, ImageFont = _pil()
    candidates = [
        "C:/Windows/Fonts/malgunbd.ttf",
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                continue
    return ImageFont.load_default()


def collect_stats():
    stats = {"lines": 0, "projects": 0, "tools": 0, "files": 0}
    # code lines
    exts = (".py", ".html", ".js", ".md", ".sh")
    for root, _, files in os.walk(WS):
        if ".git" in root or "node_modules" in root:
            continue
        for fn in files:
            if fn.endswith(exts):
                stats["files"] += 1
                try:
                    with open(os.path.join(root, fn), encoding="utf-8", errors="ignore") as f:
                        stats["lines"] += sum(1 for _ in f)
                except Exception:
                    pass
    # projects
    pj = os.path.join(WS, "projects", "projects.json")
    if os.path.exists(pj):
        try:
            stats["projects"] = len(json.load(open(pj, encoding="utf-8")))
        except Exception:
            pass
    # tools
    tdir = os.path.join(WS, "tools")
    if os.path.isdir(tdir):
        stats["tools"] = sum(1 for x in os.listdir(tdir) if x.endswith(".py") and not x.startswith("_"))
    return stats


def render(theme):
    try:
        Image, ImageDraw, _ = _pil()
    except ImportError:
        print("Pillow 필요: pip install pillow")
        return None

    t = THEMES[theme]
    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), t["bg"])
    d = ImageDraw.Draw(img)

    s = collect_stats()

    # subtle gradient dots / header accents
    d.ellipse([W - 260, -120, W + 120, 260], fill=(*t["accent"], 0)[:3] if False else tuple(int(c * 0.12) for c in t["accent"]))
    d.ellipse([-140, H - 240, 200, H + 100], fill=tuple(int(c * 0.10) for c in t["bar"]))

    # Header
    d.rectangle([0, 0, W, 8], fill=t["accent"])
    title_font = _font(64)
    brand_font = _font(30)
    sub_font = _font(26)
    stat_font = _font(52)
    statl_font = _font(22)
    footer_font = _font(20)

    d.text((60, 56), "HERMES", font=brand_font, fill=t["fg"])
    d.text((60, 118), "워크스페이스 지휘 센터", font=title_font, fill=t["fg"])
    d.text((60, 205), "자유롭게 만들어가는 나만의 명령 센터", font=sub_font, fill=t["muted"])

    # KPI cards (2x2)
    card_w = (W - 60 * 3) // 2
    card_h = 170
    kpis = [("줄 수", f"{s['lines']:,}", t["bar"]),
            ("프로젝트", str(s["projects"]), t["accent"]),
            ("도구", str(s["tools"]), (92, 230, 168)),
            ("파일", str(s["files"]), (255, 209, 102))]
    positions = [(60, 280), (60 + card_w + 60, 280), (60, 280 + card_h + 24), (60 + card_w + 60, 280 + card_h + 24)]
    for (x, y), (label, val, color) in zip(positions, kpis):
        d.rounded_rectangle([x, y, x + card_w, y + card_h], 20, fill=t["card"])
        d.rectangle([x, y, x + 8, y + card_h], fill=color)
        d.text((x + 32, y + 34), label, font=statl_font, fill=t["muted"])
        d.text((x + 32, y + 72), val, font=stat_font, fill=t["fg"])

    # Mini bar summary
    y0 = 280 + card_h * 2 + 24 + 30
    d.text((60, y0), "오늘의 성장", font=sub_font, fill=t["fg"])
    d.rounded_rectangle([60, y0 + 52, W - 60, y0 + 74], 40, fill=t["card"])
    bar_total = max(1, s["lines"])
    segs = [("코드", min(1.0, s["lines"] / 9000.0), t["bar"]),
            ("도구", min(1.0, s["tools"] / 20.0), t["accent"]),
            ("프로젝트", min(1.0, s["projects"] / 25.0), (92, 230, 168))]
    x = 60
    for _, frac, color in segs:
        w = int((W - 120) * frac)
        if w > 10:
            d.rounded_rectangle([x, y0 + 52, x + w, y0 + 74], 40, fill=color)
            x += w

    # Footer
    d.text((60, H - 90), "built by Hermes Agent · Nous Research", font=footer_font, fill=t["muted"])
    d.text((W - 260, H - 90), "#hermes #workspace", font=footer_font, fill=t["muted"])

    out_dir = os.path.join(WS, "projects", "poster")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"poster_{theme}.png")
    img.save(path)
    return path, s


def main():
    ap = argparse.ArgumentParser(description="SNS 포스터 생성")
    ap.add_argument("--theme", default="dark", help="테마: " + ",".join(THEMES))
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    if args.list:
        print("테마:", ", ".join(THEMES))
        return

    theme = args.theme if args.theme in THEMES else "dark"
    try:
        import PIL  # noqa
    except ImportError:
        print("❌ Pillow 없음 — pip install pillow")
        sys.exit(1)

    path, s = render(theme)
    if path:
        print(f"✅ 포스터 생성: {path}")
        print(f"   {s['lines']:,}줄 · {s['projects']}프로젝트 · {s['tools']}도구 · {s['files']}파일 ({theme} 테마)")


if __name__ == "__main__":
    from PIL import Image  # noqa
    main()

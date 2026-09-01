#!/usr/bin/env python3
"""
Hermes Analytics Data Builder
============================
Collate diary + sentiment + projects + git + tool stats into a single
JSON/JS blob that the HTML analytics dashboard reads.

Usage:
    python tools/analytics.py           # -> projects/analytics/analytics_data.js (window.HERMES_ANALYTICS)
"""
import json
import os
import re
import subprocess
import sys

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_diary():
    ddir = os.path.join(WS, "notes", "diary")
    entries = []
    if os.path.isdir(ddir):
        for fn in sorted(os.listdir(ddir)):
            if fn.endswith((".md", ".txt")):
                try:
                    with open(os.path.join(ddir, fn), encoding="utf-8") as f:
                        text = f.read()
                    m = re.match(r"(\d{4}-\d{2}-\d{2})", fn)
                    date = m.group(1) if m else fn[:10]
                    entries.append({"date": date, "chars": len(text.strip()), "text": text})
                except Exception:
                    pass
    return entries


def sentiment(text):
    pos = ["좋", "행복", "기쁘", "최고", "즐겁", "만족", "성공", "감사", "기대", "흥분", "멋지", "사랑", "웃", "신나", "행운", "따뜻", "힘나", "뿌듯", "설레", "편안"]
    neg = ["슬프", "화나", "짜증", "우울", "힘들", "지치", "불안", "걱정", "아쉽", "속상", "실패", "긴장", "스트레스", "외로", "후회", "답답", "무서", "피곤", "슬픔", "아프"]
    p = sum(text.count(w) for w in pos)
    n = sum(text.count(w) for w in neg)
    return {"pos": p, "neg": n, "score": p - n, "label": "긍정" if p > n else ("부정" if n > p else "중립")}


def keywords(text, top=10):
    # crude Korean word extraction: strip headings/punct, count tokens
    from collections import Counter
    text = re.sub(r"[\s#\d\-—/\\:.]", " ", text)
    tokens = [t for t in text.split() if len(t) >= 2 and not t.isdigit()]
    return [{"w": w, "c": c} for w, c in Counter(tokens).most_common(top)]


def load_projects():
    pj = os.path.join(WS, "projects", "projects.json")
    if os.path.exists(pj):
        try:
            return json.load(open(pj, encoding="utf-8"))
        except Exception:
            return []
    return []


def git_commits(n=30):
    try:
        out = subprocess.run(
            ["git", "-C", WS, "log", f"-{n}", "--format=%h|%ad|%s", "--date=short"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10,
        ).stdout.strip()
        rows = []
        for line in out.split("\n"):
            if "|" in line:
                h, d, s = line.split("|", 2)
                rows.append({"hash": h, "date": d, "msg": s})
        return rows
    except Exception:
        return []


def tools_list():
    tdir = os.path.join(WS, "tools")
    if os.path.isdir(tdir):
        return sorted(x for x in os.listdir(tdir) if x.endswith(".py") and not x.startswith("_"))
    return []


def main():
    diary = load_diary()
    diary_data = []
    for e in diary:
        senti = sentiment(e["text"])
        diary_data.append({
            "date": e["date"], "chars": e["chars"],
            "score": senti["score"], "label": senti["label"],
            "pos": senti["pos"], "neg": senti["neg"],
        })

    data = {
        "generated": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M"),
        "diary": diary_data,
        "top_keywords": keywords(" ".join(e["text"] for e in diary)),
        "projects": load_projects(),
        "git": git_commits(),
        "tools": tools_list(),
    }

    out_dir = os.path.join(WS, "projects", "analytics")
    os.makedirs(out_dir, exist_ok=True)
    js_path = os.path.join(out_dir, "analytics_data.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("window.HERMES_ANALYTICS = ")
        f.write(json.dumps(data, ensure_ascii=False, indent=2))
        f.write(";")
    print(f"✅ 분석 데이터 생성 ({len(diary)}일기, {len(data['git'])}커밋, {len(data['tools'])}도구)")
    print(f"   {js_path}")


if __name__ == "__main__":
    main()

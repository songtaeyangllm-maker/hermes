#!/usr/bin/env python3
"""
Hermes Diary Sentiment Analyzer
===============================
Analyze diary entries with a Korean positive/negative lexicon, produce a
sentiment score per day, trends, and a monthly HTML report.

Usage:
    python tools/sentiment.py                # print summary
    python tools/sentiment.py --report       # write monthly HTML report to projects/sentiment/
    python tools/sentiment.py --json         # dump JSON summary
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIARY = os.path.join(WS, "notes", "diary")

# Korean sentiment lexicon (positive / negative)
POSITIVE = [
    "좋", "행복", "기쁘", "최고", "즐겁", "만족", "성공", "감사", "기대", "흥분",
    "멋지", "대단", "사랑", "웃", "즐거", "신나", "행운", "따뜻", "힘나", "보람",
    "뿌듯", "설레", "편안", "건강", "멋있", "자랑", "자유", "가벼", "화창", "청량",
    "완벽", "훌륭", "행복하", "기쁘다", "좋아", "기대돼", "행복하", "즐거웠", "만족스러",
]
NEGATIVE = [
    "슬프", "화나", "짜증", "우울", "힘들", "지치", "불안", "걱정", "아쉽", "속상",
    "실패", "긴장", "스트레스", "괴롭", "외로", "후회", "짜증나", "답답", "무서", "피곤",
    "나쁘", "못하", "싫", "슬픔", "상처", "아프", "힘든", "어렵", "포기", "불만",
    "지루", "무기력", "슬펐", "힘들었", "우울했", "걱정되", "무서웠",
]


def tokenize_text(text):
    """Simple hangul n-gram + word tokenization for matching lexicon."""
    return text


def count_sentiment(text):
    pos = 0
    neg = 0
    # Count occurrences of each lexicon word (substring match, coarse but works for Korean)
    for w in POSITIVE:
        pos += text.count(w)
    for w in NEGATIVE:
        neg += text.count(w)
    return pos, neg


def load_diary():
    entries = []
    if not os.path.isdir(DIARY):
        return entries
    for fn in sorted(os.listdir(DIARY)):
        if fn.endswith((".md", ".txt")):
            path = os.path.join(DIARY, fn)
            try:
                with open(path, encoding="utf-8") as f:
                    text = f.read()
                # date from filename YYYY-MM-DD or content
                m = re.match(r"(\d{4})-(\d{2})-(\d{2})", fn)
                if m:
                    date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
                else:
                    date = None
                entries.append({"file": fn, "date": date, "text": text, "chars": len(text.strip())})
            except Exception:
                continue
    return entries


def analyze(entries):
    results = []
    for e in entries:
        pos, neg = count_sentiment(e["text"])
        score = pos - neg
        total = pos + neg
        valence = 0.0
        if total > 0:
            valence = (pos - neg) / total  # -1..1
        label = "긍정" if score > 0 else ("부정" if score < 0 else "중립")
        results.append({
            "date": e["date"],
            "file": e["file"],
            "chars": e["chars"],
            "positive": pos,
            "negative": neg,
            "score": score,
            "valence": round(valence, 2),
            "label": label,
        })
    return results


def main():
    ap = argparse.ArgumentParser(description="일기 감정 분석")
    ap.add_argument("--report", action="store_true", help="월간 HTML 리포트 생성")
    ap.add_argument("--json", action="store_true", help="JSON 출력")
    args = ap.parse_args()

    entries = load_diary()
    if not entries:
        print("일기가 없습니다. notes/diary/ 확인")
        return

    results = analyze(entries)
    pos_days = sum(1 for r in results if r["score"] > 0)
    neg_days = sum(1 for r in results if r["score"] < 0)
    neu_days = sum(1 for r in results if r["score"] == 0)
    total_score = sum(r["score"] for r in results)
    avg_valence = sum(r["valence"] for r in results) / len(results) if results else 0
    total_pos = sum(r["positive"] for r in results)
    total_neg = sum(r["negative"] for r in results)

    summary = {
        "total_days": len(results),
        "positive_days": pos_days,
        "negative_days": neg_days,
        "neutral_days": neu_days,
        "total_score": total_score,
        "avg_valence": round(avg_valence, 2),
        "total_positive_words": total_pos,
        "total_negative_words": total_neg,
        "entries": results,
    }

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    if args.report:
        write_report(summary)
        return

    # Console summary
    print("📔 일기 감정 분석")
    print("=" * 36)
    print(f"  분석 일기: {len(results)}편")
    print(f"  긍정: {pos_days}일  부정: {neg_days}일  중립: {neu_days}일")
    print(f"  감정 단어: 긍정 {total_pos} / 부정 {total_neg}")
    print(f"  총 감정 점수: {total_score:+d}")
    print(f"  평균 감성 비율: {avg_valence:+.2f} ({'긍정적' if avg_valence > 0.15 else ('부정적' if avg_valence < -0.15 else '중립')})")
    print()
    print("  📅 일자별:")
    for r in results:
        mark = {"긍정": "😊", "부정": "😔", "중립": "😐"}[r["label"]]
        print(f"    {r['date']}  {mark} {'+'*max(r['score'],0)}{'-'*max(-r['score'],0)} ({r['score']:+d})  {r['chars']}자")


def write_report(summary):
    out_dir = os.path.join(WS, "projects", "sentiment")
    os.makedirs(out_dir, exist_ok=True)
    now = datetime.now()
    month = now.strftime("%Y-%m")
    results = summary["entries"]

    # Color bars for each day
    def bar(score):
        if score >= 0:
            return f'<div class="bar"><div class="fill pos" style="width:{min(score*8,100)}%"></div></div>'
        return f'<div class="bar"><div class="fill neg" style="width:{min(-score*8,100)}%"></div></div>'

    rows = ""
    for r in results:
        rows += (
            f'<div class="row"><div class="date">{r["date"] or "?"}</div>'
            f'<div class="label">{r["label"]}</div>{bar(r["score"])}'
            f'<div class="score">{r["score"]:+d}</div></div>'
        )

    cards = f"""
<div class="kpis">
  <div class="kpi"><div class="n">분석 일기</div><div class="v">{summary['total_days']}</div></div>
  <div class="kpi"><div class="n">긍정 일수</div><div class="v" style="color:#5ce6a8">{summary['positive_days']}</div></div>
  <div class="kpi"><div class="n">부정 일수</div><div class="v" style="color:#ff6b6b">{summary['negative_days']}</div></div>
  <div class="kpi"><div class="n">평균 감성</div><div class="v">{summary['avg_valence']:+.2f}</div></div>
</div>
"""
    html = f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8"><title>월간 감정 리포트</title>
<style>
:root {{ --bg:#0b0b12; --card:#13131c; --text:#ececf5; --muted:#6b6f82; --border:#23233a; --accent:#7c5cff; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,'Segoe UI','Noto Sans KR',sans-serif; background:var(--bg); color:var(--text); padding:40px 24px; }}
.wrap {{ max-width:680px; margin:0 auto; }}
h1 {{ font-size:1.5rem; font-weight:800; margin-bottom:6px; }} h1 span {{ color:var(--accent); }}
.sub {{ color:var(--muted); font-size:0.82rem; margin-bottom:26px; }}
.kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr)); gap:12px; margin-bottom:28px; }}
.kpi {{ background:var(--card); border:1px solid var(--border); border-radius:16px; padding:18px; text-align:center; }}
.kpi .n {{ font-size:0.72rem; color:var(--muted); }} .kpi .v {{ font-size:1.6rem; font-weight:800; color:var(--accent); margin-top:4px; }}
.rows {{ background:var(--card); border:1px solid var(--border); border-radius:18px; padding:10px 18px; }}
.row {{ display:grid; grid-template-columns:90px 50px 1fr 50px; gap:12px; align-items:center; padding:9px 0; border-bottom:1px solid var(--border); font-size:0.85rem; }}
.row:last-child {{ border:none; }}
.date {{ color:var(--muted); }} .label {{ font-size:0.72rem; }} .score {{ text-align:right; font-weight:700; }}
.bar {{ height:12px; background:#1c1c28; border-radius:8px; overflow:hidden; }}
.bar .fill {{ height:100%; border-radius:8px; }} .fill.pos {{ background:linear-gradient(90deg,#5ce6a8,#5c8aff); }} .fill.neg {{ background:linear-gradient(90deg,#ff6b6b,#ff9d6b); }}
.sum {{ margin-top:16px; text-align:center; color:var(--muted); font-size:0.8rem; }}
</style></head><body>
<div class="wrap">
  <h1>📔 월간 <span>감정</span> 리포트</h1>
  <div class="sub">{month} · Hermes 일기 자동 분석</div>
  {cards}
  <div class="rows">{rows}</div>
  <div class="sum">긍정 단어 {summary['total_positive_words']} · 부정 단어 {summary['total_negative_words']} · 총 감정 점수 {summary['total_score']:+d}</div>
</div>
</body></html>"""

    path = os.path.join(out_dir, "report.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ 감정 리포트 생성: {path}")
    print(f"   일기 {summary['total_days']}편 · 긍정 {summary['positive_days']} / 부정 {summary['negative_days']} · 평균 {summary['avg_valence']:+.2f}")


if __name__ == "__main__":
    main()

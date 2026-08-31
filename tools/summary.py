#!/usr/bin/env python3
"""
Hermes Workspace Summary Report
===============================
Auto-generate a weekly/monthly growth report: git commits, line growth,
project count, tool count, sentiment trend. Outputs markdown + HTML.

Usage:
    python tools/summary.py                # => notes/reports/summary_YYYY-MM-DD.md + .html
    python tools/summary.py --json         # dump stats JSON
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def git_log(count=10):
    try:
        out = subprocess.run(
            ["git", "-C", WS, "log", "--oneline", f"-{count}"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10,
        ).stdout.strip()
        return [line for line in out.split("\n") if line.strip()]
    except Exception:
        return []


def git_count():
    try:
        out = subprocess.run(
            ["git", "-C", WS, "rev-list", "--count", "HEAD"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10,
        ).stdout.strip()
        return int(out)
    except Exception:
        return 0


def count_lines():
    exts = (".py", ".html", ".js", ".md", ".sh")
    total = 0
    files = 0
    for root, _, fs in os.walk(WS):
        if ".git" in root:
            continue
        for fn in fs:
            if fn.endswith(exts):
                files += 1
                try:
                    with open(os.path.join(root, fn), encoding="utf-8", errors="ignore") as f:
                        total += sum(1 for _ in f)
                except Exception:
                    pass
    return total, files


def summary_stats():
    total_lines, files = count_lines()
    projects = 0
    pj = os.path.join(WS, "projects", "projects.json")
    if os.path.exists(pj):
        try:
            projects = len(json.load(open(pj, encoding="utf-8")))
        except Exception:
            pass
    tools = 0
    tdir = os.path.join(WS, "tools")
    if os.path.isdir(tdir):
        tools = sum(1 for x in os.listdir(tdir) if x.endswith(".py") and not x.startswith("_"))
    commits = git_count()
    ddir = os.path.join(WS, "notes", "diary")
    diary = 0
    if os.path.isdir(ddir):
        diary = sum(1 for x in os.listdir(ddir) if x.endswith((".md", ".txt")))
    return {
        "lines": total_lines, "files": files, "projects": projects,
        "tools": tools, "commits": commits, "diary": diary,
    }


def main():
    ap = argparse.ArgumentParser(description="워크스페이스 요약 리포트")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    s = summary_stats()
    commits = git_log(12)
    now = datetime.now()

    if args.json:
        print(json.dumps({**s, "recent_commits": commits}, ensure_ascii=False, indent=2))
        return

    date_str = now.strftime("%Y-%m-%d")
    md = []
    md.append(f"# 📊 워크스페이스 요약 — {date_str}")
    md.append("")
    md.append("## 📈 성장 지표")
    md.append("")
    md.append("| 지표 | 값 |")
    md.append("|------|-----|")
    md.append(f"| 코드 줄 수 | **{s['lines']:,}** |")
    md.append(f"| 파일 수 | {s['files']} |")
    md.append(f"| 프로젝트 | {s['projects']} |")
    md.append(f"| 도구 | {s['tools']} |")
    md.append(f"| git 커밋 | {s['commits']} |")
    md.append(f"| 일기 | {s['diary']}편 |")
    md.append("")
    md.append("## 🕒 최근 활동 (git)")
    md.append("")
    if commits:
        for c in commits:
            md.append(f"- `{c}`")
    else:
        md.append("- 기록 없음")
    md.append("")
    md.append("_자동 생성: Hermes Summary Report_")
    mdtxt = "\n".join(md)

    report_dir = os.path.join(WS, "notes", "reports")
    os.makedirs(report_dir, exist_ok=True)
    mdp = os.path.join(report_dir, f"summary_{date_str}.md")
    with open(mdp, "w", encoding="utf-8") as f:
        f.write(mdtxt)

    # HTML version
    rows = "".join(f"<tr><td>{k}</td><td><b>{v}</b></td></tr>" for k, v in [
        ("코드 줄 수", f"{s['lines']:,}"), ("파일 수", s["files"]),
        ("프로젝트", s["projects"]), ("도구", s["tools"]),
        ("git 커밋", s["commits"]), ("일기", f"{s['diary']}편")])
    crows = "".join(f"<li>⚡ {c}</li>" for c in commits[:8])
    html = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<title>워크스페이스 요약</title>
<style>
:root{{--bg:#0b0b12;--card:#13131c;--text:#ececf5;--muted:#6b6f82;--border:#23233a;--accent:#7c5cff}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,'Segoe UI','Noto Sans KR',sans-serif;background:var(--bg);color:var(--text);padding:40px 24px}}
.wrap{{max-width:720px;margin:0 auto}}
h1{{font-size:1.5rem;font-weight:800;margin-bottom:6px}}h1 span{{color:var(--accent)}}
.sub{{color:var(--muted);font-size:0.82rem;margin-bottom:26px}}
table{{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--border);border-radius:16px;overflow:hidden;margin-bottom:24px}}
td{{padding:13px 18px;border-bottom:1px solid var(--border);font-size:0.9rem}}
td:last-child{{text-align:right;color:var(--accent);font-weight:700}}
tr:last-child td{{border-bottom:none}}
h2{{font-size:1.05rem;margin:22px 0 12px;color:var(--accent)}}
ul{{list-style:none;background:var(--card);border:1px solid var(--border);border-radius:16px;padding:16px 20px}}
li{{padding:7px 0;font-size:0.85rem;font-family:monospace;border-bottom:1px solid var(--border);color:var(--muted)}}
li:last-child{{border:none}}
.foot{{text-align:center;color:var(--muted);font-size:0.75rem;margin-top:26px}}
</style></head><body><div class="wrap">
<h1>📊 워크스페이스 <span>요약</span></h1>
<div class="sub">{date_str} · Hermes 자동 리포트</div>
<table><tbody>{rows}</tbody></table>
<h2>🕒 최근 커밋</h2>
<ul>{crows if crows else '<li>기록 없음</li>'}</ul>
<div class="foot">_자동 생성: Hermes Summary Report_</div>
</div></body></html>"""
    hp = os.path.join(report_dir, f"summary_{date_str}.html")
    with open(hp, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ 요약 리포트 생성")
    print(f"   MD:  {mdp}")
    print(f"   HTML: {hp}")
    print(f"   {s['lines']:,}줄 · {s['projects']}프로젝트 · {s['tools']}도구 · {s['commits']}커밋")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Hermes Daily Auto-Report
========================
Generates a timestamped daily report of the workspace: system health,
project status, and recent file activity. Writes to notes/reports/.

Usage:
    python tools/auto_report.py             # generate report
    python tools/auto_report.py --date 2026-08-31  # specific date
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(r"C:\hermes")

def run_diag():
    """Run system_diagnostics and return the JSON data dict."""
    diag = Path(__file__).parent / 'system_diagnostics.py'
    r = subprocess.run([sys.executable, str(diag), '--json'],
                       capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {}

def load_projects():
    tf = WORKSPACE / 'projects' / 'projects.json'
    if tf.exists():
        return json.loads(tf.read_text(encoding='utf-8'))
    return []

def workspace_activity():
    """Most recently modified files in the workspace."""
    files = []
    for f in WORKSPACE.rglob('*'):
        if f.is_file() and '__pycache__' not in str(f) and 'logs' not in str(f):
            files.append(f)
    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return files[:5]

def build_report(date_str):
    data = run_diag()
    projects = load_projects()
    active = [p for p in projects if p['status'] == 'active']

    lines = []
    lines.append("# 🤖 Hermes Daily Auto-Report")
    lines.append("")
    lines.append(f"**작성 시각:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    lines.append("## 🩺 시스템 상태")
    lines.append("")
    if data:
        cpu = f"{data.get('cpu_percent')}%" if data.get('cpu_percent') is not None else "n/a"
        m = data.get('memory', {})
        mem = f"{m.get('used_gb')}/{m.get('total_gb')} GB ({m.get('percent')}%)" if m.get('percent') else "n/a"
        d = data.get('disk', {})
        disk = f"{d.get('free_gb')} GB free ({d.get('percent')}% used)"
        lines.append(f"- 🎛️ **CPU:** {cpu}")
        lines.append(f"- 🧠 **메모리:** {mem}")
        lines.append(f"- 💾 **디스크:** {disk}")
        lines.append(f"- 🖥️ **호스트:** {data.get('hostname')} ({data.get('os')})")
    else:
        lines.append("- (진단 데이터 없음)")
    lines.append("")

    lines.append("## 📁 프로젝트")
    lines.append("")
    if projects:
        for p in projects:
            icon = {'active': '🚀', 'planned': '📋', 'paused': '⏸️',
                    'done': '✅', 'archived': '🗄️'}.get(p['status'], '📦')
            desc = p.get('description', '') or ''
            lines.append(f"- {icon} **{p['name']}** [{p['status']}] {desc}")
    else:
        lines.append("- 등록된 프로젝트 없음")
    if active:
        lines.append("")
        lines.append(f"**활성 프로젝트 {len(active)}개**")
    lines.append("")

    lines.append("## 🕐 최근 활동")
    lines.append("")
    for f in workspace_activity():
        mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime('%m-%d %H:%M')
        rel = str(f.relative_to(WORKSPACE))
        lines.append(f"- `{mtime}` {rel}")
    lines.append("")

    lines.append("---")
    lines.append("*본 보고서는 Hermes Agent가 자동 생성했습니다.*")
    return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'))
    ap.add_argument('--print', action='store_true', help='also print to console')
    args = ap.parse_args()

    report = build_report(args.date)
    out_dir = WORKSPACE / 'notes' / 'reports'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"report_{args.date}.md"
    out_path.write_text(report, encoding='utf-8')

    print(f"✅ Auto-report saved: {out_path}")
    if args.print:
        print("")
        print(report)

if __name__ == '__main__':
    main()

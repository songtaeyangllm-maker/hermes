#!/usr/bin/env python3
"""
Hermes Workspace Smoke Test
===========================
Runs every checked-in tool for real and reports PASS/FAIL + summary.
Use after changes to confirm nothing is broken.

Usage:
    python tools/smoke.py             # run all checks (default)
    python tools/smoke.py --quick     # only core tools
    python tools/smoke.py --json      # machine-readable summary
"""
import argparse
import json
import os
import subprocess
import sys

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable  # use the SAME interpreter (venv with Pillow), not bare 'python'

# (label, argv, allow_no_output)
CORE = [
    ("hermes_toolkit status", ["python", "tools/hermes_toolkit.py", "status"]),
    ("system_diagnostics", ["python", "tools/system_diagnostics.py"]),
    ("project_tracker list", ["python", "tools/project_tracker.py", "list"]),
    ("diary stats", ["python", "tools/diary.py", "stats"]),
    ("net_utils check", ["python", "tools/net_utils.py", "check"]),
    ("md2html", ["python", "tools/md2html.py", "notes/sample_post.md", "--stdout"]),
    ("treemap scan", ["python", "tools/treemap.py", WS]),
    ("badge", ["python", "tools/badge.py", "--out", "projects/badge/smoke.svg"]),
    ("search_notes", ["python", "tools/search_notes.py", "워크스페이스", "--top", "2"]),
    ("wordcloud", ["python", "tools/wordcloud.py", "--top", "15"]),
    ("timeline", ["python", "tools/timeline.py"]),
    ("sentiment", ["python", "tools/sentiment.py"]),
    ("summary", ["python", "tools/summary.py"]),
    ("poster dark", ["python", "tools/poster.py", "--theme", "dark"]),
]

# These write binary files; a non-zero exit from missing Pillow is expected
# only if Pillow isn't installed — checked separately.
PILLOW_TOOLS = ["wordcloud.py", "poster.py", "file_utils.py"]


def _has_pillow():
    try:
        import PIL  # noqa
        return True
    except ImportError:
        return False


def run_tool(label, argv):
    env = dict(os.environ)
    # force the current interpreter so venv deps (Pillow) resolve
    argv = [PY] + list(argv[1:])
    try:
        r = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=90, cwd=WS, env=env)
        ok = r.returncode == 0
        # some tools print to stderr on Windows with warnings — treat as pass if exit 0
        sample = (r.stdout or "").strip().split("\n")
        return ok, (sample[-1][:110] if sample and sample[-1] else ""), r.returncode
    except Exception as e:
        return False, str(e)[:110], -1


def main():
    ap = argparse.ArgumentParser(description="워크스페이스 스모크테스트")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    tests = CORE if not args.quick else CORE[:8]
    pillow = _has_pillow()

    results = []
    for label, argv in tests:
        ok, out, rc = run_tool(label, argv)
        results.append({"test": label, "ok": ok, "code": rc, "output": out})
        mark = "✅" if ok else "❌"
        # If a Pillow tool fails and Pillow missing, note special case
        note = ""
        for pt in PILLOW_TOOLS:
            if pt in argv[1] and not ok and not pillow:
                note = " (Pillow 미설치 — 제외)"
        print(f"  {mark} {label}{note}")

    passed = sum(1 for r in results if r["ok"])
    total = len(results)

    print("")
    print(f"  Pillow: {'✓ 설치됨' if pillow else '✗ 미설치'}")
    print(f"  결과: {passed}/{total} 통과")

    if args.json:
        print(json.dumps({"passed": passed, "total": total, "tests": results}, ensure_ascii=False, indent=2))
        return

    # Don't write a summary file unless there are failures to flag
    if passed < total:
        print("\n  ⚠ 일부 테스트 실패 — 아래 명령으로 개별 확인:")
        for r in results:
            if not r["ok"]:
                print(f"    {r['test']}: {r['output']}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())

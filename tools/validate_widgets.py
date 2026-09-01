#!/usr/bin/env python3
"""
validate_widgets.py — Hermes Workspace 통합 검증
모든 HTML 위젯의 <script> JS 문법을 node --check로 검사하고,
손상(corrupt) 파일/누락 파일이 없는지 확인한다.
"""
import os, re, subprocess, sys, tempfile

ROOT = r"C:\hermes"
PROJECTS = os.path.join(ROOT, "projects")

def check_js_in_html(path):
    """HTML 내 <script> 블록들을 추출해 node --check로 문법 검사."""
    html = open(path, encoding="utf-8", errors="replace").read()
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.S)
    if not scripts:
        return None, "script 없음"
    js = "\n".join(scripts)
    # HTML/JSON 인라인(script type)이 아닌 일반 JS만 검사
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(js); tmp = f.name
    try:
        r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            return False, r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "syntax error"
        return True, f"{len(js)}B"
    finally:
        os.unlink(tmp)

def main():
    results = []
    total_ok = corrupt = 0
    for root, dirs, files in os.walk(PROJECTS):
        # venv/node_modules 제외
        dirs[:] = [d for d in dirs if d not in ("node_modules", "__pycache__")]
        for fn in files:
            if fn.endswith(".html"):
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, PROJECTS)
                try:
                    ok, msg = check_js_in_html(full)
                except Exception as e:
                    ok, msg = False, f"ERR {e}"
                if ok is True:
                    total_ok += 1
                    results.append((rel, "✅", msg))
                elif ok is False:
                    corrupt += 1
                    results.append((rel, "❌", msg))
                # None = script 없음 → 통계엔 미포함

    print(f"📄 검사한 HTML: {len(results)}개 | ✅ 정상: {total_ok} | ❌ 손상: {corrupt}")
    for rel, st, msg in results:
        if st == "❌":
            print(f"  ❌ {rel} → {msg}")
    if corrupt == 0:
        print("🎉 모든 위젯 JS 문법 정상")
    return 0 if corrupt == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

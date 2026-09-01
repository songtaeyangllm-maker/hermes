#!/usr/bin/env python3
"""
verify_os_catalog.py — Hermes OS 앱 카탈로그 검증
hermes_os/index.html의 각 앱 항목이 가리키는 HTML 파일이 실제로 존재하는지,
그리고 포털(projects/portal) 카탈로그도 각 링크가 유효한지 확인한다.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os_path = os.path.join(ROOT, 'projects', 'hermes_os', 'index.html')
portal_path = os.path.join(ROOT, 'projects', 'portal', 'index.html')

def extract_paths(html, patterns):
    paths = []
    for pat in patterns:
        for m in re.finditer(pat, html):
            paths.append(m.group(1))
    return paths

def check(paths):
    missing = []
    for p in paths:
        clean = os.path.normpath(p.replace('../', '').replace('./', ''))
        # check under projects/ first, then under repo root (e.g. dashboard/)
        cand = os.path.normpath(os.path.join(ROOT, 'projects', clean))
        if not os.path.isfile(cand):
            cand2 = os.path.normpath(os.path.join(ROOT, clean))
            if not os.path.isfile(cand2):
                missing.append(p)
    return missing

os_html = open(os_path, encoding='utf-8').read()
os_paths = extract_paths(os_html, [r"p:'([^']+)'"])
os_missing = check(os_paths)

portal_html = open(portal_path, encoding='utf-8').read()
portal_paths = extract_paths(portal_html, [r"p:'([^']+)'"])
portal_missing = check(portal_paths)

print(f"🧊 Hermes OS 앱: {len(os_paths)}개 | 누락 {len(os_missing)}")
for m in os_missing: print(f"   ❌ {m}")
print(f"🏛️  포털 카드: {len(portal_paths)}개 | 누락 {len(portal_missing)}")
for m in portal_missing: print(f"   ❌ {m}")

ok = not os_missing and not portal_missing
print("🎉 모든 카탈로그 링크 유효" if ok else "⚠️ 누락 링크 발견")
sys.exit(0 if ok else 1)
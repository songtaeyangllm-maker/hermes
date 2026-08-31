#!/usr/bin/env python3
"""
Hermes System Diagnostics & Monitor
===================================
Real-time system health check that outputs JSON (for the dashboard)
and human-readable report (for the console).

Usage:
    python tools/system_diagnostics.py            # full report (console)
    python tools/system_diagnostics.py --json     # JSON output
    python tools/system_diagnostics.py --watch 5  # watch mode, every 5s
    python tools/system_diagnostics.py --out dashboards/data.json  # write JSON to file
"""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(r"C:\hermes")
HISTORY_FILE = WORKSPACE / 'dashboard' / 'history.json'
MAX_HISTORY = 200  # keep last 200 samples

def _ps(script):
    """Run a PowerShell snippet (via powershell -NoProfile -Command), return stdout or None."""
    try:
        return subprocess.check_output(
            ['powershell', '-NoProfile', '-Command', script],
            text=True, errors='replace', timeout=15).strip()
    except Exception:
        return None

def get_cpu():
    """Return [load_percent] or [None] on failure."""
    # PowerShell CIM is the reliable path on modern Windows.
    out = _ps("(Get-CimInstance Win32_Processor).LoadPercentage")
    if out:
        try:
            return int(out.splitlines()[0].strip())
        except (ValueError, IndexError):
            pass
    return None

def get_memory():
    """Return {total_gb, used_gb, percent} or None."""
    out = _ps(
        "$o=Get-CimInstance Win32_OperatingSystem;"
        "$t=$o.TotalVisibleMemorySize;"
        "$f=$o.FreePhysicalMemory;"
        "Write-Output ('{0}|{1}' -f $t,$f)")
    if out:
        try:
            line = [l for l in out.splitlines() if '|' in l][0]
            total_kb, free_kb = [int(x) for x in line.split('|') if x.strip().isdigit()]
            used_kb = total_kb - free_kb
            return {
                'total_gb': round(total_kb / (1024**2), 1),
                'used_gb': round(used_kb / (1024**2), 1),
                'percent': int(used_kb / total_kb * 100) if total_kb else None
            }
        except (ValueError, IndexError):
            pass
    return None

def get_disk():
    """Return total/used/free percent for workspace drive."""
    try:
        usage = shutil.disk_usage(WORKSPACE)
        return {
            'total_gb': round(usage.total / (1024**3), 1),
            'used_gb': round(usage.used / (1024**3), 1),
            'free_gb': round(usage.free / (1024**3), 1),
            'percent': int(usage.used / usage.total * 100)
        }
    except Exception:
        return None

def get_uptime():
    """System boot time in readable form."""
    try:
        if platform.system() == 'Windows':
            out = subprocess.check_output(
                ['wmic', 'os', 'get', 'LastBootUpTime'], text=True)
            for l in out.splitlines():
                l = l.strip()
                if len(l) > 8:
                    dt = datetime.strptime(l[:19], '%Y%m%d%H%M%S')
                    return dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        pass
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def get_top_processes(n=5):
    """Return top N processes by memory (Windows tasklist)."""
    try:
        out = subprocess.check_output(['tasklist', '/FO', 'CSV', '/NH'], text=True)
        procs = []
        for line in out.splitlines():
            try:
                name = line.split('","')[0].strip('"')
                # memory in last column like "123,456 K"
                mem = line.rsplit('","', 1)[1].strip('"').replace(' K', '').replace(',', '')
                if mem.replace('.', '').isdigit():
                    procs.append((name, float(mem) / 1024))  # MB
            except Exception:
                continue
        procs.sort(key=lambda x: -x[1])
        return [{'name': n, 'mem_mb': round(m)} for n, m in procs[:n]]
    except Exception:
        return []

def get_process_count():
    """Total number of running processes."""
    try:
        out = subprocess.check_output(
            ['powershell', '-NoProfile', '-Command',
             '(Get-Process).Count'], text=True, timeout=15)
        return int(out.strip().splitlines()[0])
    except Exception:
        return None

def load_history():
    """Load accumulated CPU/disk history from history.json."""
    try:
        if HISTORY_FILE.exists():
            return json.loads(HISTORY_FILE.read_text(encoding='utf-8'))
    except Exception:
        pass
    return {'cpu': [], 'mem': [], 'disk': [], 'times': []}

def save_history(cpu, mem, disk):
    """Append current sample to history and persist (trim to MAX_HISTORY)."""
    hist = load_history()
    hist.setdefault('cpu', []).append(cpu)
    hist.setdefault('mem', []).append(mem)
    hist.setdefault('disk', []).append(disk)
    hist.setdefault('times', []).append(datetime.now().strftime('%H:%M:%S'))
    for k in ('cpu', 'mem', 'disk', 'times'):
        if len(hist[k]) > MAX_HISTORY:
            hist[k] = hist[k][-MAX_HISTORY:]
    try:
        HISTORY_FILE.parent.mkdir(exist_ok=True)
        HISTORY_FILE.write_text(json.dumps(hist), encoding='utf-8')
    except Exception:
        pass
    return hist

def collect():
    """Collect all metrics into a dict."""
    cpu = get_cpu()
    mem = get_memory()
    disk = get_disk()
    # Accumulate history
    hist = save_history(cpu, mem, disk.get('percent') if disk else None)
    data = {
        'timestamp': datetime.now().isoformat(timespec='seconds'),
        'hostname': platform.node(),
        'os': f"{platform.system()} {platform.release()}",
        'python': platform.python_version(),
        'cpu_percent': cpu,
        'memory': mem or {'total_gb': None, 'used_gb': None, 'percent': None},
        'disk': disk or {'total_gb': None, 'used_gb': None, 'free_gb': None, 'percent': None},
        'boot_time': get_uptime(),
        'top_processes': get_top_processes(5),
        'process_count': get_process_count(),
        'workspace_size_mb': round(sum(f.stat().st_size for f in WORKSPACE.rglob('*')
                                       if f.is_file() and '__pycache__' not in str(f)) / (1024*1024), 2),
        'history': {k: hist[k] for k in ('cpu', 'mem', 'disk', 'times')},
    }
    return data

def health_score(data):
    """0-100 health score."""
    score = 100
    if data['cpu_percent'] is not None:
        if data['cpu_percent'] > 90: score -= 30
        elif data['cpu_percent'] > 70: score -= 20
    if data['memory']['percent']:
        if data['memory']['percent'] > 90: score -= 30
        elif data['memory']['percent'] > 75: score -= 20
    if data['disk']['percent']:
        if data['disk']['percent'] > 95: score -= 40
        elif data['disk']['percent'] > 85: score -= 20
    return max(0, min(100, score))

def print_report(data):
    score = health_score(data)
    print("🩺 Hermes System Health Report")
    print("=" * 46)
    print(f"  Host:     {data['hostname']}  ({data['os']})")
    print(f"  Time:     {data['timestamp']}")
    print(f"  Health:   {score}/100 "
          + ("🟢 EXCELLENT" if score >= 80 else "🟡 FAIR" if score >= 50 else "🔴 CRITICAL"))
    print("-" * 46)
    cpu = data['cpu_percent']
    print(f"  CPU:      {cpu}%" if cpu is not None else "  CPU:      n/a")
    m = data['memory']
    print(f"  Memory:   {m['used_gb']}/{m['total_gb']} GB ({m['percent']}%)" if m.get('percent') else "  Memory:   n/a")
    d = data['disk']
    print(f"  Disk:     {d['free_gb']} GB free ({d['percent']}% used) · {d['total_gb']} GB total")
    print(f"  Booted:   {data['boot_time']}")
    print(f"  Workspace:{data['workspace_size_mb']} MB")
    print("-" * 46)
    print("  Top processes by memory:")
    for p in data['top_processes']:
        bar = '█' * min(int(p['mem_mb'] / 100), 30)
        print(f"    {p['name'][:30]:30s} {p['mem_mb']:6d} MB {bar}")
    print("=" * 46)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', action='store_true', help='JSON output')
    ap.add_argument('--watch', type=int, metavar='N', help='watch every N seconds')
    ap.add_argument('--out', metavar='FILE', help='write JSON to file')
    args = ap.parse_args()

    if args.watch:
        try:
            while True:
                data = collect()
                if args.out:
                    Path(args.out).parent.mkdir(exist_ok=True)
                    Path(args.out).write_text(json.dumps(data), encoding='utf-8')
                print_report(data)
                print(f"\n  (refreshing every {args.watch}s — Ctrl+C to stop)\n")
                time.sleep(args.watch)
        except KeyboardInterrupt:
            print("\n👋 Monitor stopped.")
        return

    data = collect()
    if args.out:
        Path(args.out).parent.mkdir(exist_ok=True)
        Path(args.out).write_text(json.dumps(data), encoding='utf-8')
        print(f"📝 JSON written to {args.out}")
        if not args.json:
            print_report(data)
            return
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print_report(data)

if __name__ == '__main__':
    main()

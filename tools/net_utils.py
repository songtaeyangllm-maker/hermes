#!/usr/bin/env python3
"""
Hermes Network Utilities
========================
Practical network diagnostics: ping, DNS lookup, TCP port scan, external IP,
network info, and connectivity check.

Usage:
    python tools/net_utils.py ping <host> [--count 4]
    python tools/net_utils.py dns <domain>          # DNS lookup
    python tools/net_utils.py scan <host> [--ports 80,443,22] [--range 1-1000]
    python tools/net_utils.py myip                  # external IP
    python tools/net_utils.py netinfo               # local network info
    python tools/net_utils.py check [host]          # connectivity check
    python tools/net_utils.py ports [--limit 30]    # listening local ports
"""

import argparse
import ipaddress
import json
import socket
import subprocess
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

def _ps(script):
    try:
        return subprocess.check_output(
            ['powershell', '-NoProfile', '-Command', script],
            text=True, errors='replace', timeout=20).strip()
    except Exception:
        return None

def cmd_ping(host, count):
    print(f"🏓 PING {host} ({count}회)")
    print("-" * 40)
    try:
        # Windows ping (use bytes to avoid locale decode issues)
        r = subprocess.run(['ping', '-n', str(count), '-w', '3000', host],
                           capture_output=True, timeout=30)
        out = r.stdout.decode('utf-8', errors='replace') + r.stderr.decode('utf-8', errors='replace')
        for line in out.splitlines():
            if line.strip():
                print(f"  {line.strip()}")
    except FileNotFoundError:
        r = subprocess.run(['ping', '-c', str(count), host],
                           capture_output=True, text=True, timeout=30)
        print(r.stdout)

def cmd_dns(domain):
    print(f"🔍 DNS 조회: {domain}")
    print("-" * 40)
    try:
        infos = socket.getaddrinfo(domain, None)
        seen = set()
        for info in infos:
            ip = info[4][0]
            if ip not in seen:
                seen.add(ip)
                print(f"  📍 {ip} ({info[0].name})")
        if not seen:
            print("  ❌ IP 정보 없음")
    except socket.gaierror as e:
        print(f"  ❌ DNS 조회 실패: {e}")

def scan_port(host, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            if s.connect_ex((host, port)) == 0:
                return port
    except Exception:
        pass
    return None

def cmd_scan(host, ports_str, port_range):
    print(f"🔎 포트 스캔: {host}")
    print("-" * 40)
    ports = set()
    if ports_str:
        for p in ports_str.split(','):
            p = p.strip()
            if '-' in p:
                a, b = p.split('-')
                ports.update(range(int(a), int(b) + 1))
            elif p:
                ports.add(int(p))
    elif port_range:
        a, b = port_range.split('-')
        ports.update(range(int(a), int(b) + 1))
    else:
        print("  ❌ --ports 또는 --range 지정 필요")
        return
    print(f"  검사 포트 {len(ports)}개 (스레드 병렬)")
    open_ports = []
    with ThreadPoolExecutor(max_workers=50) as ex:
        results = ex.map(lambda p: (p, scan_port(host, p)), ports)
        for port, ok in results:
            if ok:
                open_ports.append(port)
                print(f"  ✅ {port:5d} 열림  ({service_name(port)})")
    if not open_ports:
        print("  🔒 열린 포트 없음")
    else:
        print(f"\n  총 {len(open_ports)}개 포트 열림")

def service_name(port):
    try:
        return socket.getservbyport(port) or '?'
    except Exception:
        return '?'

def cmd_myip():
    print("🌐 공인 IP 조회")
    print("-" * 40)
    for url in ['https://api.ipify.org?format=json',
                'https://api64.ipify.org?format=json',
                'https://ifconfig.me/ip']:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'curl/8'})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = r.read().decode()
                print(f"  📍 공인 IP: {data}")
                return
        except Exception as e:
            print(f"  ⚠️  {url} 실패: {e}")
    print("  ❌ 공인 IP 조회 실패")

def cmd_netinfo():
    print("🖧 로컬 네트워크 정보")
    print("-" * 40)
    # Use ipconfig (Windows)
    try:
        r = subprocess.run(['ipconfig'], capture_output=True, text=True, timeout=20)
        for line in r.stdout.splitlines():
            l = line.strip()
            if any(k in l for k in ['IPv4', '서브넷', '게이트웨이', 'Subnet', 'Gateway', 'DNS']):
                print(f"  {l}")
    except Exception as e:
        print(f"  ❌ ipconfig 실패: {e}")

def cmd_check(host):
    print(f"🧪 연결성 확인: {host or '인터넷'}")
    print("-" * 40)
    targets = [host] if host else ['8.8.8.8:443', 'naver.com:443', 'google.com:443', 'github.com:443']
    ok = 0
    for t in targets:
        if ':' in t:
            host_t, port = t.rsplit(':', 1)
            port = int(port)
        else:
            host_t, port = t, 443
        try:
            socket.setdefaulttimeout(4)
            socket.create_connection((host_t, port), timeout=4)
            print(f"  ✅ {t:20s} 연결 OK")
            ok += 1
        except Exception as e:
            print(f"  ❌ {t:20s} 연결 실패")
    print(f"\n  결과: {ok}/{len(targets)} 성공")
    return 0 if ok else 1

def cmd_ports(limit):
    print(f"🔄 로컬 수신 포트 (상위 {limit}개)")
    print("-" * 40)
    out = _ps(
        "$c = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | "
        "Group-Object LocalPort | Select-Object -First %d | Sort-Object Count -Descending; "
        "$c | ForEach-Object { $p=$_.Name; $n=(Get-Process -Id ($_.Group | Select-Object -First 1).OwningProcess -ErrorAction SilentlyContinue).ProcessName; "
        "Write-Output (\"{0}|{1}|{2}\" -f $p,$_.Count,$n) }" % limit)
    if out:
        for line in out.splitlines():
            if '|' in line:
                port, count, name = line.split('|')
                print(f"  🔌 :{port:>6s}  ({name or '?'})  x{count}")
    else:
        print("  ❌ 포트 정보 가져오기 실패")

def main():
    ap = argparse.ArgumentParser(prog='net_utils.py')
    sub = ap.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('ping'); p.add_argument('host'); p.add_argument('--count', type=int, default=4)
    d = sub.add_parser('dns'); d.add_argument('domain')
    s = sub.add_parser('scan'); s.add_argument('host'); s.add_argument('--ports'); s.add_argument('--range')
    sub.add_parser('myip')
    sub.add_parser('netinfo')
    c = sub.add_parser('check'); c.add_argument('host', nargs='?')
    pr = sub.add_parser('ports'); pr.add_argument('--limit', type=int, default=30)

    args = ap.parse_args()

    if args.cmd == 'ping':
        cmd_ping(args.host, args.count)
    elif args.cmd == 'dns':
        cmd_dns(args.domain)
    elif args.cmd == 'scan':
        cmd_scan(args.host, args.ports, args.range)
    elif args.cmd == 'myip':
        cmd_myip()
    elif args.cmd == 'netinfo':
        cmd_netinfo()
    elif args.cmd == 'check':
        sys.exit(cmd_check(args.host))
    elif args.cmd == 'ports':
        cmd_ports(args.limit)

if __name__ == '__main__':
    main()

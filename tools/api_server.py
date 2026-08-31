#!/usr/bin/env python3
"""
Hermes Local API Server
=======================
Serves workspace data as JSON on localhost for the command center / widgets.
Pure stdlib (http.server) — no external deps.

Endpoints:
    GET /api/health    -> {ok, time, uptime}
    GET /api/status    -> {cpu, memory, disk, processes}
    GET /api/projects  -> project list
    GET /api/tools     -> list of tools (name, desc, path)
    GET /api/notes     -> diary stats (entries, chars, streak)

Usage:
    python tools/api_server.py            # run on port 8765 (default)
    python tools/api_server.py --port 9000
"""
import argparse
import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
START = time.time()


def _sys_info():
    """Best-effort system metrics without external libs."""
    info = {"cpu": None, "memory": None, "disk": None, "processes": None}
    try:
        # Use PowerShell CIM for portability
        import subprocess
        ps = r"""
$cpu = (Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average
$os = Get-CimInstance Win32_OperatingSystem
$tot = [math]::Round($os.TotalVisibleMemorySize/1MB,1)
$free = [math]::Round($os.FreePhysicalMemory/1MB,1)
$used = [math]::Round($tot-$free,1)
$pct = [math]::Round($used/$tot*100,1)
$disk = Get-PSDrive -Name C
$dtot=[math]::Round($disk.Used+$disk.Free,1); $dused=[math]::Round($disk.Used,1)
$dFree=[math]::Round($disk.Free,1); $dpct=[math]::Round($dused/$dtot*100,1)
$procs = (Get-Process).Count
"cpu=$cpu|mem_pct=$pct|mem_used=$used|mem_total=$tot|disk_pct=$dpct|disk_used=$dused|disk_free=$dFree|disk_total=$dtot|procs=$procs"
"""
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True, text=True, timeout=12,
            encoding="utf-8", errors="replace",
        ).stdout.strip()
        # Output is pipe-delimited key=value tokens, possibly on one line
        for token in out.replace("\r", "").replace("\n", "|").split("|"):
            if "=" in token:
                k, v = token.split("=", 1)
                try:
                    v = float(v) if "." in v else int(v)
                except ValueError:
                    pass
                if k == "cpu":
                    info["cpu"] = v
                elif k == "mem_pct":
                    info["memory"] = {"percent": v}
                elif k == "mem_used":
                    if isinstance(info["memory"], dict):
                        info["memory"]["used_gb"] = v
                elif k == "mem_total":
                    if isinstance(info["memory"], dict):
                        info["memory"]["total_gb"] = v
                elif k == "disk_pct":
                    info["disk"] = {"percent": v}
                elif k == "disk_used":
                    if isinstance(info["disk"], dict):
                        info["disk"]["used_gb"] = v
                elif k == "disk_free":
                    if isinstance(info["disk"], dict):
                        info["disk"]["free_gb"] = v
                elif k == "disk_total":
                    if isinstance(info["disk"], dict):
                        info["disk"]["total_gb"] = v
                elif k == "procs":
                    info["processes"] = v
    except Exception as e:
        info["error"] = str(e)
    return info


def _projects():
    path = os.path.join(WS, "projects", "projects.json")
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _tools():
    tdir = os.path.join(WS, "tools")
    tools = []
    if os.path.isdir(tdir):
        for name in sorted(os.listdir(tdir)):
            if name.endswith(".py") and not name.startswith("_"):
                # read first docstring line as description
                desc = ""
                try:
                    with open(os.path.join(tdir, name), encoding="utf-8") as f:
                        lines = f.read().split("\n")
                    for ln in lines[1:6]:
                        s = ln.strip().strip('"').strip("'")
                        if s and not s.startswith(("=", "Usage", "import")):
                            desc = s
                            break
                except Exception:
                    pass
                tools.append({"name": name, "desc": desc})
    return tools


def _notes():
    ddir = os.path.join(WS, "notes", "diary")
    entries = 0
    chars = 0
    dates = set()
    if os.path.isdir(ddir):
        for fn in os.listdir(ddir):
            if fn.endswith((".md", ".txt")):
                try:
                    with open(os.path.join(ddir, fn), encoding="utf-8") as f:
                        txt = f.read()
                    entries += 1
                    chars += len(txt.strip())
                    dates.add(fn[:10])
                except Exception:
                    pass
    return {"entries": entries, "chars": chars, "days": len(dates)}


class Handler(BaseHTTPRequestHandler):
    def _send(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        try:
            if path == "/" or path == "/api/health":
                self._send({"ok": True, "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "uptime_s": int(time.time() - START), "workspace": WS})
            elif path == "/api/status":
                self._send(_sys_info())
            elif path == "/api/projects":
                self._send({"projects": _projects(), "count": len(_projects())})
            elif path == "/api/tools":
                tools = _tools()
                self._send({"tools": tools, "count": len(tools)})
            elif path == "/api/notes":
                self._send(_notes())
            else:
                self._send({"error": "not found", "path": path}, 404)
        except Exception as e:
            self._send({"error": str(e)}, 500)

    def log_message(self, *args):
        pass


def main():
    ap = argparse.ArgumentParser(description="Hermes local API server")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"✅ Hermes API 서버 가동  http://{args.host}:{args.port}/api/health")
    print(f"   workspace: {WS}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹ 종료")


if __name__ == "__main__":
    main()

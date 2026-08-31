#!/usr/bin/env python3
"""
Hermes Workspace Toolkit
=======================
A collection of useful utilities for the C:\hermes workspace.
Run: python hermes_toolkit.py <command>

Commands:
    init        - Initialize the workspace structure
    status      - Show workspace status
    backup      - Backup the workspace to a zip file
    cleanup     - Remove temporary files (*.tmp, *.log old than 30 days)
    tree        - Show directory tree
    info        - Show system info
    count-lines - Count lines of code in project files
    refresh     - Regenerate dashboard live data (data.js + projects.js)
    maintenance - Weekly cleanup + backup in one command
"""

import os
import sys
import zipfile
import shutil
import json
import platform
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path(r"C:\hermes")

def get_size(path):
    """Get directory size in human-readable format"""
    total = 0
    for p in path.rglob('*'):
        if p.is_file():
            total += p.stat().st_size
    if total < 1024:
        return f"{total} B"
    elif total < 1024 * 1024:
        return f"{total / 1024:.1f} KB"
    elif total < 1024 * 1024 * 1024:
        return f"{total / (1024*1024):.1f} MB"
    return f"{total / (1024*1024*1024):.2f} GB"

def cmd_init():
    """Initialize workspace structure"""
    dirs = ['dashboard', 'tools', 'scripts', 'notes', 'projects', 'logs']
    for d in dirs:
        (WORKSPACE / d).mkdir(exist_ok=True)
    print(f"✅ Workspace initialized at {WORKSPACE}")
    for d in dirs:
        print(f"   📁 {d}/")

def cmd_status():
    """Show workspace status"""
    print("📊 Hermes Workspace Status")
    print("=" * 40)
    
    total_files = 0
    for folder in sorted(WORKSPACE.iterdir()):
        if folder.is_dir():
            files = [f for f in folder.rglob('*') if f.is_file()]
            total_files += len(files)
            print(f"  📁 {folder.name:15s} - {len(files):3d} files")
    
    total_size = get_size(WORKSPACE)
    print(f"\n  📦 Total: {total_files} files · {total_size}")
    
    # Show recent activity
    print("\n🕐 Recent files:")
    recent = sorted(WORKSPACE.rglob('*'), key=lambda x: x.stat().st_mtime, reverse=True)
    for f in recent[:5]:
        if f.is_file() and '__pycache__' not in str(f):
            mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
            print(f"   {mtime}  {os.path.relpath(f, WORKSPACE)}")

def cmd_backup():
    """Backup the workspace to a zip file"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = WORKSPACE.parent / 'hermes_backups'
    backup_dir.mkdir(exist_ok=True)
    zip_path = backup_dir / f"hermes_backup_{timestamp}.zip"
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in WORKSPACE.rglob('*'):
            if f.is_file() and '__pycache__' not in str(f):
                zf.write(f, os.path.relpath(f, WORKSPACE))
    
    size = zip_path.stat().st_size / 1024
    print(f"💾 Backup saved: {zip_path}")
    print(f"   Size: {size:.1f} KB ({datetime.now().strftime('%H:%M:%S')})")

def cmd_cleanup():
    """Remove temporary files"""
    removed = 0
    cutoff = datetime.now() - timedelta(days=30)
    
    for f in WORKSPACE.rglob('*'):
        if f.is_file():
            if f.suffix in ['.tmp', '.bak']:
                f.unlink()
                removed += 1
                print(f"   🗑️  Removed: {os.path.relpath(f, WORKSPACE)}")
            elif f.suffix == '.log' and datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
                f.unlink()
                removed += 1
                print(f"   🗑️  Removed (old): {os.path.relpath(f, WORKSPACE)}")
    
    # Clean __pycache__
    for d in WORKSPACE.rglob('__pycache__'):
        shutil.rmtree(d, ignore_errors=True)
        removed += 1
        print(f"   🗑️  Removed: {os.path.relpath(d, WORKSPACE)}")
    
    if removed == 0:
        print("✨ Nothing to clean up!")
    else:
        print(f"🧹 Cleaned up {removed} items")

def cmd_tree():
    """Show directory tree"""
    def tree(path, prefix='', is_last=True):
        marker = '└── ' if is_last else '├── '
        print(f"{prefix}{marker}{path.name}/")
        prefix += '    ' if is_last else '│   '
        
        items = sorted([p for p in path.iterdir() if p.is_dir()])
        files = sorted([p for p in path.iterdir() if p.is_file()])
        
        for i, item in enumerate(items):
            tree(item, prefix, i == len(items) - 1 and not files)
        
        for i, f in enumerate(files):
            marker = '└── ' if i == len(files) - 1 else '├── '
            size = f.stat().st_size
            size_str = f"{size} B" if size < 1024 else f"{size/1024:.1f} KB"
            print(f"{prefix}{marker}{f.name} ({size_str})")
    
    print(f"🌳 {WORKSPACE.name}/")
    for item in sorted([p for p in WORKSPACE.iterdir() if p.is_dir()]):
        tree(item, '', item == sorted([p for p in WORKSPACE.iterdir() if p.is_dir()])[-1])

def cmd_info():
    """Show system info"""
    print("🖥️  System Information")
    print("=" * 40)
    print(f"  OS:        {platform.system()} {platform.release()}")
    print(f"  Machine:   {platform.machine()}")
    print(f"  Processor: {platform.processor() or 'N/A'}")
    print(f"  Python:    {platform.python_version()}")
    print(f"  Workspace: {WORKSPACE}")
    print(f"  User:      {os.environ.get('USERNAME', 'unknown')}")
    print(f"  Disk:      {shutil.disk_usage(WORKSPACE)[2] / (1024**3):.1f} GB free")

def cmd_count_lines():
    """Count lines of code"""
    extensions = {'.py', '.js', '.html', '.css', '.md', '.json', '.java'}
    total = {}
    grand_total = 0
    
    for f in WORKSPACE.rglob('*'):
        if f.is_file() and f.suffix in extensions and 'node_modules' not in str(f) and '__pycache__' not in str(f):
            try:
                with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
                    lines = sum(1 for _ in fp)
                total[f.suffix] = total.get(f.suffix, 0) + lines
                grand_total += lines
            except:
                pass
    
    print("📝 Lines of Code")
    print("=" * 40)
    for ext, count in sorted(total.items(), key=lambda x: -x[1]):
        bar = '█' * min(int(count / max(grand_total, 1) * 30), 30)
        print(f"  {ext:6s} {count:6d} lines  {bar}")
    print(f"\n  Total: {grand_total} lines")

def cmd_refresh_dashboard():
    """Regenerate live dashboard data (data.json + data.js + projects.js)."""
    import subprocess, sys
    # Step 1: run diagnostics to dashboard/data.json
    diag = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'system_diagnostics.py')
    data_path = WORKSPACE / 'dashboard' / 'data.json'
    r = subprocess.run([sys.executable, diag, '--out', str(data_path)],
                       capture_output=True, text=True)
    # Step 2: convert data.json -> data.js for file:// loading
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            payload = f.read()
        js_path = WORKSPACE / 'dashboard' / 'data.js'
        js_path.write_text('window.HERMES_DATA = ' + payload + ';', encoding='utf-8')
        print(f"✅ Dashboard data refreshed.")
        print(f"   data.json: {data_path}")
        print(f"   data.js:   {js_path}")
    except Exception as e:
        print(f"❌ Failed to generate data.js: {e}")
        print(r.stdout)
        print(r.stderr)

    # Step 3: convert projects.json -> projects.js
    tf = WORKSPACE / 'projects' / 'projects.json'
    pjs = WORKSPACE / 'dashboard' / 'projects.js'
    try:
        if tf.exists():
            proj = tf.read_text(encoding='utf-8')
            pjs.write_text('window.HERMES_PROJECTS = ' + proj + ';', encoding='utf-8')
            print(f"✅ Projects synced: {pjs}")
    except Exception as e:
        print(f"❌ Failed to generate projects.js: {e}")

def cmd_maintenance():
    """Weekly maintenance: cleanup + backup in one go."""
    print("🧹 🔄 Starting weekly maintenance...")
    print("")
    cmd_cleanup()
    print("")
    cmd_backup()

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help', 'help']:
        print(__doc__)
        return
    
    cmd = sys.argv[1]
    commands = {
        'init': cmd_init,
        'status': cmd_status,
        'backup': cmd_backup,
        'cleanup': cmd_cleanup,
        'tree': cmd_tree,
        'info': cmd_info,
        'count-lines': cmd_count_lines,
        'refresh': cmd_refresh_dashboard,
        'maintenance': cmd_maintenance,
    }
    
    if not WORKSPACE.exists():
        WORKSPACE.mkdir(parents=True)
    
    if cmd in commands:
        commands[cmd]()
    else:
        print(f"❌ Unknown command: {cmd}")
        print("Available: " + ', '.join(commands.keys()))
        sys.exit(1)

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Hermes Project Tracker
=====================
Manage projects stored in projects/projects.json.

Usage:
    python tools/project_tracker.py list                 # list all projects
    python tools/project_tracker.py add                  # interactive add
    python tools/project_tracker.py add --name X --status active --desc "..." --path C:/x
    python tools/project_tracker.py status <name> <new>  # change status
    python tools/project_tracker.py del <name>           # delete project
    python tools/project_tracker.py stats                # project stats
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

TRACKER_FILE = Path(r"C:\hermes\projects\projects.json")

STATUSES = ['active', 'planned', 'paused', 'done', 'archived']

def load():
    if TRACKER_FILE.exists():
        return json.loads(TRACKER_FILE.read_text(encoding='utf-8'))
    return []

def save(projects):
    TRACKER_FILE.parent.mkdir(exist_ok=True)
    TRACKER_FILE.write_text(json.dumps(projects, indent=2, ensure_ascii=False),
                            encoding='utf-8')

def normalize_name(name):
    return name.strip().lower().replace(' ', '-')

def find(projects, name):
    target = normalize_name(name)
    for p in projects:
        if normalize_name(p['name']) == target:
            return p
    return None

def print_project(p):
    status_icon = {'active': '🚀', 'planned': '📋', 'paused': '⏸️',
                   'done': '✅', 'archived': '🗄️'}.get(p['status'], '📦')
    desc = p.get('description', '')
    path = p.get('path', '')
    updated = p.get('updated', '')
    print(f"  {status_icon} {p['name']:<24s} [{p['status']:<8s}] {desc}")
    if path:
        print(f"                      📁 {path}")
    if updated:
        print(f"                      🕐 updated {updated}")

def cmd_list(projects, filter_status=None):
    if not projects:
        print("📂 No projects yet. Add one with: tracker.py add")
        return
    for p in projects:
        if filter_status and p['status'] != filter_status:
            continue
        print_project(p)

def _prompt(msg):
    """Safely prompt; returns '' if stdin is not interactive (automation)."""
    try:
        return input(msg).strip()
    except EOFError:
        return ""

def cmd_add(projects, args):
    name = args.name
    if not name:
        name = _prompt("Project name: ")
    if find(projects, name):
        print(f"⚠️  Project '{name}' already exists.")
        return 1
    status = args.status or 'active'
    if status not in STATUSES:
        print(f"❌ Invalid status. Use one of: {', '.join(STATUSES)}")
        return 1
    if args.desc is not None:
        desc = args.desc
    else:
        desc = _prompt("Description (optional): ")
    desc = desc or ""
    if args.path is not None:
        path = args.path
    else:
        path = _prompt("Path (optional): ")
    path = path or ""
    project = {
        'name': name,
        'status': status,
        'description': desc,
        'path': path,
        'created': datetime.now().strftime('%Y-%m-%d'),
        'updated': datetime.now().strftime('%Y-%m-%d %H:%M'),
    }
    projects.append(project)
    save(projects)
    print(f"✅ Project added: {name}")
    print_project(project)
    return 0

def cmd_status(projects, args):
    p = find(projects, args.name)
    if not p:
        print(f"❌ Project '{args.name}' not found.")
        return 1
    new = args.status
    if new not in STATUSES:
        print(f"❌ Invalid status. Use one of: {', '.join(STATUSES)}")
        return 1
    p['status'] = new
    p['updated'] = datetime.now().strftime('%Y-%m-%d %H:%M')
    save(projects)
    print(f"🔄 Project '{args.name}' -> [{new}]")
    print_project(p)
    return 0

def cmd_del(projects, args):
    p = find(projects, args.name)
    if not p:
        print(f"❌ Project '{args.name}' not found.")
        return 1
    projects.remove(p)
    save(projects)
    print(f"🗑️  Deleted project: {args.name}")
    return 0

def cmd_stats(projects):
    from collections import Counter
    counts = Counter(p['status'] for p in projects)
    print("📊 Project Stats")
    print("=" * 30)
    for s in STATUSES:
        n = counts.get(s, 0)
        bar = '█' * n
        icon = {'active': '🚀', 'planned': '📋', 'paused': '⏸️',
                'done': '✅', 'archived': '🗄️'}.get(s, '')
        print(f"  {icon} {s:<8s} {n:3d}  {bar}")
    print(f"\n  Total: {len(projects)}")
    active = counts.get('active', 0)
    print(f"  Active projects: {active}")

def main():
    ap = argparse.ArgumentParser(prog='project_tracker.py')
    sub = ap.add_subparsers(dest='cmd')

    sub.add_parser('list', help='list all projects')
    p_stats = sub.add_parser('stats', help='project stats')

    p_add = sub.add_parser('add', help='add a project')
    p_add.add_argument('--name')
    p_add.add_argument('--status', choices=STATUSES)
    p_add.add_argument('--desc')
    p_add.add_argument('--path')

    p_status = sub.add_parser('status', help='change status')
    p_status.add_argument('name')
    p_status.add_argument('status', choices=STATUSES)

    p_del = sub.add_parser('del', help='delete project')
    p_del.add_argument('name')

    args = ap.parse_args()

    projects = load()

    if args.cmd == 'list':
        cmd_list(projects)
    elif args.cmd == 'stats':
        cmd_stats(projects)
    elif args.cmd == 'add':
        sys.exit(cmd_add(projects, args))
    elif args.cmd == 'status':
        sys.exit(cmd_status(projects, args))
    elif args.cmd == 'del':
        sys.exit(cmd_del(projects, args))
    else:
        ap.print_help()

if __name__ == '__main__':
    main()

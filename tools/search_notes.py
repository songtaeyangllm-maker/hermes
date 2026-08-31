#!/usr/bin/env python3
"""
Hermes TF-IDF Note Search
=========================
Index notes/diary, notes/reports/docs and search by relevance (TF-IDF).
Returns ranked results with scores and matching snippets.

Usage:
    python tools/search_notes.py <query> [--top N] [--reindex]
    python tools/search_notes.py --list         # show indexed docs
    python tools/search_notes.py --reindex      # rebuild index
"""

import argparse
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

WS = Path('C:/hermes')
INDEX_DIR = WS / 'tools'
INDEX_FILE = INDEX_DIR / 'note_index.json'
SEARCH_DIRS = [WS / 'notes', WS / 'README.md']
EXTS = {'.md', '.html', '.txt', '.json'}
IGNORE = {'sample_post'}

def tokenize(text):
    # Korean: keep hangul chunks + ascii words
    text = text.lower()
    # ascii words
    words = re.findall(r'[a-z0-9_]{2,}', text)
    # korean sequences
    ko = re.findall(r'[가-힣]{2,}', text)
    return words + ko

def build_index():
    docs = []
    for root in [WS / 'notes']:
        for f in root.rglob('*'):
            if f.is_file() and f.suffix in EXTS and f.stem not in IGNORE:
                try:
                    text = f.read_text(encoding='utf-8', errors='ignore')
                except Exception:
                    continue
                docs.append({'id': str(f), 'name': f.name, 'text': text})
    # README
    for f in [WS / 'README.md']:
        if f.exists():
            docs.append({'id': str(f), 'name': f.name,
                         'text': f.read_text(encoding='utf-8', errors='ignore')})

    # term frequency per doc
    n_docs = len(docs)
    if n_docs == 0:
        return {'docs': [], 'df': {}, 'n_docs': 0}

    df = Counter()  # document frequency
    doc_tf = []
    for d in docs:
        tokens = tokenize(d['text'])
        tf = Counter(tokens) if tokens else Counter()
        for term in set(tokens):
            df[term] += 1
        doc_tf.append({'id': d['id'], 'name': d['name'], 'tf': tf, 'total': len(tokens)})
        # strip text for storage size (keep name + tf + total; full text reloaded on search)

    # store compact index
    index_data = {
        'docs': [{'id': d['id'], 'name': d['name']} for d in docs],
        'df': dict(df),
        'n_docs': n_docs,
    }
    INDEX_FILE.write_text(json.dumps(index_data, ensure_ascii=False), encoding='utf-8')
    # save doc_tf separately to keep index small
    (INDEX_DIR / 'note_tf.json').write_text(json.dumps(doc_tf, ensure_ascii=False), encoding='utf-8')
    return index_data

def load_index():
    if INDEX_FILE.exists():
        idx = json.loads(INDEX_FILE.read_text(encoding='utf-8'))
        tf_list = json.loads((INDEX_DIR / 'note_tf.json').read_text(encoding='utf-8'))
        return idx, tf_list
    idx = build_index()
    tf_list = json.loads((INDEX_DIR / 'note_tf.json').read_text(encoding='utf-8'))
    return idx, tf_list

def search(query, index, tf_list, top):
    q_terms = set(tokenize(query))
    if not q_terms:
        return []
    n_docs = index['n_docs']
    df = index['df']

    scores = []
    for doc in tf_list:
        total = max(doc['total'], 1)
        score = 0
        for term in q_terms:
            tf = doc['tf'].get(term, 0)
            if tf == 0:
                continue
            idf = math.log((n_docs + 1) / (df.get(term, 0) + 1)) + 1
            score += (tf / total) * idf
        if score > 0:
            scores.append((score, doc['id'], doc['name']))
    scores.sort(reverse=True)
    return [{'score': round(s, 4), 'id': i, 'name': n} for s, i, n in scores[:top]]

def snippet(path, query, limit=160):
    try:
        text = Path(path).read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return ''
    q_terms = set(tokenize(query))
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    best = None
    for l in lines:
        if any(t in l.lower() for t in q_terms):
            if best is None or len(best) < len(l):
                best = l
    if best:
        return best[:limit]
    return (text[:limit] + '…') if text else ''

def main():
    ap = argparse.ArgumentParser(prog='search_notes.py')
    ap.add_argument('query', nargs='?')
    ap.add_argument('--top', type=int, default=5)
    ap.add_argument('--reindex', action='store_true')
    ap.add_argument('--list', action='store_true')
    args = ap.parse_args()

    if args.reindex or not INDEX_FILE.exists():
        idx = build_index()
        print(f"🔍 재인덱싱 완료: {idx['n_docs']}개 문서, {len(idx['df'])}개 용어")
    else:
        idx, _ = load_index()

    if args.list:
        print(f"📚 인덱싱된 문서 {idx['n_docs']}개:")
        for d in idx['docs']:
            print(f"   • {d['name']}")
        return

    if not args.query:
        print("❌ 검색어가 필요합니다: search_notes.py <query>")
        return

    _, tf_list = load_index()
    results = search(args.query, idx, tf_list, args.top)
    print(f"🔎 '{args.query}' 검색 결과 ({len(results)}건):")
    print("=" * 50)
    if not results:
        print("   결과 없음")
        return
    for r in results:
        snip = snippet(r['id'], args.query)
        print(f"  [{r['score']:.3f}] {r['name']}")
        print(f"       {r['id']}")
        if snip:
            print(f"       💬 {snip}")
        print()

if __name__ == '__main__':
    main()

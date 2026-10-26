#!/usr/bin/env python3
"""memoir maintain: proposal list per references/spec-maintenance.md.

Read-only by default. --apply writes only the lifecycle transitions (never
archives, never merges -- those need the user). Store: $MEMOIR_STORE, else
./memory.
"""
import os
import re
import sys
import io
import datetime
import collections
import itertools

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = os.environ.get('MEMOIR_STORE') or os.path.join(os.getcwd(), 'memory')
TODAY = datetime.date.today()
FMRE = re.compile(r'^---\r?\n(.*?)\r?\n---\r?\n?', re.S)


def d(s):
    try:
        return datetime.date.fromisoformat(str(s)[:10])
    except Exception:
        return None


def load(path):
    t = open(path, encoding='utf-8', errors='replace').read()
    m = FMRE.match(t)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        km = re.match(r'^([A-Za-z_][\w-]*):\s*(.*)$', line)
        if km:
            fm[km.group(1)] = km.group(2).strip()
    return fm


def main():
    mems = {}
    for dp, dirs, files in os.walk(ROOT):
        if 'archive' in dp.lower():
            continue
        for fn in sorted(files):
            if not fn.endswith('.md'):
                continue
            p = os.path.join(dp, fn)
            fm = load(p)
            if not fm or 'importance' not in fm:
                continue
            fm['_rel'] = os.path.relpath(p, ROOT).replace(os.sep, '/')
            fm['_imp'] = int(fm['importance'])
            fm['_tags'] = re.findall(r'[\w一-鿿-]+', fm.get('tags', ''))
            fm['_rel_ids'] = re.findall(r'[\w一-鿿-]+', fm.get('related', ''))
            mems[fm.get('id', os.path.splitext(fn)[0])] = fm

    backref = collections.defaultdict(set)
    for mid, fm in mems.items():
        for r in fm['_rel_ids']:
            backref[r].add(mid)

    trans, archive, flags = [], [], []
    for mid, fm in mems.items():
        up, rc = d(fm.get('updated')), d(fm.get('recency'))
        du = (TODAY - up).days if up else None
        da = (TODAY - rc).days if rc else None
        lc, imp = fm.get('lifecycle', 'active'), fm['_imp']
        if lc == 'active' and imp >= 4 and du is not None and du > 30:
            trans.append((mid, 'active -> stable', f'i={imp}, unchanged {du}d'))
        elif lc == 'active' and imp <= 2 and da is not None and da > 60:
            trans.append((mid, 'active -> fading', f'i={imp}, untouched {da}d'))
        elif lc == 'stable' and imp <= 3 and da is not None and da > 90:
            trans.append((mid, 'stable -> fading', f'i={imp}, unaccessed {da}d'))
        if lc == 'fading' and imp <= 2 and da is not None and da > 120:
            archive.append((mid, f'i={imp}, unaccessed {da}d'))
        if imp >= 4 and da is not None and da > 90:
            flags.append((mid, f'high importance, untouched {da}d'))

    merges = []
    by_dom = collections.defaultdict(list)
    for mid, fm in mems.items():
        by_dom[fm.get('domain', '')].append(mid)
    for dom, ids in by_dom.items():
        for a, b in itertools.combinations(sorted(ids), 2):
            ta, tb = set(mems[a]['_tags']), set(mems[b]['_tags'])
            if not ta or not tb:
                continue
            ov = len(ta & tb) / len(ta | tb)
            if ov > 0.5 or b in mems[a]['_rel_ids'] or a in mems[b]['_rel_ids']:
                merges.append((dom, a, b, round(ov, 2)))

    orphans = []
    for mid, fm in mems.items():
        if fm.get('lifecycle') in ('seedling', 'fading'):
            if not fm['_rel_ids'] and not backref.get(mid):
                orphans.append((mid, fm.get('lifecycle')))

    print(f'=== memoir maintain -- {TODAY} ===\n')
    print(f'cold memories: {len(mems)}')
    print('  lifecycle:', dict(collections.Counter(fm.get('lifecycle') for fm in mems.values())))
    print('  domain:', dict(collections.Counter(fm.get('domain') for fm in mems.values()).most_common()))
    print('  layer:', dict(collections.Counter(fm.get('layer') for fm in mems.values())))
    arch_dir = os.path.join(ROOT, 'archive')
    arch_files = len([f for f in os.listdir(arch_dir) if f.endswith('.md')]) if os.path.isdir(arch_dir) else 0
    print(f'  archive/: {arch_files} files')
    hot_path = os.path.join(ROOT, 'HOT-MEMORY.md')
    if os.path.exists(hot_path):
        hot = open(hot_path, encoding='utf-8').read()
        print(f'  HOT-MEMORY: {len(hot)} chars, roughly {int(len(hot) / 1.5)} tokens\n')
    else:
        print('  HOT-MEMORY: missing\n')

    if '--apply' in sys.argv:
        changed = 0
        for mid, t, why in trans:
            new = t.split('->')[1].strip()
            p = os.path.join(ROOT, mems[mid]['_rel'].replace('/', os.sep))
            txt = open(p, encoding='utf-8').read()
            nt = re.sub(r'(?m)^lifecycle:\s*\S+', f'lifecycle: {new}', txt, count=1)
            if nt != txt:
                open(p, 'w', encoding='utf-8').write(nt)
                changed += 1
        print(f'--apply: wrote {changed} lifecycle changes\n')

    print(f'=== proposed lifecycle transitions ({len(trans)}) ===')
    for mid, t, why in sorted(trans, key=lambda x: x[0]):
        print(f'  {mid}: {t}  [{why}]')
    print(f'\n=== archive candidates (confirm, {len(archive)}) ===')
    for mid, why in archive:
        print(f'  {mid}: {why}')
    print(f'\n=== worth a look (high importance, long untouched, {len(flags)}) ===')
    for mid, why in flags:
        print(f'  {mid}: {why}')
    print(f'\n=== merge candidates ({len(merges)}) ===')
    for dom, a, b, ov in sorted(merges, key=lambda x: -x[3]):
        print(f'  [{dom}] {a} + {b}  (tag overlap {ov})')
    print(f'\n=== orphans ({len(orphans)}) ===')
    for mid, lc_ in orphans:
        print(f'  {mid} ({lc_})')


if __name__ == '__main__':
    main()

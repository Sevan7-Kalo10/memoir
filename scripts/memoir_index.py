#!/usr/bin/env python3
"""Rebuild the cold-layer index in MEMORY.md from per-file frontmatter, so the
index always agrees with the `domain` fields.

Default is dry-run (prints the block); --write replaces the section in
MEMORY.md. Store: $MEMOIR_STORE, else ./memory.
"""
import os
import re
import sys
import io
import collections

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = os.environ.get('MEMOIR_STORE') or os.path.join(os.getcwd(), 'memory')
MEM = os.path.join(ROOT, 'MEMORY.md')
SKIP = {'HOT-MEMORY.md', 'MEMORY.md', 'triggers.md'}
HEADING = '## 冷层——索引'
TAIL = '> **域索引：**'
ORDER = ['identity', 'relationship', 'behavior', 'philosophy', 'preference',
         'project', 'literature', 'existence', 'milestone']
LABEL = {'identity': '身份 identity', 'relationship': '关系 relationship',
         'behavior': '行为 behavior', 'philosophy': '哲学 philosophy',
         'preference': '偏好 preference', 'project': '项目 project',
         'literature': '书与文学 literature', 'existence': '存在 existence',
         'milestone': '里程碑 milestone'}
FMRE = re.compile(r'^---\r?\n(.*?)\r?\n---\r?\n?', re.S)


def parse(path):
    text = open(path, encoding='utf-8', errors='replace').read()
    m = FMRE.match(text)
    if not m:
        return None
    d = {}
    for line in m.group(1).splitlines():
        km = re.match(r'^([A-Za-z_][\w-]*):\s*(.*)$', line)
        if km:
            d[km.group(1)] = km.group(2).strip()
    d['_body'] = text[m.end():]
    return d


def main():
    entries = collections.defaultdict(list)
    for dp, dirs, files in os.walk(ROOT):
        if 'archive' in dp.lower():
            continue
        for fn in sorted(files):
            if not fn.endswith('.md') or fn in SKIP:
                continue
            path = os.path.join(dp, fn)
            rel = os.path.relpath(path, ROOT).replace(os.sep, '/')
            fm = parse(path)
            if not fm:
                continue
            hm = re.search(r'^#\s+(.+)$', fm['_body'], re.M)
            h1 = hm.group(1).strip().strip('# ') if hm else ''
            desc = fm.get('description', '').strip()
            title = h1 if h1 and len(h1) <= 36 else (desc or fm.get('id', fn))
            imp = fm.get('importance', '?')
            upd = fm.get('updated', '')
            entries[fm.get('domain', 'project')].append(
                (int(imp) if str(imp).isdigit() else 0, upd, title, rel))

    lines = [HEADING, '']
    lines.append('> Each line: `- [title](path) (i=importance)`. '
                 'Domain comes from the file frontmatter; rerun memoir_index.py to rebuild.')
    lines.append('')
    total = 0
    for dom in ORDER + [d for d in entries if d not in ORDER]:
        if dom not in entries:
            continue
        es = sorted(entries[dom], key=lambda x: (-x[0], x[1] or ''))
        lines.append(f'### {LABEL.get(dom, dom)}（{len(es)}）')
        for imp, upd, title, rel in es:
            lines.append(f'- [{title}]({rel}) (i={imp})')
            total += 1
        lines.append('')

    block = '\n'.join(lines).rstrip() + '\n'
    print(f'index: {total} entries across {len(entries)} domains')

    if '--write' not in sys.argv:
        print(block)
        print('DRY-RUN. Add --write to replace the index section in MEMORY.md.')
        return 0

    content = open(MEM, encoding='utf-8').read()
    a = content.find(HEADING)
    b = content.find(TAIL, a) if a >= 0 else -1
    if a < 0 or b < 0:
        print(f'ERROR: MEMORY.md has no "{HEADING}" ... "{TAIL}" section to replace.')
        return 1
    open(MEM, 'w', encoding='utf-8').write(content[:a] + block + '\n' + content[b:])
    print(f'wrote {MEM}')
    return 0


if __name__ == '__main__':
    sys.exit(main())

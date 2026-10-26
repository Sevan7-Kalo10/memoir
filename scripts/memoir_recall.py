"""Recall without being asked: given the user's prompt, surface a few old
memories that may be relevant. Prompts only -- never injects bodies.

UserPromptSubmit hook. Reads JSON on stdin, takes `prompt`, prints at most
two hits. Scoring is deliberately dumb: CJK bigrams + latin words, weighted
by rarity across the store. No index, no model, a few hundred files scan in
tens of milliseconds.

Optional: $MEMOIR_FREQ points at a frequency list ("word count" per line,
most-common first, e.g. the 2000 most common Chinese words). Terms above the
rank cut-off are not treated as evidence.
"""
import json
import math
import os
import re
import sys
from pathlib import Path

ROOT = Path(os.environ.get('MEMOIR_STORE') or Path.cwd() / 'memory')
SKIP = {'MEMORY.md', 'HOT-MEMORY.md'}
MIN_SCORE = 2.4
MAX_HITS = 2
COMMON_MAX_RANK = 2000

CJK = r"一-鿿"


def load_common():
    common = set()
    freq = os.environ.get('MEMOIR_FREQ')
    if not freq:
        return common
    try:
        for line in Path(freq).read_text(encoding='utf-8').splitlines():
            parts = line.split()
            if len(parts) == 2 and parts[1].isdigit() and int(parts[1]) <= COMMON_MAX_RANK:
                common.add(parts[0])
    except Exception:
        pass
    return common


COMMON = load_common()


def terms(text):
    text = text.lower()
    out = {w for w in re.findall(r'[a-z][a-z0-9_-]{2,}', text)}
    for run in re.findall(f'[{CJK}]+', text):
        out |= {run[i:i + 2] for i in range(len(run) - 1)}
    return out


def load():
    docs = {}
    for p in ROOT.rglob('*.md'):
        if p.name in SKIP or 'archive' in p.parts:
            continue
        try:
            raw = p.read_text(encoding='utf-8')
        except Exception:
            continue
        head = {}
        if raw.startswith('---'):
            fm = raw.split('---', 2)[1]
            for line in fm.splitlines():
                m = re.match(r'^(\w+):\s*(.*)$', line)
                if m:
                    head[m.group(1)] = m.group(2).strip()
        title = next((l[2:].strip() for l in raw.splitlines() if l.startswith('# ')), '')
        text = ' '.join([head.get('name', ''), head.get('description', ''),
                         head.get('tags', ''), title])
        docs[p.stem] = {'terms': terms(text), 'desc': head.get('description', '') or title,
                        'last': head.get('recency', '') or head.get('updated', '')}
    return docs


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    try:
        payload = json.loads(sys.stdin.buffer.read().decode('utf-8', 'ignore') or '{}')
    except Exception:
        return
    prompt = payload.get('prompt', '')
    if len(prompt) < 6:
        return
    docs = load()
    if not docs:
        return
    q = terms(prompt) - COMMON
    n = len(docs)
    df = {}
    for doc in docs.values():
        for t in doc['terms'] & q:
            df[t] = df.get(t, 0) + 1
    hits = []
    for name, doc in docs.items():
        s = sum(math.log((n + 1) / (df[t] + 1)) for t in doc['terms'] & q)
        if s >= MIN_SCORE:
            hits.append((s, name, doc['desc'], doc['last']))
    if not hits:
        return
    hits.sort(reverse=True)
    parts = [f'{name} | {desc[:26]} | {last}' for _, name, desc, last in hits[:MAX_HITS]]
    print('[recall] ' + ' / '.join(parts))


if __name__ == '__main__':
    main()

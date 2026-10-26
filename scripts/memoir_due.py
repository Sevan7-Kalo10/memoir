#!/usr/bin/env python3
"""Wall-clock fallback: warn when a full maintenance pass is overdue.

Runs on SessionStart. Prints nothing below the threshold, so it costs no
context. Threshold: $MEMOIR_MAINTAIN_DAYS (default 90). After running
maintain, write today's date into $MEMOIR_STORE/.memoir-last-maintain.
"""
import os
import sys
import datetime
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

STORE = os.environ.get('MEMOIR_STORE') or os.path.join(os.getcwd(), 'memory')
DAYS = int(os.environ.get('MEMOIR_MAINTAIN_DAYS', '90'))
stamp = os.path.join(STORE, '.memoir-last-maintain')

try:
    last = datetime.date.fromisoformat(open(stamp, encoding='utf-8').read().strip()[:10])
except Exception:
    print(f'⚠️ memoir: no maintenance timestamp at {stamp} -- cannot tell whether a pass is due. '
          f'Run one, then write the date there.')
    sys.exit(0)

overdue = (datetime.date.today() - last).days
if overdue >= DAYS:
    print(f'⚠️ memoir: {overdue} days since the last full maintenance (threshold {DAYS}) -- '
          f'run maintain before this session ends, then write {datetime.date.today().isoformat()} '
          f'into {stamp}.')

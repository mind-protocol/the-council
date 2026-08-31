# -*- coding: utf-8 -*-
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
p = sys.argv[1]
d = json.load(open(p, encoding='utf-8'))
tabs = d.get('tables') or d.get('tableaux') or []
for t in tabs:
    tit = t.get('titre')
    if len(sys.argv) > 2 and sys.argv[2] not in str(tit):
        continue
    cols = t.get('colonnes') or []
    print('=== TABLE', tit)
    print('   COLS:', [c if isinstance(c, str) else c.get('titre') for c in cols])
    for l in (t.get('lignes') or []):
        if isinstance(l, dict):
            vals = l.get('valeurs') or l
            items = list(vals.items()) if isinstance(vals, dict) else []
            short = ' | '.join('%s=%s' % (k, str(v)[:90]) for k, v in items[:4])
            print('  -', short)
        else:
            print('  -', str(l)[:200])

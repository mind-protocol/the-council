# -*- coding: utf-8 -*-
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

f = sys.argv[1]
b = json.load(open(f, encoding='utf-8'))
print(b.get('id'), '|', b.get('titre'))
for p in b.get('pages', []):
    print('PAGE:', p.get('titre'))
    print((p.get('texte') or '')[:1500])
    print()
for t in b.get('tables', []):
    print('###', t.get('titre'), '| cols:', t.get('colonnes'))
    for l in t.get('lignes', []):
        cel = l.get('cellules') or []
        print('  -', ' || '.join((c or '')[:110] for c in cel))
    print()

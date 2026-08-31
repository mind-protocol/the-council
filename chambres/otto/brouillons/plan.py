# -*- coding: utf-8 -*-
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

d = json.load(open('C:/Users/reyno/le-conseil2/etat/plans.json', encoding='utf-8'))
plans = d['plans']
for pl in plans:
    print('==', pl.get('id'), '|', pl.get('titre'), '| clefs:', list(pl.keys()))

cible = [p for p in plans if p.get('id') == 'couronne']
if not cible:
    raise SystemExit
p = cible[0]
for k, v in p.items():
    if isinstance(v, list):
        print('\n#####', k, '(%d)' % len(v))
        for e in v:
            if isinstance(e, dict):
                s = json.dumps(e, ensure_ascii=False)
                if 'trois mille' in s or 'Quatre bouches' in s or 'pupille' in s or 'Sombreval' in s or 'colonne du roi' in s:
                    print('  *', json.dumps(e, ensure_ascii=False)[:900])

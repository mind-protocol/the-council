# -*- coding: utf-8 -*-
# Ma mesure du 31.8 : ce qui reste apres le 3e de la 4e lune, table par table.
import json, collections, os

racine = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
etat = os.path.join(racine, "etat")

for f in ['actes.json', 'paroles.json', 'info.json', 'annales.json',
          'evenements.json', 'plis.json', 'pensees.json']:
    p = os.path.join(etat, f)
    try:
        d = json.load(open(p, encoding='utf-8'))
    except Exception as e:
        print(f, 'ILLISIBLE', e)
        continue
    if isinstance(d, dict):
        for kk, v in d.items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                d = v
                break
    apres = collections.Counter()
    prog = collections.Counter()
    for x in d:
        if not isinstance(x, dict):
            continue
        dt = x.get('date') or x.get('date_prevue') or {}
        if isinstance(dt, dict) and dt.get('lune') == 4 and (dt.get('jour') or 0) > 3:
            cible = prog if str(x.get('id', '')).startswith('prog-') else apres
            cible[dt['jour']] += 1
    print(f, '| total', len(d),
          '| joue apres le 3e:', dict(sorted(apres.items())),
          '| programme:', dict(sorted(prog.items())))

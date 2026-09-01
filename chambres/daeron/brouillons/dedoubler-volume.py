# -*- coding: utf-8 -*-
"""Le 12e au soir. Deux de mes mains ont ecrit le meme volume.
Je garde les lignes D.* (la premiere main), je jette mes doublons,
et je ne conserve de moi que les deux lignes qu'elle n'avait pas."""
import json

p = 'C:/Users/reyno/le-conseil2/chambres/daeron/books/affaire-daeron.json'
d = json.load(open(p, encoding='utf-8'))
buts = [t for t in d['tables'] if 'veux' in t['titre']][0]
act = [t for t in d['tables'] if 'Actions' in t['titre']][0]

# --- objectifs : ne garder que la premiere occurrence de chaque numero
vus = set()
gardes = []
for l in buts['lignes']:
    ref = l['cellules'][0]
    if ref in vus:
        continue
    vus.add(ref)
    gardes.append(l)
buts['lignes'] = gardes

# --- actions : mes P.11/P.12/P.13/P.15 refont D.2/D.3/D.6/D.5. Je les jette.
doublons = {"P.11", "P.12", "P.13", "P.15"}
renum = {"P.14": "D.8", "P.16": "D.9"}
gardes = []
for l in act['lignes']:
    ref = l['cellules'][0]
    if ref in doublons:
        continue
    if ref in renum:
        l['cellules'][0] = renum[ref]
    gardes.append(l)
act['lignes'] = gardes

json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

print('objectifs:', [l['cellules'][0] for l in buts['lignes']])
print('actions  :', [l['cellules'][0] for l in act['lignes']])
mauvais = [l['cellules'][0] for t in d['tables'] for l in t['lignes']
           if len(l['cellules']) != len(t['colonnes'])]
print('lignes decalees :', mauvais or 'aucune')

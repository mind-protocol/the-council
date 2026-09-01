# -*- coding: utf-8 -*-
import json, collections
p = 'books/affaire-daeron.json'
d = json.load(open(p, encoding='utf-8'))
act = [t for t in d['tables'] if 'Actions' in t['titre']][0]

lignes = act['lignes']
# les deux D.10 : celle du congé (dernière) double D.12, déjà ouverte.
idx = [i for i, l in enumerate(lignes) if l['cellules'][0] == 'D.10']
garde, double = idx[0], idx[-1]
texte_double = lignes[double]['cellules'][1]

# on verse la substance de la doublure dans la note de D.12, puis on la retire
for l in lignes:
    if l['cellules'][0] == 'D.12':
        l['cellules'][8] = (l['cellules'][8] + ' ').strip() + (
            " || REDRESSÉ le 12e au soir : cette action avait été écrite DEUX FOIS dans mon "
            "propre volume, ici sous D.12 et une seconde fois sous le numéro D.10 déjà pris "
            "(« %s »). Deux lignes pour un seul geste, et un numéro qui désignait deux choses : "
            "c'est la faute que je reproche à tout le monde depuis ce matin. Rien n'est effacé — "
            "la seconde est versée ici et la ligne retirée. Ma main, pas la machine." % texte_double)
        break
lignes.pop(double)

refs = [l['cellules'][0] for l in lignes]
dup = [r for r, n in collections.Counter(refs).items() if n > 1]
mauvais = [l['cellules'][0] for l in lignes if len(l['cellules']) != len(act['colonnes'])]
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('lignes:', len(lignes), '| doublons:', dup, '| cellules décalées:', mauvais)

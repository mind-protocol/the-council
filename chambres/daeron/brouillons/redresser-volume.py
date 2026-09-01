# -*- coding: utf-8 -*-
"""Le 12e au soir. Mon propre registre etait double : D.10 deux fois, et le conge
du 19e ecrit sur deux lignes sous deux numeros. Je fonds, je renumerote pas, je
supprime la ligne en trop, et je remets les etats aux quatre mots du volume."""
import json, collections

p = 'books/affaire-daeron.json'
d = json.load(open(p, encoding='utf-8'))
act = [t for t in d['tables'] if 'Actions' in t['titre']][0]

ETATS = {'a faire': 'à faire', 'à faire': 'à faire', 'en cours': 'en cours',
         'faite': 'faite', 'bloquee': 'bloquée', 'bloquée': 'bloquée'}

# 1. le conge : une seule ligne, D.12, qui porte les DEUX issues
for l in act['lignes']:
    c = l['cellules']
    if c[0] == 'D.12':
        c[1] = "Ouvrir le conge de Villevieille du 19e, ou faire attester qu'il n'y en a pas"
        c[2] = ("Le conge de sortie du 19e tire, copie et paraphe, date d'aujourd'hui, et pose a cote "
                "du role d'entree de la Nera. S'il n'a jamais existe, faire attester cette absence, "
                "datee du meme jour. Les deux reponses valent : un conge avec un patron donne l'ecart "
                "sans qu'aucun commis soit nomme ; aucun conge du tout, et une quille a quitte le port "
                "d'un lord sans papier, ce qui se demontre par une absence que nul ne peut remplir apres coup.")
        c[4] = "le conge copie et paraphe, ou l'attestation d'absence, l'un ou l'autre date"
        c[5] = 'en cours'
        c[6] = "14e de la 5e lune"
        c[8] = ("Porte au registre de lord Ormund le 12e au soir, du au 14e. Aucun commis ne sera convoque : "
                "un homme convoque explique, deux registres se contredisent en silence. C'est Ollo Marran qui "
                "m'a mis dessus en me croyant deja porteur de ce papier ; je ne l'avais pas.")

# 2. la ligne en trop (le second D.10, qui redisait le conge)
avant = len(act['lignes'])
act['lignes'] = [l for i, l in enumerate(act['lignes'])
                 if not (l['cellules'][0] == 'D.10' and 'conge' in l['cellules'][1].lower())]
supprimees = avant - len(act['lignes'])

# 3. les etats aux quatre mots, et le compte des cellules
for l in act['lignes']:
    c = l['cellules']
    while len(c) < len(act['colonnes']):
        c.append('')
    c[5] = ETATS.get(c[5].strip().lower(), c[5])

refs = [l['cellules'][0] for l in act['lignes']]
dup = [r for r, n in collections.Counter(refs).items() if n > 1]
mauvais = [c for c in (l['cellules'] for l in act['lignes'])
           if len(c) != len(act['colonnes']) or c[5] not in set(ETATS.values())]

json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('lignes supprimees :', supprimees)
print('doublons restants :', dup)
print('lignes mal formees :', len(mauvais))
print('total actions :', len(act['lignes']))

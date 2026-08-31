import json

p = 'C:/Users/reyno/le-conseil2/chambres/otto/books/affaire-otto.json'
d = json.load(open(p, encoding='utf-8'))
t = [x for x in d['tables'] if 'Actions' in x['titre']][0]

faits = {
    'P.1': "on me disait calculateur, patient, impitoyable, orgueilleux, et froid, mesure, ne haussant jamais le ton : lu en entier ce matin, et deux de ces mots sont dementis plus bas de ma main.",
    'P.2': "section « Ce que j'en tiens, et de ma main » dans `claude.md` : sept regles ecrites en « je ».",
    'P.4': "C.4, C.5 et C.6 poses de ma main sous « Ce que je veux », chacun avec sa preuve.",
    'P.5': "titre « ## Le 3e de la 4e lune » dans `claude.md` : deux regles neuves, chacune avec le fait qui me l'a apprise.",
    'P.6': "O.1 a O.6 sous les dix premieres : le Guet, les cinq pupilles, la colonne de roukerie, le prix de la tete, le brouillon, Accalmie.",
}

for l in t['lignes']:
    c = l['cellules']
    if c[0] in faits:
        c[4] = faits[c[0]]
        c[5] = 'faite'
        c[7] = '129.4.3'

json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for l in t['lignes']:
    print(l['cellules'][0], '->', l['cellules'][5])

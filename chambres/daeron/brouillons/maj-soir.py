# -*- coding: utf-8 -*-
import json

p = 'books/affaire-daeron.json'
d = json.load(open(p, encoding='utf-8'))
act = [t for t in d['tables'] if 'Actions' in t['titre']][0]

LIGNE = ("LIGNE MOT POUR MOT, portee par Ollo Marran le 12e : "
         "Jour dix-neuf | Coque : sans nom au role | D'ou : Villevieille | "
         "Ce qu'elle portait : non ouvert, deux hommes d'armes a bord | Pour qui : non porte. "
         "RIEN N'A ETE GRATTE, et la semaine est close sous le paraphe de l'officier du port. "
         "ETABLI AUSSI : la case est vide pour DEUX raisons a la fois — personne n'est venu y porter "
         "un nom, ET il lui a ete dit de bouche de n'y rien ecrire. Le nom de qui l'a dit est retire, "
         "et je ne le chasse pas. INCONNU CONSERVE : le capitaine et le port d'armement ne sont pas "
         "dans son livre et ne pouvaient pas y etre (ses colonnes sont quatre) ; les departs non plus. "
         "Il regardera les roles de SORTIE du 19 au 23 et me dira aussi s'il n'y trouve rien.")

for l in act['lignes']:
    c = l['cellules']
    if c[0] == 'D.5':
        c[8] = LIGNE

act['lignes'].append({"cellules": [
    "D.10",
    "Faire lever le conge du 19e, ou faire attester qu'il n'y en a pas",
    ("L'autre moitie de la paire. Port-Real tient une case VIDE ; Villevieille tient soit un nom, "
     "soit un rien. Demande a lord Ormund le 12e au soir : que le conge de sortie du dix-neuvieme "
     "soit leve, copie et paraphe DATE D'AUJOURD'HUI — et s'il n'y en a pas eu, que cette absence "
     "soit attestee, datee d'aujourd'hui, dans les memes formes. Les deux reponses valent."),
    "le port de Villevieille, par lord Ormund",
    "une copie du conge datee de ce jour, ou une attestation d'absence datee de ce jour",
    "en cours",
    "aujourd'hui, le 12e — pas demain",
    "",
    ("POURQUOI CE JOUR ET PAS UN AUTRE, et c'est Ollo qui me l'a appris : une case vide ne vaut que "
     "tant qu'elle reste vide. Il a vu DEUX FOIS cette lune une main sans office remplir de pareilles "
     "cases apres coup. Le jour ou un nom sera porte dans celle du 19, les deux papiers s'accorderont "
     "— faussement — et l'ecart sera efface par l'ecriture meme qui semblera le resoudre. Une absence "
     "constatee est la seule chose que personne ne peut remplir apres coup. Constatee avant, elle tient ; "
     "constatee apres, elle ne vaut rien.")
]})

json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('actions:', len(act['lignes']))
for l in act['lignes']:
    c = l['cellules']
    assert len(c) == len(act['colonnes']), (c[0], len(c))
    print('  ', c[0], '|', c[5])

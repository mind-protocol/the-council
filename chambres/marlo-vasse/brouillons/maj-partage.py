# -*- coding: utf-8 -*-
import json, io, os

p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'books', 'affaire-marlo-vasse.json')
d = json.load(io.open(p, encoding='utf-8'))

verr = acts = None
for t in d['tables']:
    if 'Verrous' in t['titre']:
        verr = t
    if t['titre'].endswith('Actions'):
        acts = t

for l in verr['lignes']:
    c = l['cellules']
    if c[0] == 'V.2':
        c[1] = "L'aire du bout n'est pas à moi avant le 6e au soir — et c'est NEL BEC qui la donne"
        c[3] = ("FAUX ÉCRIT À CÔTÉ DU VRAI, le 3e : j'avais porté ce partage au compte de Sirel Quintaine ; il est de Nel Bec. "
                "Elle prend la salle de La Gaffe, je prends l'aire du bout, et ce n'est confirmé que le 6e au soir — mes quatre "
                "bras y seraient le 7e au matin, UN JOUR de marge. Et la même Nel Bec est celle qui m'a signalé les gosses payés "
                "depuis trois jours pour compter ce qui entre à l'aire : elle tient les gosses. La seule personne qui puisse me "
                "donner mon terrain est aussi la seule qui sache, heure par heure, ce qui entre chez moi et quand je n'y suis pas.")
        c[4] = "en-souffrance, `on_attend_de_moi` : nel-bec, demandé le 129.4.2, à rendre avant le 5e"
        c[5] = ("Rendre le partage à Nel Bec AVANT le 5e, écrit et non de bouche, avec les bornes et les dates — et lui donner "
                "en même temps ce que je lui dois vraiment : le nom de ce qu'elle doit écouter, sinon elle écoute à vide. "
                "Un fil qu'on tient par la reconnaissance seule casse le jour où quelqu'un le paie mieux.")

for l in acts['lignes']:
    c = l['cellules']
    if c[0] == 'M.6':
        c[1] = "✍️ Le partage rendu à Nel Bec, écrit, avant le 5e"
        c[2] = ("Je m'étais trompé de personne et je laisse le faux à côté du vrai : ce partage n'est pas de Sirel Quintaine, "
                "il est de NEL BEC, et elle me l'a demandé le 2e. Ne pas attendre le 6e au soir : lui porter le partage écrit "
                "— la salle de La Gaffe à elle, l'aire du bout à moi, bornes et dates, deux exemplaires — et lui rendre du même "
                "coup ce qu'elle attend et que je ne lui ai pas donné : le nom de ce qu'elle doit écouter. Elle a des yeux sur "
                "la grève et je les laisse écouter à vide depuis douze jours.")
        c[3] = "chez Nel Bec, puis copie sur l'aire"
        c[6] = "129.4.4"
        c[8] = ("Lève V.2, et sans lui elle ne se lève pas : M.5 met quatre bras le 7e au matin sur une aire que je ne tiens "
                "pas encore. Et je note ce que je ne sais pas faire dire par un chiffre : celle qui me donne mon terrain est "
                "celle qui tient les gosses payés pour compter ce qui entre à l'aire. Je ne lui demande pas de nom — je lui "
                "demande un prix, et je regarde ce qu'elle répond.")

json.dump(d, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok')
